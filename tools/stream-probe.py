#!/usr/bin/env python3
"""
stream-probe.py — Diagnose a radio stream: ICY metadata vs tracklist API sync.

Polls both sources on separate threads and prints a live log so you can see
lag, stalls, and divergence between what the stream says and what the station's
"now playing" API says.

Known findings (as of 2026-06-03):
  KCRW  — ICY StreamTitle is permanently empty. App is 100% dependent on the
           tracklist API. When that stalls, there is no fallback.
  KEXP  — ICY carries an Adswizz pre-roll blob for ~14s then fires the real
           track as "Song - Artist - Album". ICY does work for KEXP.

Usage:
    python3 tools/stream-probe.py kcrw
    python3 tools/stream-probe.py kexp
    python3 tools/stream-probe.py <stream-url> [<tracklist-url>]

Options:
    --poll N        Tracklist poll interval in seconds (default: 10)
    --icy-only      Only monitor ICY stream (no tracklist)
    --api-only      Only poll tracklist API (no stream connection)
    --stale-warn N  Warn if tracklist top entry is older than N minutes (default: 15)

Output tags:
    [HH:MM:SS  ICY ]  StreamTitle from embedded ICY metadata
    [HH:MM:SS  API ]  Now-playing from the station's tracklist API
    [HH:MM:SS  STALE] API entry is suspiciously old (possible server-side stall)
    [HH:MM:SS  DIFF]  ICY and API disagree

Ctrl-C to stop.
"""

import sys
import re
import json
import time
import threading
import urllib.request
import urllib.error
import ssl
import argparse
from datetime import datetime, timezone, timedelta

# ── Known stations ────────────────────────────────────────────────────────────

