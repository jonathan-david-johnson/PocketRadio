# M4 — Full TUI shell + now-playing (with album art)

**Goal:** Stand up the full alt-screen TUI that mirrors the menubar's top half:
source pills, now-playing pane **with album art**, transport controls, and the
scrub bar. Both run modes now exist over the same engine.

**User checkpoint:** `pocket-radio` opens a menubar-like terminal UI; the
now-playing pane shows artwork (in a graphics-capable terminal) or a `chafa`
fallback; play/pause/skip/scrub work; `f` from mini upgrades into this view.

## Scope

- `internal/ui/theme`: Lip Gloss styles ported from the Pocket Casts palette
  (`primaryUi01/04/05`, `primaryText01/02`, `accent`) — light/dark via
  background detection.
- `internal/ui/full`: alt-screen Bubble Tea model:
  - top row: refresh + podcast pill + 3 stream pills + browse toggle;
  - controls row: skip-back / play-pause / skip-forward (or live indicator);
  - scrub bar (seekable sources only) with elapsed / `-remaining`;
  - now-playing pane (title + subtitle + art).
- `internal/art`: terminal-graphics **detection** ($TERM_PROGRAM, kitty/iTerm2,
  sixel caps) + renderers (kitty graphics, iTerm2 OSC 1337, sixel) + `chafa`
  shell fallback + graceful "no art" when piped/unsupported. Image fetch + cache
  by URL.
- Engine: expose pill selection / staged source (the menubar's "select vs play"
  rule — a pill stages a source; play starts it).

## Behaviors to test (red → green, one at a time)

1. `art.Detect()` maps representative `$TERM`/`$TERM_PROGRAM` values to the right
   `Protocol` (kitty / iterm2 / sixel / chafa / none) — table test.
2. `art` encoder: a tiny known image → a non-empty payload with the protocol's
   expected header/terminator (kitty `\x1b_G…`, iTerm2 `\x1b]1337;File=…`).
3. `art` fallback: with `Protocol==None` the renderer returns empty (UI shows the
   text layout) — no panic when piped.
4. theme: hex → Lip Gloss color parity with the menubar palette (spot-check a few).
5. Engine staging: selecting a pill sets `StagedSource` without changing the
   playing `Source`; `TogglePlayback` on a different staged source switches to it.
6. full model: given an engine `NowPlaying`, `View()` contains the title and a
   `play`/`pause` glyph matching `Playing` (golden-ish substring assertions).
7. scrub: dragging maps a column position to a seek time and calls
   `engine.Scrub`.

> The UI is the thin layer; keep logic in the engine. Test the model's
> `Update`/`View` for state→render mapping, not pixel layout. Art protocols are a
> boundary — encoders are pure (bytes in → bytes out) and unit-tested; the actual
> terminal render is verified by the checkpoint, not a test.

## Out of scope

Up Next / New Releases / Browse lists and detail panes (M5), lyrics + ACR (M6).
The bottom section can show now-playing only this milestone.
