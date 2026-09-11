# Configurable tab bar (M12)

Status: **designed, not implemented**. Agreed in grill session 2026-09-04.

The bottom tab bar is hard-coded at `MainTabBarController.swift:86`:

```swift
pcTabs = [.podcasts, .filter, .discover, .streams, .profile]
```

This document replaces that with a user-configurable, synced layout in which a
single playlist (e.g. "New Releases") can be promoted to a first-class tab, and
destinations the user does not promote fall into a derived **Overflow** tab.

Target layout for the primary user: `New Releases | Streams | More`.

---

## 1. Glossary

Terms below are canonical. Use them in code, milestones, and commits.

| Term | Meaning |
|------|---------|
| **Destination** | A place the app can navigate to that is *capable* of rooting a tab. Has a stable id, a title, an icon, and a `makeRootViewController()` factory. |
| **Core destination** | A Destination for which the tab bar is the **only** entry point: Podcasts, Playlists, Discover, Streams, Profile. Must always be reachable. |
| **Extra destination** | A Destination that has another home in the app, so it need not be reachable from the bar: Up Next (a segment of the Playlists host), and any specific playlist (a row in the Playlists list). |
| **Slot** | One entry in the user's layout. A Destination reference plus optional payload — e.g. `playlist:<uuid>`. Slots are ordered. |
| **Layout** | The user's ordered list of Slots. The single persisted, synced artifact. |
| **Promoted** | A Destination that has a Slot in the Layout. |
| **Capacity** | How many tab items the current device can render. `5` everywhere today. |
| **Truncation** | Slots beyond Capacity. Not an error; they fall into Overflow. |
| **Overflow** | A derived tab, always last, titled "More". Exists **iff** it would be non-empty. Contains unpromoted Core destinations plus truncated Slots of any kind. |
| **Complement** | The set of unpromoted Core destinations. The main input to Overflow. |

Deliberately *not* terms: "tab" alone is ambiguous between Slot and Destination;
prefer the precise word.

---

## 2. Data model

New files under `podcasts/Main/TabLayout/`.

```swift
enum TabDestination: Hashable {
    case podcasts, playlists, discover, streams, profile   // core
    case upNext                                            // extra
    case playlist(uuid: String)                            // extra

    var id: String            // "podcasts", ..., "playlist:<uuid>"
    var isCore: Bool
    func title() -> String    // playlist case reads the live EpisodeFilter
    func icon() -> UIImage?
    func makeRootViewController() -> UIViewController
}

struct TabSlot: Codable, Equatable {
    let destinationID: String   // stable across reorders and app versions
}

struct TabLayout: Codable, Equatable {
    var slots: [TabSlot]
    var updatedAt: Date

    static let `default` = TabLayout(slots: [.podcasts, .playlists, .discover, .streams, .profile])
}
```

`destinationID` is a `String`, not an `Int` enum rawValue, because a `.playlist`
slot has no fixed ordinal and because reordering must not change identity.

### Rendering

```
visible      = layout.slots.prefix(capacity - (needsOverflow ? 1 : 0))
truncated    = layout.slots.dropFirst(visible.count)
complement   = coreDestinations - promoted
needsOverflow = !(complement.isEmpty && truncated.isEmpty)
```

Overflow, when present, is always the last item. Capacity comes from
`TabLayout.capacity(for:)`, which returns `5` for every device today and is the
one place to change if the iPad ever stops being forced to compact width (see
§7).

### Invariants

1. Every **Core destination** is reachable — as a Slot or as an Overflow row.
2. The Layout holds at least one Slot. Settings refuses to remove the last.
3. Overflow is never stored in the Layout. It is derived at render time.
4. Slot **structure** never changes mid-session except through a controlled
   rebuild (§6). Slot **content** — titles, icons — may update live.

---

## 3. Persistence and migration

Local store is the render source of truth, so the bar builds offline with no
latency: `TabLayout` JSON-encoded into `UserDefaults`.

`Constants.UserDefaults.lastTabOpened` currently stores a raw **index**, which
becomes meaningless under reordering. It is replaced by `lastTabOpenedID`
holding a `destinationID` string.

Migration, following the idempotency rule in `pocket-radio-ios/AGENTS.md`:

1. One-shot flag `Constants.UserDefaults.lastTabOpenedMigratedM12`.
2. If set, skip.
3. Read the old integer, map through the **old** order
   `[podcasts, filter, discover, streams, profile]` to a `destinationID`.
4. Write `lastTabOpenedID`. Set the flag. Leave the old key in place.

The existing `lastTabOpenedMigratedM5` block is untouched and runs first.

---

## 4. Sync

Layout syncs through **our Supabase**, not Pocket Casts. See
`docs/ios/adr/0002-supabase-for-nav-layout-sync.md`.

