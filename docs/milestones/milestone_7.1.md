# M7.1: Mute + Stop replace skip for live streams

**Status**: COMPLETED 2026-05-18 — shipped on `pocket-casts-ios` trunk in commit `dad2b1d`.
**Builds on**: M7 (committed at `1a7134c`).

## Goal

For live radio streams (`RadioStation`), replace the skip-back / skip-forward controls with mute + stop everywhere they exist (in-app player, mini player, lock screen, CarPlay, keyboard shortcuts). Skip on a live stream forces a TCP reconnect = preroll re-injection by the upstream (e.g. KCRW). Mute keeps the connection alive; stop is an explicit teardown the user opts into.

## Done when

- While a `RadioStation` is playing, the main now-playing screen shows **mute** and **stop** buttons in place of skip-back / skip-forward.
- Mini player likewise shows mute + stop (or hides skip if layout can't fit both).
- Mute toggles `AVPlayer.isMuted`; the stream stays connected and no preroll plays on unmute.
- Stop fully tears down playback (same as Up Next end-of-queue / explicit "stop" action). Resuming the same station after stop is a fresh connection (preroll expected — by design).
- Lock screen `MPRemoteCommandCenter`: `skipBackwardCommand` / `skipForwardCommand` / `previousTrackCommand` / `nextTrackCommand` are **disabled** while a `RadioStation` is current; `stopCommand` is **enabled**. (No system "mute" command exists; user uses hardware/system volume.)
- CarPlay inherits the above via shared `MPRemoteCommandCenter` — no separate wiring needed, but smoke-test it if possible.
- Keyboard shortcut skip-back / skip-forward (`MainTabBarController+shortcuts.swift`) is a no-op when current item is a `RadioStation`.
- When the current item transitions from `RadioStation` → regular `Episode` (or vice versa), the visible/enabled controls update.
- Watch app changes are **out of scope** for M7.1 — track as M7.2 if needed.

## Architecture

- **Predicate**: `currentEpisode is RadioStation` (already in use at `podcasts/DefaultPlayer.swift:95`).
- **Mute state**: `AVPlayer.isMuted` is the source of truth. UI reflects it via KVO or a published property on `PlaybackManager`.
- **Stop semantics**: reuse the existing teardown path that pause+endPlayback already provides. Don't invent a new lifecycle — find the `PlaybackManager` end-of-queue / explicit-stop method and call it.
- **In-app button swap**: keep the existing skip-button outlets and Auto Layout slots; swap their **target action + image + accessibility label** at runtime based on the current item. This keeps XIB diffs minimal.
- **Lock-screen command toggle**: at the same place `PlaybackManager` already enables/disables MPRemoteCommands per-item, add a branch that flips skip vs stop based on `is RadioStation`.

Follow the in-repo predicate pattern (`is RadioStation`) rather than introducing a `BaseEpisode.isLiveStream` flag. The predicate is one line, already used, and we want zero ripple into `Modules/DataModel`.

## Files

### NEW

- None expected. (If the per-item command-toggle logic becomes large, factor into `podcasts/Radio/RadioPlaybackControls.swift` — but try inline first.)

### EDIT

- `podcasts/NowPlayingPlayerItemViewController.swift` — swap skip buttons → mute/stop when `currentEpisode is RadioStation`; subscribe to `isMuted` for icon state.
- `podcasts/MiniPlayerViewController.swift` — same swap; if both can't fit, hide skip and keep play/pause + stop only.
- `podcasts/PlaybackManager.swift` — gate `skipBackwardCommand` / `skipForwardCommand` / `nextTrackCommand` / `previousTrackCommand` `isEnabled` on `is RadioStation`; enable `stopCommand` with handler that tears down playback; expose `toggleMute()` + `isMuted` for the in-app UI.
- `podcasts/Main/MainTabBarController+shortcuts.swift` — `handleSkipBack` / `handleSkipForward` early-return when current item is a `RadioStation`.
- `podcasts/Radio/RadioStation.swift` — only if a small helper (e.g. `var supportsSeek: Bool { false }`) makes the call sites cleaner. Optional.

### NO CHANGE

- `podcasts/VideoViewController.swift` — radio streams aren't video. Leave as-is.
- `Pocket Casts Watch App/**` — deferred to M7.2.
- `Modules/DataModel/**` — no schema change; `RadioStation` already exists app-side.

## Risks / Edge cases

- **Mute persisting across items**: if user mutes a stream then a regular podcast starts (e.g. Up Next continues), `isMuted` must reset to `false` automatically when the current item changes. Mitigation: in the `currentEpisode` setter / change observer, set `isMuted = false` when the new item is not a `RadioStation` (or always — safer).
- **Stop button reused as skip after transition**: if the in-app buttons swap based on current item, ensure the swap runs on **every** item change, not just on player view load. Mitigation: hook into the same NotificationCenter event the play/pause icon already uses.
- **Lock-screen control flicker**: enabling/disabling `MPRemoteCommand` mid-playback can momentarily reshape the lock screen. Acceptable. Don't try to be clever about it.
- **CarPlay**: investigator reports no separate CarPlay skip wiring — defaults flow through `MPRemoteCommandCenter`. If a separate CarPlay template is in use that we missed, plan needs an addendum.
- **Stop command on regular podcasts**: don't enable `stopCommand` for regular episodes — that would change long-standing UX for the upstream app. Only enable for `RadioStation`.
- **Accessibility**: mute/stop buttons need correct `accessibilityLabel` (localized via L10n if a string already exists; otherwise add to `Localizable.strings`).

## Reference sweep

```bash
# All skip wiring (cross-check investigator's table is exhaustive)
grep -rn "skipBack\|skipForward\|skipBackwardCommand\|skipForwardCommand\|nextTrackCommand\|previousTrackCommand\|skipBackTime\|skipForwardTime" podcasts/ "Pocket Casts Watch App/" Modules/

# All current uses of `is RadioStation` (existing predicate sites — model the new ones on these)
grep -rn "is RadioStation\|as? RadioStation\|as! RadioStation" podcasts/ Modules/

# AVPlayer / isMuted access points (in case there's already a mute hook we should reuse)
grep -rn "isMuted\|\.muted\b" podcasts/ Modules/

# MPRemoteCommandCenter enable/disable patterns currently in use
grep -rn "\.isEnabled = " podcasts/PlaybackManager.swift | head -40

# stopCommand wiring (does it already exist anywhere?)
grep -rn "stopCommand" podcasts/ Modules/
```

## Automated tests

- `PocketCastsTests/Tests/Radio/RadioPlaybackControlsTests.swift` (new) — XCTest + `@testable import podcasts`. Instantiate `PlaybackManager` (or a thin testable wrapper), set current item to a `RadioStation`, assert: `skipBackwardCommand.isEnabled == false`, `stopCommand.isEnabled == true`. Set current item to a regular `Episode`, assert the reverse.
- `RadioPlaybackControlsTests.swift` — assert `toggleMute()` flips `isMuted`; setting current item to non-radio resets `isMuted = false`.
- View-controller tests are low value here (UIKit + XIB outlets) — skip unless trivial. Manual smoke covers the UI.

## Manual smoke

1. `make run_sim`
2. Play a curated KCRW station from Favorites.
3. Verify mute + stop buttons appear in the main player **and** mini player (not skip-back / skip-forward).
4. Tap mute — audio silences, stream stays connected (watch network activity or wait, then unmute: should resume instantly without preroll).
5. Tap stop — playback ends, mini player disappears (or shows whatever the upstream "no current item" state is).
6. Re-tap the same station — preroll plays (expected; this is a fresh connection).
7. Lock the device. Lock-screen controls show play/pause + stop, **no** skip buttons.
8. Unlock. Play a regular podcast episode (any subscribed podcast). Confirm skip-back / skip-forward return, mute/stop hidden, lock-screen skip buttons back.
9. Mid-podcast, switch back to a radio station via Favorites. Controls swap to mute/stop without needing to relaunch the player.
10. Keyboard shortcut: while a radio station plays, press the skip-back / skip-forward keyboard shortcut — nothing happens. Switch to a podcast; shortcuts work normally again.
11. CarPlay (if a CarPlay sim or head unit is handy): confirm radio shows stop, not skip. If not handy, log as a follow-up smoke after M7.1 ships.

## Agentic plan

Sequential phases. Each agent reads this file as ground truth.

### Phase 1 — Implementation
- Agent: `general-purpose`, model: Sonnet 4.6
- Files allowed: every file in the **EDIT** list above, plus the new test file under `PocketCastsTests/Tests/Radio/`. No edits outside this list without escalating.
- First action: run the **Reference sweep** grep block; reconcile against the EDIT list and report any unexpected sites before writing code.
- Verify: `make build_staging`, then `make test_staging ONLY_TESTING=PocketCastsTests/RadioPlaybackControlsTests`.

### Phase 2 — Review
- Agent: `caveman:cavecrew-reviewer`, model: Sonnet 4.6
- Focus:
  - Does mute reset to `false` on every item change (not just the radio → podcast transition)?
  - Is `stopCommand` enabled only for `RadioStation`? (regression risk for upstream UX)
  - Are all four skip-style remote commands disabled, not just two? (`previous`/`nextTrackCommand` are easy to miss)
  - Memory: any new NotificationCenter observers without a matching remove?
  - L10n: any user-visible strings hardcoded instead of going through `L10n` / `Localizable.strings`?

### Phase 3 — Manual smoke
- Human runs the **Manual smoke** list. Sign off before commit.
