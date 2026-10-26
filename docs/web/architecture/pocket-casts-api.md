# Pocket Casts API from the web player

What the web player's Functions call on the Pocket Casts server, in what
format, and what is known about the responses. The decision is
[ADR 0007](../adr/0007-protobuf-for-pocket-casts-account-data.md). The reference
implementations are the iOS tasks in
`pocket-radio-ios/Modules/Sources/PocketCastsServer/` and the menubar's
`APIService.swift`.

Hosts: `api.pocketcasts.com` (production) and `api.pocketcasts.net` (staging).
Select one with the server-only `PC_API_ENVIRONMENT` (`production` by default,
or `staging`). The two services don't share device grants or accounts, and the
secret tables aren't namespaced by environment, so never share a token store
between them.

## Endpoints

| Endpoint | Format | Status in the web player |
|---|---|---|
| `device/authorize`, `user/token` | JSON, scope `tv` | Built and proven in staging (Pairing, polling, refresh code). Live refresh was never exercised. |
| `user/podcast/list` | Protobuf (ADR 0007) | M1's JSON probe got HTTP 200 and a JSON object. Protobuf not yet run from the web. |
| `user/playlist/list` | Protobuf (ADR 0007) | Built in M2 (`GET /api/playlists`): request sets only `m: "mobile"`, as iOS does; reads `uuid`, `is_deleted` and `title`. Ran live on staging (`.net`) on 2026-10-23: playlist names appear in the Sidebar (user-reported). A deleted playlist has not been seen live. |
| `user/named_settings/update` | Protobuf (ADR 0007) | M1's JSON probe got HTTP 200 and a JSON object. |
| `user/podcast/episodes` | Protobuf (ADR 0007) | Allowed by the probe allowlist; no result recorded. |
| `up_next/sync`, `sync/update_episode` | Protobuf in both native clients | Blocked by the allowlist. Never called. Writes need user approval to test. |

The Function's allowlist (`functions/_lib/auth/pocket-casts.ts`) refuses any
other path. The M1 probe returns structure only, never key names or values.

## Fields (from iOS `api.pb.swift`, not observed live)

| Message | Fields |
|---|---|
| `Api_UserPlaylistListResponse` | `playlists[]` |
| `Api_PlaylistSyncResponse` | `uuid`, `title`, `is_deleted`, `manual` (Manual versus Smart playlist), `sort_position`, `episode_uuids`, `episode_order`, `episodes[]`. Smart rules: `all_podcasts`, `podcast_uuids`, `audio_video`, `downloaded`, `not_downloaded`, `finished`, `partially_played`, `unplayed`, `starred`, `filter_hours`, `sort_type`, `icon_id` |
| `Api_UserPodcastListResponse` | `podcasts[]`, `folders[]` |
| `Api_UserPodcastResponse` | `uuid`, `title`, `author`, `folder_uuid`, `sort_position`, `date_added`, `last_episode_published`, `unplayed` |

Treat every field as optional: protobuf omits defaults, and wrapper types
(`BoolValue`, `Int32Value`) can be absent. Requests: playlist list takes `m`, `v`
and `exclude_deleted`; podcast list takes `v` and `m`.

If a response arrives as JSON, expect lowerCamelCase or the original snake_case.
The token parser accepts both and rejects conflicts; do the same for any JSON.

## Pairing facts

- Device authorization needs scope `tv`. The password-login scope `mobile` is
  rejected with `invalid_scope`, in JSON and protobuf alike.
- The phone's approval and the web's polling must hit the same service. The
  fork's `StagingDebug` build approves against `.net`; a web using `.com` makes
  the phone say "Your QR code expired" because it maps every `invalid_grant` to
  that alert.
