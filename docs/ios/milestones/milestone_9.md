# iOS M9 — Synced Lyrics for Radio Streams

**Status**: DONE  
**Depends on**: M8 (complete)

---

## Goal

Show synced lyrics for the currently playing track in `StationDetailViewController`. A 1-line
lyric label (auto-advancing with a 1s timer) appears as the tracklist table's sticky section
header. Tapping any tracklist row opens a full `LyricsViewController` with the complete lyrics
scrolled to the current line.

Applies to KCRW and KEXP — the two stations with active tracklists. All other stations
(no `tracklistUrl`) simply never trigger a lyrics fetch.

---

## Lyric source: lrclib.net

Free REST API, no auth:

```
GET https://lrclib.net/api/get?artist_name=TOMORA&track_name=SOMEWHERE+ELSE&album_name=COME+CLOSER
```

Response fields used:
- `syncedLyrics` — LRC-format string `[mm:ss.xx] line text`  
- `plainLyrics` — fallback plain text  
Returns HTTP 404 when no match.

---

## Offset calculation

`entries.first?.playedAt` is already populated from the `datetime` field in the KCRW/KEXP
tracklist parsers:

```swift
let offset = entry.playedAt.map { Date().timeIntervalSince($0) } ?? 0
```

No relay changes needed. ACR `play_offset_ms` fallback is out of scope for this milestone.

---

## Done when

### LyricsService
- [x] `LyricsService.swift` created at `podcasts/Radio/LyricsService.swift`
- [x] Identical logic to `pocket-radio-menubar/PocketRadio/Services/LyricsService.swift` — no UIKit/SwiftUI imports
- [x] `fetch(artist:title:album:) async -> LyricsResult?` — hits lrclib, parses LRC, in-memory cache by `"artist|title"` key
- [x] `currentLine(in:at:) -> LyricLine?` — binary search by timestamp
- [x] Registered in `project.pbxproj` (mirror `StreamsHostViewController.swift` registration)

### LyricsViewController
- [x] `LyricsViewController.swift` created at `podcasts/Radio/LyricsViewController.swift`
- [x] Init: `entry: TracklistEntry, lyricsResult: LyricsResult, offset: TimeInterval, isCurrentSong: Bool`
- [x] Header view: `albumArtURL` (40×40 rounded), `title` (semibold), `artist` (secondary) — mirrors menubar's `LyricsDetailView` header
- [x] If synced (`lyricsResult.hasSynced`):
  - UITableView; each row = one `LyricLine`
  - Current line row: bold, `AppTheme.colorForStyle(.primaryText01)`; others: `.primaryText02`
  - On appear: scroll to `currentLineIndex` via `scrollToRow(at:at:animated:false)`
  - When `isCurrentSong`: 1s Timer starts at `initialOffset`, advances `currentLineIndex`, scrolls to new row with `animated: true`
  - Timer stopped in `viewDidDisappear`
- [x] If plain-only (`result.plain != nil`): full-screen `UITextView` with text, no auto-advance
- [x] "No lyrics found" empty state (label, centered) when both are nil
- [x] Registered in `project.pbxproj`

### StationDetailViewController — lyric section header
- [x] `lyricHeaderView: UIView` — 44pt tall, background `.primaryUi01`, separator line at bottom
- [x] `lyricHeaderLabel: UILabel` inside — `.systemFont(ofSize: 14)`, `.primaryText02`, leading "♪ " prefix, `numberOfLines = 1`, `lineBreakMode = .byTruncatingTail`
- [x] `tableView(_:viewForHeaderInSection:)` returns `lyricHeaderView` when lyrics are loaded, `nil` otherwise
- [x] `tableView(_:heightForHeaderInSection:)` returns `44` when lyrics loaded, `0` otherwise
- [x] When lyrics are active, call `tableView.reloadSections([0], with: .none)` on load and on each timer tick that changes the header text

### StationDetailViewController — lyric lifecycle
- [x] New properties: `lyricLines`, `lyricStartDate`, `lyricTimer`, `lyricFetchTask`, `currentLyricSongKey`, `currentLyricLineIndex`
- [x] `loadLyrics(for entry: TracklistEntry)`:
  - Skip if `currentLyricSongKey == artist|title` (same song, already loaded)
  - Cancel `lyricFetchTask`, stop timer, clear header label
  - Fetch via `LyricsService.shared.fetch(...)` in a Task
  - On synced result: populate `lyricLines`, compute `offset` from `entry.playedAt`, call `startLyricTimer(offset:)`
  - On plain-only result: set header label to `"♪ " + firstNonEmptyLine`, no timer
  - On nil result: header stays hidden
