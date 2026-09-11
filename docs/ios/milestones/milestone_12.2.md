# iOS M12.2 — Tab Bar settings screen and controlled rebuild

**Status**: NOT STARTED
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

- [ ] New `TableRow` case in `podcasts/SettingsViewController.swift`, labelled
      "Tab Bar", positioned directly under Appearance.
- [ ] Pushes `TabBarSettingsView` in a `UIHostingController`.
- [ ] Additive change only. No existing rows renamed or reordered.

### 2. `podcasts/Settings/TabBarSettingsView.swift` — Sonnet

- [ ] SwiftUI. Themed with `@EnvironmentObject private var theme: Theme` and
      `AppTheme.color(for:theme:)`, the SwiftUI signature.
- [ ] Section **In tab bar** — ordered, drag to reorder via `.onMove`, remove via
      swipe.
- [ ] Section **Hidden** — unpromoted destinations, plus an "Add Playlist Tab"
      row opening a picker over
      `DataManager.sharedManager.allPlaylists(includeDeleted: false)`.
- [ ] Multiple playlist slots permitted.
- [ ] Capped at 5 promoted slots. The add affordance disables at the cap.
- [ ] Refuses to remove the last remaining slot.
- [ ] Footer line stating that layout syncs when signed in. Wired in M12.3.
- [ ] No live preview of the bar. Out of scope for v1.

### 3. Controlled rebuild — Opus 5

- [ ] `func rebuildTabs(from layout: TabLayout, animated: Bool)` on
      `MainTabBarController`.
- [ ] Dismisses to root, tears down `viewControllers`, reconstructs from the
      render plan, restores selection **by `destinationID`**, never by index.
- [ ] If the previously selected destination no longer has a slot, selects the
      first slot.
- [ ] Writes `lastTabOpenedID` after the rebuild, not before.
- [ ] Mini player state survives the rebuild. Check
      `MiniPlayerViewController.swift:370` and
      `MiniPlayerViewController+Positioning.swift`.
- [ ] Called from exactly two places: settings save, and the safe sync path in
      M12.3. **Never** from a background notification.

### 4. Save flow

- [ ] Save writes `TabLayoutStore` first, stamps `updatedAt`, then calls
      `rebuildTabs`.
- [ ] Emits `tab_bar_layout_changed` carrying the ordered slot ids.

---

## Tests

- [ ] Reordering slots then rebuilding restores the same selected destination.
- [ ] Removing the selected destination falls back to the first slot.
- [ ] Rebuilding from a layout that gains Overflow, and one that loses it.
- [ ] Settings refuses a sixth promoted slot and refuses to empty the list.
- [ ] `lastTabOpenedID` after rebuild matches the visible selection.

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
