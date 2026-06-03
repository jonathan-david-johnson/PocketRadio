# M6.2: Up Next List

**Status**: PLANNED  
**Depends on**: M6.1 (layout foundation)

## Goal

When the Podcast pill is selected, the bottom section shows the full Pocket Casts up-next queue
as an episode list with titles. Currently playing episode is highlighted at the top.

## Done when

- Podcast pill selected → bottom section shows episode list
- Currently playing episode is first in the list, visually highlighted
- Each row shows: episode title (bold), truncated with `...`
- Tapping a different episode in the list switches playback to that episode
- List auto-refreshes when up-next data is re-fetched (on refresh button or login)
- Scrolling works if list exceeds available space
- Switching to a stream pill hides the episode list, switching back to Podcast restores it

## Layout

```
┌──────────────────────────────────┐
│ 📻 Podcast │ Stream 1 │ ...      │   ← top row
├──────────────────────────────────┤
│  ⏪         ⏯️          ⏩       │   ← controls
├──────────────────────────────────┤
│ ▶ The Thunder Get Physical to... │   ← currently playing (highlighted)
│   An MSG Miracle, the Wemby...   │
│   EMERGENCY REACTION: Wembany... │
│   The Press Box — Episode 42     │
│                                  │
└──────────────────────────────────┘
```

## Implementation

### Data Source
- Already fetching via `PocketCastsAPI.fetchUpNext(token:)` which returns `[UpNextEpisode]`
- Currently only stores `topEpisode` (first element) — extend to store the full array
- `@Published var upNextEpisodes: [UpNextEpisode] = []`

### Episode Row
```swift
struct UpNextRow: View {
    let episode: UpNextEpisode
    let isPlaying: Bool
    
    var body: some View {
        HStack {
            if isPlaying {
                Image(systemName: "play.fill")
                    .font(.caption2)
                    .foregroundColor(.accentColor)
            }
            Text(episode.title)
                .font(.caption)
                .fontWeight(isPlaying ? .semibold : .regular)
                .lineLimit(1)
                .truncationMode(.tail)
            Spacer()
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 4)
        .contentShape(Rectangle())
        .onTapGesture {
            // play this episode
        }
    }
}
```

### Episode Switching
- Tapping a different episode:
  1. Stop current playback
  2. Move that episode to `currentSource = .podcast(episode)`
  3. Reorder `upNextEpisodes` to put the tapped episode first
  4. Update `nowPlayingTitle`
  5. Start playback

## Files

### EDIT
- `PlayerViewModel.swift` — store full `upNextEpisodes` array, add `playEpisode(_:)` method
- `ContentView.swift` — add Up Next list view in bottom section, show when Podcast pill active

## Manual smoke
1. Log in, Podcast pill selected → bottom shows episode list
2. Currently playing episode highlighted with ▶ icon
3. Tap a different episode → playback switches, new episode moves to top, highlighted
4. Switch to stream pill → episode list hidden
5. Switch back to Podcast → episode list restored
6. Click refresh → list updates with latest up-next data