Table `nav_layout`:

| Column | Type |
|--------|------|
| `user_uuid` | `text primary key` |
| `slots` | `jsonb` |
| `updated_at` | `timestamptz` |

RLS keyed on the `x-user-uuid` header, matching `radio_favorites` and migration
`20260512000005_reenable_rls.sql`. Client built by `RadioSupabase.client()`,
which throws `notLoggedIn` without `ServerSettings.userId`.

- **Push** — on save in settings. UserDefaults written first, then upsert.
  Network failure is non-fatal and is retried on the next save.
- **Pull** — at launch, asynchronously. If remote `updated_at` is newer, apply
  it **immediately via a controlled rebuild (§6), but only when safe**: every
  tab's nav stack at root and nothing presented modally. Otherwise persist it
  and let it apply at next launch.
- **Conflict** — last-write-wins on `updated_at`. No merge; the Layout is one
  small ordered list.
- **Signed out** — local only, silent. Settings footer notes that layout syncs
  when signed in.

One shared layout across all devices. Capacity differences are handled by
truncation, so a layout written by a higher-capacity device degrades gracefully.

---

## 5. Navigation resolution

`NavigationProtocol` has 87 call sites, all landing on `MainTabBarController`,
all of which currently do `switchToTab(...)` followed by
`pcTabs.firstIndex(of:)!`. Those force-unwraps are the crash surface this design
removes.

Single resolution helper:

```swift
func host(for destination: TabDestination) -> UINavigationController
```

- **Promoted** → select that tab, return its nav controller.
- **Not promoted** → select Overflow, `popToRootViewController(animated: false)`,
  push a **fresh** instance of the destination's root VC, return the Overflow
  nav controller.

Every existing `navigateTo*` body then performs the work it does today against a
nav controller it no longer has to locate. Roughly six methods change shape:
`navigateToDiscover(_:)`, `navigateToDiscover(category:)`,
`navigateToDiscover(listID:)`, `navigateToProfile(row:)`,
`navigateToFilter(_:)`, `navigateToUpNext(_:)`, plus the fork's
`navigateToStreamsStation` and `navigateToStreamsFavorites` reached from widget
URL routes in `AppDelegate+UrlHandling.swift:281-311`.

`navigateToUpNext` is the one resolution *chain*: the Up Next tab if promoted,
otherwise the Up Next segment of `PlaylistsHostViewController` exactly as today.

Destination root VCs become **lazy**. Today all five are constructed eagerly in
`viewDidLoad`; under this design a hidden destination is built only when
something navigates to it.

---

## 6. Mutation rules

Structure and content are governed differently, because changing slot count
shifts `selectedIndex`, invalidates every `tabBarItem.tag`, and corrupts the
`lastTabOpened` write.

**Content — live.** Observe `Constants.Notifications.playlistChanged`, already
posted by `ServerSyncManager.swift:38` on sync and by `PlaylistManager` on local
edits. On fire, re-resolve every `.playlist` slot:

- Playlist renamed → update that `UITabBarItem.title` in place.
- Playlist deleted → keep the slot, retitle it, swap its root to a "This playlist
  was deleted" placeholder with a button into tab settings.

**Structure — frozen, except by controlled rebuild.** A controlled rebuild
dismisses to root, tears down and reconstructs `viewControllers` from the
Layout, then restores selection **by `destinationID`**, not by index. It runs in
exactly two situations: the user saving the settings screen, and a safe
sync-pull (§4). Never from a background notification.

This is the single riskiest piece of code in the feature.

---

## 7. Capacity and the iPad

`MainTabBarController.swift:264`, `fixTarBarTraitCollectionOnIpadForiOS18()`,
forces `traitOverrides.horizontalSizeClass = .compact` on iPad. This fork
deliberately renders the iPhone-style bottom bar on iPad rather than the iOS 18
sidebar, and no `UITab` or sidebar-mode API appears anywhere in the app.

So iPad capacity equals iPhone capacity: **5**. Screen size and orientation
change item *width*, never item *count*. `TabLayout.capacity(for:)` exists so
that a future iPad sidebar or an Android surface has one place to change.

---

## 8. Settings UI

New top-level row "Tab Bar" in `SettingsViewController`, directly under
Appearance. Adding a `TableRow` case is additive.

SwiftUI screen hosted in `UIHostingController`, themed with
`@EnvironmentObject theme` per `AGENTS.md`. Chosen over the XIB +
`UITableView`-editing path (`ShelfActionsViewController`) because it is roughly
150 lines against 400-plus, and it is a leaf screen with no deep links pointing
into it.

Two sections:

