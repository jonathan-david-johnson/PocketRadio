#!/usr/bin/env python3
"""Reads the iOS app's debug log and lines up, song by song, what each source of timing says.

The aligned session writes three kinds of lines (see StreamTrace in the iOS app):

  [trace] meta ...   a timed metadata item the stream delivered (ICY StreamTitle, ID3, ad markers), with the stream
                     date it arrived at (program=) and the wall time
  [trace] feed ...   the feed's first poll, and each new row with how long after its stamp the feed first listed it
  [anchor] heard=... a ShazamKit anchor, with the moment the song began in the stream (start=) and the feed's stamp

For each song with an anchor it prints, relative to the song's measured start in the stream:

  stamp    the feed's stamp          (positive: the stamp is later than the song really started)
  listed   when the feed listed it   (how long the feed lags the audio)
  icy      when the stream's own title for it arrived (how long the stream's titles lag the audio)

Use it on any stream the app aligns, to see which source can be trusted before choosing how to align it.

    python3 tools/stream-timeline.py path/to/debug_log [--all]
"""
import re
import sys
from datetime import datetime, timezone
from statistics import median


def parse_time(text):
    if not text or text == "nil":
        return None
    return datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(timezone.utc)


def fields(line):
    out = {}
    for key, quoted, bare in re.findall(r'(\w+)=(?:"([^"]*)"|(\S+))', line):
        out[key] = quoted if quoted != "" or bare == "" else bare
    return out


def norm(text):
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def main(argv):
    show_all = "--all" in argv
    paths = [a for a in argv[1:] if not a.startswith("--")]
    if not paths:
        print(__doc__)
        return 1
    anchors, metas, feeds, firsts = [], [], [], []
    for path in paths:
        for line in open(path, errors="replace"):
            if "[anchor] heard=" in line and " start=" in line and "start=nil" not in line:
                f = fields(line)
                heard = re.search(r'heard="(.*?) — (.*?)" ', line)
                if heard and f.get("start"):
                    anchors.append((heard.group(1), heard.group(2), parse_time(f["start"]), parse_time(f.get("stamp")),
                                    parse_time(f.get("at"))))
            elif "[trace] meta" in line:
                f = fields(line)
                if f.get("program") not in (None, "nil"):
                    metas.append((f.get("id", ""), f.get("value", ""), parse_time(f["program"]), parse_time(f.get("wall"))))
            elif "[trace] feed new" in line:
                f = fields(line)
                feeds.append((f.get("title", ""), parse_time(f.get("stamp")), parse_time(f.get("received")), f.get("lag")))
            elif "[trace] feed first poll" in line:
                firsts.append(fields(line))

    if firsts:
        print("First feed polls (age = how old the newest row already was):")
        for f in firsts:
            print(f"  newest={f.get('newest')!r} stamp={f.get('stamp')} age={f.get('age')} s")
    lags = [float(f[3]) for f in feeds if f[3] not in (None, "nil")]
    if lags:
        print(f"Feed listed {len(lags)} new rows, lag after stamp: min {min(lags):.0f} s, median {median(lags):.0f} s, max {max(lags):.0f} s")
    titles = [m for m in metas if "StreamTitle" in m[0] or m[0].endswith("title")]
    print(f"{len(metas)} timed metadata items ({len(titles)} titles). Songs with an anchor: ")
    if not anchors:
        print("  none. Run a heal on a song first.")
        return 0

    by_song = {}
    for title, artist, start, stamp, at in anchors:
        by_song.setdefault((title, artist), []).append((start, stamp))
    print(f"{'song':44} {'anchors':>7} {'stamp-start':>12} {'listed-start':>13} {'icy-start':>10}   (seconds)")
    for (title, artist), rows in by_song.items():
        start = datetime.fromtimestamp(median(r[0].timestamp() for r in rows), timezone.utc)
        stamp = next((r[1] for r in rows if r[1]), None)
        listed = next((f[2] for f in feeds if norm(f[0]) and (norm(f[0]) in norm(title) or norm(title) in norm(f[0]))), None)
        icy = next((m[2] for m in titles if norm(title) and norm(title)[:14] in norm(m[1])), None)

        def delta(t):
            return f"{(t - start).total_seconds():+.1f}" if t else "-"

        print(f"{(title + ' — ' + artist)[:44]:44} {len(rows):>7} {delta(stamp):>12} {delta(listed):>13} {delta(icy):>10}")
        if show_all:
            print(f"    start {start.isoformat()}  anchors spread {max(r[0].timestamp() for r in rows) - min(r[0].timestamp() for r in rows):.1f} s")
    print()
    print("stamp-start: the feed's stamp minus the song's real start. Negative: the feed stamps the song before it starts.")
    print("listed-start / icy-start: how long after the song really started the feed / the stream's title first said so.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
