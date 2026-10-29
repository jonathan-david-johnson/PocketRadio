#!/usr/bin/env python3
"""
source-survey.py — Profile many audio stream URLs: transport, codec, metadata, CORS.

Connects once to each URL like a player would, reads a few KB, and prints one
JSON object per URL. It discards the audio. It does not log in, solve
challenges or get around geo-blocks.

What one record holds:
  redirect chain, final scheme, status line kind (HTTP or ICY), Content-Type,
  icy-* headers, CORS headers (GET and preflight), container and codec read from
  the first bytes, playlist type (PLS, M3U, ASX, HLS) and where it pointed,
  the first ICY StreamTitle blocks, and for HLS: segment type, target duration,
  PROGRAM-DATE-TIME, DATERANGE, encryption, ID3 in the first segment.

Usage:
    python3 tools/source-survey.py URL [URL ...]
    python3 tools/source-survey.py --input urls.txt --out results.jsonl
    python3 tools/source-survey.py --input urls.jsonl --out results.jsonl -j 40

Input: one URL per line, or JSONL objects with a "url" key. Other keys are
copied into the output under "meta".

Standard library only.
"""
import argparse, json, re, socket, ssl, struct, sys, threading, time
import urllib.parse as U
from concurrent.futures import ThreadPoolExecutor, as_completed

UA = "PocketRadio-survey/0.1 (+research; one connection per URL)"
ORIGIN = "https://app.pocketradio.example"
MAX_REDIRECTS = 6
MAX_BODY = 96 * 1024

_host_locks = {}
_host_locks_guard = threading.Lock()


def host_sem(host):
    with _host_locks_guard:
        return _host_locks.setdefault(host, threading.Semaphore(2))


class Fail(Exception):
    def __init__(self, kind, detail=""):
        super().__init__(kind)
        self.kind, self.detail = kind, detail


def open_conn(url, timeout, verify=True, extra_headers=None, method="GET"):
    """Return (sock, status_line, headers dict (lower-case), leftover bytes, info)."""
    p = U.urlparse(url)
    if p.scheme not in ("http", "https"):
        raise Fail("unsupported_scheme", p.scheme)
    host = p.hostname
    port = p.port or (443 if p.scheme == "https" else 80)
    t0 = time.time()
    try:
        raw = socket.create_connection((host, port), timeout=timeout)
    except socket.gaierror as e:
        raise Fail("dns", str(e))
    except socket.timeout:
        raise Fail("connect_timeout")
    except OSError as e:
        raise Fail("connect_error", str(e))
    t_connect = time.time() - t0
    s = raw
    tls_version = None
    if p.scheme == "https":
        ctx = ssl.create_default_context()
        if not verify:
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
        try:
            s = ctx.wrap_socket(raw, server_hostname=host)
            tls_version = s.version()
        except ssl.SSLCertVerificationError as e:
            raw.close()
            raise Fail("tls_cert", str(e))
        except (ssl.SSLError, OSError) as e:
            raw.close()
            raise Fail("tls_error", str(e))
    path = p.path or "/"
    if p.query:
        path += "?" + p.query
    hdrs = {
        "Host": p.netloc.split("@")[-1],
        "User-Agent": UA,
        "Accept": "*/*",
        "Icy-MetaData": "1",
        "Origin": ORIGIN,
        "Connection": "close",
    }
    if extra_headers:
        hdrs.update(extra_headers)
    req = f"{method} {path} HTTP/1.0\r\n" + "".join(f"{k}: {v}\r\n" for k, v in hdrs.items()) + "\r\n"
    s.settimeout(timeout)
    try:
        s.sendall(req.encode())
        buf = b""
        while b"\r\n\r\n" not in buf and b"\n\n" not in buf:
            chunk = s.recv(4096)
            if not chunk:
                break
            buf += chunk
            if len(buf) > 65536:
                break
    except socket.timeout:
        s.close()
        raise Fail("header_timeout")
    except OSError as e:
        s.close()
        raise Fail("io_error", str(e))
    t_first = time.time() - t0
    sep = buf.find(b"\r\n\r\n")
    seplen = 4
    if sep < 0:
        sep = buf.find(b"\n\n")
        seplen = 2
    if sep < 0:
        s.close()
        raise Fail("no_headers", buf[:80].decode("latin-1", "replace"))
    head = buf[:sep].decode("latin-1", "replace")
    rest = buf[sep + seplen:]
    lines = head.replace("\r", "").split("\n")
    status = lines[0]
    headers = {}
    for ln in lines[1:]:
        if ":" in ln:
            k, v = ln.split(":", 1)
            k = k.strip().lower()
            v = v.strip()
            headers[k] = headers[k] + ", " + v if k in headers else v
    info = {"connect_s": round(t_connect, 3), "ttfb_s": round(t_first, 3), "tls": tls_version}
    return s, status, headers, rest, info


