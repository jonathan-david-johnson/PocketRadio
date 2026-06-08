# Go + Bubble Tea for the console TUI

We will build `pocket-radio-console` in **Go** with the **Bubble Tea** TUI
framework (Lip Gloss for styling, Bubbles for components), rather than
Python/Textual, Rust/Ratatui, or Swift (to match the menubar).

## Considered Options

- **Go + Bubble Tea (chosen).** Compiles to a single static binary, so the app
  ships as `brew install pocket-radio` with no runtime. Goroutines/channels fit
  the several background pollers (tracklist 30s, position save 30s, lyrics timer,
  mpv event loop) naturally. The Elm architecture renders both the mini one-line
  model and the full alt-screen model from one framework.
- **Python + Textual.** Produces the richest UI and has the best terminal-image
  story, but distribution needs a Python environment (pipx/uv), and Textual is
  alt-screen-first, which makes the one-line mini mode awkward.
- **Rust + Ratatui.** Also a single binary and very robust, but slower to build
  the feature surface and more async/TUI ceremony, for performance we do not need.
- **Swift (match the menubar).** Tempting for code reuse, but Swift's TUI story
  is weak and cross-platform terminal distribution is poor.

## Consequences

- The Swift `PocketCastsAPI` protobuf logic is **re-implemented**, not shared. It
  is hand-rolled varint encode/decode (~200 lines); the port is mechanical and
  covered by golden-byte tests. Accepted cost.
- Album art relies on terminal graphics protocols (kitty/iTerm2/sixel) with a
  `chafa` fallback; Go has no native image-in-terminal library as mature as
  Textual's, so we emit escape sequences ourselves.
