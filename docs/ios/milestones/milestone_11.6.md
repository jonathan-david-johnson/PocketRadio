# iOS M11.6 — Radio tab wiring (the visible feature)

**Status**: COMPLETED — 2294776
**Depends on**: M11.3, M11.4, M11.5
**Required by**: M11.7

---

## Goal

A **Radio tab** in CarPlay listing favorites + curated stations, tappable to play.
This is the slice the user actually sees; everything before it was scaffolding.

---

## Done when

### 1. The tab exists

- [ ] New file `podcasts/CarPlay/CarPlaySceneDelegate+Radio.swift`, mirroring the
      shape of `CarPlaySceneDelegate+Tabs.swift`.
- [ ] `createRadioTab() -> CPListTemplate` built with
      `CarPlayListData.template(title:emptyTitle:image:)` so it inherits the
      existing `didAppear` / `needsUpdate` reload plumbing.
- [ ] Registered in `CarPlaySceneDelegate.swift:21`:
      ```swift
      CPTabBarTemplate(templates: [
          createPodcastsTab(), createFiltersTab(),
          createDownloadsTab(), createRadioTab(), createMoreTab()
      ])
      ```
      Radio goes **before** More — More is the catch-all and belongs last. This is
      exactly 5 templates, CarPlay's hard cap. Adding a 6th silently truncates.
- [ ] Tab image: SF Symbol `dot.radiowaves.left.and.right` via
      `UIImage(systemName:)` (D12).
- [ ] `emptyTitle:` = `L10n.carplayRadioEmpty`. In practice unreachable — the
      curated section always renders — but `CarPlayListData` requires it.

### 2. Data source: sync paint, async refresh (D5, D11)

```swift
var radioTabSections: [CPListSection] {
    let model = RadioCarPlayRowBuilder.sections(
        favorites: RadioFavoritesCache.shared.snapshot(),
        curated: CuratedStationsLoader.load(),
        isSignedIn: ServerSettings.userId != nil,
        nowPlayingStationId: PlaybackManager.shared.liveStation(for: nil)?.uuid,
        maxRowsPerSection: Constants.Limits.maxCarplayItems
    )
    return model.map { convertToListSection($0) }
}
```

- [ ] The data-source closure is **fully synchronous** — cache read + bundle JSON
      only. It must never await.
- [ ] The same closure kicks `Task { await RadioFavoritesService.resolvedFavorites() }`.
      The service writes the cache and posts `.radioFavoritesChanged`; the observer
      added below reloads the template. **No bespoke completion callback** — the
      notification already needed for cross-surface updates does the job.
- [ ] Refresh on every `didAppear`, no throttle (D11). The service's in-flight guard
      (M11.4) prevents stacking.

### 3. Adapter: `RadioCarPlaySection` → `CPListSection`

- [ ] `convertToListSection(_:) -> CPListSection` in
      `CarPlaySceneDelegate+Radio.swift`. This is the **only** CarPlay-aware code in
      the feature — keep it mechanical.
- [ ] `CPListItem(text: row.title, detailText: row.detail, image: artwork)`
- [ ] `item.isPlaying = row.isPlaying`, `item.playingIndicatorLocation = .trailing`
- [ ] **Do not set `playbackProgress`.** Live streams have no progress; the existing
      `else` branch at `CarPlaySceneDelegate+Convert.swift:29` would render a
      misleading half-full bar for `duration == 0`.
- [ ] **Do not set `accessoryType = .cloud`.** That means "not downloaded" and is
      meaningless for a stream.
- [ ] `CPListSection(items:header:sectionIndexTitle:)` using `section.header`.
- [ ] Artwork this milestone: `row.logoAsset.flatMap(UIImage.init(named:))`, falling
      back to SF Symbol `dot.radiowaves.left.and.right`. Favicons land in M11.7 —
      **not** `noartwork-list-dark`, which is podcast-shaped and misleading.

### 4. Tap handler

- [ ] `stationTapped(_ row: RadioCarPlayRow)`:
      ```swift
      AnalyticsPlaybackHelper.shared.currentSource = .carPlay
      defer { interfaceController?.showNowPlaying() }

      if row.streamUrl.isEmpty {
          // Curated row — needs radio-browser resolution first (see M11.5)
          Task { await RadioPlaybackStarter.shared.play(stationId: row.stationId, source: .carPlay) }
      } else {
          RadioPlaybackStarter.shared.play(station: row.toRadioStation(), source: .carPlay)
      }
      ```
- [ ] The empty-`streamUrl` branch is **required**: `CuratedStation` carries
      `defaultSeedUUID` / `radioBrowserUUIDs`, not a stream URL. The async overload
      resolves it (registry first, then `RadioBrowserAPI`).
- [ ] `showNowPlaying()` fires in both branches via `defer`, matching
      `episodeTapped`'s pattern (`CarPlaySceneDelegate+Interaction.swift:43`).
- [ ] Tapping the already-playing station must **not** rebuffer — `RadioPlaybackStarter`
      already handles this by toggling pause instead of reloading. Do not add a
      second guard here.
- [ ] Do **not** call `AutoplayHelper.shared.playedFrom(playlist:)` — meaningless for
      a live stream.
- [ ] Do **not** route through `episodeTapped`. `RadioStation` conforms to
      `BaseEpisode` so it would compile, but it skips
      `RadioStationRegistry.register` and yields a dead-stub queue entry.

### 5. Notification wiring

