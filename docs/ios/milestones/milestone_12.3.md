# iOS M12.3 — Supabase layout sync and live playlist reconciliation

**Status**: COMPLETED (2026-09-11)
**Depends on**: M12.2
**Required by**: none
**Design**: `docs/ios/architecture/configurable-tab-bar.md` §4, §6;
`docs/ios/adr/0002-supabase-for-nav-layout-sync.md`
**Model**: **mixed**. The table, migration, and sync service are **Sonnet** work
against the proven `RadioFavoritesManager` pattern. The safe-apply gate on
pull is **Opus 5** work, because it decides when it is legal to rebuild a live
tab bar.

---

## Goal

The layout follows the user across devices, and a promoted playlist that is
renamed or deleted elsewhere is handled without a stale or dangling tab.

---

## Done when

### 1. Table — Sonnet

- [x] New migration in `supabase/migrations/` creating `nav_layout`:
      `user_uuid text primary key`, `slots jsonb`, `updated_at timestamptz`.
      Shipped as `20260911000007_nav_layout.sql`.
- [x] RLS policy keyed on the `x-user-uuid` header, matching the pattern in
      `20260512000005_reenable_rls.sql`.
- [x] Applied to the hosted project and verified with a manual upsert. See the
      isolation matrix in the completion notes.

### 2. Sync service — Sonnet

- [x] `podcasts/Main/TabLayout/TabLayoutSyncService.swift`, using
      `RadioSupabase.client()` for the authenticated client.
- [x] **Push** on settings save. `UserDefaults` written first, then upsert.
      Network failure is non-fatal and is not surfaced to the user.
- [x] **Pull** at launch, asynchronously, off the launch critical path.
- [x] Last-write-wins on `updated_at`. No merge.
- [x] Signed out — no network call, no error, no log spam.
      `RadioSupabase.client()` throws `notLoggedIn`; catch it quietly.

### 3. Safe-apply gate — Opus 5

- [x] A newer remote layout applies through `rebuildTabs` from M12.2 **only when
      safe**: every tab's navigation stack is at root, and nothing is presented
      modally. `MainTabBarController.isSafeToRebuild`.
- [x] Otherwise the layout is persisted and applies at next launch. No user
      prompt.
- [x] Never rebuilds mid-navigation. This is the rule the whole design rests on.

### 4. Live playlist reconciliation

- [x] Observe `Constants.Notifications.playlistChanged`, already posted by
      `podcasts/ServerSyncManager.swift:38` on sync and by `PlaylistManager` on
      local edits.
- [x] Playlist **renamed** → update that `UITabBarItem.title` in place.
- [x] Playlist **deleted** → keep the slot, retitle it, swap its root to a
      "This playlist was deleted" placeholder with a button into tab settings.
- [x] **Slot count never changes** in response to this notification. Content
      only. Changing structure here shifts `selectedIndex` and corrupts
      `lastTabOpenedID`.

### 5. Settings footer

- [x] The M12.2 footer becomes live: states whether the layout is syncing, and
      prompts to sign in when it is not.

---

## Tests

619 total, 0 failures, counted from the `.xcresult` bundle. 36 of them are new:
15 in `TabLayoutSyncServiceTests`, 8 in `TabLayoutReconciliationTests`, 7 in
`TabLayoutSyncApplyTests`, and 6 added to `TabLayoutEditorTests` for the drag
bug found on device — see *What manual verification found* below.

- [x] Remote layout newer than local, all stacks at root → applied immediately.
- [x] Remote layout newer than local, a modal presented → persisted, not applied.
- [x] Local layout newer than remote → pushed, remote not applied.
- [x] Signed out → no network call, layout still loads from `UserDefaults`.
- [x] `playlistChanged` for a rename updates the title and leaves the slot count
      unchanged.
- [x] `playlistChanged` for a deletion leaves the slot count unchanged.
- [x] A layout written at capacity 6 renders at capacity 5 as 4 visible plus
      Overflow.

The first three are covered in **two halves** rather than end to end, because
the network path is not unit-testable: `TabLayoutSyncService.decision(local:remote:)`
is tested for which way the comparison goes, and `TabLayoutApplier.applyFromSync`
is tested for what happens once that decision is `.applyRemote`.

Added beyond the plan: a modal presented from inside a tab blocks the rebuild
just as one presented from the bar does; the remote timestamp survives an apply;
the untouched default layout is never published; the wire format round-trips;
Postgres timestamps parse with and without fractional seconds; a deleted
playlist leaves screens pushed above it on the stack; reconciling twice does not
stack placeholders; the placeholder carries the slot's `destinationID`; posting
the notification for real reaches the reconciler.

---

## Manual verification

**Performed (2026-09-12).** The three cases below need two devices and a real
account, and none is reachable from the simulator alone. Verification surfaced
one open defect, `docs/ios/bugs/bug_1.md`: the layout pulls at launch and
nowhere else, so signing in does not pull until the next launch.

