# M3: Supabase + Favorites

**Status**: NOT STARTED

## Goal

Favorites persist to Supabase. Favorites tab populated.

## Done when

- Heart button on Station Detail saves/removes favorite
- Favorites tab shows saved stations
- Sign out → sign in → favorites still present (Supabase-backed)
- Swipe-to-delete on Favorites tab works

## What to build

- Add Supabase Swift SDK via SPM
- `SupabaseClient.swift` — init, user_uuid injection (see `docs/designs/supabase_client.md`)
- `RadioFavoritesManager.swift` — read/write `radio_favorites` table
- `FavoritesViewController` — list of favorited stations
- Heart button state in `StationDetailViewController`

## Notes

- See `docs/designs/favorites.md` for UX
- `ServerSettings.userId` is the `user_uuid` for all Supabase calls
- Not-logged-in state: show "Sign in to Pocket Casts" message, no local fallback for MVP