In `CarPlaySceneDelegate.addChangeListeners()` (`CarPlaySceneDelegate.swift:46`):

- [ ] Add `.radioFavoritesChanged` to the data-updated list
- [ ] Add `Constants.Notifications.playbackMuteChanged` to the playback list (so
      M11.1's mute icon flips when muted from the phone or lock screen)
- [ ] `playbackTrackChanged` / `playbackStarted` are **already** subscribed, and
      `handlePlaybackStateChanged` already calls both `updateNowPlayingButtons` and
      `handleDataUpdated` — so row `isPlaying` and the M11.1 radio button set both
      update for free. Add nothing for those.

The existing 0.2s `Debounce` absorbs notification bursts.

### 6. Analytics

- [ ] `AnalyticsPlaybackHelper.shared.currentSource = .carPlay` before starting
      playback (the `.carPlay` source already exists — used by `episodeTapped`).
- [ ] No new analytics events. If station-tap tracking is wanted later, it belongs
      with the widget's `.pocketRadioWidgetInteraction` family, not here.

### 7. Tests

New file `PocketCastsTests/Tests/CarPlay/RadioCarPlayAdapterTests.swift`.

The adapter touches `CPListItem`, which is constructible in a simulator-hosted test
but barely readable. Keep assertions to what is genuinely observable:

- [ ] `testSectionCountMatchesModel` — N model sections → N `CPListSection`s
- [ ] `testItemCountMatchesRows` — per-section `items.count`
- [ ] `testSectionHeaderCarriedThrough` — `CPListSection.header`
- [ ] `testCuratedRowRoutesToAsyncResolve` — a pure helper
      `RadioCarPlayRouting.needsResolution(streamUrl:) -> Bool` returns `true` for
      `""`, `false` otherwise. Extract this rather than asserting on a write-only
      `handler`.

Everything genuinely behavioral is already covered by
`RadioCarPlayRowBuilderTests` (M11.5) and `RadioPlaybackStarterTests` (M11.3). Do
not contort tests to reach through CarPlay types — that's what D13 exists to avoid.

---

## Files

| File | Change |
|---|---|
| `podcasts/CarPlay/CarPlaySceneDelegate+Radio.swift` | **new** — no pbxproj edit needed, `podcasts/CarPlay` is a `PBXFileSystemSynchronizedRootGroup` |
| `podcasts/CarPlay/CarPlaySceneDelegate.swift` | add `createRadioTab()` to the tab bar; 2 new notification subscriptions |
| `PocketCastsTests/Tests/CarPlay/RadioCarPlayAdapterTests.swift` | **new** — auto-discovered |
| `podcasts/CarPlay/RadioCarPlayRowBuilder.swift` | curated `stationId` → `defaultSeedUUID` (see below) |
| `PocketCastsTests/Tests/CarPlay/RadioCarPlayRowBuilderTests.swift` | fixture gains `seedUUID`; new `testCuratedRowUsesSeedUUIDNotSlug` |
| `podcasts/Radio/RadioFavoritesService.swift` | post `.radioFavoritesChanged` only on a real change (see below) |

---

## Two corrections to the plan, found during implementation

**1. Curated `stationId` had to become `defaultSeedUUID`.** M11.5 emitted
`CuratedStation.id`, a slug (`"kexp"`). `RadioPlaybackStarter.play(stationId:)`
resolves through the registry then `RadioBrowserAPI.station(uuid:)` — both keyed
by radio-browser UUID — so every curated tap resolved to `nil` and did nothing,
and `isPlaying` could never match `RadioStation.uuid`. Resolving by seed UUID
also gets the curated name/logo/tracklist back for free, since
`RadioBrowserStation.toRadioStation()` re-applies `enhancementsByUUID`.

**2. The data source and the notification formed a reload loop.** The plan's
design has `radioTabSections` kick `resolvedFavorites()`, which posted
`.radioFavoritesChanged` unconditionally, which reloaded the visible template,
which re-entered `radioTabSections`. `RadioFavoritesService.performResolve()` now
compares against `cache.snapshot()` and posts only on a real change, so the cycle
terminates after one network round trip. Add/remove through
`RadioFavoritesManager` still posts as before.

---

## Verification

```bash
cd pocket-radio-ios
make format
make build_staging
make test_staging ONLY_TESTING=PocketCastsTests/RadioCarPlayAdapterTests
```

Manual — **Simulator → I/O → External Displays → CarPlay**:

1. Launch → CarPlay shows **5 tabs**: Podcasts, Filters, Downloads, Radio, More
2. Radio tab → "Favorites" section (if signed in with favorites) above "Stations"
   (KCRW, KEXP, NPR)
3. Tap KCRW → plays, Now Playing pushes automatically
4. Return to Radio tab → KCRW row shows the playing indicator
5. Tap KCRW again → **does not rebuffer**; Now Playing shows
6. Add a favorite on the phone → within ~1s the CarPlay list picks it up
7. Sign out on the phone → Favorites section disappears, Stations remains
8. Airplane Mode + force-quit + relaunch → Radio tab still lists cached favorites
   with real names, and tapping one still plays if the stream is reachable
9. Verify the More tab is still reachable (proves nothing was truncated at 5)

---

## Out of scope

- Favicon artwork for non-curated rows (M11.7)
- Station detail / tracklist / lyrics in CarPlay
- Reordering favorites from CarPlay
- Search (D3)

---

## Commit

`2294776` — feat(carplay): M11.6 — Radio tab wiring
