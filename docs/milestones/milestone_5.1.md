# M5.1: Unified Segmented Header in Nav Bar

**Status**: NOT STARTED
**Builds on**: M5 (already shipped — committed at `0f3045a`).

## Goal

Replace the current two-row layout (segmented control row + standard nav bar row) with a single nav bar that contains the segmented header as its `titleView`. Left and right bar buttons swap to match the active segment.

## Visual target

Single nav bar row:
```
[ <left> ]   Playlists / Up Next   [ <right> ]
                 ^^^^^^^^^                       (active = bold, inactive = regular + dimmer)
```

- Active segment: bold weight, primary text color.
- Inactive segment: regular weight, secondary text color, dimmer.
- Separator `/`: regular weight, dimmer, inert (not tappable).
- Tap inactive label: switch active segment, swap which child is visible, swap left + right bar buttons to current child's items.
- Active label tap: no-op.

## Done when

- Tab bar still has no `Up Next` (kept from M5).
- Filter tab shows exactly one nav bar row. No segmented control row.
- `titleView` shows `Playlists / Up Next` with active label bolded.
- Left + right `UIBarButtonItem`s on the host's nav bar reflect the **current child**:
  - Playlists active: right = `+` (add playlist) per existing `customRightBtn`. Left = none (today).
  - Up Next active: left + right match Up Next's current state machine (Cancel / Select / Done / Clear etc.).
- Tapping an inactive label flips: bolding swaps, child swaps, bar buttons swap — atomically.
- Pushing a detail (playlist detail, filter detail) pushes on the **outer** tab nav controller (detail covers the whole host).
- Existing API entry points still land correctly: `Cmd+4` shortcut → Up Next segment; `navigateToUpNext` from mini-player → Up Next segment; `navigateToFilter(filter:)` → Playlist segment with detail pushed.
- All M5 tests still pass; new title-view test added.

## Architecture

### TitleView

New custom UIView `SegmentedTitleView`:
- Two `UILabel`s (or `UIControl` subclasses) for `Playlists` and `Up Next`.
- One inert `UILabel` for separator `/`.
- Horizontal stack via `UIStackView` with small spacing.
- API: `setActive(_ segment: Segment)`, `var onSelect: (Segment) -> Void`.
- `Segment` enum: `.playlists`, `.upNext`.
- Theming: read colors via `AppTheme.color(for:)` and listen for `Constants.Notifications.themeChanged` to refresh.

### Host

`PlaylistsHostViewController` rewrite:
- Drop `segmentedControl`, `containerView`, `segmentChanged`.
- Drop inner `UINavigationController` wrappers per child.
- Children: `PlaylistsViewController` and `UpNextViewController(source: .tabBar, showingInTab: true)` instantiated lazily as plain VCs (no nav wrapper).
- `viewDidLoad`:
  - Create `SegmentedTitleView`, assign to `navigationItem.titleView`.
  - `titleView.onSelect = { [weak self] in self?.selectSegment($0) }`
  - Default segment: `.playlists` → `showChild(playlists)`.
- `showChild(_ newChild:)`:
  - Remove old child (`willMove(toParent: nil)`, `removeFromSuperview`, `removeFromParent`).
  - `addChild(newChild)` BEFORE accessing `newChild.view` so `parent` is set in time for `viewDidLoad`.
  - Add child's view directly to host view with safe-area top + leading/trailing/bottom anchors.
  - `didMove(toParent: self)`.
  - Call `syncBarButtonsFromChild()`.
- `syncBarButtonsFromChild()`:
  - `navigationItem.leftBarButtonItem = currentChild?.navigationItem.leftBarButtonItem`
  - `navigationItem.rightBarButtonItem = currentChild?.navigationItem.rightBarButtonItem`
  - Run after every swap. Children later updates flow through `effectiveNavigationItem` (see below), bypassing the need for KVO.
- Public API preserved: `selectPlaylist()`, `selectUpNext()`, `playlistsViewController` getter. Behavior identical to callers.

### Child → host nav-item delegation

Children currently write to `self.navigationItem.{left,right}BarButtonItem`. Without inner nav controllers those writes are invisible. Fix with one indirection.

- New file `podcasts/Common Components/View Controllers/UIViewController+EffectiveNavigationItem.swift`:
  ```swift
  extension UIViewController {
      /// When this VC is hosted inside another VC (no inner nav controller),
      /// returns the parent's navigationItem so bar-button writes land on the
      /// visible nav bar. Falls back to self when not hosted.
      var effectiveNavigationItem: UINavigationItem {
          parent?.navigationItem ?? navigationItem
      }
  }
  ```
- `PCViewController.refreshRightButtons()` (line 101): replace every `navigationItem.rightBarButtonItem` / `.rightBarButtonItems` write with `effectiveNavigationItem.…`. Covers `PlaylistsViewController` automatically (and any other PCViewController subclass; verify nothing breaks for stand-alone PCViewControllers — `effectiveNavigationItem` falls back to `self.navigationItem` when `parent` is nil or when parent is a `UINavigationController`, which is the normal case).
  - Edge: when a PCViewController is the root of a `UINavigationController`, `parent` is the nav controller. Writes to `parent?.navigationItem` would target the nav controller's own navigationItem — wrong. Refine the property:
    ```swift
    var effectiveNavigationItem: UINavigationItem {
        if let parent, !(parent is UINavigationController) { return parent.navigationItem }
        return navigationItem
    }
    ```