1. Change the layout on the iPhone. Relaunch on iPad. Layout matches.
2. Delete a promoted playlist from another surface while the tab is visible.
   The tab retitles and shows the placeholder. It does not disappear, and the
   app does not crash.
3. Sign out. Layout still renders from local storage.

What *was* performed, on an iPhone 15 running iOS 26.6.1 and an iPhone 17 Pro
simulator running iOS 26.4, is the tab settings drag interaction. It found a bug
this milestone's tests could not have caught, recorded below.

---

## Risks

| Risk | Mitigation |
|------|-----------|
| Pull races the initial tab build | Pull is async and applies only through the gate, never to a half-built bar |
| Safe-apply gate rebuilds under the user | Two explicit conditions, both checked at apply time, not at fetch time |
| Playlist UUID drift between devices | Pocket Casts playlist UUIDs are sync-stable; a missing one is handled by reconciliation |
| RLS misconfigured, layouts leak between users | Mirror the existing policy exactly; verify with a second account before shipping |

---

## Completion notes (2026-09-11)

`make format` produced no changes, and the full suite ran 612 tests with 0
failures. Counts come from the `.xcresult` bundle rather than scraped log lines.
The build succeeded as part of that run.

### The table was applied and its isolation proven, not assumed

Pushed to hosted project `brvtspdculqyvdrmdtef` — the same project
`SUPABASE_URL` names in every build configuration. All six prior migrations were
already applied, so `supabase db push` applied exactly one. Verified through
PostgREST with the publishable key and a hand-set `x-user-uuid` header:

| Check | Result |
|-------|--------|
| Upsert as user A | `201`, row written |
| Select as user A | Returns A's row |
| Select as user B | `[]` |
| User B upserts a row whose `user_uuid` is A | `401`, `42501` policy violation |
| No `x-user-uuid` header | `[]` |

The test row was deleted afterwards and the table is empty. This also settled a
question the code depends on: PostgREST returns `updated_at` as
`2026-09-11T18:32:03.309123+00:00` — six fractional digits, which a default
`ISO8601DateFormatter` rejects. `parsePostgresTimestamp` handles both shapes and
is pinned by tests.

### The M12.2 open question, settled

M12.2 left this to decide "before M12.3, not after": should the rows below the
More row become reorderable? **No.** The order stays derived. Making it
user-controlled means storing a hidden order for destinations that are
represented by their *absence* from the layout, which turns `slots` from one
ordered list into a two-part structure that every future reader of that column
pays for. Nothing in the design asks for a curated More order — it is a fallback
list, not something people arrange. So `slots` is a flat ordered array of
destination id strings, and that is the wire contract.

### What manual verification found

Two defects, neither of them reachable from a unit test. Both are fixed here.

**The two drop positions beside the More row were unreachable.** Dragging a row
from inside More up into the last bar slot, and dragging a tab down to the first
position inside More, both animated correctly under the finger and then snapped
back on release. The cause was not index arithmetic, which is where the search
naturally starts. `TabBarSettingsView` marked the More row `.moveDisabled(true)`
— it is structure rather than a tab, so it should not be draggable — and a
`moveDisabled` row is not a legal *drop target* either. UIKit refuses any
reorder whose final index is the one that row occupies, and both of those drops
land exactly there. `onMove` was never called, so no change to
`TabLayoutEditor.move(fromRows:toRow:)` could ever have fixed it.

Proven rather than inferred: a temporary `NSLog` in `move(fromRows:toRow:)`,
read back out of the simulator's unified log, logged one line for a drop higher
up the bar and **nothing at all** for the two failing drops.

The fix makes the More row draggable, which makes its index a legal drop target
again, and gives that drag a meaning rather than leaving a lift-and-snap-back
row behind: **dragging More moves the boundary, and whatever ends up above it is
the bar.** That completes the single-list model — either drag an item across the
line, or drag the line across the items — and it removes the dead zone from both
sides. Over-capacity boundary drags are clamped by `normalize`, not refused, so
dragging More to the bottom promotes as much as the device can render and stops.
Dragging it to the top is refused outright, because the bar may never be empty.

The six new `TabLayoutEditorTests` cases use the exact indices the real screen
produced, recorded in a comment above them. They pin the model; only a device or
simulator can prove the drops arrive at all, which is the whole lesson here.

**A unit test was reaching the network and depending on who was signed in.**
`testPullAtLaunchSignedOutMakesNoNetworkCallAndLeavesLocalLayoutUnchanged`
asserted `ServerSettings.userId == nil` as a precondition. That held only
because nobody had signed in on the simulator running the suite — which means
the 612/0 figure this document previously reported was environment-dependent.
Signing in by hand to test M12.3 made the test fetch the real remote layout and
write it over the local one. `TabLayoutSyncService.currentUserID` is now an
injectable closure defaulting to `ServerSettings.userId`, the test injects
signed-out, and a second test covers an empty user id as the same case.

### Deviations from the plan as written

