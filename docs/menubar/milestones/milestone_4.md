# M4: Radio Favorites from Supabase

**Status**: COMPLETED — 2026-05-21

## Goal

User's favorite radio stations from Supabase appear in the menubar popover and can be played.

## Data Flow

1. Get userId from Keychain (stored at login)
2. `GET {supabase}/rest/v1/radio_favorites?select=station_id` with `x-user-uuid` header
3. For each station_id, `GET de1.api.radio-browser.info/json/stations/byuuid/{id}`
4. Display station name + play button in popover
5. Play station stream URL via AVPlayer

## Done when

- After login, favorites list appears below the up-next episode in the player view
- Each favorite shows station name and has a play button
- Clicking a station plays its stream URL
- Switching from podcast → station and back works correctly
- If user has 0 favorites, show "No favorites yet" message
- Refresh button updates both up-next and favorites
