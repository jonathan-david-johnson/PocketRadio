# Bug 1 — Album art not rendering; pause/resume broken on live streams

**Status:** Fixed (2026-06-08)

---

## Symptom A: Album art placeholder always shown

Album art box shows a placeholder rectangle regardless of source.

### Root cause

Two separate causes:

1. **tmux blocks terminal graphics detection.** When running inside tmux, `TERM_PROGRAM=tmux` and `LC_TERMINAL=""`. `art.DetectEnv` correctly returns `ProtocolNone`. Not a bug — expected behavior.

2. **Missing `c` (columns) parameter in the kitty graphics escape sequence.** Without `c`, the terminal picks a default size based on the image pixel dimensions and the cell size. A 50×50 pixel album-art thumbnail typically occupies only 2–3 columns, leaving a 9-column gap between the image and the text. Additionally, the escape sequence had no `i` (image ID) parameter, so each new image accumulated with a fresh random ID instead of replacing the previous one.

### Status

Protocol detection works correctly. Art fetch (HTTP download + image decode) works correctly — verified via `full.artReady` log line. The escape sequence reaches the terminal intact (confirmed in Ghostty/kitty). The failure was in the image-sizing parameters: the image was rendering, but in a tiny footprint that made it look like the placeholder was still visible.

### Fix applied (2026-06-08)

1. **`kittyEncode` now sets `c=<width>`** so the image occupies exactly the art-block width (12 columns). The terminal calculates the row height automatically from the aspect ratio and cell size, which for square art yields ~6 rows — matching the placeholder box.

2. **`kittyEncode` now sets `i=1`** (fixed image ID). Every new image overwrites the previous one instead of stacking on top.

3. **`art.DetectEnv` now detects Ghostty** (`TERM_PROGRAM=ghostty`) as kitty-compatible, so the protocol is `ProtocolKitty` instead of `ProtocolNone`.

4. The escape sequence remains embedded in the Bubble Tea `View()` string — no bypass is needed. The original hypothesis that `lipgloss`/`charmbracelet/x/ansi` would corrupt the bytes was not observed in Ghostty; the bytes reach the terminal intact.

5. **Chafa continues to work in `View()`** — its block-character output is plain ANSI and is handled correctly by width measurement.

### Workaround

Install `chafa` (`brew install chafa`) and run outside tmux. Chafa renders block-character approximations of album art via shell subprocess, producing plain ANSI output that Bubble Tea can handle. Detection: `art.Detect()` falls back to `ProtocolChafa` when no graphics protocol is found but `chafa` is on PATH.

---

## Symptom B: Pause/resume broken after switching sources; live streams stuck "playing"

After switching from a podcast to a live radio station (or vice versa), pressing space would not toggle playback correctly. The UI glyph changed but the engine immediately flipped back to "playing" on the next key press.

### Root cause

The pump's Tick handler unconditionally overwrote `NowPlaying.Playing` with the raw mpv player state on every position tick (~1 Hz):

```go
// Before fix — in engine.go pump()
case player.Tick:
    st := e.player.State()
    e.update(func(n *NowPlaying) {
        n.Position = st.Position
        n.Playing = st.Playing   // ← overwrote engine intent
        n.IsLive = st.IsLive
    })
```

For live streams (AAC over HTTP), mpv can auto-reconnect after a pause: the TCP connection drops, mpv reconnects, and fires `pause=false` (playing) again. The next Tick then reset `n.Playing = true`, making `TogglePlayback` think the stream was still playing and issue another `Pause()` command instead of `Resume()`.

Additionally, `TogglePlayback` was reading `e.player.State().Playing` (raw mpv state) rather than `e.now.Playing` (engine intent), so it always saw the mpv-side value that Ticks had just restored.

### Fix applied (2026-06-08)

1. Removed `n.Playing = st.Playing` from the Tick handler. The `Playing` field is now set only by explicit engine calls: `PlayTarget` (→ true), `TogglePlayback`/`Pause` (→ false), `TogglePlayback`/`Resume` (→ true).

2. Changed `TogglePlayback` to read `e.now.Playing` (the engine's intent state) instead of `e.player.State().Playing`.

The engine's intent is now authoritative for the UI playing state. mpv's raw pause property is no longer allowed to override it via Ticks.

### Files changed

- `internal/library/engine.go` — pump Tick handler, TogglePlayback (Symptom B)
- `internal/art/art.go` — `kittyEncode` (added `c` and `i` params), `DetectEnv` (added Ghostty detection) (Symptom A)
