# iOS M12.2 — Tab Bar settings screen and controlled rebuild

**Status**: COMPLETED (2026-09-11)
**Depends on**: M12.1
**Required by**: M12.3
**Design**: `docs/ios/architecture/configurable-tab-bar.md` §6, §8
**Model**: **mixed**. The SwiftUI screen is **Sonnet** work — a two-section list
with `.onMove`, following the theming pattern in `pocket-radio-ios/AGENTS.md`.
The controlled rebuild is **Opus 5** work: it tears down and reconstructs
`viewControllers` on a live controller, and it is the single riskiest function
in the feature. Split the two tasks; do not hand the rebuild to Sonnet.

---

## Goal

Let the user change the layout from Settings and see it apply immediately,
without relaunching.

---

## Done when

### 1. Settings entry point — Sonnet

- [x] New `TableRow` case in `podcasts/SettingsViewController.swift`, labelled
      "Tab Bar", positioned directly under Appearance.
- [x] Pushes `TabBarSettingsView` in a `UIHostingController`.
- [x] Additive change only. No existing rows renamed or reordered.

### 2. `podcasts/Settings/TabBarSettingsView.swift` — Sonnet

Shipped at `podcasts/Main/TabLayout/TabBarSettingsView.swift`, and as one
ordered list rather than two sections. See the deviations below.

- [x] SwiftUI. Themed with `@EnvironmentObject private var theme: Theme` and
      `AppTheme.color(for:theme:)`, the SwiftUI signature.
- [x] Ordered, drag to reorder via `.onMove`, remove via swipe.
      **Superseded**: one list with a fixed More row, not a section named
      "In tab bar".
- [x] Unpromoted destinations, plus an add affordance opening a picker over
      `DataManager.sharedManager.allPlaylists(includeDeleted: false)`.
      **Superseded**: the rows below the More row, and a `+` in the navigation
      bar rather than an "Add Playlist Tab" row.
- [x] Multiple playlist slots permitted — *different* playlists only. A second
      slot for the same playlist is refused.
- [x] Capped. **Changed**: the cap is 4 while a More tab exists and 5 when it
      does not, because More occupies a tab slot. The add affordance never
      disables, because an add lands in More rather than the bar.
- [x] Refuses to remove the last remaining slot.
- [x] Footer line stating that layout syncs when signed in. Wired in M12.3.
- [x] No live preview of the bar. The More row is structure, not a preview —
      confirmed with the user before building it.

### 3. Controlled rebuild — Opus 5

- [x] `func rebuildTabs(from layout: TabLayout, animated: Bool)` on
      `MainTabBarController`.
- [x] Dismisses to root, tears down `viewControllers`, reconstructs from the
      render plan, restores selection **by `destinationID`**, never by index.
- [x] If the previously selected destination no longer has a slot, selects the
      first slot.
- [x] Writes `lastTabOpenedID` after the rebuild, not before.
- [x] Mini player state survives the rebuild, via `reassertMiniPlayerPosition()`.
- [x] Called from exactly one place today, `TabLayoutApplier.apply`, which M12.3
      calls for the safe sync path. Never from a background notification.

### 4. Save flow

- [x] Save writes `TabLayoutStore` first, stamps `updatedAt`, then calls
      `rebuildTabs`.
- [x] Emits `tab_bar_layout_changed` carrying the ordered slot ids and the
      source.

---

## Tests

583 total, 0 failures, counted from the `.xcresult` bundle. 27 of them are new:
15 in `TabBarRebuildTests`, 12 in `TabLayoutEditorTests`.

- [x] Reordering slots then rebuilding restores the same selected destination.
- [x] Removing the selected destination falls back to the first slot.
- [x] Rebuilding from a layout that gains Overflow, and one that loses it.
- [x] Settings refuses a sixth promoted slot and refuses to empty the list.
- [x] `lastTabOpenedID` after rebuild matches the visible selection.

Added beyond the plan: the rebuild reinstalls the positional keyboard
shortcuts; the mini player survives a rebuild; a stored layout with duplicate
slots is deduplicated on load; the editor's list and
`TabLayout.renderPlan(capacity:)` agree on both the bar and the More tab
contents.

---

## Manual verification

1. Set the bar to New Releases, Streams, More. Confirm it applies without a
   relaunch and that the mini player is still playing and correctly positioned.
2. Rebuild while audio is playing. Playback must not stop.
3. Rebuild with the full-screen player open. Confirm the dismiss-to-root path
   behaves and does not leave an orphaned modal.

---

## Risks

