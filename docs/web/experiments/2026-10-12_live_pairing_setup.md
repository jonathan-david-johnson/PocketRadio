# Web M1 live Pairing, sessions, probes and relay smoke check

**Scope update, 2026-10-15:** [ADR 0006](../adr/0006-direct-https-playback-without-an-audio-relay.md)
replaces the relay with direct HTTPS browser playback. Relay/DO/ICY evidence and
instructions below are historical, not active capabilities or evidence of direct
listening. Pairing/session/API findings remain applicable; the active milestone
lists the new playback checks. No cloud deployment was performed.

**Result:** the authorized web migration is applied to the linked PocketRadio
Supabase project. The local HTTPS runtime reaches Pocket Casts: JSON
`device/authorize` returns an approval code, and JSON `user/token` reports
pending approval. Phone approval now succeeds on staging after matching the web
API to the phone's `.net` service. The user reported “PAIRED!”, and a read-only
check confirmed a consumed Pairing and a nonexpired server session. The user
also confirmed reload persistence, both sign-outs, three authenticated
HTTP/JSON-object probes, and local relay audio/title behavior. Identity comparison
with iOS, remaining API permissions, live refresh and production Cloudflare
behavior remain untested.

## Authorization and database changes

The user explicitly approved configuring the local server against the existing
Supabase project and applying the web-only migration. Linked project:
`PocketRadio`, ref `brvtspdculqyvdrmdtef`.

`supabase migration list --linked` showed migrations 1–7 applied.
`supabase db push --linked --dry-run` listed **only**
`20261011000008_web_auth.sql`. A metadata preflight found none of its five
new tables. `supabase db push --linked --yes` applied that file successfully;
the subsequent history listed `20261011000008` remotely. No unrelated migration,
existing app table change, database reset, or cloud page/Worker deployment occurred.

Live metadata checks found:

- RLS enabled on `pc_tokens`, `web_sessions`, `web_pairings`,
  `web_account_revocations`, and `web_relays`.
- No table SELECT/INSERT/UPDATE/DELETE privileges for `anon` or `authenticated`.
- 18 web RPCs, zero executable by either client role.
- A service-role nonrolling check returned HTTP 200 / false for an unknown
  synthetic session handle.
- Each of the five table reads with the anon key and a forged synthetic
  `x-user-uuid` returned HTTP 401, PostgreSQL permission code `42501`.
  No row data or credentials were printed.

The local Pages and relay Worker each have ignored `.dev.vars` files with the
server-only database URL and service-role key, permissions `0600`. Keys were
retrieved through the authenticated Supabase CLI and written without displaying
them. These are local files, not production Cloudflare secrets or browser variables.

## Scope mismatch and fix

The first configured local Pairing attempt returned 502. A bounded upstream
probe identified OAuth `invalid_scope`, not a database failure:

| Request to `device/authorize` | Response |
|---|---|
| JSON, `scope: mobile` | HTTP 400, `invalid_scope` |
| Protobuf, `scope: mobile` | HTTP 400, `invalid_scope` |
| JSON, `scope: tv` | HTTP 200, expected device/user codes, verification URIs, expiry and interval |

The iOS enum `AuthenticationScope` selects `.tv` under tvOS. Its existing
`Pocket Casts TV App/UI/Auth/PairingSession.swift` caller uses that default
for device authorization and approval polling. Password-login `.mobile` was
incorrectly reused by the web spike.

The web client now uses `.tv` for authorization, device-token polling and
refresh. This retains Pairing as the sign-in method; it does not establish
that every subsequent API call permits this scope. Three assertions failed
before the fix (authorization, poll and refresh scope), then the full suite
passed: **179 Vitest tests, 41 isolated database/handler tests, both offline
runtime checks, typechecking and local builds**. No authenticated refresh
was performed live.

## Local live HTTP validation

At `https://127.0.0.1:8788`, using a disposable in-memory cookie jar:

1. `POST /api/pair/start`: HTTP 200, six-character approval code and matching
   `pktc://pair?user_code=…` payload. Only public response fields were returned;
   the device grant stayed server-side. Cookie attributes were Secure/httpOnly.
2. After the returned poll interval, `GET /api/pair/poll`: HTTP 200,
   `status: pending`. This exercises real Pocket Casts JSON polling before
   approval, not a fixture.
3. `POST /api/signout`: HTTP 200, canceling this disposable local Pairing.
4. `GET /api/session`: HTTP 200, signed out.

The runtime is left running so the user can refresh the browser and create a
new Pairing. The user previously confirmed the local page loads. The disposable
HTTP check did not approve an account, reuse the user's browser cookies,
print codes/grants/keys, or start radio playback.

## Phone approval failure: upstream environment mismatch

The user reported the phone alert “Your QR code expired” immediately after
refreshing the page, starting Pairing and scanning each new six-letter code.
This is not the browser's expiration timer: a database check still showed the
latest Pairing pending with 782 seconds remaining.

Read-only phone-log diagnostics found 76 references to `api.pocketcasts.net`,
none to `api.pocketcasts.com`, and three approval errors: HTTP 400,
`invalid_grant`. Only host counts and these error classifications were printed;
no account details, codes, cookies or tokens were exposed. The fork's
`config/PocketCasts.staging.xcconfig` defines `STAGING`; its
`ServerSyncManager.production()` returns false under that flag, selecting `.net`
for `device/approve`. The web previously hardcoded `.com`. Separate services do
not share these device grants. `DeviceApproveViewModel` maps `invalid_grant` to
the expired-code alert even for a fresh code from the wrong service.

