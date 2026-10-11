# Bug 10 — Station detail buttons shift when the Identify button comes and goes, and "Pause" is really a stop

**Status:** Open. Reported by the user on 2026-10-10 on the device. Not fixed. The layout cause is read from the code and not yet seen in a debugger. Deferred: "down the road".
**Evidence:** `pocket-radio-ios/podcasts/Radio/StationDetailViewController.swift` (`setupLayout`, `updateIdentifyButton`, `updatePlayButton`, `togglePlay`). The user wrote "song id (ADR?)": it is the ACR **Identify** button, the `music.note.list` icon that listens to the stream and identifies the song.

## Symptom A — the Play/Pause and heart buttons are spaced oddly, and it changes

The row under the station logo holds Identify, Play/Pause, and Favorite. Sometimes the Identify icon is there and sometimes it isn't, and when it is missing the other two buttons are spaced strangely.

### Root cause (read from the code, unconfirmed on screen)

- `buttonStack` is a horizontal `UIStackView` with `distribution = .equalSpacing`, `alignment = .center`, and its width pinned to the full width of `mainStack`.
- `identifyButton` is `isHidden = true` until `updateIdentifyButton` runs. It is hidden whenever the station has no tracklist, **or while an Apply session is live** (`isHidden = !hasTracklist || isApplying`).
- A hidden arranged subview leaves the stack's layout. With three buttons, `.equalSpacing` spreads them across the whole width. With two, it pushes Play/Pause and the heart to the two opposite edges.
- `isApplying` flips when an Apply session starts or stops, so the row re-lays out with no user action. That is the "random" part.
- The Play/Pause title changes width ("Play" and "Pause"), which shifts the gaps a little more.

### Proposed fix

- Lay the buttons out as a centered cluster with fixed spacing, for example `distribution = .fill` inside a container that centers it, so two or three buttons sit together whatever is hidden.
- Keep the buttons' order and spacing the same whether or not Identify is visible. Its slot can collapse without moving the others apart.
- Test with a snapshot or a frame check for three cases: Identify shown, Identify hidden in Apply, Identify hidden for a station with no tracklist.

## Symptom B — the button says "Pause", but nothing is paused

Tapping it calls `PlaybackManager.shared.pause()`. The next tap reloads the station (`RadioPlaybackStarter.reload`), a fresh connection. A live stream can't resume from where it was paused, so in practice this is a stop.

### Proposed fix

- Rename the title and the symbol to **Stop** (`stop.fill`). Keep **Play** for the other state.
- Call `PlaybackManager.stopRadioPlayback()` instead of `pause()`, so it matches the lock-screen Stop and keeps the restartable stopped entry ([ADR 0006](../adr/0006-stopping-live-radio-keeps-a-restartable-lock-screen-entry.md)). Check what the screen shows while stopped.
- The accessibility label should say "Stop" as well.

## Files involved

- `podcasts/Radio/StationDetailViewController.swift`: `setupLayout`, `updateIdentifyButton`, `updatePlayButton`, `togglePlay`.
- A test through the screen's existing `_…ForTesting` seams for the three layout cases and the title.
