# Web M1 — Prove pairing, the stream relay, and the Cloudflare deploy

**Status**: PLANNED
**Depends on**: Web ADRs 0001–0005 (planning session 2026-10-11)
**Required by**: Web M2–M7

## Where the work happens

| | |
|---|---|
| Plan | Shell `main`: this file, experiment reports in `docs/web/experiments/` |
| Code | `pocket-radio-web`, branch `feature/m1-spikes` from the first `main` commit (empty project setup: Vite + React + TS, Pages Functions, Vitest, Makefile, `AGENTS.md`, one-line `CLAUDE.md`) |
| Worktree | `pocket-radio-web/` |
| Shell changes | Additive: a `supabase/migrations/` file for the web-only secret tables, `web-*` delegating targets in the top-level `Makefile` |

**Goal:** Prove the three things the web player can't work without, before
building any screens. Pairing must sign a browser in to Pocket Casts through
our Worker. The stream relay must play a continuous radio stream to an
`https://` page and report its track titles. Pages must deploy the page and
its server code together on one origin, with a session cookie that works in
Safari. Each experiment confirms or overturns an accepted ADR.

**User checkpoint:** Open the `*.pages.dev` address in Safari and in Chrome.
Scan the QR code with the PocketRadio iPhone app and approve. The page now
shows your Pocket Casts email. Start a plain `http://` station that sends ICY
titles (for example SomaFM Groove Salad's `http://` MP3 stream). It plays
through the relay, and the title on the page changes when the song changes.
Reload: you are still signed in.

## Scope

- **Repo setup (`main`, before the branch).** `pocket-radio-web` has no
  commits. First commit: Vite + React + TypeScript, `functions/` for Pages
  Functions, Vitest, `wrangler` config, a `Makefile` (`dev`, `test`, `deploy`),
  `AGENTS.md`, and a `CLAUDE.md` containing only `@AGENTS.md`. Then `make hooks`
  from the shell.
- **Supabase (shell).** Migration for the web-only secret tables:
  `web_sessions` (hashed session id, `user_uuid`, `expires_at`) and
  `pc_tokens` (`user_uuid`, Pocket Casts refresh and access tokens, expiry).
  RLS enabled with **no** anon-key policy (ADR 0002). The Worker uses the
  service-role key, stored as a Cloudflare secret.
- **Experiment code** lives in `functions/api/` and a bare test page. It is
  spike-quality and may be rewritten in M2. Its findings outlive it.

## Hypotheses (not yet observed)

- H1. `device/authorize` and the device-code `user/token` grant accept
  `application/json` from a Worker. The response includes `user_code`,
  `verification_uri_complete`, and, after approval, tokens whose `uuid`
  matches iOS `ServerSettings.userId`.
- H2. The fork's `DeviceApproveView` can be reached from a QR code through the
  fork's `pktc://` scheme, routed by JLRoutes `/pair`. A `pocketcasts.com`
  universal link would open Automattic's app or website instead.
- H3. Authenticated Pocket Casts calls from a Worker take
  `Authorization: Bearer <access token>` and speak JSON on the paths M2–M6
  need.
- H4. A Worker can relay an `http://` ICY stream for 60 minutes or more without
  being cut off. Piping uses well under the Workers CPU limit, and ICY
  stripping adds no audible glitches.
- H5. A first-party, httpOnly, `SameSite=Lax` session cookie set by a Pages
  Function survives reload in Safari and Chrome.

## Experiments

Record each result in `docs/web/experiments/YYYY-MM-DD_<topic>.md`.

| # | Question | Method | Pass criterion | Feeds |
|---|---|---|---|---|
| E1 | Can a Worker complete Pairing? | `POST /api/pair/start` calls `device/authorize` with JSON; the page shows a QR code of `pktc://pair?user_code=…` and the human-readable code; `GET /api/pair/poll` polls the device-code grant until approved | Worker holds Pocket Casts tokens, and the derived `uuid` equals the iPhone's `ServerSettings.userId` | ADR 0003 stands, or fall back to email/password |
| E2 | Does the fork approve from a QR code? | Scan with the iPhone camera, with and without Automattic's app installed; also try `verification_uri_complete` | Fork's approval screen opens with the code pre-filled and approval completes | QR format; whether ADR 0003 needs a manual-entry path |
| E3 | Which Pocket Casts calls work as JSON with a bearer token? | From the Worker call `up_next/sync` (or the web player's equivalent), `user/podcast/list`, `user/podcast/episodes`, `user/playlist/list`, `sync/update_episode`, `user/named_settings` | Each returns usable JSON, or the report names which need protobuf (reuse `supabase/functions/pc-relay/protobuf.ts`) | M5 and M6 API client design |
| E4 | Can the relay play a station for an hour and report titles? | `GET /api/relay/:stationId` resolves the URL server-side (ADR 0004), sends `Icy-MetaData: 1`, strips metadata blocks, and pushes titles over Server-Sent Events. Run 60+ minutes on an `http://` station, then on an `https://` station | No disconnect, no audible glitch at metadata boundaries, CPU per request recorded and under the plan limit, titles correct | ADR 0004 stands; Workers Free or Paid plan |
| E5 | Is relaying audio allowed? | Read Cloudflare's current Service-Specific Terms and Workers terms on proxying audio | A cited clause permits it, or a named risk with a fallback | ADR 0004 stands, or narrows to `http://` only |
| E6 | Does the session work on our own origin? | Pages Function sets the session cookie after E1; reload; Sign out; Sign out everywhere; a forged `x-user-uuid` request with the anon key against `pc_tokens` | Signed in after reload in Safari and Chrome; both sign-outs work; forged read returns zero rows | ADR 0002's single-origin and secret-table claims |

## Decision gate

| Decision | Evidence |
|---|---|
| Keep Pairing as the only sign-in (ADR 0003), or add email/password | E1, E2 |
| QR payload: `pktc://` link, Pocket Casts URL, or code only | E2 |
| JSON-only API client, or JSON plus a protobuf codec | E3 |
| Keep relaying every station (ADR 0004), or relay `http://` only | E4, E5 |
| Cloudflare plan: Free or Workers Paid | E4 |
| Session design holds (ADR 0002) | E6 |

## Out of scope

- Every screen, the Layout, Streams UI, lyrics, podcasts, and playlists (M2–M7).
- KCRW alignment, ACRCloud, remote control, and smart playlists (later; see
  `docs/web/README.md`).
- A custom domain.

## Docs impact

- **Docs this changes or makes stale:** `docs/web/README.md` (repo no longer
  "not scaffolded"); shell `AGENTS.md` platform table (web row);
  `docs/security_concerns.md` (web secret tables, relay); top-level `Makefile`
  web section; web ADRs 0002–0004 if any experiment fails.
- **Questions this must settle:** the six decisions in the Decision gate.

## Hand-performed interactions

- [ ] Scan the QR code with the iPhone camera — the fork's approval screen opens with the code filled in
- [ ] Approve on the phone — the browser signs in within a few seconds
- [ ] Listen through one song change on the relay — no audible gap, and the title updates
