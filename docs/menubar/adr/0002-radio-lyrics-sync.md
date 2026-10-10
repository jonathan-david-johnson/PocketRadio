# 0002 — How radio lyrics find their position

**Status:** Accepted (2026-06-03, tuned 2026-06-15). The KCRW offset policy is
refined by the alignment work that closes with iOS M14; see the note at the end.

## Context

Synced lyrics need the number of seconds since the current song started. Radio
streams don't say. KCRW Eclectic 24 advertises `icy-metaint: 16000` on both
`e24_mp3` and `e24_aac`, but its `StreamTitle` is always empty, so ICY is no
song-change signal there.

## Decision

- **Song change:** the KCRW tracklist API
  (`tracklist-api.kcrw.com/Music/all/1`). The app already polls it every 30 s.
  A new top entry starts the lyric lookup.
- **Position:** `now − entry.datetime`. `datetime` is the absolute time the song
  started. `offset` in the same response is seconds into the *program*, not
  the song; don't use it.
- **Fallback:** ACRCloud `play_offset_ms`, when the tracklist is down. With
  neither, start at 0.
- **Lyrics source:** lrclib.net, no auth. Prefer `syncedLyrics` (LRC, parsed to
  `(timestamp, text)` pairs and found by binary search). Fall back to plain
  lyrics with no auto-advance. Cache by `artist|title`.
- **Lookup:** `LyricsService.sanitize()` strips decorations such as `(Edit)`,
  `(CLEAN)`, `[Explicit]` and `- Remastered 2010`, using a qualifier word
  list. Then three tiers: exact `/api/get` with title and album, the same
  without album, then `/api/search` (first synced result, else first).
- **Per-station live offset:** a station's HLS or Icecast buffer puts the
  audio behind the tracklist clock by a station-specific amount. The user
  nudges it with `[− +]` in the lyrics header. It is saved per station in
  Supabase `lyric_offsets(user_uuid, station_id, offset_seconds)`, with
  header-based RLS. Saves are debounced by 800 ms. Values the author tuned in
  June 2026 were KCRW −42 s (HLS live-buffer delay) and KEXP +1 s.
- **Between tracks:** a line is shown only while the corrected position is in
  `[firstLine − 3 s, (lrclib duration ?? lastLine + 12 s) + 12 s]`. Outside
  that window the lyric bar shows the station name, not a frozen last line.
  `LyricStatus` is `.none`, `.fetching`, `.found`, `.notFound` or `.betweenTracks`.

## Consequences

- A constant per-station offset is a hack. It breaks when a station's buffer
  depth changes. The player's own media clock is the better source for HLS.
- Lyrics hide silently when none are found.
- A lyric lookup that fails for any reason is indistinguishable from "no
  lyrics", by design.

## Rejected alternatives

- **ICY titles** for song change: empty on KCRW Eclectic 24.
- **The tracklist `offset` field** as song position: it counts from the start
  of the program.
- **Extracting a pure `LyricSync` engine for unit tests.** Wanted, deferred.
  The lyric logic is still in `PlayerViewModel` and `LyricsService`.

## Note on the KCRW offset

For the eligible KCRW AAC/HLS stream, normal playback now selects the
occurrence from the player's own clock and a feed-to-program offset, instead
of a hand-tuned lyric offset. That policy belongs to the KCRW alignment work
(menubar M10–M12, iOS M14). Its ADR is written when M14 closes, and it should
supersede the offset paragraph above for that station.

Evidence: `archive/menubar-m7:docs/menubar/milestones/milestone_7_lyrics.md`
and `archive/menubar-m9:docs/menubar/milestones/milestone_9.md`.
