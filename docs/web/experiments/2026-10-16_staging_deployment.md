# Private staging deployment — provisioning, privacy and first upload

**Status: CLOSED 2026-10-18. Deployed behind Access, and the user's browser checks passed (user-reported).** On 2026-10-18 the staging app was uploaded to `pocket-radio-web-m1-staging` behind two email-only Access applications, with the staging database's secrets installed. The browser checks are listed under *Browser checks* below.

**Update, later on 2026-10-18.** The uncommitted work noted below is now committed on `feature/m1-spikes` as `d885ea2` and `faf4fd7`; whether the uploaded bundle matches those commits was not verified. The user also reported a 25+ minute direct playback run and an invalid-ID error on the deployed site, which replace the "short listen" caveat. The station-switch report used two IDs that resolve to the same stream; see [formats and terms](2026-10-18_api_formats_and_station_terms.md). Original provisioning was 2026-10-16 UTC: the user approved creating and deploying `pocket-radio-web-m1-staging` under these limits: private Pages access, a separate Free Supabase database, the web-only migration, server-only secrets, staging Pocket Casts (`.net`), no relay, no billing changes and no changes to the existing PocketRadio database.

## What was done on 2026-10-18

| Step | Result |
|---|---|
| Zero Trust organization | `mute-night-443d` created in the dashboard. Onboarding asked for a payment method even on the Free plan; Cloudflare's setup page says Free "is still needed but you will not be charged". The card was entered by the user |
| Access applications | Two self-hosted applications, each with one Allow policy "Owner only" for the owner's email address, no Everyone or Bypass: `pocket-radio-web-m1-staging.pages.dev` and `*.pocket-radio-web-m1-staging.pages.dev`. Created through the API with a scoped token, not through the Pages page |
| Access enforcement | Unauthenticated requests to the main host, two preview-style hosts, `/api/health`, `/api/session` and the deployment-hash host all return HTTP 302 to `mute-night-443d.cloudflareaccess.com`. The user signed in |
| Empty project | After sign-in the browser showed **Cloudflare error 522** ("Connection timed out", Host: Error). A project with no deployments gives a 522 behind Access. A one-line placeholder deployment fixed it |
| Server secrets | `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` and `PC_API_ENVIRONMENT=staging` set in the Pages **production** environment from the ignored staging secrets file. The project ref matches the staging project, and the key differs from the existing local key. The preview environment has none |
| Checks before upload | `make test typecheck build`: 247 unit tests, the SQL and handler suites and the local Pages runtime passed. No secret value is in `dist/` or the Functions bundle |
| Upload | `wrangler pages deploy dist --project-name pocket-radio-web-m1-staging --branch main`: three files plus the Functions bundle. No stray project was created |

### Two things that went wrong

- **A placeholder deploy also uploaded the app's server code.** Wrangler uploads `./functions` from the working directory, and the placeholder was deployed from the app folder. It was caught from the output ("Uploading Functions bundle"), redeployed from an empty folder, and the first deployment was deleted. No secrets existed then and Access was on. Deploy placeholders from an empty directory, and run `wrangler pages deploy` only after reading which files it says it uploads.
- **The deploy shipped uncommitted work.** `pocket-radio-web` had 28 modified, uncommitted files on `feature/m1-spikes`. The deployed code is the working tree, not a commit, so the deployment is not reproducible from git until that work is committed.

## Dashboard changes since this was written (the old steps below are stale)

The Pages page no longer has "Enable access policy". It has **Restrict previews**, whose own text says it protects preview URLs only and that `pages.dev` and custom domains are managed in Zero Trust. Cloudflare's Known Issues page still describes the older flow. The working order was: finish Zero Trust onboarding, then create two Access applications (main host and the preview wildcard) in Zero Trust, then confirm both. "Restrict previews" was not needed.

Wrangler's OAuth login cannot hold Access scopes (`wrangler login --scopes-list` has none), so the Access applications were created with a user API token (`cloudflare_pi`): Access Apps and Policies Edit, Access Organizations/IdP/Groups Read, Cloudflare Pages Edit, one account, the user's IP only, expiring 2026-10-26. It is kept in the ignored `.wrangler/cf-token`. Wrangler needs `CLOUDFLARE_ACCOUNT_ID` set with this token, because it has no account-read scope. Delete the token when the work is done. The Cloudflare MCP server (`mcp.cloudflare.com`) is also configured in pi and its docs search works; its write scopes were not used.

## Browser checks (user-reported, 2026-10-18)

On `https://pocket-radio-web-m1-staging.pages.dev/`, signed in through Access, the user reported all of these as passing:

1. Pairing.
2. Reload (session persists).
3. Stop playback.
4. Both sign-outs, each stopping the audio.
5. HTTP-only station rejected.
6. Cross-browser session revocation.
7. Direct HTTPS playback of Radio Paradise Global (`566476bf-d03c-4cac-b5d3-468f99a874b8`, `https://stream.radioparadise.com/world-etc-320`, AAC 320).

What this does and does not show:

- These are the user's reports. No log, trace or screenshot was captured, and the browsers, versions and listening time were not recorded. The browsers are presumed to be Chrome and Safari as the plan said; that was not confirmed.
- It is a short listen, not the 60-plus-minute endurance run (E4).
- It is not a rights clearance for Radio Paradise: the stream is HTTPS and played, and its terms were not reviewed.
- Still unchecked: a signed-in request to each Function from outside a browser, Free-plan CPU or limit errors (none reported), Linux, production `.com` behavior, whether the Zero Trust one-time-PIN login is enabled, and that the deployed code is uncommitted work (see above).

---

## Original record (2026-10-16)

## Created and verified

| Resource/check | Result |
|---|---|
| Supabase organization | Management API confirms `free` plan |
| Database | New `pocket-radio-web-m1-staging`, `us-east-1`, requested `nano`; `ACTIVE_HEALTHY` |
| Free capacity | Provider accepted creation in the verified Free organization; no upgrade or other-project pause/deletion |
| Pages | New direct-upload `pocket-radio-web-m1-staging`; production branch `main`, compatibility date `2026-10-11` |
| Pages hostname | `pocket-radio-web-m1-staging.pages.dev` |
| Application deployment | None; empty Pages project only |
| Existing PocketRadio database | Untouched |

The new database's public schema was empty before applying only
`supabase/migrations/20261011000008_web_auth.sql`. Migration version
`20261011000008` and its source statements were recorded in standard
`supabase_migrations.schema_migrations` tracking in the same transaction. No
other platform migrations were applied. PostgREST schema reload was requested.
The migration's retained relay tables/RPCs do not enable a relay or require a DO.

Live checks on the **new database**, not the existing one:

- All five public secret tables have RLS enabled.
- Forged anon-key reads of all five tables fail with HTTP 401/403 and PostgreSQL
  permission denial `42501`.
- Anon RPC calls to all 18 web functions fail with the same permission denial.
- SQL privilege checks deny `authenticated` RPC execution and allow the service
  role. No real account grants, tokens or personal data were inserted.

## Secrets and artifacts

Dedicated new-project database password, identifiers and server bindings are
held only in ignored local `.wrangler/staging-state.json` and
`.wrangler/staging-secrets.json`, mode `0600`. The local operator helper is also
ignored and `0600`. Existing local `.dev.vars` and its shared-project sessions
were not changed. No Cloudflare server secrets have been installed yet.

`make test typecheck build` passed again: **247 unit/UI tests**, **41 isolated
SQL/handler tests**, the offline Pages runtime, typechecks and browser/Functions
build. Both the new staging service key and existing local service key are absent
from the four browser artifact files. Normal config has no relay binding.
This is not deployed-site or browser-cookie acceptance evidence.

Context7 was rate-limited. Before the provisioning calls, current Supabase
Management OpenAPI at `https://api.supabase.com/api/v1-json`, the official CLI
source and installed Wrangler help/API source were inspected. Credential
retrieval stayed in process; no credential values were printed.

## Remaining privacy and account-plan checkpoint

Wrangler OAuth has Pages permissions but lacks Access-management permissions.
The read-only account-subscriptions request returned HTTP 403, so the Cloudflare
Workers plan/capacity is **not verified**. No subscription or billing setting was
changed. Confirm Workers Free in the dashboard; stop if a paid plan, card or
upgrade is required rather than silently proceeding.

Use the documented Pages Access setup; the preview-only toggle does not protect
the primary host:

1. In Cloudflare **Workers & Pages**, open `pocket-radio-web-m1-staging`.
2. Open **Settings → General → Enable access policy**. If prompted to onboard
   Zero Trust, use Free only; stop at any payment requirement.
3. Select **Manage** for the generated preview application. In **Access →
   Applications**, configure it: remove the `*` subdomain to protect
   `pocket-radio-web-m1-staging.pages.dev`, rename the application if necessary,
   and save. Restrict the allow policy to the approved tester's email; no
   Everyone or Bypass rule.
4. Return to Pages and enable the preview access policy again. Confirm a second
   application protects `*.pocket-radio-web-m1-staging.pages.dev`. Restrict it
   to the same approved tester.
5. Confirm both applications/policies exist. Do not treat an empty site's 404
   as proof of Access enforcement.

Source: [Pages primary-host Access instructions](https://developers.cloudflare.com/pages/platform/known-issues/#enable-access-on-your-pagesdev-domain).
If the empty-project dashboard does not expose these controls, report that;
do not upload the authenticated app just to make the control appear.

## Resume after the dashboard checkpoint

- Verify primary, hash and branch aliases reject unauthenticated access. Account
  sign-in is separate from the app's Pocket Casts Pairing/session.
- Install only the dedicated database's server secrets in the approved Pages
  environment and explicitly set `PC_API_ENVIRONMENT=staging`. Do not copy the
  existing project's key, enable untrusted preview builds or add a relay binding.
- Recheck the source/artifact and upload explicitly to this staging project,
  never the root configuration's default `pocket-radio-web` target. No git push.
- Perform Pairing, email/reload, both sign-outs, cross-browser session revocation
  and direct HTTPS playback in Chrome and Safari on the deployed origin. Record
  Free CPU/limit errors; do not upgrade automatically.

This checkpoint does not close M1. Linux, 60+ minute endurance, live refresh,
identity comparison, remaining API schemas and production `.com` behavior still
need their own evidence. Resource deletion remains separately gated.
