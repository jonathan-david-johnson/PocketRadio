# Bug 4 — A song missing from a stale tracklist keeps the previous song's artwork

**Status:** Open — reproduced in the M13 test harness (2026-10-04); not yet observed on a device. Not fixed.

Found by M13 E7 (H1). Evidence: `archive/ios-m13:docs/ios/experiments/2026-10-04_m13_e7.md`, the original `@h1` draft in `contracts/features/now_playing/carplay_artwork.feature`. M13.2 replaces that draft with named scenarios; its unmarked baselines (`archive/ios-m13.2:docs/ios/experiments/2026-10-07_m13_2_baselines.md`) reproduce stale artwork and a wrong album when the new ICY song has no album.

---

## Symptom

The now-playing display (lock screen, CarPlay) shows the new song's title and artist with the **previous song's artwork**.

Timeline from the harness: Song A plays with its artwork. The stream announces Song B. The display changes to "Song B" and the artwork stays on A's image. It does not change again.

## When it happens

All of these must hold:

- The station is a curated one with a `tracklistUrl` (so artwork resolution runs).
- The cached tracklist does not contain the new song. The tracklist is fetched at playback start and again only when the station detail screen is visible, so a phone that never opens that screen keeps the start-up copy.

It does **not** happen when the new song is in the cached tracklist.

## Additional M13.2 symptom — mismatched album

When Song B's ICY frame supplies title and artist but no album, the cached top
entry's Album A is published with Song B. `handleRadioTrackChanged` uses the
cached first row to fill an absent ICY album without checking that it matches
the current song. M13.2's one-song-behind scenario fails `display.album.not-equal`.
This is the S2 violation in the same stale-feed condition; it is not an ICY
fixture-album mismatch.

## Root cause (from code, confirmed by the harness)

`TrackArtworkResolver.bestResolveEntry` falls back to the cached tracklist's top entry when the ICY artist and title match nothing. `PlaybackManager.resolveRadioArtworkForLockScreen` builds its dedupe key from that entry. The top entry is still the previous song, so the key equals `lastResolvedRadioKey` and the function returns early. The title and artist come from a separate write (`setRadioTrackInfo`), so they update while the artwork does not.

The existing test `testBestResolveEntryPopulatedCacheICYMismatchFallsBackToTop` asserts the top-entry fallback, so a fix must change that test deliberately.

## Not decided

How to fix it. The M13 plan keeps fixes in `fix/stream-presentation`. Options include refreshing the tracklist on a miss, falling back to the station logo when the ICY song is not in the list, or keying on the ICY pair instead of the fallback row.

## Open question

How often a real KCRW user meets it. It depends on whether the real tracklist usually has the new song when the ICY title changes. Not measured.

## Harness update — 2026-10-08 UTC

The accepted baseline verification (`archive/ios-m13.2:docs/ios/experiments/2026-10-08_m13_2_verification.md`) records
three full 128-test passes with three strict bug-4 output checks:

- Closed detail: `display.artwork.station-logo`.
- One-song-behind feed: `display.album.not-equal` and `display.artwork.station-logo`.

The album check permits absent, empty or different albums; only borrowing Album A
is the defect. Wrong song identity and input/readiness failures remain ordinary.
The detail-open scenario passes unmarked. This adds regression targets, not a fix.
