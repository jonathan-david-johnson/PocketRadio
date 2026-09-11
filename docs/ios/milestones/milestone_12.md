# iOS M12 — Tab layout model and render engine

**Status**: COMPLETED (2026-09-10)
**Depends on**: none
**Required by**: M12.1, M12.2, M12.3
**Design**: `docs/ios/architecture/configurable-tab-bar.md`
**Model**: **Opus 5**. Touches `MainTabBarController.viewDidLoad`, an index-based
UserDefaults migration, and a reference sweep across an enum with force-unwrapped
lookups. Sonnet is likely to miss a straggler and ship a build that compiles but
crashes on a deep link.

---

## Goal

Replace the hard-coded `pcTabs = [.podcasts, .filter, .discover, .streams, .profile]`
at `MainTabBarController.swift:86` with a persisted `TabLayout` that renders the
same five tabs by default.

**No user-visible change.** The bar looks and behaves exactly as it does today.
Success is measured by tests and by the absence of regressions, not by a feature.

---

## Done when

### 1. The model exists

- [x] `podcasts/Main/TabLayout/TabDestination.swift` — enum with cases
      `podcasts`, `playlists`, `discover`, `streams`, `profile`, `upNext`,
      `playlist(uuid:)`. Exposes `id: String`, `isCore: Bool`, `title()`,
      `icon()`, `makeRootViewController()`.
- [x] `id` for `.playlist` is `"playlist:<uuid>"`. All others are the bare case
      name. These strings are persisted and synced — do not change them later.
- [x] `isCore` is `true` for the first five, `false` for `upNext` and
      `playlist`. See `docs/ios/adr/0001-core-vs-extra-destinations-and-derived-overflow.md`.
- [x] `podcasts/Main/TabLayout/TabLayout.swift` — `Codable` struct holding
      `slots: [TabSlot]` and `updatedAt: Date`, plus `static let default`
      matching today's five.
- [x] `TabLayout.capacity(for: UITraitCollection) -> Int` returns `5` for every
      device. Single source of truth; do not inline the literal elsewhere.
- [x] `podcasts/Main/TabLayout/TabLayoutStore.swift` — reads and writes the
      layout as JSON in `UserDefaults`. Returns `.default` when absent or when
      decoding fails.

### 2. Render rules

- [x] Pure function producing the render plan from a layout and a capacity:
      visible slots, truncated slots, complement, `needsOverflow`.
- [x] `needsOverflow == !(complement.isEmpty && truncated.isEmpty)`.
- [x] With the default layout, `needsOverflow` is `false`. This is the property
      that keeps the bar identical to today.
- [x] Overflow itself is **not** built in this milestone. Only the flag.

### 3. `MainTabBarController` builds from the layout

- [x] `viewDidLoad` asks `TabLayoutStore` for the layout, computes the plan, and
      builds `viewControllers` from it.
- [x] `pcTabs` retained only if it makes the diff smaller; otherwise removed with
      a full reference sweep.
- [x] Destination root view controllers are built through
      `makeRootViewController()`, not inline in `viewDidLoad`.
- [x] `tabBarItem.tag` no longer carries meaning. Anything reading it is
      converted to read a `destinationID`.

### 4. Selection persistence migrates

- [x] New key `Constants.UserDefaults.lastTabOpenedID` holding a
      `destinationID` string.
- [x] New one-shot flag `Constants.UserDefaults.lastTabOpenedMigratedM12`.
- [x] Migration reads the old `lastTabOpened` integer once, maps through the
      **old** order `[podcasts, filter, discover, streams, profile]`, writes the
      new key, sets the flag. Old key left in place.
- [x] Idempotent: running twice produces the same result.
- [x] Existing `lastTabOpenedMigratedM5` block untouched and still runs first.

### 5. Peripheral updates

- [x] `MainTabBarController+shortcuts.swift` — ⌘1–⌘N become positional over the
      visible slots, titles read from the slot. The ⌘4 Up Next binding is
      removed, since Up Next is not promoted by default.
