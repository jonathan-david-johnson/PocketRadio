# M9: UI Rebuild — Backdrop + Now Playing State

**Status**: IN PROGRESS

Several M9 features were built during the M8 bugs polish pass (see `m8_bugs.md` resolution). Remaining items are backdrop debounce/fade animation and the NOW badge.

## Goal

Top panel comes alive: backdrop fades in on focus settle, progress bar and controls appear while something is playing, currently-playing tile shows a NOW badge. This milestone completes the "top panel IS now playing" design.

## Done when

- [ ] Focusing a tile for 150ms triggers backdrop load (artwork URL → `backdrop.uri`); faster D-pad movement cancels and restarts the timer — no flicker
- [ ] Backdrop fades in at 0.2 opacity with 0.3s `inOutQuad` animation on load
- [x] When audio is playing:
  - [x] Progress bar visible in top panel, updates every 1s (reuses `onPosTimer` pattern)
  - [x] Controls hint visible
  - [x] Top panel title/subtitle locked to **playing item** while browsing (via `updateTopPanelMeta` guard)
- [ ] Playing tile: NOW badge (small ACCENT-colored Rectangle + Label overlay, top-right of tile Poster)
- [x] Live streams: progress bar hidden, controls hint shows play/pause only
- [x] `onAudioState` updates top panel progress visibility on play/pause/stop/error
- [x] **Full-screen NowPlaying overlay** added (not originally in M9 spec but built during M8 bugs): large artwork, title, progress, skip, Back return
- [ ] **Remaining:** FF/REW transport keys in grid/nav modes (currently only active in nowplaying mode)

## Already Built (during M8 bugs)

### Now Playing top panel state (MainScene.brs)
- `m.nowPlayingActive` toggled on playEpisode/playStation; hides progress/controls on stop/error/finish
- `onPosTimer` drives `progressFill.width` + `timeLabel.text` every 1s
- `onAudioState` handles play/pause/stop/finished/error states
- Top panel title/subtitle locked to playing item via `if m.nowPlayingActive = true then return` guard in `updateTopPanelMeta()`

### NowPlaying overlay (MainScene.xml + NowPlaying.xml/.brs)
- Full-screen overlay component with large artwork (480×480), title, podcast name, progress bar, time, skip hints
- Navigable from nav bar via **Up** when `m.nowPlayingActive`
- **Play/Pause** via Play button or D-pad **OK**
- **Skip** via Left/Right D-pad or Rewind/FastForward media keys
- **Back** returns to nav bar

### Transport keys (MainScene.brs)
- Rewind/FastForward mapped to skip back/forward in `nowplaying` mode
- Left/Right D-pad also mapped to skip in `nowplaying` mode
- Live streams correctly gated (`not m.isCurrentlyLive`)

## What to Build

### Backdrop debounce + fade animation
```
m.focusTimer = Timer, duration=0.15s, repeat=false
onTileFocused() → m.focusTimer.control = "start" (restart cancels previous)
onFocusTimer() → set backdrop.uri = artworkUrl; trigger fade-in animation
```

```xml
<Animation id="backdropFade" duration="0.3" easeFunction="inOutQuad">
  <FloatFieldInterpolator fieldToInterp="backdrop.opacity"
                          keyValue="[0.0, 0.2]" key="[0.0, 1.0]" />
</Animation>
```
Reset opacity to 0 before firing. Currently backdrop loads immediately on every tile focus change (no debounce, no fade).

### NOW badge (TileItem.brs)
- Interface field `isNowPlaying` (boolean, onChange="onNowPlayingChanged")
- Show/hide a small Rectangle + "NOW" Label overlay when true
- MainScene sets `tileGrid` item's `isNowPlaying` field after finding the playing item index

### Global transport keys (MainScene.brs)
Move FF/REW (`fastforward`/`rewind`) handling into `grid` and `nav` modes too (whenever `m.nowPlayingActive` and not live). Currently only active in `nowplaying` mode.

## Implementation Strategy

1. Backdrop debounce timer + fade animation.
2. Top panel progress + controls visibility toggle on play/stop.
3. `onPosTimer` drives progress bar in top panel (same 1s cadence).
4. NOW badge on TileItem.
5. Transport key handling global (not mode-gated).

## User Checkpoint

Navigate tiles fast → backdrop doesn't flicker, settles 150ms after stop. Play episode → progress bar appears in top panel, updates live. Pause → bar freezes. Stop → bar disappears. Play KCRW → live, no progress bar. Look at tile grid → playing tile has NOW badge.

## Commit

TBD.
