# iOS M12.1 — Overflow tab and navigation resolution

**Status**: COMPLETED (2026-09-11)
**Depends on**: M12
**Required by**: M12.2
**Design**: `docs/ios/architecture/configurable-tab-bar.md` §5, §2
**Model**: **Opus 5**. Rewrites the resolution path behind 87 `NavigationProtocol`
call sites, including deep links reached from Siri, widgets, and notifications.
A wrong guess here is a crash or a dead link, not a visual bug.

---

## Goal

Make a layout that hides a core destination actually work. Build the Overflow
tab, and replace `switchToTab` with a resolver that either selects a promoted
tab or pushes onto Overflow.

Verified by hand-setting a layout in `UserDefaults`; there is still no settings
UI at this point.

---

## Done when

### 1. Overflow tab

- [x] `podcasts/Main/TabLayout/OverflowViewController.swift` — grouped
      `UITableView`, one row per entry, pushing the destination's root VC onto
      the Overflow navigation stack.
- [x] Rows are the unpromoted **core** destinations plus any truncated slots of
      any kind. An unpromoted *extra* never appears.
- [x] Title "More", SF Symbol `ellipsis`. Always the last tab item.
- [x] Present only when `needsOverflow` is `true`.
- [x] Themed via `AppTheme.colorForStyle(...)`, the UIKit signature.

### 2. Resolver

- [x] `func host(for destination: TabDestination) -> UINavigationController` on
      `MainTabBarController`.
- [x] Promoted → select that tab, return its navigation controller.
- [x] Not promoted → select Overflow, `popToRootViewController(animated: false)`,
      push a **fresh** instance, return the Overflow navigation controller.
- [x] Called twice in a row, does not stack two instances of the destination.
- [x] No `firstIndex(of:)!` remains anywhere in the file.

### 3. Call sites retargeted

- [x] `navigateToDiscover(_:)`, `navigateToDiscover(category:)`,
      `navigateToDiscover(listID:)` — cast the pushed VC to `DiscoverDelegate`
      rather than reaching into `viewControllers[index]`.
- [x] `navigateToProfile(row:)`.
- [x] `navigateToFilter(_:)`.
- [x] `navigateToUpNext(_:)` — resolution **chain**: the Up Next tab if promoted,
      otherwise `PlaylistsHostViewController.selectUpNext()` exactly as today.
- [x] Fork-added `navigateToStreamsStation` and `navigateToStreamsFavorites`,
      reached from the widget URL routes at
      `podcasts/AppDelegate+UrlHandling.swift:281-311`.

### 4. Lazy instantiation

- [x] Only promoted destinations are constructed at launch. An unpromoted
      destination is built on first navigation.
- [x] `ProfileViewController` end-of-year badge logic
      (`MainTabBarController.swift:20`) tolerates Profile not being promoted.

### 5. Playlist slots render

- [x] A `.playlist(uuid)` slot roots `PlaylistDetailViewController(playlist:)`,
      the same VC `PlaylistsViewController.showFilter` builds at
      `podcasts/PlaylistsViewController.swift:236`.
- [x] Title is the playlist's live name. Icon is
      `EpisodeFilter.iconImageName()` as a template image, falling back to SF
      Symbol `list.bullet`.
- [x] A slot whose UUID resolves to nothing at build time is dropped from the
      render plan.

### 6. Analytics

- [x] Add `overflow_tab_opened`. Existing event names unchanged.

---

## Tests

- [x] Overflow contains unpromoted core destinations only, never an unpromoted
      extra.
- [x] Truncated extras **do** appear in Overflow.
- [x] `host(for:)` on an unpromoted destination selects Overflow and pushes.
- [x] Two consecutive `host(for:)` calls leave one instance on the stack.
- [x] `navigateToUpNext` with Up Next unpromoted lands on the Playlists segment.
- [x] A layout with an unresolvable playlist UUID renders without it and does
      not crash.

---

## Manual verification