def read_upto(sock, have, n, deadline):
    buf = bytearray(have)
    while len(buf) < n and time.time() < deadline:
        try:
            sock.settimeout(max(0.5, deadline - time.time()))
            chunk = sock.recv(min(16384, n - len(buf)))
        except (socket.timeout, OSError):
            break
        if not chunk:
            break
        buf += chunk
    return bytes(buf)


def status_code(status):
    m = re.match(r"(?:HTTP/\d\.\d|ICY)\s+(\d{3})", status)
    return int(m.group(1)) if m else None


MP3_BR = {  # MPEG1 layer III
    1: [0, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320],
}
MP3_BR_V2 = [0, 8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160]
MP3_SR = {3: [44100, 48000, 32000], 2: [22050, 24000, 16000], 0: [11025, 12000, 8000]}
ADTS_SR = [96000, 88200, 64000, 48000, 44100, 32000, 24000, 22050, 16000, 12000, 11025, 8000, 7350]


def sniff(data):
    """Return dict(container, codec, detail) from leading bytes."""
    d = {"container": None, "codec": None}
    if not data:
        return d
    head = data[:2048]
    ls = head.lstrip()
    if ls.startswith(b"#EXTM3U") or b"#EXT-X-" in head[:512]:
        d["container"] = "m3u8" if b"#EXT-X-" in head else "m3u"
        return d
    if ls[:10].lower() == b"[playlist]":
        d["container"] = "pls"
        return d
    if ls[:4].lower() in (b"<asx", b"<?xm") and b"asx" in head.lower():
        d["container"] = "asx"
        return d
    if ls[:1] == b"<" and (b"<html" in head.lower() or b"<!doctype" in head.lower()):
        d["container"] = "html"
        return d
    if head.startswith(b"OggS"):
        d["container"] = "ogg"
        if b"OpusHead" in head:
            d["codec"] = "opus"
        elif b"\x01vorbis" in head:
            d["codec"] = "vorbis"
        elif b"\x7fFLAC" in head:
            d["codec"] = "flac"
        return d
    if head.startswith(b"fLaC"):
        d["container"], d["codec"] = "flac", "flac"
        return d
    if head.startswith(b"RIFF") and head[8:12] == b"WAVE":
        d["container"], d["codec"] = "wav", "pcm"
        return d
    if head[4:8] == b"ftyp":
        d["container"] = "mp4"
        return d
    if head[:4] == b"\x30\x26\xb2\x75":
        d["container"], d["codec"] = "asf", "wma"
        return d
    if head[:1] == b"\x47" and len(head) > 376 and head[188] == 0x47:
        d["container"] = "mpegts"
        return d
    # skip ID3v2 tag
    off = 0
    if head.startswith(b"ID3") and len(data) > 10:
        size = (data[6] << 21) | (data[7] << 14) | (data[8] << 7) | data[9]
        off = 10 + size
        d["id3v2_at_start"] = True
    # scan up to 4 KB for a sync word
    window = data[off:off + 4096]
    for i in range(len(window) - 4):
        b0, b1 = window[i], window[i + 1]
        if b0 == 0xFF and (b1 & 0xF6) == 0xF0:  # ADTS (layer == 00)
            sr_i = (window[i + 2] >> 2) & 0xF
            prof = (window[i + 2] >> 6) & 0x3
            ch = ((window[i + 2] & 1) << 2) | (window[i + 3] >> 6)
            if sr_i < len(ADTS_SR) and 1 <= ch <= 7:
                d.update(container="adts", codec="aac", sample_rate=ADTS_SR[sr_i],
                         aac_profile=["main", "lc", "ssr", "ltp"][prof], channels=ch)
                return d
        if b0 == 0xFF and (b1 & 0xE0) == 0xE0 and (b1 & 0x06) == 0x02:  # MPEG audio layer III
            ver = (b1 >> 3) & 3
            br_i = (window[i + 2] >> 4) & 0xF
            sr_i = (window[i + 2] >> 2) & 3
            if ver != 1 and br_i not in (0, 15) and sr_i != 3:
                br = MP3_BR[1][br_i] if ver == 3 else MP3_BR_V2[br_i]
                d.update(container="mpeg-audio", codec="mp3", bitrate_kbps=br,
                         sample_rate=MP3_SR[ver][sr_i], channels=1 if (window[i + 3] >> 6) == 3 else 2)
                return d
    return d