STATIONS = {
    "kcrw": {
        "name": "KCRW Eclectic 24",
        "stream_url": "https://streams.kcrw.com/e24_mp3",
        "tracklist_url": "https://tracklist-api.kcrw.com/Music/all/1?page_size=10",
        "tracklist_parser": "kcrw",
        # ICY StreamTitle is permanently '' on this stream — confirmed 2026-06-03.
        # All track info must come from the tracklist API.
        "icy_dead": True,
    },
    "kexp": {
        "name": "KEXP",
        "stream_url": "https://kexp.streamguys1.com/kexp160.aac",
        "tracklist_url": "https://api.kexp.org/v2/plays/?limit=10",
        "tracklist_parser": "kexp",
        # ICY fires after Adswizz pre-roll (~14s). Format: "Song - Artist - Album".
        "icy_dead": False,
    },
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def ts():
    return datetime.now().strftime("%H:%M:%S")

def log(source, msg):
    label = f"[{ts()}  {source:<5}]"
    for i, line in enumerate(str(msg).splitlines()):
        if i == 0:
            print(f"{label} {line}", flush=True)
        else:
            print(f"{'':16} {line}", flush=True)

def parse_iso(s: str):
    """Parse ISO 8601 string to aware datetime, return None on failure."""
    if not s:
        return None
    try:
        # Python 3.7+ fromisoformat doesn't handle trailing Z
        s = s.replace("Z", "+00:00")
        return datetime.fromisoformat(s)
    except Exception:
        return None

def age_str(dt) -> str:
    """Human-readable age of a datetime relative to now."""
    if dt is None:
        return "unknown age"
    now = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    delta = now - dt
    secs = int(delta.total_seconds())
    if secs < 0:
        return "future?"
    if secs < 60:
        return f"{secs}s ago"
    if secs < 3600:
        return f"{secs//60}m ago"
    return f"{secs//3600}h {(secs%3600)//60}m ago"

# ── ICY stream reader ─────────────────────────────────────────────────────────

def read_icy_title(stream_url: str, icy_dead: bool, callback, stop_event: threading.Event):
    """
    Connect with Icy-MetaData: 1, read embedded metadata blocks.
    Skips Adswizz ad-preroll blocks (adw_ad=true, empty StreamTitle).
    Calls callback(title: str, raw_meta: str) on each new non-empty real title.
    """
    headers = {
        "Icy-MetaData": "1",
        "User-Agent": "PocketRadio-StreamProbe/1.0",
        "Accept": "*/*",
    }
    req = urllib.request.Request(stream_url, headers=headers)

    log("ICY", f"Connecting to {stream_url}")
    if icy_dead:
        log("ICY", "NOTE: this station is known to send empty ICY — monitoring anyway")

    try:
        ctx = ssl.create_default_context()
        resp = urllib.request.urlopen(req, context=ctx, timeout=30)
    except Exception as e:
        log("ICY", f"Connection failed: {e}")
        return

    # Print ICY response headers
    icy_headers = [(k, v) for k, v in resp.headers.items()
                   if k.lower().startswith("icy") or k.lower() in ("server", "content-type")]
    log("ICY", "Stream headers:")
    for k, v in icy_headers:
        log("ICY", f"  {k}: {v}")

    metaint_str = resp.headers.get("icy-metaint")
    if not metaint_str:
        log("ICY", "WARNING: no icy-metaint header — stream has no embedded metadata")
        log("ICY", "First 256 bytes (hex):")
        chunk = resp.read(256)
        hex_dump(chunk)
        return

    metaint = int(metaint_str)
    log("ICY", f"icy-metaint = {metaint}  ({metaint * 8 / 1000:.1f}ms @ stream bitrate)")

    last_title = None
    empty_run = 0
    EMPTY_WARN = 50  # warn after this many consecutive empty/blank blocks

    while not stop_event.is_set():
        try:
            # Read metaint audio bytes (discard)
            audio = b""
            while len(audio) < metaint and not stop_event.is_set():
                chunk = resp.read(min(8192, metaint - len(audio)))
                if not chunk:
                    log("ICY", "Stream closed by server")
                    return
                audio += chunk

            # 1-byte length indicator
            len_byte = resp.read(1)
            if not len_byte:
                log("ICY", "Stream closed reading meta length")
                return
            meta_len = len_byte[0] * 16

            if meta_len == 0:
                empty_run += 1
                if empty_run == EMPTY_WARN:
                    log("ICY", f"WARNING: {EMPTY_WARN} consecutive empty metadata blocks — ICY title likely dead on this stream")
                continue

            meta_bytes = resp.read(meta_len)
            raw = meta_bytes.rstrip(b"\x00").decode("utf-8", errors="replace")
            empty_run = 0

            title = parse_stream_title(raw)

            # Skip Adswizz ad-preroll blocks (empty StreamTitle + adw_ad=true)
            is_ad = "adw_ad='true'" in raw or 'adw_ad="true"' in raw
            if is_ad and not title:
                ad_dur = re.search(r"durationMilliseconds='(\d+)'", raw)
                dur_s = f" ({int(ad_dur.group(1))//1000}s)" if ad_dur else ""
                log("ICY", f"[AD pre-roll{dur_s}] — skipping until music title appears")
                continue

            if title != last_title:
                last_title = title
                callback(title or "(empty)", raw)

        except Exception as e:
            if not stop_event.is_set():
                log("ICY", f"Read error: {e}")
            return


def parse_stream_title(raw_meta: str) -> str:
    m = re.search(r"StreamTitle='([^']*)'", raw_meta)
    if m:
        return m.group(1).strip()
    m = re.search(r'StreamTitle="([^"]*)"', raw_meta)
    if m:
        return m.group(1).strip()
    return ""


def hex_dump(data: bytes):
    for i in range(0, min(len(data), 256), 16):
        chunk = data[i:i+16]
        hex_part = " ".join(f"{b:02x}" for b in chunk)
        asc_part = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        print(f"  {i:04x}  {hex_part:<48}  {asc_part}")


# ── Tracklist API pollers ─────────────────────────────────────────────────────

def parse_kcrw(data) -> tuple:
    """(display_str, airdate_str, full_entry)"""
    entries = data if isinstance(data, list) else []
    for entry in entries:
        artist = (entry.get("artist") or "").strip()
        title  = (entry.get("title") or "").strip()
        if artist and artist != "[BREAK]":
            display = f"{artist} — {title}" if title else artist
            airdate = entry.get("datetime") or entry.get("airdate") or ""
            return display, airdate, entry
    return "(no track found)", "", {}


def parse_kexp(data) -> tuple:
    """(display_str, airdate_str, full_entry)"""
    results = data.get("results", [])
    for entry in results:
        if entry.get("play_type") == "trackplay":
            artist = (entry.get("artist") or "").strip()
            song   = (entry.get("song") or "").strip()
            display = f"{artist} — {song}" if artist else song
            airdate = entry.get("airdate") or entry.get("air_date") or ""
            return display, airdate, entry
    return "(no trackplay found)", "", {}


PARSERS = {
    "kcrw": parse_kcrw,
    "kexp": parse_kexp,
}


def poll_tracklist(tracklist_url: str, parser_name: str, poll_interval: int,
                   stale_warn_minutes: int, callback, stale_callback,
                   stop_event: threading.Event):
    """
    Poll tracklist API every poll_interval seconds.
    Calls callback(title, airdate_str, entry) on title change.
    Calls stale_callback(age_minutes, title) when top entry is older than stale_warn_minutes.
    """
    parser = PARSERS.get(parser_name)
    if not parser:
        log("API", f"No parser for '{parser_name}' — dumping raw JSON")
        def parser(data):
            return json.dumps(data)[:120], "", data

    log("API", f"Polling every {poll_interval}s  (stale warn > {stale_warn_minutes}min)")
    last_title = None
    last_stale_warn = None

    while not stop_event.is_set():
        try:
            req = urllib.request.Request(
                tracklist_url,
                headers={"User-Agent": "PocketRadio-StreamProbe/1.0"},
            )
            ctx = ssl.create_default_context()
            with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
                raw = resp.read().decode("utf-8")
            data = json.loads(raw)
            title, airdate_str, entry = parser(data)

            # Staleness check
            airdate_dt = parse_iso(airdate_str)
            if airdate_dt:
                now = datetime.now(timezone.utc)
                if airdate_dt.tzinfo is None:
                    airdate_dt = airdate_dt.replace(tzinfo=timezone.utc)
                age_min = (now - airdate_dt).total_seconds() / 60
                if age_min > stale_warn_minutes:
                    # Rate-limit stale warnings to once per 5 min
                    if last_stale_warn is None or time.time() - last_stale_warn > 300:
                        last_stale_warn = time.time()
                        stale_callback(age_min, title)

            if title != last_title:
                last_title = title
                callback(title, airdate_str, entry)

        except Exception as e:
            log("API", f"Fetch error: {e}")

        stop_event.wait(poll_interval)


# ── Sync comparison ───────────────────────────────────────────────────────────

class SyncState:
    def __init__(self):
        self._lock = threading.Lock()
        self.icy_title = None
        self.api_title = None
        self.icy_time = None
        self.api_time = None

    def update_icy(self, title):
        with self._lock:
            self.icy_title = title
            self.icy_time = time.time()
        self._check()

    def update_api(self, title):
        with self._lock:
            self.api_title = title
            self.api_time = time.time()
        self._check()

    def _check(self):
        with self._lock:
            icy, api = self.icy_title, self.api_title
            icy_t, api_t = self.icy_time, self.api_time
        if icy is None or api is None:
            return

        # Normalize: KEXP ICY format is "Song - Artist - Album"; API is "Artist — Song"
        # We can't do a perfect match without parsing, so do substring containment check
        icy_lower = icy.lower()
        api_lower = api.lower()
        # Extract first token from each (usually song title or artist)
        icy_first = icy_lower.split(" - ")[0].strip()
        api_first = api_lower.split("—")[0].strip()  # API is "Artist — Song"
        api_second = api_lower.split("—")[-1].strip() if "—" in api_lower else ""

        in_sync = (
            icy_first in api_lower
            or api_first in icy_lower
            or (api_second and api_second in icy_lower)
        )
        if not in_sync:
            lag = abs((icy_t or 0) - (api_t or 0))
            log("DIFF", f"MISMATCH (updates {lag:.0f}s apart):")
            log("DIFF", f"  ICY: {icy}")
            log("DIFF", f"  API: {api}")


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("target", help="'kcrw', 'kexp', or a stream URL")
    ap.add_argument("tracklist_url", nargs="?",
                    help="Tracklist API URL (required for custom URLs)")
    ap.add_argument("--poll", type=int, default=10,
                    help="Tracklist poll interval seconds (default: 10)")
    ap.add_argument("--icy-only", action="store_true")
    ap.add_argument("--api-only", action="store_true")
    ap.add_argument("--stale-warn", type=int, default=15,
                    help="Warn if top tracklist entry older than N minutes (default: 15)")
    ap.add_argument("--tracklist-parser", default=None,
                    help="Force parser: 'kcrw' or 'kexp'")
    args = ap.parse_args()

    if args.target.lower() in STATIONS:
        cfg = STATIONS[args.target.lower()]
        stream_url    = cfg["stream_url"]
        tracklist_url = cfg["tracklist_url"]
        parser_name   = cfg["tracklist_parser"]
        icy_dead      = cfg.get("icy_dead", False)
        print(f"\n=== stream-probe: {cfg['name']} ===")
    else:
        stream_url    = args.target
        tracklist_url = args.tracklist_url
        parser_name   = args.tracklist_parser or "unknown"
        icy_dead      = False
        print(f"\n=== stream-probe: {stream_url} ===")

    if not args.icy_only and not tracklist_url:
        print("ERROR: provide a tracklist URL or use --icy-only")
        sys.exit(1)

    print(f"Stream:    {stream_url}")
    if tracklist_url:
        print(f"Tracklist: {tracklist_url}  (poll {args.poll}s, stale>{args.stale_warn}min)")
    print("-" * 70)

    stop = threading.Event()
    state = SyncState()

    if not args.api_only:
        def on_icy(title, raw_meta):
            log("ICY", title if title else "(empty)")
            if not args.icy_only and title:
                state.update_icy(title)

        threading.Thread(
            target=read_icy_title,
            args=(stream_url, icy_dead, on_icy, stop),
            daemon=True,
        ).start()

    if not args.icy_only and tracklist_url:
        def on_api(title, airdate_str, entry):
            age = age_str(parse_iso(airdate_str)) if airdate_str else ""
            log("API", f"{title}  [{age}]" if age else title)
            state.update_api(title)

        def on_stale(age_min, title):
            log("STALE", f"Top entry is {age_min:.0f}min old: {title}")
            log("STALE", "Tracklist API may be stalled server-side (known KCRW issue)")

        threading.Thread(
            target=poll_tracklist,
            args=(tracklist_url, parser_name, args.poll, args.stale_warn,
                  on_api, on_stale, stop),
            daemon=True,
        ).start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n--- stopped ---")
        stop.set()


if __name__ == "__main__":
    main()
