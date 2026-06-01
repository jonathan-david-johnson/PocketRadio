# M3: Radio Favorites + Browse/Search (Tracer Bullet)

**Status**: DONE

## Goal

Favorite radio streams: list from Supabase → resolve via radio-browser.info, play, add/remove, plus Browse/Search. **All JSON, called directly from Roku** (no relay, no protobuf). Deliberately before Up Next: this builds the reusable scaffolding — generic list UI, `Audio` playback of a *dynamic* URL, streamformat inference, live-vs-seekable gating — on the easy path, so Up Next (M4/M5) only adds resume/sync on top.

## Done when

- Favorites list: Supabase `radio_favorites` station_ids → resolved to name/logo/stream via radio-browser `byuuid`
- Selecting a favorite plays its stream; **live streams = play/pause only** (no scrub — `duration` 0/indefinite)
- Add favorite (Supabase POST, merge-duplicates) + remove (Supabase DELETE) work and refresh the list
- Browse shows radio-browser `topvote`; Search by name returns results; add-from-browse persists
- streamformat inferred from `codec`/URL (`hls` for `.m3u8`, else `aac`/`mp3`) — not hardcoded
- Empty favorites + offline/rate-limited radio-browser show a message, not a crash

## What to Build

### Direct HTTP (reuse `HttpGetTask`; add POST/DELETE variants)
**Supabase** (HANDOFF §6.9) — headers `apikey: <anon key>`, `x-user-uuid: <userId>`:
- List `GET /rest/v1/radio_favorites?select=station_id`
- Add `POST /rest/v1/radio_favorites` + `Content-Type: application/json` + `Prefer: return=minimal,resolution=merge-duplicates`; body `{user_uuid, station_id}`
- Remove `DELETE /rest/v1/radio_favorites?station_id=eq.<id>&user_uuid=eq.<userId>` + `Prefer: return=minimal`

**radio-browser** (HANDOFF §6.10) — **always** `User-Agent: PocketRadio/1.0`:
- `GET /stations/byuuid/{uuid}` (resolve favorite; uses `url` not `url_resolved`)
- `GET /stations/search?name=<q>&limit=40&hidebroken=true&order=votes&reverse=true`
- `GET /stations/topvote?limit=50&hidebroken=true`
- Skip rows with empty name/stream. Mirror note: `de1.api.radio-browser.info` is one mirror — if it fails, fall back to another host (`de2`/`nl1`) rather than dying.

### Reusable UI + playback (the tracer bullet)
- Generic list (`MarkupList`/`RowList`); OK plays, `*`/Options to add/remove favorite.
- `Audio` playback of the selected `url` with inferred `streamformat`.
- **Live-vs-seekable gating** introduced here: `m.audio.duration` 0/indefinite → hide scrub, play/pause only. M4 reuses this for finite content.

## Implementation Strategy

1. Generic list UI + Supabase favorites list + radio-browser `byuuid` resolve.
2. Play a favorite (live, no scrub) with streamformat inference.
3. Add/remove favorite + refresh.
4. Browse `topvote` + name Search + add-from-browse.

## User Checkpoint

See favorites (KCRW Eclectic 24, KEXP, NPR Hourly) → play one. Remove one → gone. Search a station → add → appears in favorites.

## Commit
TBD.