def parse_icy_blocks(sock, rest, metaint, deadline, max_blocks=3):
    """Read audio+metadata cycles; return list of metadata strings (raw)."""
    blocks = []
    buf = bytearray(rest)
    pos = 0
    total = len(buf)
    while len(blocks) < max_blocks and time.time() < deadline:
        need = pos + metaint + 1
        while len(buf) < need and time.time() < deadline and len(buf) < MAX_BODY * 2:
            try:
                sock.settimeout(max(0.5, deadline - time.time()))
                chunk = sock.recv(16384)
            except (socket.timeout, OSError):
                chunk = b""
            if not chunk:
                return blocks
            buf += chunk
        if len(buf) < need:
            break
        n = buf[pos + metaint] * 16
        end = need + n
        while len(buf) < end and time.time() < deadline:
            try:
                sock.settimeout(max(0.5, deadline - time.time()))
                chunk = sock.recv(4096)
            except (socket.timeout, OSError):
                chunk = b""
            if not chunk:
                return blocks
            buf += chunk
        if len(buf) < end:
            break
        raw = bytes(buf[need:end]).rstrip(b"\0")
        blocks.append(raw.decode("utf-8", "replace") if raw else "")
        pos = end
    return blocks


def stream_title(block):
    m = re.search(r"StreamTitle='(.*?)';(?:\s*StreamUrl=|$|\s*\w+=)", block, re.S)
    if not m:
        m = re.search(r"StreamTitle='(.*)'", block, re.S)
    return m.group(1) if m else None


def playlist_target(kind, text):
    if kind == "pls":
        m = re.search(r"^File\d*=(\S+)", text, re.M | re.I)
        return m.group(1) if m else None
    if kind == "asx":
        m = re.search(r'href\s*=\s*"([^"]+)"', text, re.I)
        return m.group(1) if m else None
    if kind == "m3u":
        for ln in text.splitlines():
            ln = ln.strip()
            if ln and not ln.startswith("#"):
                return ln
    return None


def analyse_hls(url, text, timeout, deadline, out):
    """Fill out['hls'] from master/media playlist text. May fetch a media playlist and one segment."""
    h = out.setdefault("hls", {})
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if any(l.startswith("#EXT-X-STREAM-INF") for l in lines):
        h["master"] = True
        variants = []
        for i, l in enumerate(lines):
            if l.startswith("#EXT-X-STREAM-INF"):
                attrs = l.split(":", 1)[1]
                bw = re.search(r"BANDWIDTH=(\d+)", attrs)
                codecs = re.search(r'CODECS="([^"]+)"', attrs)
                uri = lines[i + 1] if i + 1 < len(lines) else None
                variants.append({"bandwidth": int(bw.group(1)) if bw else None,
                                 "codecs": codecs.group(1) if codecs else None, "uri": uri})
        h["variants"] = [{k: v for k, v in x.items() if k != "uri"} for x in variants]
        h["media_groups"] = sorted({m for l in lines if l.startswith("#EXT-X-MEDIA") for m in re.findall(r"TYPE=(\w+)", l)})
        first = next((v for v in variants if v["uri"]), None)
        if not first:
            return
        murl = U.urljoin(url, first["uri"])
        try:
            s, st, hd, rest, _ = open_conn(murl, timeout)
            body = read_upto(s, rest, MAX_BODY, deadline)
            s.close()
            text = body.decode("utf-8", "replace")
            url = murl
            lines = [l.strip() for l in text.splitlines() if l.strip()]
        except Fail as e:
            h["media_playlist_error"] = e.kind
            return
    h["version"] = next((int(l.split(":")[1]) for l in lines if l.startswith("#EXT-X-VERSION")), None)
    td = next((l for l in lines if l.startswith("#EXT-X-TARGETDURATION")), None)
    h["target_duration"] = int(td.split(":")[1]) if td else None
    segs = [l for l in lines if not l.startswith("#")]
    h["segments_listed"] = len(segs)
    h["endlist"] = any(l.startswith("#EXT-X-ENDLIST") for l in lines)
    h["playlist_type"] = next((l.split(":")[1] for l in lines if l.startswith("#EXT-X-PLAYLIST-TYPE")), None)
    h["program_date_time"] = any(l.startswith("#EXT-X-PROGRAM-DATE-TIME") for l in lines)
    h["daterange"] = any(l.startswith("#EXT-X-DATERANGE") for l in lines)
    dr = [l for l in lines if l.startswith("#EXT-X-DATERANGE")]
    if dr:
        h["daterange_sample"] = dr[-1][:300]
    h["discontinuity"] = any(l.startswith("#EXT-X-DISCONTINUITY") for l in lines)
    h["map_fmp4"] = any(l.startswith("#EXT-X-MAP") for l in lines)
    h["low_latency"] = any("EXT-X-PART" in l or "EXT-X-SERVER-CONTROL" in l for l in lines)
    key = next((l for l in lines if l.startswith("#EXT-X-KEY")), None)
    h["encryption"] = (re.search(r"METHOD=([\w-]+)", key).group(1) if key and re.search(r"METHOD=([\w-]+)", key) else None)
    if segs:
        path = U.urlparse(segs[0]).path.lower()
        h["segment_ext"] = path.rsplit(".", 1)[-1] if "." in path.rsplit("/", 1)[-1] else None
        surl = U.urljoin(url, segs[-1])
        try:
            s, st, hd, rest, _ = open_conn(surl, timeout, extra_headers={"Icy-MetaData": "0"})
            body = read_upto(s, rest, 48 * 1024, deadline)
            s.close()
            h["segment_status"] = status_code(st)
            h["segment_content_type"] = hd.get("content-type")
            sn = sniff(body)
            h["segment_container"] = sn.get("container")
            h["segment_codec"] = sn.get("codec")
            if sn.get("bitrate_kbps"):
                h["segment_bitrate_kbps"] = sn["bitrate_kbps"]
            ids = []
            for m in re.finditer(rb"ID3\x04\x00", body):
                ids.append(m.start())
            h["id3_tags_in_segment"] = len(ids)
            frames = sorted({f.decode() for f in re.findall(rb"(TIT2|TPE1|TALB|TXXX|PRIV|WXXX)", body)})
            h["id3_frames"] = frames
            if b"com.apple.streaming.transportStreamTimestamp" in body:
                h["id3_ts_timestamp_priv"] = True
        except Fail as e:
            h["segment_error"] = e.kind


