# M1 — Spike: PC auth + Vite/React scaffold + radio favorites parity

**Goal:** De-risk the auth/hosting plumbing before building any UI. Prove the
PC-account-as-identity model works end-to-end (browser → PC API or proxy →
Supabase RLS), and stand up the repo with radio-only feature parity to
console/menubar (curated stations, favorites, listen-time).

**User checkpoint:** deployed Vercel preview where a user logs in with their
Pocket Casts account, sees curated stations, can favorite/unfavorite, and
favorites sync to `radio_favorites` (visible in iOS app too).

## Scope

- Repo init: `pocket-radio-web` (own git repo), Vite + React, deployed to
  Vercel (preview deploys per PR).
- **CORS spike (do first):** call Pocket Casts' login API directly from the
  browser. If it works, skip the proxy. If blocked, build a Supabase Edge
  Function proxy for login + token validation.
- Auth: PC account login only (no separate Supabase Auth). Resulting
  `user_uuid` used for Supabase RLS — via Edge Function-issued
  short-lived token if proxy needed (see spike), or directly if not.
- Supabase: reuse `radio_favorites` table/schema from iOS. Add RLS policy
  keyed by validated `user_uuid`.
- UI: curated stations list (reuse `curated_stations.json` from iOS), play
  via `<audio>` element, favorite/unfavorite toggle, favorites list.
- Add `pocket-radio-web/` to top-level Makefile (`checkout`, `status`,
  `web-*` delegated targets) and `docs/web/`.

## Behaviors to test (red → green, one at a time)

1. CORS spike: direct browser fetch to PC login endpoint — succeeds or fails
   with CORS error (determines whether proxy is needed).
2. PC login form → authenticated session (token stored, survives reload).
3. Curated stations list renders from `curated_stations.json` (or shared
   source of truth — TBD if duplicated or fetched from Supabase).
4. Station playback via `<audio>` — play/pause/stream URL resolution.
5. Favorite toggle writes to `radio_favorites` with correct `user_uuid`,
   respecting RLS (unauthenticated/wrong-user writes rejected).
6. Favorite added on web appears in iOS app (and vice versa) — cross-platform
   sync check.
7. Vercel preview deploy works from a PR (CI smoke).

## Out of scope

Podcast/episode playback, PC subscriptions/library, listen-time sync, queue,
Remix/SSR, Electron parity.