A bounded JSON staging `device/authorize` probe with `scope: tv` returned HTTP
200 with the expected device-code field and six-character user code. The shared
web secret store contained no tokens or sessions before changing local mode.
The fix adds the server-only `PC_API_ENVIRONMENT` selector, allowing only
`production` (default, `.com`) and `staging` (`.net`). Authorization, polling,
refresh and probes select the same service. Five regression assertions failed
before the fix; the focused 15-test suite passed after it. Full verification also
passed: 186 Vitest tests, 41 isolated SQL/handler tests, both offline workerd
checks, typechecking and builds. After the local restart, a disposable HTTP
Pairing returned 200 with a six-character code, polling returned 200 / pending,
and sign-out canceled only that diagnostic attempt. The runtime is ready for
the user's new browser attempt.

The authorized local test now uses staging; no phone reinstall, database schema
change or deployment is involved. Phone approval must be retried with a **new**
code after the restart. Staging evidence is not production evidence. These M1
tables do not namespace tokens by service: concurrent staging/production use
requires separate databases, and future production setup must isolate or clear
this test store with explicit approval.

## User-confirmed staging approval

After the environment fix and restart, the user reported “PAIRED!”. A read-only
storage check confirmed that the latest Pairing was `consumed` and a nonexpired
web session existed. The handler consumes only a grant that passes its identity
and token checks. No identity, email, cookie or token values were printed.

The user then confirmed that the browser still shows “Signed in as …” after
reload. This establishes phone approval, server session creation, browser email
display and reload persistence for this local staging browser. The browser type
was not identified. It does not prove equality with the phone's account UUID,
authenticated endpoint permissions, production Pairing or production
Safari/Chrome cookies.

After being asked to use **Sign out / cancel Pairing** and reload, the user
reported “shows ready to pair”. This confirms the local browser returns to
signed-out state after ordinary sign-out and reload; it does not establish
revocation of other browser sessions by itself.

The user subsequently reported “worked” after being asked to pair in both a
normal window and a private/incognito window, use **Sign out everywhere**, and
reload both. This is user-confirmed local evidence that both independent web
sessions returned to “Ready to pair”. It is not production cookie evidence.

## Probe feedback correction

The user reported that `user/podcast/list` “does nothing”. Sanitized local
request-log inspection showed probe requests reaching the server, including
several HTTP 429 responses and later HTTP 200 responses. These are the status
codes of our probe route, not evidence of the upstream API's status or format.
The UI cleared the previous result while waiting and placed failures only in
the page-wide status near the top, away from the probe controls.

The page now shows loading, errors and results directly below the probe button,
explains that choosing an endpoint does not run it, and explains why probes are
disabled while signed out. HTTP 429 feedback uses a bounded `Retry-After` delay
instead of a misleading server-bindings message. It still shows only sanitized
status/format evidence, not the user's podcast or playlist contents. No automatic
retry or write-capable request was added.

Seven regression assertions failed before the fix; all passed afterward. Full
verification passed: 192 Vitest tests, 41 SQL/handler tests, both offline workerd
checks, typechecking and builds. The local HTTPS server was restarted, health
returned 200, and the served browser bundle contains the new inline feedback.
The user must reload before retrying; authenticated upstream status/format is
still awaiting their visible result.

## User-reported read-only probe status

After the inline-feedback fix, the user reported HTTP 200 from both
`user/podcast/list` and `user/playlist/list`, then confirmed `json-object` for
both. These are local staging probes using the TV-scope Pairing grant. This
establishes authenticated HTTP/JSON-object responses for these two endpoints,
not validation of their usable schemas, compatibility of the remaining
endpoints or production API behavior.

The user also supplied the sanitized `user/named_settings` result:
`status: observed`, `httpStatus: 200`, `format: json-object`. This adds a third
live staging HTTP/JSON-object response. The probe calls the source-backed
empty-settings read path; no write-capable sync probe was requested.

## User-confirmed local relay smoke check

A read-only radio-browser lookup found SomaFM Groove Salad (256k MP3), station
`0e6a676d-cd09-4f93-a079-4a5eeb9da3b8`, with an HTTPS stream on the spike's
allowed SomaFM hosts. The lookup did not open an audio connection. The user
then entered this ID, started the relay and pressed Play. Asked whether audio
played and the Track title appeared and updated at a song change, the user
answered “YES!”. This is user-reported local audio/title smoke evidence with a
staging-authenticated session, not a timed or instrumented endurance result.

The check does not establish an HTTP-origin stream, 60-minute playback, CPU or
quota behavior, audible metadata alignment, redistribution rights or permission
under Cloudflare terms. No cloud deployment occurred.

**Follow-up, 2026-10-15:** the [terms review](2026-10-15_cloudflare_terms_and_deployment_plan.md)
found explicit SomaFM third-party/restreaming restrictions. Further SomaFM relay
tests and deployments are paused. The user was asked to stop any continuing
playback; no stop was confirmed. This earlier technical success remains evidence
of behavior only, not a recommended or rights-cleared test source.

## Remaining checks

- Compare identity to iOS without exposing the UUID to the page.
- Production Safari/Chrome reload and both sign-outs; local staging checks
  passed, including sign-out everywhere across independent browser sessions.
- Remaining endpoint formats/schemas and scope permissions, plus live refresh.
  Podcast list, playlist list and named settings returned 200 / json-object.
- Cloudflare Pages/Worker deployment, secret/binding verification, legal/rights
  clearance, plan choice and hour-long HTTP/HTTPS listening.

E1/E2 now have local staging approval/session evidence; E3 has three structural
JSON-object results; E4 has a local HTTPS-station audio/title smoke check; E6
has local reload, both sign-outs and live secret-storage denial evidence. These
do not complete the full experiment matrix or decision gate. M1 remains open;
no milestone checkbox was changed or milestone closed.
