# M6.1: Redesigned Layout + Source Pills + Controls

**Status**: PLANNED

## Goal

Replace the current single popover with the new layout matching the iOS widget design:
top row of source pills, context-sensitive transport controls, and a scrubber.

## Done when

- Popover shows top row with 4 pills: `Podcast | Stream 1 | Stream 2 | Stream 3`
- Right of the pills is a `⋮` (three-dot) button (opens M6.4 Favorites/Browse)
- Clicking Podcast pill → plays the top up-next episode immediately
- Clicking a Stream pill → plays that radio station immediately
- If < 3 favorites, remaining slots show radio icon placeholders
- Controls row shows ⏪ ⏯️ ⏩ by default (10s back, play/pause, 45s forward)
- If AVPlayer reports indefinite duration after playback starts, controls swap to ⏯️-only
- No scrubber (deferred to future milestone)
- Skip amounts use hardcoded defaults: 10s back, 45s forward (fetch from Pocket Casts config later)

## Layout

```
┌──────────────────────────────────┐
│ 📻 Podcast │ Stream 1 │ Stream 2 │ Stream 3 │  ⋮  │
├──────────────────────────────────┤
│  ⏪ 10s           ⏯️            ⏩ 45s           │
├──────────────────────────────────┤
│                                  │
│         bottom section           │  ← M6.2 / M6.3 / M6.4 content
│                                  │
└──────────────────────────────────┘
```

## Implementation

### Stream Pill Selection
- Stream pill 1 = first favorite, Stream pill 2 = second, Stream pill 3 = third
- Names truncated to ~10 chars with `...`
- Radio icon placeholder shown for empty slots (no stream name)
- Clicking an empty pill does nothing

### Control Detection
Same logic as iOS `PlaybackManager.shouldUseMuteControls`:
```swift
func shouldUseMuteControls() -> Bool {
    guard currentSource?.isRadio == true else { return false }
    let duration = audioPlayer.currentItem?.duration
    return duration == .indefinite
      || CMTimeGetSeconds(duration) <= 0
}
```
- Start with ⏪ ⏯️ ⏩ immediately on play
- Observe `currentItem.duration` via KVO or `publisher(for:)`
- Swap to ⏯️-only when duration resolves to indefinite

### Skip Amounts
- Hardcoded: skip back 10s, skip forward 45s
- Later: fetch from Pocket Casts settings API (`SyncSettingsTask` pattern)
- `audioPlayer.seek(to: currentTime + skipAmount)` for forward
- `audioPlayer.seek(to: currentTime - skipAmount)` for backward

## Files

### EDIT
- `ContentView.swift` — complete rewrite with new layout
- `PlayerViewModel.swift` — add source pill state, skip amounts, scrubber logic, duration observation
- `PocketRadioApp.swift` — update popover size for new layout (~300×500)

## Manual smoke
1. Log in → Podcast pill shows "Podcast" label, click it → up-next episode plays, controls show ⏪ ⏯️ ⏩
2. Click ⏪ → seeks back 10s. Click ⏩ → seeks forward 45s. Click ⏯️ → pauses
3. Click a stream pill → station plays, controls swap to ⏯️-only after duration detection
4. Click Podcast pill again → switches back to podcast, controls return to ⏪ ⏯️ ⏩
5. Log out → only 1 stream favorite → Stream 1 shows name, Stream 2 and Stream 3 show radio icon placeholders