def survey_one(url, timeout=6.0, total=15.0):
    t0 = time.time()
    deadline = t0 + total
    out = {"url": url, "ok": False, "redirects": []}
    cur = url
    depth = 0
    verify = True
    try:
        while True:
            p = U.urlparse(cur)
            sem = host_sem(p.hostname or "")
            with sem:
                try:
                    s, status, hd, rest, info = open_conn(cur, timeout, verify=verify)
                except Fail as e:
                    if e.kind in ("tls_cert", "tls_error") and verify:
                        out["tls_verify_failed"] = e.detail[:160]
                        verify = False
                        continue
                    raise
                code = status_code(status)
                out.setdefault("steps", []).append({"url": cur if len(cur) < 200 else cur[:200], "status": status[:40]})
                if code in (301, 302, 303, 307, 308) and "location" in hd:
                    s.close()
                    depth += 1
                    if depth > MAX_REDIRECTS:
                        raise Fail("too_many_redirects")
                    nxt = U.urljoin(cur, hd["location"])
                    out["redirects"].append(nxt[:200])
                    cur = nxt
                    continue
                out["final_url"] = cur
                out["final_scheme"] = p.scheme
                out["final_host"] = p.hostname
                out["status"] = code
                out["status_kind"] = "ICY" if status.startswith("ICY") else "HTTP"
                out.update(info)
                out["content_type"] = hd.get("content-type")
                out["server"] = hd.get("server")
                out["icy"] = {k: v for k, v in hd.items() if k.startswith("icy-") or k.startswith("ice-")}
                out["cors"] = {k: v for k, v in hd.items() if k.startswith("access-control-")}
                if code != 200:
                    s.close()
                    raise Fail(f"http_{code}")
                # read initial bytes
                body = read_upto(s, rest, 8192, min(deadline, time.time() + timeout))
                sn = sniff(body)
                out["container"] = sn.get("container")
                for k in ("codec", "bitrate_kbps", "sample_rate", "channels", "aac_profile", "id3v2_at_start"):
                    if k in sn:
                        out[k] = sn[k]
                kind = sn.get("container")
                ct = (out["content_type"] or "").lower()
                if kind in ("pls", "m3u", "asx"):
                    more = read_upto(s, body, 16384, min(deadline, time.time() + 3))
                    s.close()
                    out["playlist_kind"] = kind
                    tgt = playlist_target(kind, more.decode("utf-8", "replace"))
                    if not tgt:
                        raise Fail("playlist_no_target")
                    depth += 1
                    if depth > MAX_REDIRECTS:
                        raise Fail("too_many_redirects")
                    out["redirects"].append(("playlist→" + tgt)[:200])
                    cur = U.urljoin(cur, tgt)
                    continue
                if kind == "m3u8":
                    more = read_upto(s, body, MAX_BODY, min(deadline, time.time() + 4))
                    s.close()
                    out["transport"] = "hls"
                    analyse_hls(cur, more.decode("utf-8", "replace"), timeout, deadline, out)
                    out["ok"] = True
                    break
                if kind == "html":
                    s.close()
                    raise Fail("html_not_audio")
                # progressive audio
                out["transport"] = "progressive"
                metaint = hd.get("icy-metaint")
                if metaint and metaint.isdigit() and int(metaint) > 0:
                    blocks = parse_icy_blocks(s, body, int(metaint), deadline)
                    out["icy_blocks"] = [b[:300] for b in blocks]
                    out["icy_titles"] = [stream_title(b) for b in blocks]
                else:
                    more = read_upto(s, body, 24 * 1024, min(deadline, time.time() + 3))
                    # Ogg: look for Vorbis/Opus comment tags
                    if kind == "ogg":
                        tags = re.findall(rb"(TITLE|ARTIST|ALBUM)=([^\x00-\x1f]{1,120})", more)
                        out["ogg_comments"] = [f"{a.decode()}={b.decode('utf-8','replace')}" for a, b in tags[:6]]
                    if kind in (None, "mpeg-audio", "adts") and not out.get("codec"):
                        sn2 = sniff(more)
                        for k in ("container", "codec", "bitrate_kbps", "sample_rate"):
                            if sn2.get(k) and not out.get(k):
                                out[k] = sn2[k]
                s.close()
                if not out.get("container") and not out.get("codec"):
                    out["container"] = "unknown"
                out["ok"] = True
                break
    except Fail as e:
        out["fail"] = e.kind
        out["fail_detail"] = (e.detail or "")[:160]
    except Exception as e:  # keep the sweep going
        out["fail"] = "exception"
        out["fail_detail"] = f"{type(e).__name__}: {e}"[:160]
    # CORS preflight for header-bearing fetch (what a browser needs to read ICY)
    if out.get("ok") and out.get("transport") == "progressive" and out.get("final_url") and time.time() < deadline + 5:
        try:
            s, st, hd, rest, _ = open_conn(out["final_url"], 4.0, verify=verify, method="OPTIONS", extra_headers={
                "Access-Control-Request-Method": "GET", "Access-Control-Request-Headers": "icy-metadata"})
            s.close()
            out["preflight_status"] = status_code(st)
            out["preflight_allow_headers"] = hd.get("access-control-allow-headers")
            out["preflight_allow_origin"] = hd.get("access-control-allow-origin")
        except Fail as e:
            out["preflight_fail"] = e.kind
    out["elapsed_s"] = round(time.time() - t0, 2)
    return out