- [x] `startLyricTimer(offset:)`: finds starting line, updates `lyricHeaderLabel.text`, schedules `Timer.scheduledTimer(withTimeInterval: 1...)`
- [x] Timer callback: compute offset from `lyricStartDate`, call `updateCurrentLyricLine()`, update label if line changed
- [x] `stopLyricTimer()`: invalidates timer, clears `lyricLines`, `lyricStartDate`, `lyricFetchTask`
- [x] **Trigger**: call `loadLyrics(for: entries.first)` at the end of `refetchTracklist()` (after `self.entries = Array(fresh.prefix(5))`)
- [x] `stopLyricTimer()` called in `viewDidDisappear`

### StationDetailViewController — tap-to-lyrics
- [x] Implement `tableView(_:didSelectRowAt:)` in the existing empty `UITableViewDelegate` extension:
  - Deselect row immediately
  - Fetch lyrics for `entries[indexPath.row]` via `LyricsService.shared.fetch(...)`
  - If result is non-nil: create `LyricsViewController(entry:lyricsResult:offset:isCurrentSong:)` and push onto `navigationController`
    - `isCurrentSong`: true when `indexPath.row == 0 && entries.first` matches `currentLyricSongKey`
    - `offset`: current `lyricStartDate.map { Date().timeIntervalSince($0) } ?? 0` if `isCurrentSong`, else 0
  - If result is nil: `Toast.show("No lyrics found")`

---

## File list

| File | Action | Notes |
|------|--------|-------|
| `podcasts/Radio/LyricsService.swift` | New | Copy from menubar, no UIKit imports |
| `podcasts/Radio/LyricsViewController.swift` | New | UIKit full-lyrics VC |
| `podcasts/Radio/StationDetailViewController.swift` | Edit | Lyric header + lifecycle + tap delegate |
| `project.pbxproj` | Edit | Register both new files |

---

## Layout sketch

```
┌──────────────────────────────────┐
│  [logo]                          │
│  Station Name                    │
│  Track Title                     │
│  Artist Name                     │
│  [Play]    [Favorite]            │
│  [Identify]                      │
├──────────────────────────────────┤  ← tracklistTable.topAnchor
│  ♪ And I know that you're the…  │  ← lyric section header (h=44, sticky)
├──────────────────────────────────┤
│  [art]  Track Title              │  ← tracklist row 0 (tap → LyricsVC)
│         Artist · 2 min ago       │
├──────────────────────────────────┤
│  [art]  Previous Track           │  ← row 1
│         Artist · 35 min ago      │
└──────────────────────────────────┘
```

### LyricsViewController (synced)

```
┌──────────────────────────────────┐
│  [art] Track Title               │  ← header: artwork + title + artist
│        Artist Name               │
├──────────────────────────────────┤
│  Some earlier line               │  ← dim (.primaryText02)
│  ▶ And I know that you're the…   │  ← current: bold + .primaryText01
│  Next lyric line                 │  ← dim
└──────────────────────────────────┘
```

---

## Edge cases

| Case | Behavior |
|------|----------|
| No lyrics on lrclib | Header stays hidden; `Toast.show("No lyrics found")` on row tap |
| Plain-only lyrics | Header shows first non-empty line (static); full view shows UITextView |
| Song changes before fetch completes | `lyricFetchTask?.cancel()` before starting new fetch |
| Offset > last lyric timestamp | Clamp to last line |
| `viewDidDisappear` | Stop lyric timer; cancel fetch task |
| `entry.playedAt` is nil | Use offset 0 (start from beginning) |

---

## Testing

1. Open KCRW station detail while a track is playing
2. Wait for tracklist to populate — section header should appear with current lyric line
3. Watch for lyric to advance every ~1s
4. Tap the top tracklist row — `LyricsViewController` pushes, scrolled to current line
5. Leave and re-enter the VC — lyrics re-fetch and resume at correct offset
6. Test a track not in lrclib — header hidden, tap row shows toast

```bash
# Confirm lrclib returns synced lyrics for the current KCRW track:
curl "https://lrclib.net/api/get?artist_name=TOMORA&track_name=SOMEWHERE+ELSE" | python3 -m json.tool | grep syncedLyrics
```

---

## Commit

TBD.
