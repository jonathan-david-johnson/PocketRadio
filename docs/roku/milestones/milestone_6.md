# M6: Polish — Skip Settings, Scrub, Tracklist, Now Playing

**Status**: NOT STARTED

## Goal

Final feature-parity pass: skip amounts from account settings, scrub/seek with live-vs-seekable logic, KCRW/KEXP tracklist while playing, Now Playing artwork + scrolling title, channel icons/splash.

## Done when

- Skip back/fwd amounts read from `/user/named_settings/update` (this account: back 15, fwd 30); defaults back 10 / fwd 45 on failure; UI shows actual numbers (not hardcoded)
- Seekable content (podcasts + finite MP3 like NPR hourly) → scrub bar + transport-key seek; live streams → play/pause only
- KCRW/KEXP tracklist polls ~every 30s while that stream is active; shows "Title — Artist"
- Now Playing: artwork + scrolling title + progress
- Channel icons + splash finalized (blue PocketStreams mark)

## What to Build

### Skip settings (HANDOFF §6.6) — READ-ONLY
- **NamedSettingsTask** — `POST /user/named_settings/update` (`f2="PocketRadio"`, send no settings → effectively a read). Decode `f5=skipForward`, `f6=skipBack`, each `Api_Int32Setting{f1=Int32Value{f1=int}}`. Unwrap `f5/f6 → f1 → f1`. Defaults back 10 / fwd 45.
- Map skip back/fwd to remote keys + on-screen glyphs labeled with actual seconds.

### Scrub / live-vs-seekable (HANDOFF §7)
- `m.audio.duration` 0/indefinite → hide scrub, play/pause only (mirrors menubar `shouldUseMuteControls`). Else show scrub; `m.audio.seek = newPos`.

### Tracklist (HANDOFF §6.11)
- **TracklistTask**, poll ~30s while active stream:
  - name contains "kcrw" → `GET https://tracklist-api.kcrw.com/Music/all/1?page_size=10`; skip empty/`[BREAK]` artist.
  - name contains "kexp" → `GET https://api.kexp.org/v2/plays/?limit=10`; keep `play_type=="trackplay"`.
- Show "Title — Artist" overlay/list.

### Assets (HANDOFF §10)
- Blue PocketStreams mark (red→blue, hue +156°, white logo preserved). Downscale 1024px source → icons HD 290x218 / FHD 336x210 + splash.

## Implementation Strategy

1. NamedSettingsTask → wire skip amounts + labels.
2. Scrub bar + live-vs-seekable gating + transport-key seek.
3. TracklistTask polling for KCRW/KEXP.
4. Now Playing artwork + scrolling title.
5. Finalize icons/splash.

## User Checkpoint

Play a podcast → scrub + skip by 15/30. Play KCRW/KEXP → see now-playing track update. Play NPR hourly → scrubs (finite). Play live stream → play/pause only. Channel icon + splash look finished.

## Commit
TBD.
