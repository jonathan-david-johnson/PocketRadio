# Web M1 handoff — local implementation verified

## Staging deployed and browser-checked — 2026-10-18

The app is deployed to the private `pocket-radio-web-m1-staging` Pages project behind two email-only Access applications, with the staging database's secrets installed. The user reported Pairing, reload, Stop, both sign-outs, HTTP rejection, cross-browser session revocation and direct HTTPS playback (Radio Paradise Global) all passing. These are user reports with no captured trace, a short listen, and no rights review. Details, two mistakes made during the upload, and what is still unchecked: [staging deployment](../experiments/2026-10-16_staging_deployment.md).

Later on 2026-10-18 the user also reported a 25+ minute direct playback run (the bar was lowered from 60+), an invalid-ID error, and a station switch. The switch used two IDs that resolve to the same stream, so it was redone with Radio Paradise Global then KEXP, and the user reported that switch worked. E3 and E5 are written up in [formats and terms](../experiments/2026-10-18_api_formats_and_station_terms.md). The deployed code is now committed on `feature/m1-spikes` (`d885ea2`, `faf4fd7`).

Still open for M1: E1 identity comparison with iOS, E2 QR routing (not tested; assumed fine by the user's choice), live token refresh and production `.com` (accepted as known risks), and the gate decision. M1 stays open until the user accepts the gate.

## Current playback scope — 2026-10-15

The user chose direct HTTPS playback, recorded in
[ADR 0006](../adr/0006-direct-https-playback-without-an-audio-relay.md).
The page resolves a radio-browser UUID with an authenticated metadata-only
lookup, then gives the validated HTTPS URL to native audio controls. HTTP-only
stations fail explicitly; no scheme rewrite, audio proxy, SSE title subscription
or generic title/lyrics feature remains. Stop/switch/error/local sign-out/unmount
release the media source. Global sign-out cannot revoke a public URL already
loaded in another browser.

Old relay entry routes return 410 without network/binding access. Normal dev,
build and Pages config do not use the relay Worker/DO. Legacy source/tests and
already-applied SQL remain; no database/cloud cleanup was performed. The old
relay implementation/evidence sections below are historical, not current
playback instructions or proof that direct listening works.

Current verification: **247 unit/UI + 41 isolated SQL/handler tests**, the offline
Pages runtime, typechecks and browser/Functions build passed. Optional legacy
DO smoke passed separately. The local HTTPS site was restarted Pages-only;
health, rebuilt UI, security headers and all four 410 routes were verified.
See [direct implementation evidence](../experiments/2026-10-15_direct_playback.md).
These are not live browser listening or production results.

The user subsequently reported **“played”** after receiving the Radio Paradise
Global UUID (`566476bf-d03c-4cac-b5d3-468f99a874b8`); this is a local direct
playback smoke check, not endurance or browser/OS-matrix evidence.

The user also confirmed that **Stop playback** and local **Sign out / cancel
Pairing** audibly stop the direct stream. This is not cross-browser audio
revocation evidence. The user then confirmed **Ready to pair** after reload,
verifying the signed-out state persisted. The user identified this test platform
as **Chrome on macOS**, then confirmed the same playback/Stop/local-sign-out/
reload checks all passed in **Safari on macOS**. Versions were not supplied.
The user subsequently reported **20 minutes of successful playback**; the
browser for that run was not separately identified. Linux, deployed-origin
checks and 60+ minute endurance remain unverified.

The user approved private Free-only provisioning and upload. Pages and
Supabase projects `pocket-radio-web-m1-staging` were created; the Supabase
organization is verified Free and the new `nano` instance is healthy. Only web
migration `20261011000008` was applied; all five table and 18 RPC anon calls are
denied. Existing database/local sessions were not changed. Dedicated secrets are
saved only in ignored `0600` files, not installed in Cloudflare.

**Next: dashboard checkpoint.** OAuth lacks Access-management and billing-read
permissions. Protect primary and wildcard preview hosts, confirm Workers Free,
then install dedicated server secrets with `.net` and upload explicitly to the
staging target. No app upload or billing change occurred. See
[provisioning/privacy instructions](../experiments/2026-10-16_staging_deployment.md).

Current next steps: verify station switching/errors and HTTP rejection, then
complete the active milestone's identity, refresh, schema,
production-cookie and timed listening checks. Any cloud setup still needs
separate scoped approval and a private Pages project/isolated database. No
cloud resource, billing change, upload, push, merge or milestone closure occurred.

## Original relay implementation record

**Status:** M1 remains IN PROGRESS. The plan was executed through local
implementation, independent review, regression fixes, and commits. External
experiments and the user decision gate are pending. Nothing was pushed.

## Commits and location

| Repo | Revision / branch | Contents |
|---|---|---|
| Shell | `e05b49f`, `main` | Updated shell guidance, approved subagent plan, pinned Codex role |
| Web | `9ea6c56`, `main` | First commit: Vite/React/TS, Pages Functions, tests, Makefile and instructions |
| Web | `25f9933`, `feature/m1-spikes` | Pairing/sessions, probes, restricted relay and bare experiment page |
| Web | `2ce9a87`, `feature/m1-spikes` | Default handler/SQL interleaving test wiring |
| Shell | Commit containing this handoff, `main` | Additive auth migration, web targets, status/security docs and reports |

Worktree: `pocket-radio-web/`. No merge or milestone close occurred.
Unrelated untracked `.pi/agents/` definitions were left untouched.

## Verification

- `make web-test web-typecheck web-build`: 177 unit/UI tests, 41 isolated
  database/handler checks (including two parent tests), two offline workerd
  integration checks, typechecks, browser/Functions build and relay dry run.
- `make hooks-check`: passed for all repos/worktrees.
- Local HTTPS multi-worker server: page, health and signed-out session returned 200.
- Production dependency audit: zero vulnerabilities. Browser bundle secret-schema
  name scan and whitespace checks passed.
- Independent review findings were fixed. Final focused review accepted the
  same-tab cookie-restoration serialization. No verified blocking code finding
  remains from those reviews; external checks below are not waived.

Detailed methods and limits:
[local implementation evidence](../experiments/2026-10-12_local_implementation.md)
and [platform constraints](../experiments/2026-10-11_platform_constraints.md).
All roles used `openai-codex/gpt-6.1-sol` with OAuth. Exact delegated usage and
included subscription consumption were unavailable, so no measured cost is claimed.

## What exists

- Browser-bound Pairing with expiring server-side device grants; source-backed
  identity validation; hashed rolling 90-day sessions and both sign-outs.
- Service-only SQL storage/RPCs, account revocation fences, rate limits and
  approval/refresh/sign-out race tests. Migration was applied with user approval
  on 2026-10-12; live client-role access checks pass.
- Sanitized JSON probes; write-capable `up_next/sync` and `sync/update_episode`
  remain manual/pending, not automatically called.
- One listener-owned SQLite Durable Object joins audio and SSE through Pages.
  Default Worker ingress denies public requests. Revocation/admission/cleanup
  tests and true separate-Worker local integration pass.
- Bare QR/account/relay/probe page. Auth transitions wait for restoration before
  issuing new cookie-changing requests. This is not M2's navigation shell.

## Next actions and gates

1. **User/lead:** clarify permission with Cloudflare and establish station
   redistribution rights before enabling production audio. Current terms do
   not explicitly establish this relay's permission. Workers Paid is a candidate,
   not an approved choice or verified exception.
2. **User:** separately approve deploying Pages plus the relay Worker, configure
   their production secrets, and verify production/preview binding isolation.
   The Supabase migration and local server-secret setup were approved and
   completed on 2026-10-12. No cloud page/Worker deployment occurred.
3. **User/lead:** run E1/E2/E3/E6 with the deployed origin and real account.
   Confirm phone approval and account UUID, JSON endpoints, Safari/Chrome cookie
   reload, both sign-outs and denied forged-key reads. The user performs camera
   gestures with and without Automattic's app installed.
4. **User/lead after permission:** run E4 for 60+ minutes on HTTP and HTTPS
   stations; record CPU/quotas, native chunk sizes, disconnects, cancellation,
   titles and audible continuity. Local synthetic fixtures cannot replace this.
5. **User:** decide M1's gate from the resulting evidence. Do not close M1 or
   start M2 on the assumption that these unperformed experiments passed.

## Known restrictions

The relay allows only exact `ice1.somafm.com` / `ice2.somafm.com` hosts and trusts
operator DNS. It does not yet resolve curated IDs or safely serve arbitrary
Browse hosts. Broadening requires a reliable approved egress defense and actual
curated-table schema. This fail-closed spike restriction does not change ADR 0004.

Two live relays and five starts/minute are per-account limits, not a global cost
cap. Session delivery bounds and retention are deterministic local evidence;
production scheduling and PostgreSQL lock contention still need validation.
Browser receipt timestamps are not measured audible alignment. Cross-tab account
switching, real phone routing and production cookie persistence are unverified.

Menubar M12 and all other platform work were left unchanged.

## Local launch — 2026-10-12

At the user's request, the local HTTPS Pages/relay runtime was started at
`https://127.0.0.1:8788` and the address opened in the default browser. The
server was left running for user inspection; process metadata is in the web
repo's ignored `.wrangler/local-dev.json`. The user subsequently confirmed that the page loads and Pairing is blocked
as predicted. Browser type and certificate handling were not specified; this
is user-reported local rendering evidence, not production cookie validation.

The full suite passed again: 177 Vitest tests, 41 isolated database/handler
checks, both offline runtime checks, typechecking and local builds. HTTP checks
confirmed page/health/signed-out session success, 401 for unauthenticated relay,
and 403 for cross-origin Pairing. Same-origin Pairing returned 503 as expected
without server database configuration.

Neither runtime has a `.dev.vars` file. Real phone Pairing remains blocked on
server-only database secrets and the unapplied web migration. No migration,
cloud deployment, real Pocket Casts approval or station playback was attempted.
Local startup authorization was not treated as permission to change Supabase.

## Authorized database setup and live pre-approval check — 2026-10-12

The user subsequently explicitly authorized the shared-project web migration
and local secret configuration. Migration `20261011000008` is applied; all
five new tables deny forged anon reads, and all 18 RPCs deny client execution.
Both local runtimes have ignored, permission-0600 server secrets and were
restarted. See [live setup evidence](../experiments/2026-10-12_live_pairing_setup.md).

Real Pairing exposed the wrong scope: `mobile` is rejected with JSON and
protobuf; the source-backed TV caller uses `tv`. Authorization, polling and
refresh now consistently use `tv`, covered by red/green regressions. Full
verification passes with 179 Vitest tests, 41 isolated SQL/handler tests,
both offline runtime checks, typechecking and builds. The scope fix and this
session's documentation updates remain uncommitted while the user validates
phone approval; web HEAD is still `2ce9a87`.

Live local start now returns HTTP 200 and a six-character code/QR payload;
the device-token request returns pending after its poll interval. The disposable
test pairing was canceled without account approval. The browser should reload
and create its own code for the user's camera/approval test. Approved grant
identity, account email, API permissions, real refresh, browser persistence,
production Cloudflare behavior and audio remain pending.

## Fresh-code rejection diagnosed — 2026-10-12

The user's phone opened approval but reported “Your QR code expired” for each
fresh browser code. Read-only phone-log diagnostics confirmed staging `.net`
requests and HTTP 400 / `invalid_grant`; the web had issued production `.com`
codes. The phone's `StagingDebug` build selects `.net`, and its UI labels any
`invalid_grant` as expired.

The web now has a server-only, allowlisted `PC_API_ENVIRONMENT` selector:
`production` (default) or `staging`. The ignored local configuration uses
staging, and the HTTPS server was restarted. A fresh disposable local Pairing
returned 200, polled pending, and was canceled. Verification passed: 186 Vitest
tests, 41 database/handler tests, both offline runtime checks, typechecks and
builds. All fixes remain uncommitted.

The user subsequently reported **“PAIRED!”**. A read-only check confirmed the
latest Pairing was consumed and a nonexpired server session exists. Phone
approval and server session creation now have live staging evidence. The user
also confirmed the browser still displays “Signed in as …” after reload.
Browser type was not identified; UUID comparison with iOS remains pending.

The user then used ordinary sign-out and reported “shows ready to pair” after
being asked to reload. Local ordinary sign-out/reload now has user evidence.

The user also confirmed sign-out everywhere worked after pairing normal and
private/incognito windows and reloading both. Local staging Pairing, reload,
ordinary sign-out and cross-browser sign-out everywhere now have user evidence.

The user then reported that the podcast-list probe “does nothing”. Local logs
show requests and repeated 429s; probe failures were displayed only at the top
of the page. Inline loading/error/result feedback and bounded `Retry-After`
guidance are now implemented. All 192 Vitest tests, 41 SQL/handler tests, both
offline runtime checks, typechecks and builds pass. The runtime was restarted
and serves the updated UI; existing database sessions were not cleared.

After reloading, the user reported HTTP 200 from `user/podcast/list` and
`user/playlist/list`, then confirmed `json-object` for both. Authenticated
HTTP/JSON-object responses now have live staging evidence for those endpoints.

The user also supplied `user/named_settings`: `observed`, HTTP 200,
`json-object`. Three read-only endpoints now have live staging HTTP/JSON-object
evidence.

The user also confirmed local relay audio and title updates using the HTTPS
SomaFM Groove Salad (256k MP3) station
`0e6a676d-cd09-4f93-a079-4a5eeb9da3b8`. This is a user-reported smoke check,
not 60-minute playback, HTTP-origin transport, measured alignment or a rights
clearance.

The [2026-10-15 terms review and isolated deployment plan](../experiments/2026-10-15_cloudflare_terms_and_deployment_plan.md)
is now written. It found explicit SomaFM third-party/restreaming restrictions;
further SomaFM relay testing and deployment are paused. Cloudflare's proxy
classification and continuous-audio permission remain unresolved. The user was
asked to stop any continuing SomaFM playback; no stop was confirmed.

**Original next step (superseded):** prepare auth-only staging before permitted
relay tests. The later direct-playback decision removes the relay phase; current
next steps are at the top of this handoff. Dedicated database/private access and
separate approval for cloud provisioning, migrations, upload and billing remain.
Identity comparison, refresh, remaining endpoint/schema checks and rights-cleared
timed HTTP/HTTPS playback are still pending. These
staging successes do not establish all endpoint permissions or production
Pairing/API behavior.
The secret tables are not environment-namespaced: do not share tokens between
staging and production. Before production deployment, isolate the database or
obtain approval to clear this staging test store. It was empty before this
local switch; no cleanup, phone reinstall or deployment occurred.
