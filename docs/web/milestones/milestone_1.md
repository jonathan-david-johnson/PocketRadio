# Web M1 — Prove Pairing, direct playback and the Cloudflare deploy

**Status:** IN PROGRESS — scope updated 2026-10-15 by the user's direct-playback
decision ([ADR 0006](../adr/0006-direct-https-playback-without-an-audio-relay.md)).
Setup is web `9ea6c56`; implementation is on `feature/m1-spikes`.
**Depends on:** web ADRs 0001–0006, with 0006 superseding the relay decision.
**Required by:** Web M2–M7.

## Where the work happens

| Work | Location |
|---|---|
| Plan, evidence, additive database contract | Shell `main`; `docs/web/` and the existing web migration |
| Code | `pocket-radio-web/`, branch `feature/m1-spikes` |
| Cloud operations | User approved private `pocket-radio-web-m1-staging` Pages/database setup and upload on Free only; no billing changes or existing database changes |

## Goal and user checkpoint

Prove browser-bound phone Pairing and sessions on one Pages origin, selected
Pocket Casts API formats, and direct HTTPS station playback. Do not build M2–M7
screens or require a native helper. Standalone Linux PWA installation remains
M3 work, not an M1 claim.

On the eventual approved Pages test site, pair from the phone, see the account
email, reload, and exercise both sign-outs in Safari and Chrome. Load a permitted
HTTPS station by ID and play it through the browser's native audio element.
Confirm stop/switch/error cleanup. An HTTP-only station must show an unsupported
message without fallback. No generic track title or lyrics are expected.

## Scope

- Retain Vite/React/TypeScript and same-origin Pages Functions. Supabase remains
  database-only. Secret tables have RLS and no client policies; only the server
  holds Pocket Casts/database credentials.
- Retain browser-bound expiring Pairing, rolling 90-day sessions, sign-out and
  sign-out everywhere. Derive identity from verified Pocket Casts responses.
- Resolve a radio-browser UUID server-side through the fixed, bounded metadata
  endpoint. Return a validated public HTTPS URL; never open/probe audio from the
  backend. The browser validates again and uses that URL as its audio source.
- Do not upgrade HTTP blindly, attach a relay fallback, open a second metadata
  stream or display guessed track titles. Current direct URL policy also
  rejects credentials, local/literal-IP hosts, fragments and nondefault ports.
- Retire relay HTTP/SSE/stop entry points with 410. Remove normal DO/Worker
  bindings, build and dev wiring. Retain legacy offline fixtures and existing
  applied SQL until deliberate cleanup; no database deletion is authorized.
- Keep all experiments bounded and sanitized. Do not call write-capable sync
  endpoints without approval.

## Current evidence and its limits

[Local results](../experiments/2026-10-12_live_pairing_setup.md) record successful
staging phone approval, browser email/reload, both sign-outs, and three
authenticated 200 / JSON-object probes. The phone uses `.net`; keep
`PC_API_ENVIRONMENT=staging` while testing with it. UUID comparison with the
phone, live refresh, full response schemas and production `.com` behavior remain
open.

[Direct implementation evidence](../experiments/2026-10-15_direct_playback.md)
records passing unit/UI, SQL and offline Pages tests and a Pages-only local
restart. The user subsequently reported “played” after receiving the Radio
Paradise Global UUID: local direct playback has smoke evidence in **Chrome and
Safari on macOS**, as confirmed by the user. The user also reported 20 minutes
of successful playback; the browser for that run was not separately identified.
Browser/OS versions and the remaining live checks are not established here;
see the 2026-10-18 deployed results below. The user confirmed that both
**Stop playback** and local
**Sign out / cancel Pairing** stop the audio. Reload after local sign-out showed
**Ready to pair**, also confirmed by the user. The user reported all these
checks passed in Safari on macOS as well; deployed-origin checks remain pending.

**Deployed staging (2026-10-18).** The app is on the private `pocket-radio-web-m1-staging`
Pages project behind two email-only Access applications, with the staging
database's secrets installed (production environment only). The user reported
Pairing, reload, Stop, both sign-outs, explicit HTTP-only rejection,
cross-browser session revocation and Radio Paradise Global playback all passing
there. These are user reports without a captured trace or browser/version
record. Signed-in requests to each Function from outside a browser were not
made. The code deployed then was uncommitted work; it is now committed on
`feature/m1-spikes` as `d885ea2` and `faf4fd7`, though whether the uploaded
bundle equals those commits was not verified. See the
[staging record](../experiments/2026-10-16_staging_deployment.md).

**Later the same day, on the deployed origin (user-reported).** The user
reported a **25+ minute** direct playback run with no problem (browser and
dropout detail not supplied), a station switch that worked, and, for a
deliberately invalid station ID, the message *Request failed (400). Check
server bindings and the experiment notes.* That message is correct as an error
path but is a developer string, not a listener message; M3 must replace it. The
second station ID offered for the switch turned out to resolve to the **same
stream URL** as the first (both Radio Paradise Global, 320k AAC), so the switch
report does not show a real change of stream. Redo it with KEXP (see the
checklist). QR routing (E2) was **not tested**; the user directed that it be
assumed fine, which is an assumption, not evidence.

The earlier user-reported relay audio/title smoke check is historical. It does
not prove direct playback or rights to use that station. The
[terms review](../experiments/2026-10-15_cloudflare_terms_and_deployment_plan.md)
found SomaFM client/restreaming restrictions and an unresolved Cloudflare relay
classification. Direct playback removes the server audio path, not station terms.

## Experiments

Stable experiment IDs are retained so old evidence remains interpretable.
E4/E5's former relay criteria are **replaced by the user decision**, not passed.

