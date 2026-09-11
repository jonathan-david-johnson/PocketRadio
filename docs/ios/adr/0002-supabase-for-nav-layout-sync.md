# Tab layout syncs through Supabase, not Pocket Casts

The user's tab bar Layout is stored locally in `UserDefaults` and synced through
this project's own Supabase backend, in a `nav_layout` table keyed by
`user_uuid`, with last-write-wins on `updated_at`.

## Why

The obvious place for a synced user preference is
`Modules/Sources/PocketCastsServer/Public/AppSettings.swift`, which already
carries `@ModifiedDate` fields and rides Pocket Casts' own sync. It cannot be
used. That struct is protobuf-backed against **Automattic's** server, which this
fork does not control; an unknown field is silently dropped, so the setting
would appear to sync and then vanish. There is no failure mode that surfaces
this to the user, which makes it worse than not syncing at all.

Supabase is already the fork's answer for its own synced state —
`radio_favorites`, `custom_streams`, `listen_time`, `lyric_offsets` — with an
established client in `podcasts/Radio/RadioSupabase.swift` that attaches the
`x-user-uuid` header from `ServerSettings.userId` and RLS policies keyed on it.
Adding one table reuses a proven path rather than opening a new one.

Local `UserDefaults` remains the render source of truth so the bar builds
offline with no latency and no network on the launch path. Sync is a background
reconcile on top.

## Considered Options

- **Supabase table, local-first, LWW (chosen).** Reuses an existing pattern.
  Works signed out, degrades silently.
- **Pocket Casts `AppSettings`.** Impossible without server changes we cannot
  make. Fails silently, which is the worst property available.
- **Local only, no sync.** Simplest, and the only surface with a bottom nav
  today is iOS. Rejected because a second iOS device is a real case now, and
  Android is scaffolded in the docs tree.
- **Per-device rows keyed by device id.** Preserves different layouts per
  device, but "I only ever look at one playlist" is not a device-specific
  preference, and it doubles the reconcile logic.

## Consequences

- Sync requires a Pocket Casts login, because `RadioSupabase.client()` derives
  the user id from `ServerSettings.userId` and throws `notLoggedIn` otherwise.
  Signed out, the layout is local and silent.
- One shared layout across devices. A device with lower capacity than the writer
  truncates into Overflow rather than erroring.
- A `.playlist` slot syncs a playlist UUID. Pocket Casts playlist UUIDs are
  sync-stable across devices, so the reference survives; a playlist deleted
  elsewhere is handled by the live-reconciliation rule, not by sync.
- Pull-at-launch collides with the rule that slot structure is frozen per
  session. Resolved by applying a newer remote layout through the same
  controlled rebuild the settings screen uses, and only when every nav stack is
  at root with nothing presented modally.
- The layout is not readable by the menubar, console, or Roku surfaces unless
  they implement the same table. None of them have a bottom nav, so this is
  latent, not a gap.
