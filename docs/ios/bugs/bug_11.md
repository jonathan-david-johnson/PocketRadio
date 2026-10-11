# Bug 11 — The "now playing" mark in the tracklist sits on the right, and it can disappear and not come back

**Status:** Open. Reported by the user on 2026-10-10 on the device. Not fixed. Deferred: "down the road". The cause of the second symptom is not found; the candidates below are unconfirmed.
**Evidence:** `pocket-radio-ios/podcasts/Radio/StationDetailViewController.swift` (`alignedMarkView`, `cellForRowAt`, `refreshAlignedDisplay`, `viewWillDisappear`) and `podcasts/Radio/TracklistCell.swift`. The mark is a `speaker.wave.2.fill` icon, the marker ADR 0005 added for the aligned song. The user called it a "music icon".

## Symptom A — wrong side

In Apply, the row for the song that is playing shows a speaker icon. It appears at the far right of the row, to the right of the album art. The user wants it to the left of the album art.

### Root cause

The mark is the table cell's `accessoryView`, which UIKit places at the trailing edge, outside the content view. `TracklistCell` pins its 60 pt album art to the content view's trailing edge (`artView.trailingAnchor = contentView.trailingAnchor − 16`), so the accessory sits beyond the art.

### Proposed fix

Draw the mark inside `TracklistCell`: a small image view between the text column and the art, which lays out the title labels with a trailing limit at the mark. Drive it from a cell property (for example `isNowPlaying`) set in `cellForRowAt` and cleared in `prepareForReuse`. Remove the `accessoryView` use. Keep the "Now playing" accessibility label.

## Symptom B — the mark disappears after stopping and restarting the stream, and stays gone

### Root cause (unconfirmed)

The mark shows only when `alignedEntry` is set. That happens in `refreshAlignedDisplay`, from an aligned `radioStationNowPlayingDidChange` post and from the playback notifications. After a Stop, `refreshAlignedDisplay` finds no Apply session and clears `alignedEntry`, and the new session must set it again. Candidates, none of them tested:

1. **Playback observers lost.** `viewWillDisappear` calls `removeAllCustomObservers()`, and the observers for playback started, paused and ended are added only in `viewDidLoad`. If the user left the screen and came back, nothing refreshes the marks on a restart. The aligned-post observer is a plain `NotificationCenter` observer and survives.
2. **No match against the five rows shown.** `markedRow(in:aligned:)` marks a row only if the aligned song matches one of `entries` (the first five feed rows). After a restart the aligned song may not be among them yet, because the history refetch runs only about 2 s after a post and then every 30 s.
3. **First post is "unavailable".** A new session publishes "unavailable" first, which clears the marker, and the song post that follows may be dropped by the `isApplying == aligned` guard if the session registered late.

### To find it

Reproduce on the device with the log: Stop, Play, and watch for the aligned `publish song=` line, then check `_markedRowsForTesting`. Compare against a fresh visit to the screen. If the marker returns after leaving and re-entering the screen, candidate 1 is the cause.

### Proposed fix

Re-add the playback observers in `viewWillAppear`, or use observers that live as long as the screen does. Refresh the marks whenever the history refetch finishes. Add a test that stops and restarts an Apply session while the screen is up and asserts the marked row comes back.

## Files involved

- `podcasts/Radio/TracklistCell.swift`: a mark inside the cell, laid out left of the art.
- `podcasts/Radio/StationDetailViewController.swift`: `cellForRowAt`, `alignedMarkView` (remove), observer lifetime, refresh after the history refetch.
- Tests under `PocketCastsTests/Tests/Radio/StationDetailLyricsTests.swift` or a new file, using the existing `_markedRowsForTesting` seam.