- `UpNextViewController` — replace the ~10 setters at lines 417–438 to use `effectiveNavigationItem.leftBarButtonItem` / `rightBarButtonItem`. Read sites stay as `navigationItem` (no functional impact).

### Detail pushes

`child.navigationController` resolves through view hierarchy and returns the outermost nav controller. With host placed directly in the tab's nav controller (no inner wrapper), `child.navigationController` is the tab's nav controller. Existing push code (`navController.pushViewController(detailVC, animated: true)`) works unchanged.

Verify call sites:
- `PlaylistsViewController.showFilter(_:)` — pushes detail. Must continue to work.
- `MainTabBarController.navigateToFilter` — currently does `navController.popToRootViewController(animated: false)` then `host.playlistsViewController.showFilter(filter)`. With host as the root of the outer nav controller, popToRoot brings us back to the host, then showFilter pushes the detail onto the same outer nav controller. Still works.

### Theming

- TitleView colors update via `Constants.Notifications.themeChanged` observer.
- Host's outer nav controller already themed by existing `PCViewController` / `MainTabBarController` infrastructure; titleView just respects current theme colors at draw time.

## Files

### NEW

- `podcasts/PlaylistsHostViewController.swift` — full rewrite (replace existing).
- `podcasts/SegmentedTitleView.swift` — new custom titleView.
- `podcasts/Common Components/View Controllers/UIViewController+EffectiveNavigationItem.swift` — extension.

### EDIT

- `podcasts/Common Components/View Controllers/PCViewController.swift` — `refreshRightButtons` writes to `effectiveNavigationItem` instead of `navigationItem`.
- `podcasts/UpNextViewController.swift` — replace ~10 `navigationItem.{left,right}BarButtonItem` setters with `effectiveNavigationItem.…`. Lines 417, 419, 421, 423, 426, 428, 431, 434, 436, 438 per current grep.

### NO CHANGE

- `MainTabBarController.swift` — host is still the root VC of the filter tab's nav controller. Migration + navigateToUpNext / navigateToFilter logic unchanged.
- `PlaylistsViewController.swift` — uses PCViewController, gets the effectiveNavigationItem change for free.
- Tests for M5 tab-bar wiring stay valid.

## Risks / Edge cases

- **`addChild` ordering**: `addChild(newChild)` must run before the child's view is loaded so `parent` is set when its `viewDidLoad` writes bar buttons. UIKit guarantees `parent` is set inside `addChild`, but `viewDidLoad` does not fire until view is accessed. The order in `showChild` is `addChild` → access `view` → `didMove`. Safe.
- **Child's `viewDidLoad` writes**: PlaylistsViewController writes `customRightBtn` in `viewDidLoad` (line 86–88, 90). Goes through PCViewController.refreshRightButtons → effectiveNavigationItem → host. Then host's `viewDidLoad` runs `syncBarButtonsFromChild` AFTER `showChild(playlists)` so the buttons are already on host's nav item. Verify order is `addChild → showChild → child viewDidLoad fires → syncBarButtonsFromChild`. If syncBarButtonsFromChild runs before child viewDidLoad, items will be nil. Force layout by accessing `newChild.view` (or call `loadViewIfNeeded()`) before sync.
- **UpNextViewController nav bar back behavior**: When pushed by another flow (deep link from notification?) UpNext might rely on its own nav controller. Confirm no caller pushes UpNextViewController directly onto a nav stack with `showingInTab: false` in a way that depends on `navigationItem` writes — those paths still work since `parent` is the nav controller and `effectiveNavigationItem` falls back to self.
- **PCViewController used outside host**: When PCViewController is the root of a regular `UINavigationController` (e.g. Podcasts tab, Profile tab), `parent` is the nav controller, `effectiveNavigationItem` falls back to `self.navigationItem`. No regression.
- **Accessibility**: titleView labels need `isAccessibilityElement = true` + appropriate `accessibilityTraits` (`.button` for inactive, `.selected | .button` or `.header` for active). Test with VoiceOver.
- **Dynamic Type**: labels should use `UIFontMetrics(forTextStyle: .headline)` to scale.

## Reference sweep

Before declaring done, grep for stale assumptions:
```
grep -rn "navigationItem\.\(left\|right\)BarButtonItem" podcasts/PlaylistsViewController.swift podcasts/UpNextViewController.swift
grep -rn "PlaylistsHostViewController" podcasts/ PocketCastsTests/
```

## Automated tests

### EDIT `PocketCastsTests/Tests/Playlists/PlaylistsHostViewControllerTests.swift`

Keep the three existing tests. Add:

