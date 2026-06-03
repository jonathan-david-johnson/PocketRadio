# M6.3: Tracklist for Enhanced Streams

**Status**: PLANNED  
**Depends on**: M6.1 (layout foundation)

## Goal

When an enhanced stream (one with a tracklist URL) is playing, the bottom section shows
the tracklist: song title, artist, album, and artwork for each track.

## Done when

- Enhanced stream pill selected + playing → bottom section shows tracklist
- Each track row shows: title (bold), artist (gray), album (lighter gray), artwork thumbnail (right)
- Tracklist is fetched from the stream's `tracklistUrl` (configured in curated enhancements)
- Tracklist refreshes periodically (every 60s while stream is playing)
- Switching away from the enhanced stream hides the tracklist
- Unenhanced streams (no tracklist URL) show empty bottom section (no ICY history)
- If tracklist fetch fails, show a "Tracklist unavailable" message

## Layout

```
┌──────────────────────────────────┐
│ Podcast │ 📻 KCRW │ Stream 2  ...│   ← top row (KCRW selected)
├──────────────────────────────────┤
│               ⏯️                 │   ← controls (live stream)
├──────────────────────────────────┤
│                                  │   ← no scrubber for live
├──────────────────────────────────┤
│ Take Cover                       │
│   Steven Bamidele · Take Cover   │ [art]
│ Where To Begin                   │
│   My Morning Jacket · (2025...)  │ [art]
│ Everywhere                       │
│   Thundercat · Greatest Hits...  │ [art]
│                                  │
└──────────────────────────────────┘
```

## Implementation

### Curated Enhancements
Copy the hardcoded list from iOS `CuratedEnhancement` + `curated_stations.json`.
These map station UUIDs to tracklist URLs:

```swift
// Example from iOS curated_stations.json
struct CuratedEnhancement {
    let stationId: String   // radio-browser UUID
    let name: String
    let tracklistUrl: String?  // KCRW, KEXP have these
    let logoAsset: String?
}
```

Enhanced stations include at minimum: KCRW Eclectic 24, KEXP.

### Tracklist API
The tracklist URL returns JSON. KCRW format example (from iOS `RadioTracklistService`):
```json
[{
  "title": "Take Cover",
  "artist": "Steven Bamidele",
  "album": "Take Cover",
  "albumImage": "https://..."
}]
```

KEXP format uses a different API (`api.kexp.org/v2/plays`).

### Track Row
```swift
struct TrackRow: View {
    let title: String
    let artist: String
    let album: String
    let artworkURL: String?
    
    var body: some View {
        HStack {
            VStack(alignment: .leading, spacing: 1) {
                Text(title).font(.caption).fontWeight(.semibold)
                Text(artist).font(.caption2).foregroundColor(.secondary)
                Text(album).font(.caption2).foregroundColor(.secondary).opacity(0.7)
            }
            Spacer()
            if let url = artworkURL, let imageURL = URL(string: url) {
                AsyncImage(url: imageURL) { phase in
                    if case .success(let image) = phase {
                        image.resizable().scaledToFit().frame(width: 24, height: 24).cornerRadius(2)
                    }
                }
            }
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 2)
    }
}
```

## Files

### NEW
- `Services/CuratedEnhancements.swift` — hardcoded list copied from iOS
- `Services/TracklistService.swift` — KCRW + KEXP tracklist API clients

### EDIT
- `PlayerViewModel.swift` — tracklist state, periodic refresh timer
- `ContentView.swift` — tracklist view in bottom section when enhanced stream active

## Manual smoke
1. Play KCRW Eclectic 24 (enhanced stream) → bottom shows tracklist with title/artist/album/artwork
2. Tracklist refreshes after 60s
3. Switch to KEXP → tracklist updates for KEXP
4. Switch to NPR Hourly Newscast (unenhanced) → bottom section empty
5. Switch back to KCRW → tracklist reappears
