# Web M7 — Edit the Layout from the Sidebar

**Status**: PLANNED
**Depends on**: Web M2 (render rules, fixtures, Layout read), Web M6 (playlist list for adding playlist tabs); web ADR 0005
**Required by**: first release

## Where the work happens

| | |
|---|---|
| Plan | Shell `main`: this file |
| Code | `pocket-radio-web`, branch `feature/m7-layout-editing` from `main` after M6 merges |
| Worktree | `pocket-radio-web/` |
| Shell changes | Additive: `contracts/nav_layout/editor/` fixtures for editing operations |

**Goal:** Let the user change the Layout in the web player, with the same rules
as the iOS Tab Bar settings screen. The Sidebar gains an Edit mode. Above the
Bar line, items can be dragged to reorder. Items can be dragged across the Bar
line to promote or demote them, and the Bar line itself can be dragged.
Playlist tabs can be added and removed; core Destinations can only move. Items
below the Bar line keep their derived order. Saving writes `nav_layout` through
the Worker, last write wins, so the iPhone picks up the change.

**User checkpoint:** Click Edit in the Sidebar. Drag Up Next above the Bar
line, drag News below it, add a playlist tab, and save. The Sidebar updates at
once. Relaunch Pocket Casts on the iPhone: its tab bar shows the same order.

## Scope

- **Editor (`src/nav/layoutEditor.ts`).** Port of iOS `TabLayoutEditor`: `bar`,
  `extras`, `rows`, `belowMore`, `needsMoreRow`, `barCapacity`, `canDelete`,
  `move(fromRows:toRow:)`, `moveBoundary`, `delete`, and `currentLayout`.
  Core Destinations below the line are written as absences.
- **Editor fixtures (shell).** `contracts/nav_layout/editor/*.json`: a start
  Layout, an operation sequence, and the expected `slots`. Derived from the iOS
  `TabLayoutEditor` tests, so both ports can run them.
- **Layout write (`functions/api/layout`).** `PUT {slots}` upserts with
  `updated_at = now()` and the server-set user id. Refuses an empty slot list
  and unknown ids.
- **UI (`src/nav/SidebarEditor.tsx`).** Edit and Done, keyboard-accessible
  drag (dnd-kit or similar), the Bar line drawn as a draggable row, an "Add
  playlist tab" picker, delete on extras, and a footer that names how many
  tabs the phone's bar holds.
- **Freshness.** Entering Edit re-fetches the Layout. If the server's
  `updated_at` changed while editing, saving warns before overwriting.

## Behaviors to test (red -> green, one at a time)

1. Every editor fixture produces its expected `slots` (shared with iOS).
2. A core Destination can't be deleted; an extra can; the bar can't be emptied.
3. Moving the Bar line promotes or demotes exactly the items it crosses.
4. Items below the line can't be reordered among themselves.
5. `PUT /api/layout` writes the row for the session's user only, stamps
   `updated_at`, and rejects empty or unknown slots.
6. A save after a remote change made during editing asks before overwriting.
7. Cancelling Edit leaves the Layout and the Sidebar untouched.

## Out of scope

- Merging concurrent edits (last write wins, per iOS ADR 0002).
- Per-device layouts.
- Reordering below the Bar line. That needs an iOS change; see ADR 0005.

## Docs impact

- **Docs this changes or makes stale:** `docs/ios/adr/0002-supabase-for-nav-layout-sync.md`
  (a second writer exists); `docs/ios/architecture/configurable-tab-bar.md` §4
  and §8; `contracts/nav_layout/README.md`.
- **Questions this must settle:** Should iOS run the shared editor fixtures in
  its own tests now, or in a follow-up iOS milestone?

## Hand-performed interactions

- [ ] Drag an item above the Bar line to a new position — it lands there
- [ ] Drag an item across the Bar line in each direction — it is promoted or demoted
- [ ] Drag the Bar line itself up and down — items cross as expected
- [ ] Reorder using only the keyboard — the same results as dragging
- [ ] Save, then relaunch the iPhone app — its tab bar matches
