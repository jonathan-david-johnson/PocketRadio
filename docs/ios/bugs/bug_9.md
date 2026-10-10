# Bug 9 — Mini player and home-screen widget show the station logo instead of the song's album art

**Status:** Open. Reported by the user on 2026-10-10 during the device checkpoint for Apply mode ([ADR 0005](../adr/0005-kcrw-aligned-now-playing-single-writer.md)). Not investigated.
**Evidence:** Two user screenshots, not stored in the repo. (1) iPhone, 8:36, Streams tab (Favorites), KCRW Eclectic 24 playing. The mini player at the bottom shows the KCRW logo and the title "KCRW Eclectic 24". (2) 8:38, home screen: the PocketStreams widget shows the aligned song, "Simetachin (featuring Deri…)" by Cut Chemist, next to the KCRW logo instead of album art. The Dynamic Island also shows the KCRW logo.

## Symptom

While KCRW Eclectic 24 plays, the mini player shows the KCRW station logo. Tapping the mini player opens the full player, which shows the current song's album art.

The home-screen widget has the same difference: it shows the current song's title and artist, but the station logo instead of the album art. The user suspects the same cause.

**Expected:** the mini player and the widget show the same album art as the full player.

## What is known

- Observed on the Apply-mode build (now `trunk` `a8254b8c4`) with the alignment mode set to Apply. The user reported that title timing was correct in the same session.
- Not yet known: whether mode Off (today's ICY path) shows the same difference, which would make this pre-existing rather than caused by Apply mode.
- Not yet known: whether the mini player stays on the logo for the whole song, or only until the next song change.

## Where to look

- `MiniPlayerViewController.resolveRadioArtwork` paints the station logo as a baseline, then resolves art through `TrackArtworkResolver.bestResolveEntry` on `.radioStationNowPlayingDidChange` and `.radioTracklistDidRefresh`. In Apply, `bestResolveEntry` returns the aligned song, so the mini player only updates when a notification reaches it after it exists.
- The full player runs the same resolve independently (`NowPlayingPlayerItemViewController+Update.swift`), so the two can disagree if one missed a notification.
- The mini player's title stays the station name in both modes; this bug is about artwork only.
- The widget path is separate: `WidgetHelper.publishPocketRadioLiveTrack` reads `bestResolveEntry` (so its title follows the aligned song) and passes that entry's `albumArtURL` plus the station's `logoAssetName`. It shows the logo when `albumArtURL` is nil, which happens when the feed row has no artwork; the iTunes fallback that the full player uses is not applied there. Whether the widget shares the mini player's cause is unconfirmed.
- The Dynamic Island showing the logo may be a third surface with the same behavior; not investigated.