- [x] `AnalyticsHelper.tabSelected` — additive only. Existing four event names
      unchanged. Add `playlist_tab_opened` with the UUID as a parameter.
      `overflow_tab_opened` lands in M12.1.

### 6. Reference sweep

Per `pocket-radio-ios/AGENTS.md`, list every hit before declaring the file list
complete:

```bash
grep -rn "pcTabs\|MainTabBarController.Tab\|firstIndex(of: \." podcasts/ Modules/ PocketCastsTests/
```

- [x] Every hit addressed in this change set.
- [x] `make build_staging` passes.

---

## Tests

- [x] Default layout renders exactly the five current destinations, no Overflow.
- [x] `needsOverflow` truth table across all four combinations of empty and
      non-empty complement and truncation.
- [x] 7 slots at capacity 5 produces 4 visible and 3 truncated.
- [x] `TabLayout` round-trips through `Codable`, including a `.playlist` slot.
- [x] Migration idempotency: run twice, assert one result.
- [x] `TabLayoutStore` returns `.default` on absent and on corrupt JSON.
- [x] Update `PocketCastsTests/Tests/Main/MainTabBarControllerTests.swift:21`,
      which currently asserts `pcTabs.count == 5`.

---

## Risks

| Risk | Mitigation |
|------|-----------|
| A force-unwrapped `firstIndex(of:)` survives the sweep | Grep is in the checklist; `make build_staging` after |
| `tabBarItem.tag` read somewhere unexpected | Sweep includes `.tag` |
| Migration runs before `lastTabOpenedMigratedM5` | Assert ordering explicitly in `viewDidLoad` |

---

## Completion notes (2026-09-10)

Verified independently of the implementing agent's report: `make build_staging`
succeeded, `make test_staging` ran 525 tests with 0 failures, `make format`
produced no changes, and the reference sweep left zero force-unwrapped
`firstIndex(of:)` lookups. `pcTabs` and `enum Tab` are gone entirely.

Migration confirmed on real upgrade data on the simulator, not only in tests:
an install holding `SJLastTabOpened = 1` produced `SJLastTabOpenedID =
playlists` with `SJTabLayout` absent, and the app opened on Playlists.
Persistence confirmed by force-quitting and relaunching: the stored id was
`streams` and the app came back up on Streams.

### Deviations from the plan as written

- **`project.pbxproj` was not touched.** `podcasts/Main` is a
  `PBXFileSystemSynchronizedRootGroup`, so files under
  `podcasts/Main/TabLayout/` register automatically. The registration rule in
  `AGENTS.md` does not apply to that subtree.
- **One user-visible change, accepted by the user.** `PlaylistsViewController`
  is a child of `PlaylistsHostViewController`, so its auto-created `tabBarItem`
  had `tag == 0` and its tap-to-scroll-to-top only ever fired when *Podcasts*
  was re-tapped. Resolving by `tabDestinationID` walks the parent chain and
  fixes it. M12 otherwise ships no visible change.
- **`tabDestinationID` is a `UIViewController` associated object** with a
  parent-chain fallback, living at the bottom of `TabDestination.swift` to keep
  the milestone's three-file list exact.
- **Migration writes nothing when `lastTabOpened` was never set**, so a fresh
  install still gets the "podcasts or discover" first-launch choice, which now
  tests `lastTabOpenedID`.
- **`navigateToUpNext` gained the resolution chain early** (Up Next tab if
  promoted, else the Playlists host segment). A no-op under the default layout;
  it stops M12.2 from shipping a dead promotion.
- **`.upNext` now emits `.upNextTabOpened`**, an existing analytics case that
  was previously unreachable from the bar. Additive, per §5.

### Carried forward

- `tabBar(_:didSelect:)` derives position from `tabBar.items?.firstIndex(of:)`
  with a `viewControllers` fallback. Exercised by hand on iOS 26.4 and correct,
  but not covered by tests on the LiquidGlass tab-accessory path.
- Streams tab icon weight mismatch — logged in `docs/todo.md`, to be settled
  with the Overflow and playlist icons in M12.1.
