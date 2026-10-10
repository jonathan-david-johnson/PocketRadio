# Bug 9 — Mini player shows the station logo while the full player shows the song's album art

**Status:** Open. Reported by the user on 2026-10-10 during the M14.2 device checkpoint. Not investigated.
**Evidence:** User screenshot, iPhone, 8:36, Streams tab (Favorites), KCRW Eclectic 24 playing. The mini player at the bottom shows the KCRW logo and the title "KCRW Eclectic 24". The screenshot is not stored in the repo.

## Symptom

While KCRW Eclectic 24 plays, the mini player shows the KCRW station logo. Tapping the mini player opens the full player, which shows the current song's album art.

**Expected:** the mini player shows the same album art as the full player.

## What is known

- Observed on the M14.2 build (`feature/kcrw-apply`, uncommitted) with the alignment mode set to Apply. The user reported that title timing was correct in the same session.
- Not yet known: whether mode Off (today's ICY path) shows the same difference, which would make this pre-existing rather than caused by M14.2.
- Not yet known: whether the mini player stays on the logo for the whole song, or only until the next song change.

## Where to look

- `MiniPlayerViewController.resolveRadioArtwork` paints the station logo as a baseline, then resolves art through `TrackArtworkResolver.bestResolveEntry` on `.radioStationNowPlayingDidChange` and `.radioTracklistDidRefresh`. In Apply, `bestResolveEntry` returns the aligned song, so the mini player only updates when a notification reaches it after it exists.
- The full player runs the same resolve independently (`NowPlayingPlayerItemViewController+Update.swift`), so the two can disagree if one missed a notification.
- The mini player's title stays the station name in both modes; this bug is about artwork only.