| Risk | Mitigation |
|------|-----------|
| Rebuild while a nav stack or modal is live | Dismiss to root first; the only caller here is a user-initiated save |
| Mini player detaches or duplicates | Explicit manual check; `setupMiniPlayer` runs once, not per rebuild |
| Playback interrupted by VC teardown | `PlaybackManager` is a singleton independent of the VC tree — verify, do not assume |
| SwiftUI theming diverges from the rest of Settings | Follow the `AGENTS.md` theming rule; compare against an existing SwiftUI settings screen |

---

## Completion notes (2026-09-11)

`make format` produced no changes, `make build_staging` succeeded, and
`make test_staging` ran 583 tests with 0 failures. Counts come from the
`.xcresult` bundle rather than scraped log lines. Signed off by the user after
driving the rewritten screen on the simulator.

### The screen was redesigned mid-milestone

The two-section screen was built as specified, shown to the user, and rejected:
*"I don't think that settings page is intuitive."* Two sections make promote,
demote and reorder three separate interactions, and they hide the fact that
More costs a tab slot — the "In tab bar" section could show five items while
the real bar showed four plus More.

It was replaced with **one ordered list containing a fixed More row**. Above
that row is the bar, below it is the More tab. Dragging across the row is the
same gesture as reordering. The row appears and disappears exactly when the
real More tab does, so dragging the last item up out of More retires the row
and hands the bar its fifth slot back.

**No data model change was needed.** `TabLayoutEditor.bar` is the only ordered,
user-controlled array. `belowMore` is derived as the extras not in the bar
followed by the core destinations not in the bar, which is exactly
`TabRenderPlan.overflowDestinations` — truncated slots first, then the
complement. Serialization is `bar + extras-not-in-bar`, so a core destination
below More is written as an *absence* and an extra below More as a slot past
the visible cut. `testTheListMatchesWhatTheBarAndMoreTabWillActuallyRender`
proves the round trip.

### Deviations from the plan as written

- **File location.** `podcasts/Settings/` does not exist in this project. The
  screen lives in `podcasts/Main/TabLayout/` with the rest of the feature,
  because that directory is a `PBXFileSystemSynchronizedRootGroup` and
  registers with the build automatically. A new directory would have forced a
  `project.pbxproj` edit, which the in-flight radio work is also touching.
- **`TabLayoutEditor.swift` is a third new file** the milestone does not name.
  Every editing rule lives there and the view only renders it, which is what
  makes the rules unit-testable without a hosting controller.
- **An explicit Save button in the navigation bar**, enabled only when the
  layout differs from what the screen opened on. The milestone never named a
  save trigger. Tapping Back discards silently, with no confirmation — the one
  rough edge left on this screen.
- **Adding lands in More, never the bar.** Dropping a new tab straight into a
  full bar would have to evict something the user did not choose. The add is
  shown; the promotion is a separate drag whose consequence is visible.
- **Core destinations have no delete affordance at all**, only demotion below
  More. That makes "the layout can never be emptied" structural rather than a
  refusal the user has to discover by trying.
- **A slot whose playlist was deleted is kept and labelled** "Deleted playlist"
  in italics, per design §6. Dropping it on screen-open, which an earlier draft
  did by passing `isAvailable:` to `renderPlan`, meant that merely opening
  Settings and saving silently discarded the slot.
- **Hardcoded English strings, not `L10n`.** Every string on this screen and its
  add sheet. Localization is unaddressed for the whole feature.
- **Settings row icon** is SF Symbol `rectangle.bottomthird.inset.filled`.

### Carried forward

- **Rows below More cannot be reordered.** `TabLayout` has no way to store an
  order for an unpromoted core destination, which is represented by its absence
  rather than by a slot. The screen renders them in the canonical order the
  real More tab uses and normalizes any drag within that group, so a drag among
  them snaps back. Fixing it properly means storing a hidden order, which
  changes the shape M12.3 syncs to Supabase — decide before M12.3, not after.
- **Back discards without confirmation.** See above.
- **Manual cases 2 and 3 were not separately reported.** The user exercised the
  screen and the live rebuild and signed off; playback-during-rebuild and
  rebuild-with-the-full-screen-player-open were not confirmed as distinct
  passes. Case 3 is now reachable by hand, since Save triggers the rebuild.

### Written without independent review

The single-list redesign — `TabLayoutEditor`, `TabBarSettingsView` and
`TabLayoutEditorTests` in their entirety — was written by the
project-managing agent, not by an implementing agent, and has not had
independent review. The same is true of three bugs found in the Sonnet agent's
first pass, all of which the redesign preserves structurally:

1. The hidden list filtered only `TabDestination.core`, so **Up Next could
   never be promoted**, despite design §9 depending on exactly that.
2. The add flow permitted **the same playlist twice**, which renders two
   identical tabs and makes the second unselectable, because selection
   restoration resolves an id to its first match.
3. The slot `ForEach` was **keyed by array offset**, which animates the wrong
   row when reorder and delete are both active.
