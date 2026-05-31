# M6: Polish — Skip Settings, Scrub, Tracklist, Now Playing

**Status**: NOT STARTED

## Goal

Final feature-parity pass: real skip amounts, transport-key seek, KCRW/KEXP tracklist, Now Playing artwork + scrolling title, finalized assets, and an error/empty-state sweep.

## Done when

- Skip back/fwd amounts come from relay `namedSettings` (this account: back 15, fwd 30); defaults back 10 / fwd 45 on failure; UI shows the actual numbers (replaces M4's hardcoded values)
- Seekable content scrubs via transport keys (FF/REW) + skip-by-amount; live streams stay play/pause-only (gating from M3)
- KCRW/KEXP tracklist polls ~30s while that stream is active and shows "Title — Artist"; **polling stops on stream change/stop** (no leaked timers, no stale tracks)
- Now Playing: artwork + scrolling title + progress
- Channel icons + splash finalized (blue PocketStreams mark)
- Error/empty/offline sweep: no-network, empty queue, stream 404, mid-session 401 all show a message rather than crashing

## What to Build

### Skip settings (relay `namedSettings`, read-only)
Relay action already built (`namedSettings` → `{skipForward, skipBack}`, defaults 45/10). Wire to skip keys + on-screen glyphs labeled with the actual seconds. Replaces the M4 hardcoded defaults.

### Scrub / transport keys (HANDOFF §7)
- Map FF/REW to `m.audio.seek = pos ± skipAmount`; Play/Pause to control.
- Reuse M3's live-vs-seekable gating (`duration` 0/indefinite → no scrub).

### Tracklist (HANDOFF §6.11) — direct JSON, with cleanup
- Poll ~30s while the active stream's name contains "kcrw"/"kexp":
  - kcrw → `GET tracklist-api.kcrw.com/Music/all/1?page_size=10`; skip empty/`[BREAK]` artist.
  - kexp → `GET api.kexp.org/v2/plays/?limit=10`; keep `play_type=="trackplay"`.
- **Stop the poll timer when the stream changes or stops** — otherwise it leaks and shows wrong-stream tracks.

### Assets (HANDOFF §10)
- Replace placeholder PNGs with the blue PocketStreams mark (red→blue hue +156°, white logo preserved): icons HD 290x218 / FHD 336x210 + splash.

## Implementation Strategy

1. Relay `namedSettings` → skip amounts + labels (replace M4 defaults).
2. Transport-key seek + skip; confirm live gating still holds.
3. Tracklist poll for KCRW/KEXP with start/stop tied to active stream.
4. Now Playing artwork + scrolling title.
5. Finalize icons/splash.
6. Error/empty/offline sweep across all screens.

## User Checkpoint

Play a podcast → scrub + skip by 15/30. Play KCRW/KEXP → now-playing track updates; switch streams → old poll stops. Play a live stream → play/pause only. Pull the network → graceful errors. Icon + splash look finished.

## Commit
TBD.