- **The wire format is a bare JSON array of id strings**, e.g.
  `["podcasts","streams","playlist:<uuid>"]` — not a serialized `TabLayout` or
  `[TabSlot]`. The milestone said `slots jsonb` without saying what shape. A
  flat array is readable in the Supabase table editor and matches the ordered
  ids the `tab_bar_layout_changed` analytics event already carries. The
  migration's leading comment documents it so the next reader is not guessing.
- **`TabLayoutSyncService.isWorthPublishing` is a guard the plan does not
  mention.** `TabLayout.default` carries `updatedAt` of the Unix epoch, and
  `TabLayoutApplier.apply` stamps `Date()` on every real change, so the epoch is
  an exact marker for "never configured". Without the guard, a fresh device that
  launched before the configured one would seed the table with a layout the user
  never chose, and that row's timestamp is one nothing can lose to.
- **Only `RadioError.notLoggedIn` is silent.** The first implementation caught
  every `RadioError`, which would have hidden `serverError("SUPABASE_URL not
  configured")` as though it were a signed-out user. A developer
  misconfiguration should be visible in the log; a signed-out user should not
  be.
- **`TabLayoutApplier.applyFromSync(_:to:)` is a test seam.** The one-argument
  form resolves the live controller through `SceneHelper`, which a unit test has
  no scene to provide.
- **`MissingPlaylistViewController` is a new file.** M12.1 left the deleted
  playlist placeholder as an inline label built inside `TabDestination`. §4 asks
  for a button into tab settings, which needs a real view controller. The tab
  item retitles to "Unavailable" with SF Symbol `exclamationmark.triangle` —
  keeping the dead playlist's name would be a lie, and the settings screen
  already says "Deleted playlist" in the one place there is room for it.
- **A deletion replaces only index 0 of the stack**, not the whole stack.
  Screens pushed above the playlist root belong to what the user is doing right
  now. `setViewControllers([placeholder])` would throw them out mid-gesture; a
  single-element swap means they finish, then meet the placeholder when they pop
  back.
- **Reconciliation also reloads the Overflow list.** A renamed playlist in a
  *truncated* slot lives there rather than in the bar, and its row would
  otherwise keep the old name. `OverflowViewController.refreshRows()` is one
  `reloadData()`, because each cell asks its destination for a title at draw
  time.
- **Hardcoded English strings, not `L10n`**, continuing M12.2. Localization is
  unaddressed for the whole feature.

### Carried forward

- **A deferred layout makes the settings screen disagree with the bar.** When
  the gate defers, the store holds the new layout while the bar still renders
  the old one. Opening tab settings then shows the pending layout, and Save is
  disabled because nothing differs from it. This follows the design as written
  (§4: "persist it and let it apply at next launch"), so it is recorded rather
  than fixed. The fix, if it ever matters, is a separate pending key that
  `TabLayoutStore.load()` promotes at launch.
- **The three cross-device manual verification cases are unperformed.** They
  need a second device and a real Pocket Casts account. The drag interaction
  *was* exercised by hand, which is what found the two defects above.
- **`inFlightPull` is unsynchronized mutable state** on a non-`Sendable` class,
  touched from a `Task`. It mirrors `RadioFavoritesService.inFlight` exactly, so
  it is consistent with the codebase rather than newly wrong, and `pullAtLaunch`
  is called once per launch. Worth fixing if either becomes a hot path.
- **The rest of the suite still runs against whatever account is signed in on
  the simulator.** Only `TabLayoutSyncService` was made injectable, because only
  its test was actually caught doing this. Any future test that reaches
  `ServerSettings` directly has the same latent problem.
- **The layout pulls at launch and nowhere else**, so signing in does not fetch
  it — filed as `docs/ios/bugs/bug_1.md`, with an open design question attached:
  last-write-wins would let a signed-out local customization overwrite every
  other device at sign-in.
- **Running the unit suite deletes the saved layout on that simulator**, because
  three of this milestone's suites clear the real defaults key. Raised as
  `docs/ios/bugs/bug_2.md` as a suggestion, since the remedy is a design choice.
- **From M12.1, still open:** the widget deep link and Siri "open Discover"
  cases were never fired by hand, and the tab bar icon weight fix is diagnosed
  in `docs/todo.md` but not implemented.

### Written without independent review

Parts 3 and 4 — the safe-apply gate, live reconciliation,
`MissingPlaylistViewController`, and their 15 tests — were written by the
project-managing agent, not by an implementing agent, and have not had
independent review.

The implementing agent's work (parts 1, 2, 5) *was* reviewed, and three things
came out of it:

1. A test used `try XCTUnwrap` inside a non-throwing function, so the test
   target **never compiled**. The agent reported its test run as "in progress"
   twice and stopped without results both times; its own output files were
   empty. Nothing it claimed about testing was verifiable, which is why the
   suite was re-run from scratch here.
2. Catching every `RadioError` silently, fixed as described above.
3. Publishing the untouched default layout, fixed as described above.

The lesson for later milestones is the same one M12.1 produced: an agent's
report of a green test run is not evidence. The `.xcresult` bundle is.
