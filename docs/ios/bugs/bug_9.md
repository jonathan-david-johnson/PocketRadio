# Bug 9 — Mini player and home-screen widget show the station logo instead of the song's album art

**Status:** Open, in two parts. Reported by the user on 2026-10-10 during the device checkpoint for Apply mode ([ADR 0005](../adr/0005-kcrw-aligned-now-playing-single-writer.md)).
- **Mini player:** a fix is built and unit-tested in the `pocket-radio-ios-alignment` worktree, uncommitted. It waits for a device check. The cause below is read from the code and not yet confirmed on the phone.
- **Widget:** not a regression. It has never shown album art. Showing it is new work and needs a decision. See *Investigation, 2026-10-10*.
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
- The widget path is separate: `WidgetHelper.publishPocketRadioLiveTrack` reads `bestResolveEntry` (so its title follows the aligned song) and writes `albumArtURL` plus the station's `logoAssetName`. See *Investigation, 2026-10-10* for what the widget does with them.
- The Dynamic Island showing the logo may be a third surface with the same behavior; not investigated.

## Investigation, 2026-10-10

**Mini player (read from the code, not yet seen on the phone).**
- Anything that fires `currentlyPlayingEpisodeUpdated` calls `MiniPlayerViewController.updateRequired()`. That calls `updateArtwork(forceReload: true)`, which for radio paints the station logo and does not resolve the song's art again.
- The notification fires on every `DefaultPlayer` time-control status change (`playerDidChangeNowPlayingInfo`, play, pause or buffering), so a buffering blip on the HLS stream is enough.
- Art returns only when a later `.radioStationNowPlayingDidChange` or `.radioTracklistDidRefresh` reaches the mini player. In Apply, `.radioTracklistDidRefresh` is not guaranteed to fire, so the logo can stay until the next song. The full player doesn't repaint on that notification, which is why it kept the art.
- **Fix, uncommitted:** the mini player now remembers which song its art was resolved for (`RadioArtworkRepaint.songKey`). A repaint for the same song is skipped. A forced repaint of the same station resolves the art again instead of leaving the logo. A cancelled image request no longer resets the slot to the logo. Tests: `RadioArtworkRepaintTests`.
- **Check on the phone:** start KCRW in Apply, let a song start, then cause a rate change (pause and resume, or wait for a buffering blip). The mini player should keep the song's art. Then let the song change.

**Widget (a missing feature, in every mode).**
- `PocketRadioEntryView.artworkView` shows `logoAssetName` for a live station. Nothing in the widget reads `albumArtURL`. The decoder keeps the field, and no view uses it.
- The publishing code comment says widgets render synchronously and "Phase 2 will add per-station JPEG caching". That phase was never built.
- To show album art, the app must download the image into the App Group, as it does for podcast episodes (`widget_images/`), and the widget must load it from that file. That is also a contract change for `WidgetLiveTrack`.

**Dynamic Island.** Not investigated. It is probably the system Now Playing artwork, which ADR 0005 sets to the station logo until the song's art arrives. Whether it later switches to the song's art is unconfirmed.
