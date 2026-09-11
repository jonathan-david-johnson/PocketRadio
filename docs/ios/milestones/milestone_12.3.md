# iOS M12.3 — Supabase layout sync and live playlist reconciliation

**Status**: NOT STARTED
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

- [ ] New migration in `supabase/migrations/` creating `nav_layout`:
      `user_uuid text primary key`, `slots jsonb`, `updated_at timestamptz`.
- [ ] RLS policy keyed on the `x-user-uuid` header, matching the pattern in
      `20260512000005_reenable_rls.sql`.
- [ ] Applied to the hosted project and verified with a manual upsert.

### 2. Sync service — Sonnet

- [ ] `podcasts/Main/TabLayout/TabLayoutSyncService.swift`, using
      `RadioSupabase.client()` for the authenticated client.
- [ ] **Push** on settings save. `UserDefaults` written first, then upsert.
      Network failure is non-fatal and is not surfaced to the user.
- [ ] **Pull** at launch, asynchronously, off the launch critical path.
- [ ] Last-write-wins on `updated_at`. No merge.
- [ ] Signed out — no network call, no error, no log spam.
      `RadioSupabase.client()` throws `notLoggedIn`; catch it quietly.

### 3. Safe-apply gate — Opus 5

- [ ] A newer remote layout applies through `rebuildTabs` from M12.2 **only when
      safe**: every tab's navigation stack is at root, and nothing is presented
      modally.
- [ ] Otherwise the layout is persisted and applies at next launch. No user
      prompt.
- [ ] Never rebuilds mid-navigation. This is the rule the whole design rests on.

### 4. Live playlist reconciliation

- [ ] Observe `Constants.Notifications.playlistChanged`, already posted by
      `podcasts/ServerSyncManager.swift:38` on sync and by `PlaylistManager` on
      local edits.
- [ ] Playlist **renamed** → update that `UITabBarItem.title` in place.
- [ ] Playlist **deleted** → keep the slot, retitle it, swap its root to a
      "This playlist was deleted" placeholder with a button into tab settings.
- [ ] **Slot count never changes** in response to this notification. Content
      only. Changing structure here shifts `selectedIndex` and corrupts
      `lastTabOpenedID`.

### 5. Settings footer

- [ ] The M12.2 footer becomes live: states whether the layout is syncing, and
      prompts to sign in when it is not.

---

## Tests

- [ ] Remote layout newer than local, all stacks at root → applied immediately.
- [ ] Remote layout newer than local, a modal presented → persisted, not applied.
- [ ] Local layout newer than remote → pushed, remote not applied.
- [ ] Signed out → no network call, layout still loads from `UserDefaults`.
- [ ] `playlistChanged` for a rename updates the title and leaves the slot count
      unchanged.
- [ ] `playlistChanged` for a deletion leaves the slot count unchanged.
- [ ] A layout written at capacity 6 renders at capacity 5 as 4 visible plus
      Overflow.

---

## Manual verification

1. Change the layout on the iPhone. Relaunch on iPad. Layout matches.
2. Delete a promoted playlist from another surface while the tab is visible.
   The tab retitles and shows the placeholder. It does not disappear, and the
   app does not crash.
3. Sign out. Layout still renders from local storage.

---

## Risks

| Risk | Mitigation |
|------|-----------|
| Pull races the initial tab build | Pull is async and applies only through the gate, never to a half-built bar |
| Safe-apply gate rebuilds under the user | Two explicit conditions, both checked at apply time, not at fetch time |
| Playlist UUID drift between devices | Pocket Casts playlist UUIDs are sync-stable; a missing one is handled by reconciliation |
| RLS misconfigured, layouts leak between users | Mirror the existing policy exactly; verify with a second account before shipping |
