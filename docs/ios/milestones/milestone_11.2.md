# iOS M11.2 — CarPlay connection flag + lyric suppression

**Status**: COMPLETED (`6728697`)
**Depends on**: nothing (M11 umbrella: `milestone_11.md`)
**Parallel-safe with**: M11.1, M11.3, M11.4

---

## Goal

Introduce a single reliable "is CarPlay connected right now?" signal, and use it
to stop live lyric lines from hijacking the CarPlay album field (D9).

---

## The problem

`NowPlayingHelper.setRadioAlbumTitle(_:)` (`podcasts/NowPlayingHelper.swift:115`)
replaces `MPMediaItemPropertyAlbumTitle` with the currently-synced lyric line.
Its only caller is `StationDetailViewController.swift:620`.

Consequences:

- CarPlay's Now Playing screen reads the same `MPNowPlayingInfoCenter` as the lock
  screen, so the album field on the car display flickers lyric lines.
- Worse, it only happens **while that view controller is alive**. Whether your car
  dash scrolls lyrics depends on which screen the phone happened to be on when you
  plugged in. Nondeterministic behavior is worse than either consistent choice.

Decision (D9): **no lyric lines in CarPlay.** The album field keeps the stable
track album.

---

## Done when

### 1. Connection flag

- [x] `CarPlaySceneDelegate` gains `static private(set) var isConnected: Bool = false`.
- [x] Set `true` in `templateApplicationScene(_:didConnect:)`
      (`CarPlaySceneDelegate.swift:15`).
- [x] Set `false` in `templateApplicationScene(_:didDisconnectInterfaceController:)`
      (`CarPlaySceneDelegate.swift:28`).
- [x] Expose a test seam so the flag can be driven without a CarPlay scene:
      `static func setConnectedForTesting(_ value: Bool)`, or make the setter
      `internal`. Keep it obviously test-only in the doc comment.

Why a static flag rather than scanning `UIApplication.shared.connectedScenes` for a
`CPTemplateApplicationScene`: the scan is main-thread-only, allocates, and would run
on every lyric tick (~1/s). The delegate already has exact connect/disconnect
callbacks — use them.

### 2. Suppression

- [x] `NowPlayingHelper.setRadioAlbumTitle(_:)` returns early when
      `CarPlaySceneDelegate.isConnected == true`.
- [x] Suppress at the **helper**, not at the `StationDetailViewController` call
      site, so any future caller inherits the rule.
- [x] Guard the reference for non-iOS targets. `NowPlayingHelper` is compiled for
      watchOS / App Clip / tvOS; `CarPlaySceneDelegate` is not. Wrap in the same
      `#if !os(watchOS) && !APPCLIP && !os(tvOS)` fence used elsewhere in that file
      (see `stationLogoImage(for:)` at `NowPlayingHelper.swift:70`).

### 3. Album field recovers on disconnect

When CarPlay disconnects mid-track, the album field is whatever the last lyric line
left behind.

- [x] On disconnect, if a live station is playing, re-publish the correct album via
      `NowPlayingHelper.setRadioTrackInfo(...)` so the field returns to the real
      album title rather than a stale lyric fragment.

### 4. Tests

New file `PocketCastsTests/Tests/CarPlay/CarPlayConnectionStateTests.swift`.

- [x] `testDefaultsToDisconnected` — `isConnected` is `false` at start
- [x] `testAlbumTitleWritesWhenDisconnected` — with the flag `false`,
      `setRadioAlbumTitle("line one")` results in
      `MPNowPlayingInfoCenter.default().nowPlayingInfo?[MPMediaItemPropertyAlbumTitle]`
      equal to `"line one"`
- [x] `testAlbumTitleSuppressedWhenConnected` — with the flag `true`, the same call
      leaves the previous album title untouched
- [x] `tearDown` resets the flag to `false` and clears
      `MPNowPlayingInfoCenter.default().nowPlayingInfo`

`MPNowPlayingInfoCenter` is readable and writable in a simulator-hosted unit test —
no player or CarPlay hardware required. Set a known album title in `setUp` so the
"untouched" assertion has something concrete to compare against.

---

## Files

| File | Change |
|---|---|
| `podcasts/CarPlay/CarPlaySceneDelegate.swift` | add static flag + set/clear in the two scene callbacks + album recovery on disconnect |
| `podcasts/NowPlayingHelper.swift` | early return in `setRadioAlbumTitle` |
| `PocketCastsTests/Tests/CarPlay/CarPlayConnectionStateTests.swift` | **new** — auto-discovered |

No `project.pbxproj` change — no new app-side source file.

---

## Verification

```bash
cd pocket-radio-ios
make format
make build_staging
make test_staging ONLY_TESTING=PocketCastsTests/CarPlayConnectionStateTests
```

Manual (Simulator → I/O → External Displays → CarPlay):

1. Play KCRW, open `StationDetailViewController` on the phone, wait for synced lyrics
2. Phone header still scrolls lyric lines — unchanged
3. CarPlay Now Playing album field shows the **track album**, not a lyric line
4. Disconnect CarPlay → album field on the phone's lock screen returns to the album
   title (not a frozen lyric fragment), then lyrics resume in the phone header

---

## Out of scope

- Any other CarPlay-conditional behavior — this milestone establishes the flag; other
  slices may consume it later
- Showing lyrics in CarPlay via a proper template (explicitly rejected, D9)

---

## Commit

TBD.
