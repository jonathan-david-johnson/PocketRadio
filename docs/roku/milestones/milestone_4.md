# M4: Radio Favorites + Browse/Search

**Status**: NOT STARTED

## Goal

Favorite radio streams: list from Supabase → resolve via radio-browser.info, play, add/remove favorite, and browse/search the radio-browser catalog. All JSON (no protobuf).

## Done when

- Favorites list: Supabase `radio_favorites` station_ids → resolved to name/logo/stream via radio-browser `byuuid`
- Selecting a favorite plays its stream (play/pause-only; no scrub for live)
- Add favorite (Supabase POST, merge-duplicates) and remove favorite (Supabase DELETE) work + reflect in list
- Browse shows radio-browser `topvote` (default); Search by name returns results
- Add-from-browse/search persists to favorites

## What to Build

### Supabase Tasks (HANDOFF §6.9)
Base `https://brvtspdculqyvdrmdtef.supabase.co`. Headers: `apikey: <anon key>`, `x-user-uuid: <userId>`.
- **List**: `GET /rest/v1/radio_favorites?select=station_id`
- **Add**: `POST /rest/v1/radio_favorites` + `Content-Type: application/json` + `Prefer: return=minimal,resolution=merge-duplicates`; body `{user_uuid, station_id}`
- **Remove**: `DELETE /rest/v1/radio_favorites?station_id=eq.<id>&user_uuid=eq.<userId>` + `Prefer: return=minimal`

### radio-browser Tasks (HANDOFF §6.10) — **always** `User-Agent: PocketRadio/1.0`
Base `https://de1.api.radio-browser.info/json`.
- **byuuid**: `GET /stations/byuuid/{uuid}` (resolve favorite; uses `url` not `url_resolved`)
- **search**: `GET /stations/search?name=<q>&limit=40&hidebroken=true&order=votes&reverse=true`
- **topvote**: `GET /stations/topvote?limit=50&hidebroken=true`
- Fields: `stationuuid`, `name`, `url_resolved`/`url`, `favicon`, `country`, `language`, `tags`, `codec`, `bitrate`, `votes`, `homepage`. Skip rows with empty name/stream.

### UI
- Favorites + Browse as `RowList`/`MarkupList`; OK plays. `*`/Options to add/remove favorite. Search via keyboard node.
- Live stream → play/pause-only (duration 0/indefinite → hide scrub).

## Implementation Strategy

1. Supabase list Task + radio-browser byuuid resolve → favorites list.
2. Play a favorite (live audio, no scrub).
3. Add/remove favorite + list refresh.
4. Browse topvote + name search + add-from-browse.

## User Checkpoint

See favorites (KCRW Eclectic 24, KEXP, NPR Hourly) → play one. Remove one → gone. Search a station → add it → appears in favorites.

## Commit
TBD.