Set a layout by hand, relaunch, and confirm each case:

1. `[playlist:<new-releases-uuid>, streams]` — bar shows New Releases, Streams,
   More. More lists Podcasts, Playlists, Discover, Profile.
2. Tap a podcast in a widget deep link while Podcasts is unpromoted. Lands in
   the Overflow stack, back button returns to the More list.
3. Siri "open Discover" with Discover unpromoted.

---

## Risks

| Risk | Mitigation |
|------|-----------|
| A deep link path not covered by the six known methods | Grep `NavigationManager.sharedManager.navigateTo` — 87 call sites, all funnelling through this file |
| Playlist icons illegible at 25pt | Visual check on device; SF Symbol fallback exists |
| Overflow stack grows unboundedly across repeat deep links | `popToRootViewController` before every push |

---

## Completion notes (2026-09-11)

Verified independently of the implementing agent, which was cut off by a
session limit partway through its own verification sweep. `make format`
produced no changes, `make build_staging` succeeded, and `make test_staging`
ran 556 tests with 0 failures. Counts come from the `.xcresult` bundle rather
than scraped log lines.

Manual verification case 1 confirmed on the simulator with a hand-written
layout of `[playlist:<new-releases-uuid>, streams]`: the bar rendered New
Releases, Streams, More, the promoted playlist rooted its tab with no back
chevron, and the More list held the four unpromoted core destinations. Signed
off by the user.

### One bug found and fixed during verification

A playlist row tapped in the More list was a navigational dead end. Both
`OverflowViewController.didSelectRowAt` and `host(for:)` push
`makeRootViewController()`, which for `.playlist` returns
`PlaylistTabRootViewController` with `backBtn.isHidden = true` and
`showNavBarOnHide = false` — correct for a tab root, fatal on a pushed stack,
where the fake nav bar's chevron is the only way back and the real navigation
bar stays hidden. Reachable through an existing passing test, which asserts
that truncated playlist slots land in `overflowDestinations`.

Fixed by making the back affordance conditional on whether the screen is
actually the root of its navigation stack (`applyBackAffordance()`, re-applied
in `viewWillAppear` because a pushed instance has no navigation controller yet
at `viewDidLoad`). A missing navigation controller is read as the root case,
which preserves existing behaviour.

**The fix and its regression test were written by the project-managing agent,
not by the implementing agent, and have not had independent review.** The test
gap that let this ship green is worth noting for later milestones: the Overflow
tests asserted which destinations the list holds, never what tapping a row
produces.

### Deviations from the plan as written

- **§5 roots a subclass, not `PlaylistDetailViewController` directly.**
  `PlaylistTabRootViewController` adapts that screen to root a stack: it owns a
  no-op `FilterCreatedDelegate` and now decides its own back affordance.
- **`renderPlan` gained an `isAvailable:` parameter** so an unresolvable
  playlist slot is dropped at build time without `TabLayout` reaching into
  `DataManager`. Defaults to "everything is available", keeping the function
  pure for tests.
- **`TabRenderPlan.overflowDestinations`** was added to keep Overflow's row
  order (truncated slots first, then the complement) out of the view
  controller.
- **The end-of-year badge falls back to the Overflow tab item** when Profile is
  unpromoted, rather than being suppressed.
- **`host(for:)` logs and falls back** rather than trapping when a destination
  resolves to no host.

### Carried forward

- **Manual verification cases 2 and 3 were not exercised by hand.** The widget
  deep link and the Siri "open Discover" paths are covered by unit tests that
  assert resolution through Overflow, but no physical deep link was fired.
- **The back-chevron fix was not exercised by hand either.** It needs a layout
  of six or more slots with a playlist last, which puts a playlist row in the
  More list.
- **Icon weights are now visibly inconsistent** in the bar: the playlist clock
  and the Overflow ellipsis are thin outlines, the Streams radio grille is much
  heavier. Logged in `docs/todo.md`. M12.1 was meant to settle the whole set and
  did not.
