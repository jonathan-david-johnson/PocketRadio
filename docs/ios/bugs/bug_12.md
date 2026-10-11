# Bug 12 — The tracklist shows the station logo for a song whose album art the player shows

**Status:** Open. Reported by the user on 2026-10-11 on the device. Not fixed. Deferred: "I'll come back to it later". The cause below is read from the code and matches the symptom; the song's feed row was not captured, so "the feed row had no art" is not confirmed.
**Evidence:** The user saw "All Is Full of Love" (Björk) with album art in the player but the KCRW logo on that song's row in the station-detail tracklist. `pocket-radio-ios/podcasts/Radio/TracklistCell.swift` (`configure`) and `RadioTracklistService.swift` (comment at line 129, and the parse at lines 155 and 192).

## Symptom

In station detail, a tracklist row sometimes shows the station logo where the album art should be, for a song whose art the full player does show.

## Root cause

- `TracklistCell.configure(with:fallbackArt:)` sets the image to the fallback (the station logo) and loads art **only** from `entry.albumArtURL`, the URL the feed row carries. When the feed row has no art, the cell keeps the logo.
- The full player, the lock screen and the mini player resolve art through `TrackArtworkResolver`, which tries the feed's URL and then an iTunes Search lookup. The cell never calls it. So a song with no feed art shows real art in the players and the logo in the list.
- `RadioTracklistService` already notes this case: for KCRW the entry's art can be nil, "and the artwork resolver falls through".
- The widget had the same gap and now uses the resolver ([ADR 0005](../adr/0005-kcrw-aligned-now-playing-single-writer.md)).

## Why the fix is not a one-liner

`TrackArtworkResolver` is built for one song at a time: a new lookup cancels the one in flight, and it tracks a single current key. A tracklist shows up to five rows at once, so calling it from each cell would cancel all but the last. A fix needs either a lookup that can run for several entries at once, with the same cache, or a pass in the screen that resolves missing art for the rows and reloads them.

## Proposed fix

- Give the resolver a concurrent-safe lookup that shares its cache (a static helper for the iTunes lookup keyed by artist and title, no single-flight cancel), or add a small per-screen resolver.
- In `cellForRowAt`, when an entry has no art URL, ask for it and reload that row when it arrives. Guard against reuse with the cell's art generation, as the existing load does.
- Test through the screen's seams: a row with no art URL ends with the resolved image, and a reused cell never shows another row's art.

## Files involved

- `podcasts/Radio/TracklistCell.swift`, `podcasts/Radio/StationDetailViewController.swift` (`cellForRowAt`), `podcasts/Radio/TrackArtworkResolver.swift`.
- Tests under `PocketCastsTests/Tests/Radio/`.
