# M3: Supabase + Favorites

**Status**: COMPLETE 2026-05-10

## Goal

Favorites persist to Supabase. Favorites tab populated.

## Done when

- Heart button on Station Detail saves/removes favorite ✓
- Favorites tab shows saved stations ✓
- Sign out → sign in → favorites still present (Supabase-backed) ✓
- Swipe-to-delete on Favorites tab works ✓

## What was built

- `RadioSupabase.swift` — `SupabaseClient` factory; called per-operation so `ServerSettings.userId` is always current. Passes `x-user-uuid` header for RLS.
- `RadioFavoritesManager.swift` — `loadFavorites`, `addFavorite`, `removeFavorite`, `isFavorite` via Supabase PostgREST
- `FavoritesViewController.swift` — table view with swipe-to-delete, empty state ("No favorites yet"), not-logged-in state ("Sign in to Pocket Casts")
- `StationDetailViewController` — heart button with optimistic UI (rolls back on error), checks `isFavorite` on load
- `StreamsHostViewController` — Favorites segment now shows real `FavoritesViewController`
- `supabase/migrations/20260510000002_rls_header_auth.sql` — drops `current_setting('app.user_uuid')` RLS and replaces with `request.header.x-user-uuid` (PostgREST 10+)
- `supabase-swift` v2.46.0 added to `Modules/Package.swift`
- `SUPABASE_URL` / `SUPABASE_ANON_KEY` added to `podcasts-Info.plist` (populated via Xcode build settings)

## Commits

- `93fc74f` (fork) — M3: Supabase favorites — heart button, Favorites tab, RLS-ready client

## Setup (local dev)

```bash
cd PocketRadio
supabase start        # start local Postgres
supabase db push      # apply both migrations
# Copy API URL + anon key from output → set in Xcode scheme environment:
# SUPABASE_URL = http://127.0.0.1:54321
# SUPABASE_ANON_KEY = <local anon key>
```

## Lessons learned

- **RLS without Supabase Auth**: The schema initially used `current_setting('app.user_uuid', true)` which has no standard way to inject per-request from the iOS SDK. PostgREST 10+ exposes request headers as `request.header.*` GUC variables — set via `SupabaseClientOptions.Global(headers:)`. Migration 002 switches to this pattern.
- **SupabaseClient per-operation**: Create a new client per operation (not a singleton) so `ServerSettings.userId` is always current. `SupabaseClient` is cheap to construct for REST-only usage.
- **Optimistic UI for toggle**: `setFavoriteUI` called immediately on tap; Task runs the network call; reverts on error. Keeps UI snappy without blocking on network.
- **FavoritesViewController resolution**: `FavoriteStation` from Supabase only has `station_id`. Full station data (name, city, logo) resolved from `CuratedStationsLoader`. Browse stations (M4) will get name/favicon from radio-browser.info at that point.