- **In tab bar** — ordered, drag to reorder via `.onMove`, remove via swipe.
  Capped at 5. Refuses to empty the last slot.
- **Hidden** — unpromoted destinations, plus "Add Playlist Tab", which opens a
  picker over `DataManager.sharedManager.allPlaylists(includeDeleted: false)`.
  Multiple playlist slots are permitted.

Save triggers a controlled rebuild (§6) plus a sync push (§4). No live preview
of the bar in v1.

---

## 9. Peripheral surfaces

**Keyboard shortcuts** (`MainTabBarController+shortcuts.swift`) become
**positional**: ⌘1–⌘N map to promoted slots in bar order, titles read from the
slot. Hidden destinations lose their shortcut. Today's ⌘4 Up Next binding
disappears unless Up Next is promoted. Every nav shortcut already routes through
a `navigateTo*` method, so it inherits §5 for free.

**Analytics** (`AnalyticsHelper.tabSelected`, `AnalyticsHelper.swift:270`) is an
exhaustive switch. Changes are additive only — existing four event names
untouched for continuity, plus `overflow_tab_opened`, `playlist_tab_opened`
(playlist UUID as parameter), and `tab_bar_layout_changed` on save carrying the
ordered slot ids.

**Titles and icons.** Playlist slot reuses `EpisodeFilter.iconImageName()`
(`EpisodeFilter+Formatting.swift:44`) as a template image, falling back to SF
Symbol `list.bullet`. Playlist slot title is the playlist's live name; no
user-set label override in v1. Overflow is "More" with SF Symbol `ellipsis`.
The Streams tab title stays the hardcoded `"Streams"` rather than expanding
scope into localization.

**Not affected.** CarPlay, the Watch app, widgets, and the App Clip hold no
reference to `MainTabBarController` or `Tab`. Widget deep links reach it only
through the URL routes named in §5.

**No feature flag.** The fork has one user. A dual rendering path would rot.

---

## 10. Blast radius

New files, all requiring `project.pbxproj` registration (`PocketCastsTests/`
does not, per `AGENTS.md`):

- `podcasts/Main/TabLayout/TabDestination.swift`
- `podcasts/Main/TabLayout/TabLayout.swift`
- `podcasts/Main/TabLayout/TabLayoutStore.swift`
- `podcasts/Main/TabLayout/TabLayoutSyncService.swift`
- `podcasts/Main/TabLayout/OverflowViewController.swift`
- `podcasts/Settings/TabBarSettingsView.swift`

Modified:

- `podcasts/Main/MainTabBarController.swift` — `viewDidLoad` reduced to asking
  `TabLayout` for slots; `switchToTab` replaced by `host(for:)`; six-plus
  `navigateTo*` bodies retargeted; migration block added.
- `podcasts/Main/MainTabBarController+shortcuts.swift` — positional commands.
- `podcasts/AnalyticsHelper.swift` — additive cases.
- `podcasts/SettingsViewController.swift` — new `TableRow` case.
- `podcasts/Constants.swift` — new UserDefaults keys.
- `PocketCastsTests/Tests/Main/MainTabBarControllerTests.swift` — currently
  asserts `pcTabs.count == 5`.
- `supabase/migrations/` — new `nav_layout` migration.

Upstream-merge posture: `MainTabBarController.swift` is a file Automattic edits
often. Keep logic in the new files and the edits inside it minimal.

---

## 11. Test plan

- Default Layout renders exactly today's five destinations, no Overflow.
- `needsOverflow` truth table: empty complement + no truncation → false; each
  other combination → true.
- Overflow contains unpromoted **core** destinations only, never an unpromoted
  extra, plus truncated slots of any kind.
- Layout with 7 slots on capacity 5 → 4 visible + Overflow holding 3.
- `lastTabOpenedID` migration is idempotent: run twice, same result.
- Selection restored by id after a reorder, not by index.
- `host(for:)` on an unpromoted destination pushes onto the Overflow stack, and
  twice in a row does not stack two instances.
- Deleting a promoted playlist keeps the slot count stable.
- Round-trip `TabLayout` through `Codable`, including a `.playlist` slot.

---

## 12. Risks

| Risk | Mitigation |
|------|-----------|
| Controlled rebuild while a nav stack or modal is live | Guarded by the safety condition in §6; the only unguarded caller is user-initiated save |
| Force-unwrap stragglers in `navigateTo*` | Reference sweep per `AGENTS.md`; grep `firstIndex(of:` across `podcasts/` |
| Playlist icon assets look wrong at 25pt | Visual check on device; SF Symbol fallback already in place |
| Upstream merge conflict in `MainTabBarController.swift` | Logic concentrated in new files |
| Sync pull racing the initial tab build | Pull is async and applies through §6, never mutating a half-built bar |