```swift
func testTitleViewBoldsActiveSegment() {
    let host = PlaylistsHostViewController()
    host.loadViewIfNeeded()
    let titleView = host.navigationItem.titleView as? SegmentedTitleView
    XCTAssertNotNil(titleView, "Host should install SegmentedTitleView as navigationItem.titleView")
    XCTAssertEqual(titleView?.activeSegment, .playlists, "Default active segment is .playlists")
    host.selectUpNext()
    XCTAssertEqual(titleView?.activeSegment, .upNext, "selectUpNext updates titleView active segment")
}

func testNavBarButtonsMirrorActiveChild() {
    let host = PlaylistsHostViewController()
    host.loadViewIfNeeded()
    // After loadViewIfNeeded the playlists child viewDidLoad has run; right button is the add-playlist '+'
    XCTAssertNotNil(host.navigationItem.rightBarButtonItem, "Host should mirror Playlists right bar button after viewDidLoad")
    host.selectUpNext()
    // UpNext sets a 'Select' right button in default state
    XCTAssertNotNil(host.navigationItem.rightBarButtonItem, "Host should mirror Up Next right bar button after segment swap")
}
```

### NEW `PocketCastsTests/Tests/Playlists/SegmentedTitleViewTests.swift`

```swift
import XCTest
@testable import podcasts

final class SegmentedTitleViewTests: XCTestCase {
    func testDefaultActiveSegment() {
        let v = SegmentedTitleView()
        XCTAssertEqual(v.activeSegment, .playlists)
    }

    func testTapInactiveSegmentFiresCallback() {
        let v = SegmentedTitleView()
        var fired: SegmentedTitleView.Segment?
        v.onSelect = { fired = $0 }
        v.simulateTap(on: .upNext)
        XCTAssertEqual(fired, .upNext)
    }

    func testTapActiveSegmentDoesNotFire() {
        let v = SegmentedTitleView()
        var fired: SegmentedTitleView.Segment?
        v.onSelect = { fired = $0 }
        v.simulateTap(on: .playlists) // already active
        XCTAssertNil(fired)
    }
}
```

`simulateTap(on:)` — internal test hook on `SegmentedTitleView` that calls the same handler the gesture recognizer invokes. Avoid sending touches via `UIApplication`.

## Manual smoke

1. `make run_sim` — launch on iPhone 17 Pro - No Watch.
2. Open Playlists tab. Confirm:
   - One nav bar row, no segmented control.
   - `Playlists / Up Next` titleView, `Playlists` bold.
   - Right bar button = `+`.
3. Tap `Up Next`:
   - `Up Next` becomes bold, `Playlists` regular weight.
   - Right bar button changes to `Select`.
   - View below shows Up Next queue.
4. Tap `Playlists`:
   - Reverse.
5. Tap an existing playlist → detail pushes on outer nav controller, header disappears (detail covers).
6. Back button on detail → returns to host with last active segment.
7. `Cmd+4`: should land on Up Next segment.
8. From mini-player: tap "Up Next" arrow → lands on host, Up Next segment active.
9. Up Next's `Select` → multi-select mode → Cancel/Select All toggle correctly.
10. Dark mode toggle: titleView colors update.

## Agentic plan

Sequential phases. Each agent reads this file as ground truth.

### Phase 1 — Extension + PCViewController + UpNext nav-item rewrites
- Agent: `general-purpose`, model: Sonnet 4.6
- Files allowed:
  - NEW `podcasts/Common Components/View Controllers/UIViewController+EffectiveNavigationItem.swift`
  - EDIT `podcasts/Common Components/View Controllers/PCViewController.swift`
  - EDIT `podcasts/UpNextViewController.swift`
- Verify: `make build_staging` succeeds; existing tests still pass:
  `make test_staging ONLY_TESTING=PocketCastsTests/PlaylistsHostViewControllerTests`
- Done when: build green, M5 tests green.

### Phase 2 — SegmentedTitleView + Host rewrite + tests
- Agent: `general-purpose`, model: Sonnet 4.6
- Depends on Phase 1.
- Files allowed:
  - NEW `podcasts/SegmentedTitleView.swift`
  - REWRITE `podcasts/PlaylistsHostViewController.swift`
  - EDIT `PocketCastsTests/Tests/Playlists/PlaylistsHostViewControllerTests.swift` (add 2 tests)
  - NEW `PocketCastsTests/Tests/Playlists/SegmentedTitleViewTests.swift`
- Pbxproj: `SegmentedTitleView.swift` needs registration mirroring `PlaylistsHostViewController.swift` entries. Tests auto-pickup.
- Verify:
  - `make test_staging ONLY_TESTING=PocketCastsTests/SegmentedTitleViewTests`
  - `make test_staging ONLY_TESTING=PocketCastsTests/PlaylistsHostViewControllerTests`
  - `make build_staging`

### Phase 3 — Review
- Agent: `caveman:cavecrew-reviewer`, model: Sonnet 4.6
- Focus: child-parent ordering in `showChild`, theme observer cleanup in titleView, accessibility, Dynamic Type, regressions in PCViewController stand-alone use.

### Phase 4 — Manual smoke
- Human runs Manual smoke list.
- Sign off before commit.

## Notes

- Keep changes additive; do not remove M5 migration logic in `MainTabBarController`.
- Do not introduce a new feature flag — this is a direct replacement of M5's UI.