| ID | Question and method | Pass criterion |
|---|---|---|
| E1 | Complete phone Pairing through Pages, then verify server-derived identity | Approved grant creates one bound browser session; UUID comparison with iOS recorded without exposing it |
| E2 | Scan with the fork, check prefill/cold/warm routing, and assess official-app scheme collisions/manual fallback | Actual tested routing behavior and limitations recorded |
| E3 | Test read-only Pocket Casts responses and identify JSON/protobuf needs; keep sync writes separately approved | Status, format and needed schema/permission evidence per endpoint; live refresh separately demonstrated |
| E4 | Resolve a permitted HTTPS station, use its URL directly in the browser, and observe 25+ minutes (lowered from 60+ by the user on 2026-10-18); test stop/switch/errors and HTTP rejection | Audio plays directly, cleanup works, HTTP is unsupported, and no server audio or title-subscription path exists; duration/codec/browser limitations recorded |
| E5 | Verify the direct-only architecture and review station/client restrictions | No relay deployment/binding or fallback; no unsupported permission claims; permitted test source selected |
| E6 | Validate Pages cookies in Safari/Chrome, reload, both sign-outs, forged headers and database client denial | Session behavior and denial evidence on the deployed isolated origin |

Sign-out everywhere revokes web sessions, not the public station URL already
loaded in another browser. Local sign-out must stop this tab's audio. Do not
reuse relay delivery/revocation timing guarantees.

## Deployment gate

Keep a dedicated staging database and private Pages test project. The current
direct design needs no relay Worker or DO; the prior plan's later relay/audio
phase is superseded by ADR 0006. Confirm account, isolation, free capacity/costs,
testers, secrets and the exact upload target before asking for scoped approval.
Do not reset the existing PocketRadio database or silently switch its token
store between `.net` and `.com`.

The user approved the private Free-only setup and upload. New Pages and
Supabase projects named `pocket-radio-web-m1-staging` now exist. Supabase's Free
plan was verified; creation at `nano` was accepted, only web migration
`20261011000008` was applied, and all five table/18 RPC anon-denial checks pass.
The existing database was not changed. The app has **not** been uploaded and no
Cloudflare secrets are installed.

Wrangler OAuth lacks Access-management and billing-read permissions. Complete
the dashboard privacy setup for primary and wildcard preview hosts and confirm
Workers Free before uploading. Stop at any payment requirement. See
[the staging provisioning checkpoint](../experiments/2026-10-16_staging_deployment.md)
for completed actions and exact resume steps. No billing changes occurred.

## Decision gate

- Pairing-only sign-in and its routing behavior: E1/E2. E1 passed on
  2026-10-18: the web-derived UUID matches the one iOS writes under, for this
  account on `.net` ([record](../experiments/2026-10-18_api_formats_and_station_terms.md)).
  E2 was not tested; the user chose to assume QR routing works.
- JSON-only or mixed JSON/protobuf client: E3. **User decided protobuf**
  for Pocket Casts account data on 2026-10-18
  ([ADR 0007](../adr/0007-protobuf-for-pocket-casts-account-data.md),
  [E3 record](../experiments/2026-10-18_api_formats_and_station_terms.md)).
- Direct HTTPS playback, unsupported HTTP and unavailable generic titles:
  **user accepted**, ADR 0006; local implementation and user-reported playback
  smoke verified, remaining E4 live checks pending.
- Pages plan choice based on API usage/CPU, not audio proxy bandwidth or DOs.
- Session/security design: E6.
- Remaining risks and revised M3/M4/M5 expectations recorded before closure.

## Out of scope

M2–M7 screens, installable PWA implementation, a native helper, generic ICY
extraction, metadata/lyrics integrations, a replacement audio relay, custom
domains, KCRW alignment, ACRCloud and destructive schema cleanup.

## Docs impact

- **Docs this changes or makes stale:** `docs/web/README.md` (current state and roadmap rows), `docs/web/CONTEXT.md` (glossary), `docs/security_concerns.md` (web credentials and direct playback), web ADR 0004 (already marked superseded by 0006).
- **Questions this must settle:** which stations the web player may play and under what terms (rights review, now only for the stations chosen for testing); the Pocket Casts schema and JSON-versus-protobuf decision (E3); whether production `.com` Pairing behaves like staging `.net`; how the phone's Pocket Casts account UUID is compared with the web session's without exposing it (E1). Each may become an ADR at close.

## Hand-performed checks still to record

- [x] Local direct HTTPS playback smoke after the switch — user reported “played”
- [x] Timed direct HTTPS playback, **25+ minutes** (user lowered the bar from 60+ on 2026-10-18; user-reported on the deployed site, browser not recorded)
- [x] Local **Stop playback** audibly stops the direct stream — user confirmed
- [x] Local sign-out stops direct audio; reload remains signed out (**Ready to pair**) — user confirmed
- [x] Explicit HTTP-only rejection on the deployed origin — user reported 2026-10-18
- [x] Station switch between two different streams (Radio Paradise Global, then KEXP `445cbb3a-1c4e-49aa-a268-f5b6acfa8f2e`) — user reported 2026-10-18 on the deployed site; browser not recorded
- [x] Invalid station ID shows an error (HTTP 400, generic developer text) — user reported 2026-10-18
- [x] E2 QR routing — **accepted untested** by the user on 2026-10-18; not a pass, a decision to assume it works
- [x] Pairing, reload, both sign-outs and cross-browser session revocation on the deployed origin — user reported 2026-10-18 (which browsers and versions were not recorded; the plan was Safari and Chrome)

Close this milestone only through the close-milestone skill after its remaining
evidence and decision gate are accepted. The prior relay smoke check is not a
substitute for the new direct-playback checks.
