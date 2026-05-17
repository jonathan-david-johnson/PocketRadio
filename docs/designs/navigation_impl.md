# Navigation Implementation

## Decision: Add Streams tab to existing PC tab bar (not contextual home layer)

The design doc specifies a "contextual bottom nav" with a Home layer. After reading PC source, implementing that requires wrapping `MainTabBarController` in a parent coordinator — significant complexity, high risk of breaking PC's existing nav.

**MVP approach**: Add "Streams" as a 6th tab alongside PC's existing 5 tabs.

Tradeoff: Less design-doc fidelity. No "Home" abstraction. Initial shape was `[Podcasts] [Playlists] [Discover] [Up Next] [Streams] [Profile]`. Acceptable for MVP; revisit post-launch.

**Post-M5 shape** (current): `[Podcasts] [Playlists] [Discover] [Streams] [Profile]` — Up Next removed as a top-level tab and folded into the Playlists tab behind a segmented title view. See "M5: Up Next folded into Playlists tab" below.

---

## Changes to PC source

### `podcasts/Main/MainTabBarController.swift` (~line 86)

```swift
// Before:
pcTabs = [.podcasts, .filter, .discover, .upNext, .profile]

// After:
pcTabs = [.podcasts, .filter, .discover, .upNext, .streams, .profile]
```

Add `.streams` case to the `PCTab` enum (find it, add):
```swift
case streams
```

Add VC creation for streams tab in the programmatic tab setup block (same pattern as other tabs):
```swift
case .streams:
    let streamsVC = StreamsHostViewController()
    streamsVC.tabBarItem = UITabBarItem(title: "Streams", image: UIImage(systemName: "radio"), tag: 5)
    return streamsVC
```

---

## StreamsHostViewController

File: `podcasts/Radio/StreamsHostViewController.swift`

UIViewController containing a `UISegmentedControl` (Stations / Favorites / Browse) and a container view that swaps child VCs.

```
┌────────────────────────────────────────┐
│  [ Stations ]  [ Favorites ]  [ Browse ]  ← UISegmentedControl
├────────────────────────────────────────┤
│                                        │
│  <child VC content>                    │
│                                        │
└────────────────────────────────────────┘
```

Child VCs:
- `StationsViewController` — curated list (KCRW, KEXP, NPR Hourly)
- `FavoritesViewController` — user favorites from Supabase
- `BrowseViewController` — radio-browser.info search

Segment switch: remove old child VC, add new child VC via `addChild` / `transition`.

---

## PCTab enum

File: grep for `enum PCTab` — likely in `MainTabBarController.swift` or a separate file.

Add case before `.profile`:
```swift
case streams
```

---

## Summary of PC files modified

| Milestone | File | Change |
|-----------|------|--------|
| Streams MVP | `MainTabBarController.swift` | Add `.streams` to pcTabs array; add VC instantiation case |
| Streams MVP | `PCTab` enum file | Add `.streams` case |
| M5 | `MainTabBarController.swift` | Drop `.upNext` from `Tab` enum + `pcTabs`; replace Filter tab content with `PlaylistsHostViewController`; rewrite `navigateToUpNext` to route through the host; add `lastTabOpenedMigratedM5` migration |
| M5 | `podcasts/AnalyticsHelper.swift` | Remove `.upNext` analytics case |
| M5 | `podcasts/Constants.swift` | Add `lastTabOpenedMigratedM5` UserDefaults key |
| M5 (new) | `podcasts/PlaylistsHostViewController.swift` | Segmented container hosting `PlaylistsViewController` + `UpNextViewController` |
| M5.1 | `PlaylistsHostViewController.swift` | Rewrite: drop segmented control row, install `SegmentedTitleView` as `navigationItem.titleView`, mirror child bar buttons |
| M5.1 (new) | `podcasts/SegmentedTitleView.swift` | Custom titleView with two tappable labels + inert separator |
| M5.1 (new) | `UIViewController+EffectiveNavigationItem.swift` | `effectiveNavigationItem` extension |
| M5.1 | `PCViewController.swift` | `refreshRightButtons` writes to `effectiveNavigationItem` |
| M5.1 | `UpNextViewController.swift` | `navigationItem.{left,right}BarButtonItem` setters routed through `effectiveNavigationItem` |

All Streams UI lives in new files under `podcasts/Radio/`. M5/M5.1 UI lives under `podcasts/` root and `podcasts/Common Components/View Controllers/`.

---

## M5: Up Next folded into Playlists tab

`Up Next` removed from the tab bar. `PlaylistsHostViewController` becomes the Filter tab's root VC, hosting `PlaylistsViewController` and `UpNextViewController` as swappable children behind a segmented header.

`pcTabs` now: `[.podcasts, .filter, .discover, .streams, .profile]`.

`navigateToUpNext` switches to the Filter tab and calls `host.selectUpNext()`. `Cmd+4` shortcut and mini-player Up Next arrow continue to land on the Up Next view via this path.

A one-shot `Constants.UserDefaults.lastTabOpenedMigratedM5` flag remaps old raw `lastTabOpened` indices (old `upNext=3 → filter`, old `streams=4 → new streams`, old `profile=5 → new profile`) so users who last opened Up Next aren't stranded on a crashing index.

## M5.1: Single-bar segmented header

The segmented control row was removed. The host installs `SegmentedTitleView` as `navigationItem.titleView`:

```
[ <left> ]   Playlists / Up Next   [ <right> ]
                ^^^^^^^^^                          (active = bold, inactive = dim)
```

Children no longer have their own inner `UINavigationController`. Their nav-item writes route through `effectiveNavigationItem` — a `UIViewController` extension that returns `parent?.navigationItem` when hosted (and falls back to `self.navigationItem` when standing alone or directly inside a `UINavigationController`) — so left/right bar buttons appear on the host's bar and swap atomically with the active segment.

`PCViewController.refreshRightButtons` writes through this property, so any `PCViewController` subclass hosted inside another VC automatically renders its right buttons on the host. `UpNextViewController` opts in by routing its dynamic bar-button setters (multi-select / cancel / clear / done) through `effectiveNavigationItem`.

Detail pushes (e.g. tap a playlist → detail screen) still target the outer tab nav controller, since `child.navigationController` resolves up through the view hierarchy. The detail covers the host completely (no segmented header on the detail screen), matching upstream PC behavior.
