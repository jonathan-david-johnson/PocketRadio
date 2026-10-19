# E1, E3 and E5 — identity match, Pocket Casts response formats, and Radio Paradise's terms

**Date:** 2026-10-18. **Status:** written for the M1 decision gate. E1 passed (below). E3 is partly
source-derived (labelled below); E5 is a public-page review, not legal advice.

## E1 — the web session's UUID matches the one iOS writes under

**Method (user-approved, read-only).** One script read `user_uuid` from the
existing PocketRadio database with the local service key. It compared SHA-256
hash prefixes, so no UUID or email was printed or recorded here. Nothing was
written.

**Result: match.** The one row in `pc_tokens` (made by the earlier local staging
Pairing, so web-derived from Pocket Casts' own response) has the same UUID as
rows the iOS app wrote to `radio_favorites` and `nav_layout`. That second table
is the Layout M2 reads. The database also holds a second user in those two
tables; the web token row is not that user.

**What it shows.** For this account on the staging (`.net`) account store, the
web session's UUID equals `ServerSettings.userId`, so the web player will find
this user's `nav_layout` row. **What it doesn't show.** The deployed staging
project's own database has no iOS rows, so this used the existing database's
earlier local pairing. Production `.com` UUIDs were not compared. `listen_time`
and `custom_streams` are empty, so they gave no evidence.

## E3 — which format the web client should use

### What was observed live

The web Function posts **JSON** (`Content-Type` and `Accept: application/json`)
and the staging server answered. The user reported these results from the
deployed and local staging probes:

| Endpoint | Result |
|---|---|
| `user/podcast/list` | HTTP 200, a JSON object |
| `user/playlist/list` | HTTP 200, a JSON object |
| `user/named_settings` (sent to `user/named_settings/update`) | HTTP 200, a JSON object |

The probe reports structure only. It never returns key names, values, UUIDs or
emails (`functions/_lib/auth/handlers.ts`). So **no live field name has been
observed**. The shapes below come from the iOS protobuf source, not from a live
response.

### Source of truth

The native clients use **protobuf** (`application/octet-stream`), not JSON, for
every endpoint in the table below: the iOS tasks in
`Modules/Sources/PocketCastsServer/` and the menubar's `APIService.swift`. The
menubar uses JSON only for the public `cache.pocketcasts.com` pages. That the
same endpoints also answer JSON is a server behavior we observed, not one the
native clients depend on.

Protobuf's JSON form normally uses lowerCamelCase (`isDeleted`), but a server
may send the original snake_case (`is_deleted`). The token parser in
`pocket-casts.ts` already accepts both and rejects a conflict. Do the same for
every field read from these endpoints.

### Fields from `api.pb.swift` (source-derived)

| Message | Fields the web player will read |
|---|---|
| `Api_UserPlaylistListResponse` | `playlists[]` |
| `Api_PlaylistSyncResponse` (one playlist) | `uuid`, `title`, `is_deleted`, `manual` (Manual versus Smart playlist), `sort_position`, `episode_uuids`, `episode_order`, `episodes[]`; Smart rules: `all_podcasts`, `podcast_uuids`, `audio_video`, `downloaded`, `not_downloaded`, `finished`, `partially_played`, `unplayed`, `starred`, `filter_hours`, `sort_type`, `icon_id` |
| `Api_UserPodcastListResponse` | `podcasts[]`, `folders[]` |
| `Api_UserPodcastResponse` | `uuid`, `title`, `author`, `folder_uuid`, `sort_position`, `date_added`, `last_episode_published`, `unplayed` |

Protobuf wrapper types (`BoolValue`, `Int32Value`) are plain values in JSON, and a
field left at its default may be **absent**. Treat every field as optional.

Request bodies: playlists take `m`, `v` and `exclude_deleted`; podcast list takes
`v` and `m`. The probe sends `v="2"` and `m="mobile"`. The iOS playlist task
sends only `m`. The server accepted the probe's body.

### What M2 needs, and the decision it supports

M2 needs only each playlist's `uuid` and `title`, and whether it is deleted
(unavailable). Those come from `user/playlist/list`, which answered JSON.

| Question | Answer | Basis |
|---|---|---|
| JSON or protobuf for M2? | **Protobuf (user's choice).** JSON was the observed alternative. | JSON answered 200 and a JSON object on the list endpoints; native clients use protobuf for all of them. |
| Is protobuf needed later? | **Probably, for M5 sync writes.** | `up_next/sync` and `sync/update_episode` are protobuf in both native clients. The web allowlist blocks them and they were never called, so JSON support is **unknown**. |
| Confirm protobuf works live | **First M2 step.** | Not yet run from the web. Make a read-only playlist-list call and record the outcome, no values. |

**Decision (user, 2026-10-18): protobuf** for Pocket Casts account data, recorded
in [ADR 0007](../adr/0007-protobuf-for-pocket-casts-account-data.md). The
JSON-only recommendation above is superseded. The table's last row is now M2's
first step: a read-only protobuf call to confirm it works from the Function.

### Not covered (accepted by the user on 2026-10-18)

Live token refresh, the production `.com` host, and signed-in calls from outside
a browser. They stay open as known risks.

## E5 — Radio Paradise, the permitted test station

Reviewed with a headless Chrome render of `radioparadise.com` on 2026-10-18,
because the site is a JavaScript app that plain HTTP fetches cannot read.

What the site says:

- **Stream Links** page: "Stream URL for WiFi Radios & other players … copy the
  generated URL and paste it into your player." It offers channel, bitrate and
  codec choices, including `http://stream.radioparadise.com/aac-128` and 320k AAC.
- **FAQ**: tells users to open `http://stream.radioparadise.com/aac-128` in
  iTunes and to use their own radio or player, and lists many third-party and
  device platforms. It describes the service as free and ad-free.
- No terms-of-service, licence or privacy link appeared on the home page, the
  FAQ, Ways to Listen or Stream Links, and the obvious URLs (`/terms`, `/legal`)
  return the app shell, not a document.

Reading: Radio Paradise **publishes its stream URLs for listeners to play in any
player**. That fits a personal browser player that plays the public URL directly,
as ADR 0006 does. It is not a written grant to build a product on the stream,
and it says nothing about metadata or redistribution. The web player does neither:
no relay, no re-hosting, no title or lyric extraction.

Decision for M1: Radio Paradise is the **permitted test source** for the playback
checks. Before any public release, ask the station for written confirmation. Do
not use SomaFM (explicit client and restreaming limits, see the
[terms review](2026-10-15_cloudflare_terms_and_deployment_plan.md)).

### A correction to the station-switch test

The two Radio Paradise IDs used on 2026-10-18 resolve to the **same stream**:
`566476bf-d03c-4cac-b5d3-468f99a874b8` ("Radio Paradise Global") and
`21a282be-44f4-4b8e-aae9-b4c2041af4a5` ("Radio Paradise World/Etc Mix 320k AAC")
both resolve to `https://stream.radioparadise.com/world-etc-320`. The reported
switch therefore did not change stream. For a real switch, use Global then KEXP
`445cbb3a-1c4e-49aa-a268-f5b6acfa8f2e`
(`https://kexp.streamguys1.com/kexp160.aac`, AAC). KEXP's terms were not reviewed,
so treat it as a short functional test only.
