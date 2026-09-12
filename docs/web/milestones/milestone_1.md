# M1 — Spike: PC auth + Vite/React scaffold + radio favorites parity

**Goal:** De-risk the auth/hosting plumbing before building any UI. Prove the
PC-account-as-identity model works end-to-end (browser → PC API → Edge
Function → Supabase, with `x-user-uuid` set only server-side), and stand up
the repo with radio-only feature parity to console/menubar (curated stations,
favorites). Listen-time is out of scope for M1.

**User checkpoint:** deployed Vercel preview where a user logs in with their
Pocket Casts account, sees curated stations, can favorite/unfavorite, and
favorites sync to `radio_favorites` (visible in iOS app too).

## Spikes 0 + 1 — resolved 2026-08-23

Resolved via a captured HAR of `pocketcasts.com`'s own web player (browser
already logged in, refresh-token flow observed) plus a read of the iOS
`PocketCastsServer` module. Findings:

- **Spike 0 (PC token → `user_uuid`): confirmed, endpoint exists.**
  `POST https://api.pocketcasts.com/user/token`, body
  `{"grantType":"refresh_token","refreshToken":"<jwt>"}`. Response includes a
  stable `uuid` field (matched the `_ui=` param on every analytics beacon in
  the same capture) — same identity iOS reads as `ServerSettings.userId`.
  Both refresh and access tokens are JWTs carrying a `pc:uuid` claim in the
  payload, so `user_uuid` is derivable client-side from a decoded token
  without an extra round trip. Initial credential login is
  `POST /user/login` (same host — confirmed via iOS `TokenHelper.swift:154`,
  not independently captured in the HAR since the browser session was
  already authenticated).
- **Spike 1 (CORS): confirmed, and it forecloses "direct fetch."**
  `api.pocketcasts.com` responds with
  `Access-Control-Allow-Origin: https://pocketcasts.com` (exact-match
  allowlist, not a wildcard or reflected origin) +
  `Access-Control-Allow-Credentials: true`. A Vercel-hosted origin will not
  be on that allowlist. **"Direct browser fetch to PC login endpoint" is no
  longer a live option for M1** — drop it from the design space rather than
  spiking it further. The Edge Function proxy is required for login
  transport, not only for the Supabase write path.
- **Wire format: iOS and web hit identical paths on the same host with
  different bodies.** iOS sends `application/octet-stream` +
  serialized protobuf (`Api_UserLoginRequest`, `Api_UserTokenLogin`, per
  `Modules/Sources/PocketCastsServer/Private/Protobuffer/api.pb.swift` in
  `pocket-radio-ios`). The captured web traffic sends
  `application/json` to `user/token`, `user/podcast/list`, ... and gets
  JSON back — `api.pocketcasts.com` already speaks JSON natively for the
  web client on the paths actually observed. `user/login` was **not** in
  the capture (see Spike 0 above); JSON support there is inferred from
  parity with `/user/token`, not confirmed. **The Edge Function does
  not need `pc-relay`'s protobuf↔JSON translation** (`supabase/functions/pc-relay/protobuf.ts`)
  for the confirmed paths; treat `/user/login` as unconfirmed until the
  first real call. It's a plain JSON reverse-proxy that adds session-token
  issuance and sets `x-user-uuid` server-side — materially simpler than
  `pc-relay`.
- **Not yet resolved:** how subsequent authenticated calls attach the access
  token (Authorization header presumed — `tokenType: "Bearer"` in the
  `/user/token` response — but the captured HAR had Authorization/Cookie
  headers stripped by Chrome's HAR export privacy redaction on every
  endpoint after `/user/token`). Re-capture with "include sensitive data"
  checked before writing the Edge Function's forwarding logic, or just
  assume standard `Authorization: Bearer <accessToken>` and confirm on
  first real call.

## Security model (non-negotiable)

Current Supabase RLS is **header-trust, not auth**: policies match
`user_uuid` against the client-supplied `x-user-uuid` header
(`20260512000005_reenable_rls.sql`). iOS tolerates this (anon key buried in
a binary). A browser ships the anon key in plaintext and can set any
`x-user-uuid` from devtools → **any user can read/write any user's rows.**
For web, therefore:

