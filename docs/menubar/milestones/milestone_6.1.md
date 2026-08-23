# M6.1: Redesigned Layout + Source Pills + Controls

**Status**: COMPLETED — 3fdea62

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

## Corrections

This doc sat at **PLANNED** long after the described work actually shipped —
commit `3fdea62` ("M6.1: Redesigned layout with pill-based source selection",
22 May 2026) implemented this milestone's goal almost verbatim: 4-pill top
row, `⋮` stub toggling a browse placeholder, hardcoded 10s/45s skip amounts,
Combine-based duration observation swapping to ⏯️-only controls, and a
300×400 popover. Development then continued directly through M6.2–M6.9, M7,
M8, M9 without ever circling back to flip this file's status line. Found and
closed during a docs-sync pass on 2026-08-23; **no source changes were made**
to `ContentView.swift`, `PlayerViewModel.swift`, or `PocketRadioApp.swift`,
since the code already exceeds this milestone's scope. Reopening a `PLANNED`
milestone whose files are 15+ commits stale and reimplementing it to the
letter would have been a regression. Noted deviations, all *later*,
deliberate changes layered on top of the M6.1 baseline — not corrections to
this milestone's own implementation:

1. **Pills are artwork images, not truncated text labels.** M6.1 shipped
   text pills ("Stream 1", truncated station names). M6.4 (`e6f7001`)
   replaced them with 36×36 artwork/logo pills (podcast art, station logos,
   or a text/icon placeholder) to match the iOS widget more closely. The
   `PillType`/`selectedPill` state model this doc describes is unchanged;
   only the pill's visual rendering moved.
2. **`⋮` is no longer a stub.** M6.1 shipped it as a placeholder toggle onto
   an empty panel, exactly as this doc specifies ("no-op stub... in a later
   milestone"). M6.4 wired it to a real Favorites/Browse panel (search,
   reorder-by-drag, favorite toggle). By the time this status line was
   caught up, the "later milestone" had already landed.
3. **Pill tap no longer plays immediately.** M6.1 shipped "click pill →
   play immediately" per this doc. M6.8 (`f9f4316`, commit message "pill
   tap = visual only; play button = stop or start staged source")
   deliberately reversed this: tapping a pill now only stages/selects it
   (visual selection + tracklist prefetch); a separate ⏯️ press starts or
   resumes playback of the staged source. This was a considered UX change
   (avoid interrupting current playback just by browsing pills), not a bug.
4. **A scrubber exists**, despite this milestone explicitly deferring it. A
   later milestone (post-M6.2.5, tracked outside this doc) added
   `scrubBar` in `ContentView.swift`, gated to seekable (non-live) sources.
5. **Skip amounts are now fetched from the server**, despite this milestone
   saying to hardcode them and fetch "later." `PlayerViewModel.skipBackSeconds`
   / `skipForwardSeconds` still default to 10/45 but are overwritten by
   `fetchSkipSettings()` on login, which was pulled forward from this doc's
   stated future work.
