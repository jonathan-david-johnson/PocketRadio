# Milestone 7 — Synced Lyrics for Radio Streams

**Status**: DONE  
**Depends on**: M6 (ACR fingerprinting, merged to main 2026-06-03)

---

## Goal

Show synced lyrics for the currently playing track on KCRW Eclectic 24 (and
KEXP). Lyrics scroll to the correct line based on how far into the song we are,
without any user interaction after the track starts.

---

## Research Findings (2026-06-03)

### ICY metadata

Both `e24_mp3` and `e24_aac` advertise `icy-metaint: 16000` but send
**empty** StreamTitle chunks (`StreamTitle=''`) on connect and never update
mid-stream. ICY is dead on Eclectic 24 — not a viable song-change signal.

### Song-change detection

The KCRW tracklist API is the only reliable source:

```
GET https://tracklist-api.kcrw.com/Music/all/1?page_size=3
```

Fires (new top entry) approximately when a song changes. The app already polls
this every 30s in `RadioTracklistService`. **No additional song-change
detection needed** — piggyback on the existing tracklist update notification
(`.radioTracklistDidRefresh`).

### Play offset (sync position)

The tracklist API response includes a `datetime` field — the absolute time the
current track started playing:

```json
{
  "title": "SOMEWHERE ELSE (fade)",
  "artist": "TOMORA",
  "datetime": "2026-06-03T18:29:42-07:00",
  "offset": 1782
}
```

`offset` = seconds into the *program* (not the song). Use `datetime` instead:

```swift
let songOffset = Date().timeIntervalSince(ISO8601DateFormatter().date(from: entry.datetime)!)
// → seconds elapsed since this song started
```

This gives the correct lyric line position without ACR.

### ACR fallback (when tracklist is down)

ACRCloud response includes `play_offset_ms` in the music match result:
```json
{ "play_offset_ms": 22660 }
```

Convert to seconds → use as starting offset when tracklist is unavailable.
Both platforms already have `ACRFingerprinter` / `TrackFingerprinter` built.

### Lyrics source: lrclib.net

Free, no auth, REST API, returns both plain and **synced (LRC)** lyrics:

```
GET https://lrclib.net/api/get?artist_name=TOMORA&track_name=SOMEWHERE+ELSE&album_name=COME+CLOSER
```

Response:
```json
{
  "trackName": "SOMEWHERE ELSE",
  "artistName": "TOMORA",
  "plainLyrics": "...",
  "syncedLyrics": "[00:14.32] Some lyric line\n[00:18.10] Next line\n..."
}
```

Synced lyrics use LRC format: `[mm:ss.xx] text`. Parse into
`[(TimeInterval, String)]` pairs, find the line whose timestamp ≤ current
offset, display it.

Falls back to `plainLyrics` if synced not available. Returns 404 if no match.

---

## Architecture

### New service: `LyricsService`

```swift
struct LyricLine {
    let timestamp: TimeInterval  // seconds
    let text: String
}

struct LyricsResult {
    let lines: [LyricLine]       // empty = plain-only or not found
    let plain: String?
}

final class LyricsService {
    static let shared = LyricsService()
    private var cache: [String: LyricsResult] = [:]  // key = "artist|title"

    func fetch(artist: String, title: String, album: String?) async -> LyricsResult?
    func currentLine(in result: LyricsResult, at offset: TimeInterval) -> LyricLine?
}
```

### Lyrics display in menubar app

Small text area below the tracklist in `ContentView`. Shows:
- Current lyric line (large, primary color)
- Next lyric line (small, secondary color — optional, like Apple Music)
- Hidden when no lyrics found or when playing a podcast

Offset advances via a `Timer` (1s tick) starting from `playedAt` timestamp.

### Lyrics display in iOS app

`StationDetailViewController` already has `tracklistTable`. Add a collapsible
lyrics section above or below the table, or a separate "Lyrics" tab.
Simpler: show current line in a label below the now-playing title labels.

---

## Implementation Plan

### Phase 1 — Menubar (no iOS yet)

1. **`LyricsService.swift`** (new file, `pocket-radio-menubar/PocketRadio/Services/`)
   - `fetch(artist:title:album:)` — hits lrclib, parses LRC, caches by artist+title
   - `parseLRC(_ raw: String) -> [LyricLine]` — split on newlines, parse `[mm:ss.xx]`
   - `currentLine(in:at:) -> LyricLine?` — binary search by timestamp

2. **`PlayerViewModel`** additions
   - `@Published var currentLyric: String = ""`
   - `@Published var showLyrics: Bool` — true when radio + lyrics found
   - `private var lyricTimer: Timer?`
   - `private var lyricLines: [LyricLine] = []`
   - `private var lyricStartDate: Date?`
   - `func loadLyrics(for entry: TracklistEntry)` — called on tracklist top-entry change
   - `func startLyricTimer(offset: TimeInterval)` — ticks every second, updates `currentLyric`
   - `func stopLyricTimer()`

3. **Trigger point**: `refreshNowPlayingFromTracklist(for:)` already fires when
   top entry changes. Add `loadLyrics(for: tracklist.first)` there.

4. **`ContentView`** — add lyrics line below scrub bar or above tracklist:
   ```swift
   if vm.showLyrics && !vm.currentLyric.isEmpty {
       Text(vm.currentLyric)
           .font(.system(size: 12, weight: .medium))
           .foregroundColor(PocketCastsTheme.primaryText02)
           .lineLimit(2)
           .padding(.horizontal, 12)
   }
   ```

### Phase 2 — iOS app

Mirror `LyricsService` into iOS target (same logic, no SwiftUI dependencies).
Add lyric label to `StationDetailViewController` between now-playing labels and
the button row. Trigger from `.radioTracklistDidRefresh` notification observer
already in the VC.

---

## Offset calculation summary

| Source | How to get offset |
|--------|------------------|
| Tracklist working | `Date() - ISO8601(entry.datetime)` |
| ACR fallback | `result.play_offset_ms / 1000.0` |
| Neither | Start from 0 (song just detected) |

---

## Edge cases

- **Lyrics not found**: hide the lyrics area silently, no error shown
- **Synced lyrics missing, plain available**: show plain in a scrollable area (no auto-advance)
- **Song changes before lyrics load**: cancel in-flight fetch, start new one
- **Offset > song duration**: clamp to last line
- **lrclib rate limit**: service has no documented limit; add 1s debounce on fetch to be safe

---

## Files to create/edit

| File | Action |
|------|--------|
| `pocket-radio-menubar/PocketRadio/Services/LyricsService.swift` | New |
| `pocket-radio-menubar/PocketRadio/View Models/PlayerViewModel.swift` | Edit — lyric state + timer |
| `pocket-radio-menubar/PocketRadio/ContentView.swift` | Edit — lyric display |
| `pocket-radio-ios/podcasts/Radio/LyricsService.swift` | New (Phase 2) |
| `pocket-radio-ios/podcasts/Radio/StationDetailViewController.swift` | Edit (Phase 2) |

---

## Testing approach

1. Fetch KCRW current track title from tracklist API
2. Query lrclib directly to confirm lyrics exist before building UI
3. Compute offset from `datetime` and verify correct line is highlighted
4. Test with tracks that have no lyrics — confirm graceful hide

```bash
# Quick lrclib test
curl "https://lrclib.net/api/get?artist_name=TOMORA&track_name=SOMEWHERE+ELSE" | python3 -m json.tool
```