- **All identity-bearing Supabase access routes through a Supabase Edge
  Function.** The browser never reads/writes `user_uuid`-scoped tables
  directly. The Edge Function sets `x-user-uuid` from a server-validated
  token; the browser cannot forge it.
- **No "direct" fallback.** Even if the CORS spike succeeds, direct
  browser→Supabase with a browser-set `x-user-uuid` is forbidden — zero
  access control. CORS result decides PC-login *transport* only, never
  whether the proxy exists.
- **Token storage:** Edge Function issues a short-lived session token
  (httpOnly cookie preferred over localStorage to limit XSS). Raw PC token
  never persisted in JS-readable storage.

## Scope

- Repo init: `pocket-radio-web` (own git repo), Vite + React, deployed to
  Vercel (preview deploys per PR).
- ~~Spike 0 — PC token → `user_uuid`~~ and ~~Spike 1 — CORS~~: **resolved,
  see "Spikes 0 + 1 — resolved" above.** `POST /user/token` confirmed
  reachable and JSON-speaking; `POST /user/login` inferred from parity,
  unconfirmed until first real call; direct browser fetch is CORS-blocked
  for a non-`pocketcasts.com` origin, so login goes through the Edge
  Function too.
- Auth: PC account login only (no separate Supabase Auth). Edge Function
  validates the PC token, derives `user_uuid`, issues a short-lived session
  token, and is the sole setter of `x-user-uuid` on Supabase calls.
- Supabase: reuse `radio_favorites` table/schema from iOS. Verify the
  header-based RLS policy is satisfiable *only* via the Edge Function path
  (browser anon key must not match arbitrary uuids).
- **Curated stations source of truth — resolve now, not "TBD":** promote
  `curated_stations.json` to a Supabase table (single source for
  iOS/menubar/console/web) OR explicitly accept a 4th duplicated copy with
  a tracked debt item. Default: Supabase table. No silent drift.
- **Stream URLs — mixed-content audit:** many radio streams are plain
  `http://`; browsers block http media on an https (Vercel) page with no
  override. Audit `curated_stations.json` for http URLs; per URL plan
  https upgrade or an Edge Function / relay proxy. Can break `<audio>`
  playback for a chunk of stations — resolve before the checkpoint.
- UI: curated stations list, play via `<audio>` (https streams only — see
  audit), favorite/unfavorite toggle, favorites list.
- Add `pocket-radio-web/` to top-level Makefile (`checkout`, `status`,
  `web-*` delegated targets) and `docs/web/`.

## Behaviors to test (red → green, one at a time)

0. PC token → `user_uuid`: `POST /user/token` (refresh-token grant) resolves
   to a stable `user_uuid`, matching iOS `ServerSettings.userId` — confirmed
   via HAR capture (see "Spikes 0 + 1 — resolved"); write a regression test
   against the real endpoint from the Edge Function, not a fresh spike.
1. Edge Function ↔ PC JSON round trip: Edge Function forwards `/user/token`
   as JSON and gets JSON back — no protobuf translation needed (confirmed).
   Assert the same for `/user/login` — this is the test that confirms the
   inferred-from-parity claim above, not a given. Confirm the Authorization
   scheme for subsequent authenticated calls (presumed `Bearer
   <accessToken>`, unconfirmed — see "Not yet resolved" above) on first
   real call.
2. PC login form → authenticated session via Edge Function; short-lived
   session token (httpOnly) survives reload; raw PC token not in JS storage.
3. Curated stations list renders from the chosen source of truth (Supabase
   table by default — see scope; not a 4th JSON copy unless debt-tracked).
4. Station playback via `<audio>` for an **https** stream — play/pause.
   Confirm a known `http://` stream is blocked (drives the proxy decision).
5. Favorite toggle writes to `radio_favorites` via Edge Function with the
   server-derived `user_uuid`.
6. **Security: forged-header write rejected.** Direct browser→Supabase write
   with anon key + arbitrary `x-user-uuid` must NOT land another user's row
   (proves header-trust is closed on the web path).
7. Favorite added on web appears in iOS app (and vice versa) — cross-platform
   sync check.
8. Vercel preview deploy works from a PR (CI smoke).

## Out of scope

Podcast/episode playback, PC subscriptions/library, listen-time sync, queue,
Remix/SSR, Electron parity.
