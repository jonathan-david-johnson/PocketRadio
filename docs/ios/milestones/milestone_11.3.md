# iOS M11.3 — `RadioPlaybackStarter` extraction (pure refactor)

**Status**: COMPLETED (`87d288c`)
**Depends on**: nothing (M11 umbrella: `milestone_11.md`)
**Parallel-safe with**: M11.1, M11.2, M11.4
**Required by**: M11.6

---

## Goal

One function that starts a radio station, used everywhere. **No behavior change**
to existing call sites — this is a mechanical extraction whose value is that the
register-before-load invariant stops being copy-pasted.

---

## Why

Starting a station has a non-obvious mandatory ordering. Per
`RadioStationRegistry`'s own doc comment: `PlaybackQueue` reloads episodes from
SQLite by UUID after queuing, and `RadioStation` is not in SQLite, so **without
registering first the queue holds a dead stub**.

There are already three call sites, and two have drifted:

| Call site | Registers | Loads | Tracklist prefetch | Widget republish |
|---|---|---|---|---|
| `podcasts/AppPlayRadioStationIntentExtension.swift:32-53` | yes | yes | yes | yes |
| `podcasts/Radio/StationDetailViewController.swift:494-495` | yes | yes | no | no |
| M11.6 CarPlay tap | — | — | — | — |

Adding CarPlay as a fourth hand-rolled copy is how the invariant eventually gets
dropped.

---

## Done when

### 1. The type exists

New file `podcasts/Radio/RadioPlaybackStarter.swift`.

```swift
/// Single entry point for starting live radio playback. Encapsulates the
/// register-before-load invariant (see `RadioStationRegistry`) plus the
/// optional tracklist prefetch and widget republish.
final class RadioPlaybackStarter {
    static let shared = RadioPlaybackStarter(...)

    /// - Parameters:
    ///   - station: already-resolved station
    ///   - source: analytics source for `AnalyticsPlaybackHelper.currentSource`
    ///   - prefetchTracklist: kick a `RadioTracklistService` fetch so artist/title
    ///     populate before the first ICY frame (KCRW's ICY cadence lags 10–20s)
    ///   - republishWidgetState: force a `WidgetHelper` App Group write + reload
    /// - Returns: `.startedPlayback`, `.toggledPause`, or `.resumed`
    @discardableResult
    func play(
        station: RadioStation,
        source: AnalyticsSource,
        prefetchTracklist: Bool = true,
        republishWidgetState: Bool = true
    ) -> StartResult

    /// Resolve then play. Registry first (instant), radio-browser by-UUID fallback.
    /// Returns nil if unresolvable.
    @discardableResult
    func play(stationId: String, source: AnalyticsSource, ...) async -> StartResult?
}
```

Behavior, lifted verbatim from `AppPlayRadioStationIntentExtension.intentPlayStation`:

- [x] If `PlaybackManager.shared.currentEpisode()?.uuid == station.uuid`, call
      `PlaybackActionHelper.playPause()` and return `.toggledPause`. Do **not**
      re-load — reloading a live stream forces a TCP reconnect and upstream preroll
      re-injection.
- [x] Otherwise `RadioStationRegistry.shared.register(station)` **then**
      `PlaybackManager.shared.load(episode: station, autoPlay: true, overrideUpNext: false)`.
      Order is load-bearing.
- [x] When `prefetchTracklist` and `station.tracklistUrl` is non-nil and non-empty,
      fire a detached `Task` calling
      `RadioTracklistService.shared.fetch(stationId:url:)`. Best-effort, errors
      swallowed.
- [x] When `republishWidgetState`, call
      `WidgetHelper.shared.republishAllPocketRadioState()` before returning.
- [x] Set `AnalyticsPlaybackHelper.shared.currentSource = source` before loading.

### 2. Testability seam

`PlaybackManager` and `WidgetHelper` are singletons; do not try to refactor them.
Inject narrow protocols instead:

```swift
protocol RadioStationRegistering { func register(_ station: RadioStation) }
protocol RadioEpisodeLoading {
    func currentEpisodeUuid() -> String?
    func load(station: RadioStation)
    func togglePlayPause()
}
```

- [x] Production adapters forward to `RadioStationRegistry.shared` /
      `PlaybackManager.shared` / `PlaybackActionHelper`.
- [x] `RadioPlaybackStarter.shared` wires the production adapters.
- [x] `init` takes both protocols so tests inject fakes.
- [x] Tracklist prefetch and widget republish are injected as closures
      (`(RadioStation) -> Void`) so tests can observe them without network.

### 3. Call sites migrated — **no behavior change**

- [x] `AppPlayRadioStationIntentExtension.intentPlayStation` delegates to the async
      `play(stationId:source:)`. Keep its existing `FileLog` lines and the two
      `Analytics.track(.pocketRadioWidgetInteraction, ...)` calls at the call site —
      analytics event names differ per caller and do not belong in the starter.
- [x] `StationDetailViewController.swift:494-495` calls
      `play(station:source:.player, prefetchTracklist: false, republishWidgetState: false)`
      — flags chosen to **preserve today's behavior exactly**. Changing them is a
      separate decision, not this refactor.

### 4. Tests

New file `PocketCastsTests/Tests/Radio/RadioPlaybackStarterTests.swift`.

- [x] `testRegistersBeforeLoading` — fakes record an ordered call log; assert
      `register` appears before `load`. **This is the regression test that
      justifies the whole milestone.**
- [x] `testAlreadyCurrentTogglesPauseAndDoesNotReload` — `currentEpisodeUuid()`
      returns the station's uuid → `togglePlayPause` called once, `load` never
- [x] `testPrefetchFiresWhenTracklistUrlPresent`
- [x] `testPrefetchSkippedWhenTracklistUrlNil`
- [x] `testPrefetchSkippedWhenTracklistUrlEmptyString` — the existing intent guards
      on `!url.isEmpty`; preserve it
- [x] `testPrefetchSkippedWhenDisabledByFlag`
- [x] `testWidgetRepublishSkippedWhenDisabledByFlag`

No network, no Supabase, no simulator UI.

---

## Files

| File | Change |
|---|---|
| `podcasts/Radio/RadioPlaybackStarter.swift` | **new** — needs `project.pbxproj` registration |
| `podcasts/AppPlayRadioStationIntentExtension.swift` | delegate to starter |
| `podcasts/Radio/StationDetailViewController.swift` | delegate to starter (lines ~494-495) |
| `PocketCastsTests/Tests/Radio/RadioPlaybackStarterTests.swift` | **new** — auto-discovered |

> `StationDetailViewController.swift` has **uncommitted changes on `remoteplay`**
> from in-progress Global M1.1 remote-playback work. Rebase/coordinate before
> editing, and keep this milestone's diff limited to the play call.

---

## Verification

```bash
cd pocket-radio-ios
make format
make build_staging
make test_staging ONLY_TESTING=PocketCastsTests/RadioPlaybackStarterTests
```

Manual — this is a refactor, so the check is that **nothing changed**:

1. Tap a station in the phone's Favorites tab → plays as before
2. Tap the same station again while playing → shows detail, does not rebuffer
3. Tap a station on the Pocket Radio home-screen widget → plays, widget face
   updates immediately (this is what `republishAllPocketRadioState` protects)
4. Widget tap on the already-playing station → pauses (does not restart the stream)

---

## Out of scope

- Changing whether `StationDetailViewController` prefetches the tracklist or
  republishes widget state — deliberately preserved as-is
- Refactoring `PlaybackManager` itself
- CarPlay usage of the starter (M11.6)

---

## Commit

TBD.
