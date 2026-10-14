# Bug 14 — Station detail's lyric header says "No lyrics found" for a song whose lyrics open fine from the tracklist

**Status:** Open. Reported by the user on 2026-10-14 on the device. Not fixed. The cause below is a ranked guess from the code; no log captured it, because the lyric path logs only to the system log and not to the app's debug file.
**Evidence:** User report: "On start of song 1/2 way through, lyrics always say 'no lyrics found' even though if I click into the track I can see lyrics." `podcasts/Radio/LyricSyncController.swift` (`load`), `podcasts/Radio/LyricsService.swift` (`fetch`), `podcasts/Radio/StationDetailViewController.swift` (`reloadLyrics`, `didSelectRowAt`).

## Symptom

With a song already part-way through (the user's words are "on start of song 1/2 way through"; whether this means opening the station screen mid-song, or launching the app mid-song, is not confirmed), the lyric header row on station detail reads "No lyrics found". Tapping that song's row opens full-screen lyrics, which do load. It is described as happening "always".

## What the code does

- The header and the full-screen screen use the **same loader** (`LyricSyncController.loader`, which calls `LyricsService.fetch`). The tapped row passes its feed row; the header passes the aligned song's entry (title, artist and album from the aligned state).
- `LyricsService.fetch` returns `nil` for any failure: a network error, a non-200 reply, an unparseable reply, or a real miss. It **caches nothing** on `nil`, so the next call tries again.
- `LyricSyncController.load` turns a `nil` result into the header "No lyrics found" and status `.notFound`. It does not retry. A second `load` for the same song and occurrence returns early (`currentSongKey == key && currentOccurrenceID == occurrenceID`), so the screen stays on "No lyrics found" until the song changes.
- Tapping the row builds a new `LyricsViewController`, which fetches again. That fetch can succeed where the first failed.

## Likely cause (unconfirmed, in order)

1. **A failed first fetch looks the same as "not found".** The first fetch fails (the lrclib request times out, is throttled, or loses the network at launch), the header reports a miss, and nothing tries again. The row tap fetches again and works. This fits "always when it starts mid-song", since the first fetch then runs at launch or screen open, when other requests compete.
2. **The two paths send different arguments.** The aligned entry's album or title may differ from the feed row's (decoration, spacing, case), so the exact lookup misses for one and not the other. The service retries without the album and then does a fuzzy search, which makes this less likely.
3. **The header's load runs before the aligned entry is complete** and loads a song that has no album yet. Less likely, since the entry comes from one published song.

## To find it

- Reproduce on the device: start KCRW, wait for a song to be part-way through, open the station screen, and see the header.
- Read the lyric log in Console (`log stream --predicate 'category == "Lyrics"'`), which has "fetch start" and "fetch done: result=… " lines for both the header and the row.
- Add `FileLog` lines to `LyricSyncController.load` (artist, title, album, result) so a device run is readable from the debug file. That change is also worth keeping.

## Direction for a fix

- Tell a **failed** fetch apart from a **miss**: `LyricsService.fetch` returns a result type, or a flag, so a failure is not reported as "No lyrics found".
- On a failure, retry once after a short wait, and show "Fetching…" meanwhile. After a few failures, show a retry affordance, or retry on the next song tick.
- A test: a loader that returns `nil` once and a result the second time ends with lyrics, not "No lyrics found".

## Files involved

- `podcasts/Radio/LyricsService.swift`, `podcasts/Radio/LyricSyncController.swift`, `podcasts/Radio/StationDetailViewController.swift`.
- Tests: `PocketCastsTests/Tests/Radio/LyricSyncControllerTests.swift` (an existing fake loader).
