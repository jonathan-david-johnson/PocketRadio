# Navigation Implementation

## Decision: Add Streams tab to existing PC tab bar (not contextual home layer)

The design doc specifies a "contextual bottom nav" with a Home layer. After reading PC source, implementing that requires wrapping `MainTabBarController` in a parent coordinator — significant complexity, high risk of breaking PC's existing nav.

**MVP approach**: Add "Streams" as a 6th tab alongside PC's existing 5 tabs.

Tradeoff: Less design-doc fidelity. No "Home" abstraction. User sees `[Podcasts] [Playlists] [Discover] [Up Next] [Streams] [Profile]`. Acceptable for MVP; revisit post-launch.

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

| File | Change |
|------|--------|
| `MainTabBarController.swift` | Add `.streams` to pcTabs array; add VC instantiation case |
| `PCTab` enum file | Add `.streams` case |

All Streams UI lives in new files under `podcasts/Radio/`. No other PC files touched.
