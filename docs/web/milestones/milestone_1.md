# M1 — Spike: PC auth + Vite/React scaffold + radio favorites parity

**Goal:** De-risk the auth/hosting plumbing before building any UI. Prove the
PC-account-as-identity model works end-to-end (browser → PC API → Edge
Function → Supabase, with `x-user-uuid` set only server-side), and stand up
the repo with radio-only feature parity to console/menubar (curated stations,
favorites). Listen-time is out of scope for M1.

**User checkpoint:** deployed Vercel preview where a user logs in with their
Pocket Casts account, sees curated stations, can favorite/unfavorite, and
favorites sync to `radio_favorites` (visible in iOS app too).

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
- **Spike 0 — PC token → `user_uuid` (do first, biggest risk):** confirm a
  PC API endpoint takes a login token and returns a stable `user_uuid`
  (the value iOS reads as `ServerSettings.userId`). Web has no PC SDK, so
  this mapping must be proven to exist and be reachable. If it doesn't
  exist, M1 is blocked — escalate before building.
- **Spike 1 — CORS:** call PC login API from the browser. Determines login
  *transport* (direct fetch vs. Edge Function proxy) only. Does **not**
  affect the security model — Supabase access is always proxied.
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

0. PC token → `user_uuid`: login token resolves to a stable `user_uuid`
   matching iOS `ServerSettings.userId` (spike 0; blocks everything below).
1. CORS spike: direct browser fetch to PC login endpoint — succeeds or fails
   with CORS (determines login transport only, not the proxy's existence).
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
