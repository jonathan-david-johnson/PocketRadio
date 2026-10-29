"""Prototype now-playing adapters. Each adapter returns a normalized dict or None.

Normalized fields:
  kind        song | show | ad | station_id | placeholder | unknown
  title, artist, album, artwork
  started_at  epoch seconds (UTC) or None
  duration    seconds or None
  show        programme/show name or None
  source      adapter id
"""
import html, json, re, time, urllib.request, urllib.parse as U
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

UA = "PocketRadio-survey/0.1 (+research)"


def http(url, timeout=10, n=400000, headers=None):
    req = urllib.request.Request(url, headers={"User-Agent": UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read(n).decode("utf-8", "replace")


def jget(url, **kw):
    kw.setdefault("n", 4_000_000)
    return json.loads(http(url, **kw))


def iso(s, tz=None):
    """Parse many ISO-ish formats. Naive strings use tz (a ZoneInfo) or UTC."""
    s = s.strip().replace("Z", "+00:00")
    s = re.sub(r"\.(\d+)", lambda m: "." + (m.group(1) + "000000")[:6], s)  # normalise fraction
    m = re.match(r"(.*[+-]\d\d)(\d\d)$", s)  # +0100 -> +01:00
    if m and re.search(r"\d[T ]\d", s):
        s = m.group(1) + ":" + m.group(2)
    d = datetime.fromisoformat(s)
    if d.tzinfo is None:
        d = d.replace(tzinfo=tz or timezone.utc)
    return d.timestamp()


HTML_LEAK = re.compile(r"<!doctype|<html|<head|</?body", re.I)
AD_PAT = re.compile(r'spot block|text="spot|adContext|adw_ad|\badvert(isement)?\b|\bad break\b', re.I)
STRUCTURAL = re.compile(
    r"\{[a-z_]+\}"                                   # unfilled template token
    r"|\.(mp3|wav|flac|m4a|aac)\s*$"                  # file name
    r"|(^|[\s_-])XYZ_ID\d*|_ID\d+\b"                   # automation slate ids
    r"|^\s*-*\s*$", re.I)                             # empty-ish
PHRASE = re.compile(
    r"probl[eè]me technique|technical difficult|this station will continue|^searching\W*$|^unknown( artist| title)?$"
    r"|^live$|^on air$|^station id\b|station identification|^jingle[\s_-]*\d*$", re.I)


PHRASE_ARTIST = re.compile(r"probl[eè]me technique|technical difficult|this station will continue", re.I)


def classify(title, artist, default="song"):
    tt = (title or "").strip(); aa = (artist or "").strip()
    if not tt:
        return "unknown"
    t = f"{aa} - {tt}"
    if AD_PAT.search(t):
        return "ad"
    if HTML_LEAK.search(t):
        return "placeholder"
    if aa.lower() == "unknown artist" or STRUCTURAL.search(tt) or (aa and STRUCTURAL.search(aa)):
        return "placeholder"
    # bare phrases count only when they are the whole title (no artist) or the whole artist
    if (not aa and PHRASE.search(tt)) or (aa and PHRASE_ARTIST.search(aa)):
        return "placeholder"
    return default


def mk(source, title, artist=None, album=None, artwork=None, started_at=None, duration=None, show=None, kind=None, extra=None):
    title = html.unescape((title or "")).strip() or None
    artist = html.unescape((artist or "")).strip() or None
    return {"source": source, "kind": kind or classify(title, artist), "title": title, "artist": artist,
            "album": (album or None), "artwork": artwork or None, "started_at": started_at,
            "duration": duration, "show": show, "extra": extra or {}}


# ---- station-own APIs ----
def somafm(cfg):
    j = jget(f"https://somafm.com/songs/{cfg['channel']}.json")["songs"][0]
    return mk("somafm", j["title"], j["artist"], j.get("album"), j.get("albumArt"), float(j["date"]))


def radioparadise(cfg):
    j = jget("https://api.radioparadise.com/api/now_playing")
    return mk("radioparadise", j["title"], j["artist"], j.get("album"), j.get("cover"))


def kexp(cfg):
    r = jget("https://api.kexp.org/v2/plays/?limit=1")["results"][0]
    if r.get("play_type") != "trackplay":
        return mk("kexp", None, kind="station_id", started_at=iso(r["airdate"]))
    return mk("kexp", r["song"], r["artist"], r.get("album"), r.get("image_uri"), iso(r["airdate"]))


def kcrw(cfg):
    r = jget("https://tracklist-api.kcrw.com/Music/all/1?page_size=1")[0]
    return mk("kcrw", r["title"], r["artist"], r.get("album"), r.get("albumImage"), iso(r["datetime"]) if r.get("datetime") else None,
              show=r.get("program_title"))


def nts(cfg):
    j = jget("https://www.nts.live/api/v2/live")["results"][cfg.get("ch", 0)]["now"]
    return mk("nts", j["broadcast_title"], kind="show", started_at=iso(j["start_timestamp"]),
              show=j["broadcast_title"])


# ---- hosting platforms ----
def azuracast(cfg):
    api = cfg["api"]
    if cfg.get("shortcode") and api.rstrip("/").endswith("/api/nowplaying"):
        api = api.rstrip("/") + "/" + cfg["shortcode"]  # per-station endpoint: the list endpoint can exceed 400 KB
    j = jget(api)
    if isinstance(j, list):
        j = next((s for s in j if s["station"]["shortcode"] == cfg.get("shortcode")), j[0])
    np_ = j["now_playing"]; s = np_["song"]
    return mk("azuracast", s.get("title") or s.get("text"), s.get("artist"), s.get("album"), s.get("art"),
              float(np_["played_at"]), np_.get("duration"), extra={"elapsed": np_.get("elapsed"), "live": j["live"]["is_live"]})


def laut(cfg):
    j = jget(f"https://api.laut.fm/station/{cfg['name']}/current_song")
    return mk("laut.fm", j.get("title"), (j.get("artist") or {}).get("name"), j.get("album"), None,
              iso(j["started_at"]) if j.get("started_at") else None, j.get("length"))


def radioco(cfg):
    j = jget(f"https://public.radio.co/stations/{cfg['sid']}/status")["current_track"]
    return mk("radio.co", j["title"], None, None, j.get("artwork_url_large"), iso(j["start_time"]) if j.get("start_time") else None,
              extra={"combined": True})


def triton(cfg):
    x = http(f"https://np.tritondigital.com/public/nowplaying?mountName={cfg['mount']}&numberToFetch=1&eventType=track")
    props = dict(re.findall(r'<property name="(\w+)"><!\[CDATA\[(.*?)\]\]>', x))
    if not props:
        return None
    st = int(props["cue_time_start"]) / 1000 if props.get("cue_time_start") else None
    dur = int(props["cue_time_duration"]) / 1000 if props.get("cue_time_duration") else None
    return mk("triton", props.get("cue_title"), props.get("track_artist_name"), props.get("track_album_name"), None, st, dur)


def radiojar(cfg):
    j = jget(f"https://www.radiojar.com/api/stations/{cfg['id']}/now_playing/")
    return mk("radiojar", j.get("title"), j.get("artist"), j.get("album"), j.get("thumb"), duration=float(j["duration"]) if j.get("duration") else None)


def live365(cfg):
    j = jget(f"https://api.live365.com/station/{cfg['mount']}")["current-track"]
    return mk("live365", j["title"], j.get("artist"), None, j.get("art"), iso(j["start"]), j.get("duration"))


def iheart(cfg):
    body = http(f"https://us.api.iheart.com/api/v3/live-meta/stream/{cfg['id']}/currentTrackMeta")
    if not body.strip():
        return None
    j = json.loads(body)
    return mk("iheart", j["title"], j.get("artist"), j.get("album"), j.get("imagePath"), j["startTime"] / 1000,
              j.get("trackDuration"))


def radioking(cfg):
    j = jget(f"https://api.radioking.io/widgets/api/v1/radio/{cfg['id']}/track/current")
    return mk("radioking", j["title"], j.get("artist"), j.get("album"), j.get("cover"), iso(j["started_at"]), j.get("duration"))


def airtime(cfg):
    j = jget(f"https://{cfg['host']}/api/live-info-v2")
    tz = ZoneInfo(j["station"]["timezone"])
    c = j["tracks"]["current"]
    if not c:
        return None
    md = c.get("metadata") or {}
    return mk("airtime", md.get("track_title") or c["name"], md.get("artist_name"), md.get("album_title"), None, iso(c["starts"], tz),
              iso(c["ends"], tz) - iso(c["starts"], tz))


def icecast(cfg):
    j = json.loads(http(f"{cfg['origin']}/status-json.xsl", n=300000))["icestats"]
    src = j.get("source")
    src = [src] if isinstance(src, dict) else (src or [])
    m = next((s for s in src if cfg["path"] in (s.get("listenurl") or "")), src[0] if src else None)
    if not m:
        return None
    t = m.get("title") or m.get("yp_currently_playing")
    return mk("icecast", t, m.get("artist"), extra={"combined": " - " in (t or "") and not m.get("artist")})


def shoutcast(cfg):
    x = http(f"{cfg['origin']}/7.html", n=4000)
    m = re.search(r"<body>(.*?)</body>", x, re.S)
    parts = m.group(1).split(",", 6)
    return mk("shoutcast", parts[6] if len(parts) > 6 else None, extra={"combined": True})


# ---- other broadcaster APIs ----
def npr_composer(cfg):
    j = jget(f"https://api.composer.nprstations.org/v1/widget/{cfg['ucs']}/now?format=json")["onNow"]
    s = j.get("song")
    if not s:
        st_, en_ = iso(j["start_utc"]), iso(j["end_utc"])
        return mk("npr_composer", j["program"]["name"], kind="show", show=j["program"]["name"], started_at=st_, duration=en_ - st_)
    st = datetime.strptime(s["_start_time"], "%m-%d-%Y %H:%M:%S")
    st = st.replace(tzinfo=ZoneInfo(cfg.get("tz", "America/Chicago"))).timestamp()
    return mk("npr_composer", s["trackName"], s["artistName"], s.get("collectionName"), None, st, s.get("_duration", 0) / 1000 or None, show=j["program"]["name"])


def sr(cfg):
    j = jget(f"https://api.sr.se/api/v2/playlists/rightnow?channelid={cfg['channel']}&format=json")["playlist"].get("song")
    if not j:
        return None
    ms = lambda v: int(re.search(r"\d+", v).group()) / 1000
    return mk("sverigesradio", j["title"], j["artist"], j.get("albumname"), None, ms(j["starttimeutc"]), ms(j["stoptimeutc"]) - ms(j["starttimeutc"]))


def abc(cfg):
    i = jget(f"https://music.abcradio.net.au/api/v1/plays/search.json?station={cfg['station']}&limit=1")["items"][0]
    rec = i["recording"]
    art = None
    try:
        art = rec["releases"][0]["artwork"][0]["url"]
    except Exception:
        pass
    return mk("abc", rec["title"], ", ".join(a["name"] for a in rec["artists"]), (rec["releases"] or [{}])[0].get("title"), art,
              iso(i["played_time"]), rec.get("duration"))


def radiofrance(cfg):
    j = jget(f"https://api.radiofrance.fr/livemeta/pull/{cfg['id']}")
    now = time.time()
    cur = [s for s in j["steps"].values() if s["start"] <= now < s["end"] and s.get("embedType") == "song"]
    if not cur:
        return None
    s = cur[-1]
    return mk("radiofrance", s["title"], s.get("authors") or s.get("performers"), s.get("titreAlbum"), s.get("visual"), s["start"], s["end"] - s["start"])


def npo(cfg):
    j = jget("https://www.nporadio2.nl/api/tracks")["data"]
    tz = ZoneInfo("Europe/Amsterdam")
    now = time.time()
    for t in j:
        a, b = iso(t["startdatetime"], tz), iso(t["enddatetime"], tz)
        if a <= now < b:
            return mk("npo", re.sub(r"^#\d+:\s*", "", t["title"]), t["artist"], None, t.get("image_url_400x400"), a, b - a)
    return None


def tunein(cfg):
    j = jget(f"https://opml.radiotime.com/Describe.ashx?id={cfg['id']}&render=json")["body"][0]
    if not j.get("current_song"):
        return None
    return mk("tunein", j["current_song"], j.get("current_artist"), j.get("current_album"), j.get("current_album_art"))


ADAPTERS = {k: v for k, v in globals().items() if callable(v) and k in (
    "somafm radioparadise kexp kcrw nts azuracast laut radioco triton radiojar live365 iheart radioking airtime icecast "
    "shoutcast npr_composer sr abc radiofrance npo tunein").split()}


def split_combined(np_):
    """For feeds that give one 'Artist - Title' string, split it."""
    if np_ and np_["extra"].get("combined") and np_["title"] and " - " in np_["title"] and not np_["artist"]:
        a, t = np_["title"].split(" - ", 1)
        np_["artist"], np_["title"] = a.strip(), t.strip()
        np_["kind"] = classify(np_["title"], np_["artist"])
    return np_


def stale(np_, now=None, grace=60):
    """True when the feed's newest item has ended (or is implausibly old)."""
    now = now or time.time()
    if not np_ or not np_.get("started_at"):
        return None
    end = np_["started_at"] + (np_["duration"] or 900)
    return now > end + grace


STAR_FORMAT = re.compile(r"^Song\*(?P<title>[^*]+)\*(?P<artist>[^*]*)\*")


def split_star(np_):
    """Automation format 'Song*TITLE*ARTIST*YEAR*ID' -> title/artist."""
    if np_ and np_["title"]:
        m = STAR_FORMAT.match(np_["title"])
        if m:
            np_["title"], np_["artist"] = m.group("title").strip(), (m.group("artist").strip() or None)
            np_["kind"] = classify(np_["title"], np_["artist"])
    return np_


AUTOMATION = re.compile(r'^(?P<artist>.*?)\s+-\s+text="(?P<text>[^"]*)"(?P<rest>.*)$', re.S)


def icy(cfg):
    """Parse one raw ICY metadata block (the text after the length byte)."""
    m = re.search(r"StreamTitle='(.*?)';(?:\s*StreamUrl=|$|\s*\w+=)", cfg["block"], re.S) or re.search(r"StreamTitle='(.*)'", cfg["block"], re.S)
    t = m.group(1) if m else ""
    if not t.strip():
        return None
    a = AUTOMATION.match(t)
    if a:  # automation attributes, e.g. iHeart: Artist - text="Title" song_spot="M" ... amgArtworkURL="..." length="00:03:23"
        attrs = dict(re.findall(r'(\w+)="([^"]*)"', a.group("rest")))
        text, artist = a.group("text"), a.group("artist").strip(" -") or None
        dur = None
        if re.match(r"^\d\d:\d\d:\d\d$", attrs.get("length", "")):
            h, mi, se = map(int, attrs["length"].split(":")); dur = h * 3600 + mi * 60 + se or None
        kind = "ad" if AD_PAT.search(text) else ("song" if attrs.get("song_spot") == "M" else "station_id")
        if kind == "song":
            kind = classify(text, artist)
        return mk("icy", text, artist, None, attrs.get("amgArtworkURL") or None, None, dur, kind=kind)
    name = (cfg.get("station_name") or "").strip().lower()
    if name and (t.strip().lower() == name or t.strip().lower() in name):
        return mk("icy", t, kind="station_id", extra={"combined": True})
    return mk("icy", t, extra={"combined": True})


ADAPTERS["icy"] = icy


def to_record(np_, now, station_id, channel="api", adapter=None):
    """Reference normalizer: adapter output -> contract record. now = epoch seconds."""
    from datetime import datetime, timezone
    iso_ = lambda e: datetime.fromtimestamp(e, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    rec = {"stationId": station_id, "status": "unavailable", "item": None, "show": None,
           "provenance": {"adapter": adapter, "channel": channel, "observedAt": iso_(now), "timing": "none"},
           "pollAfterSec": 10}
    if np_ is None:
        rec["status"] = "between"; return rec
    np_ = split_combined(np_); np_ = split_star(np_)
    rec["provenance"]["timing"] = "stamped" if np_.get("started_at") else "observed"
    if np_["show"]:
        rec["show"] = {"title": np_["show"]}
    if np_["kind"] in ("ad", "station_id", "placeholder", "unknown"):
        rec["status"] = "between"; rec["provenance"]["suppressed"] = np_["kind"]; return rec
    ends = (np_["started_at"] + np_["duration"]) if (np_.get("started_at") and np_.get("duration")) else None
    item = {"kind": np_["kind"], "title": np_["title"], "artist": np_["artist"], "album": np_["album"],
            "artworkUrl": ("https://" + np_["artwork"][7:]) if (np_["artwork"] or "").startswith("http://") else np_["artwork"],
            "startedAt": iso_(np_["started_at"]) if np_.get("started_at") else None,
            "durationSec": round(np_["duration"]) if np_.get("duration") else None,
            "endsAt": iso_(ends) if ends else None}
    if np_["kind"] == "show":
        item["artist"] = None
    status = "playing"
    if ends and now > ends + 60:
        status = "between" if now <= ends + 900 else "stale"
    elif not ends and np_["kind"] != "show" and np_.get("started_at") and now > np_["started_at"] + 900:
        status = "stale"
    rec["status"] = status
    rec["item"] = item if status == "playing" else None
    if status != "playing":
        rec["provenance"]["suppressed"] = "ended" if status == "between" else "stale"
        rec["pollAfterSec"] = 10 if status == "between" else 30
    return rec