def load_inputs(args):
    items = []
    for u in args.urls:
        items.append({"url": u})
    if args.input:
        with open(args.input) as f:
            for ln in f:
                ln = ln.strip()
                if not ln:
                    continue
                if ln.startswith("{"):
                    items.append(json.loads(ln))
                else:
                    items.append({"url": ln})
    return items


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("urls", nargs="*")
    ap.add_argument("--input", help="file of URLs (one per line) or JSONL with a 'url' key")
    ap.add_argument("--out", help="write JSONL here (default stdout)")
    ap.add_argument("-j", "--jobs", type=int, default=24)
    ap.add_argument("--timeout", type=float, default=6.0, help="per-socket timeout, seconds")
    ap.add_argument("--total", type=float, default=15.0, help="per-URL deadline, seconds")
    args = ap.parse_args()
    items = load_inputs(args)
    if not items:
        ap.error("no URLs")
    out = open(args.out, "w") if args.out else sys.stdout
    done = 0
    with ThreadPoolExecutor(max_workers=args.jobs) as ex:
        futs = {ex.submit(survey_one, it["url"], args.timeout, args.total): it for it in items}
        for fu in as_completed(futs):
            it = futs[fu]
            rec = fu.result()
            meta = {k: v for k, v in it.items() if k != "url"}
            if meta:
                rec["meta"] = meta
            out.write(json.dumps(rec, ensure_ascii=False) + "\n")
            out.flush()
            done += 1
            if args.out and done % 50 == 0:
                print(f"{done}/{len(items)}", file=sys.stderr)
    if args.out:
        out.close()


if __name__ == "__main__":
    main()
