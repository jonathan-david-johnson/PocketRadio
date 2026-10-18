# Web M1 — terms review and isolated deployment plan

**Current decision, 2026-10-15:** the user chose
[direct HTTPS station-to-browser playback](../adr/0006-direct-https-playback-without-an-audio-relay.md).
There is no backend audio relay, DO binding or native helper. HTTP-only audio,
generic ICY titles and lyrics are unavailable in the initial implementation.
The normal build/dev config now implements this decision; it has not been deployed.

**Later provisioning, 2026-10-16:** the user approved the private Free-only setup.
Pages and a dedicated Free Supabase project now exist; the web-only migration and
security checks passed. No app has been uploaded or billing changed. Follow
[the current provisioning/privacy checkpoint](2026-10-16_staging_deployment.md),
not the historical relay execution plan below.

**Current deployment recommendation:** a private Pages staging project with a
separate Supabase database and permitted direct HTTPS test source. Confirm target,
secrets, access controls and API plan/capacity before seeking scoped approval.
No relay Worker, owned-audio relay phase or Cloudflare audio-proxy clearance is
required for this design. Station/client/metadata terms still require care;
direct playback is not blanket permission, including for SomaFM.

**Historical review and proposal below:** the original “go” authorized this
review, not deployment, billing, provisioning, permission requests or cleanup.
Its auth-only and later DO/relay phases were proposals, never executed. The
later direct-playback decision supersedes those audio phases, not the useful
private-access/database-isolation guidance. No cloud resources were created,
changed or deleted. Statements about continuous-relay restrictions below do not
mean that private one-to-one personal listening is definitively prohibited or
legally equivalent to public broadcasting; classification was unresolved.

## What the local evidence establishes

[Live local results](2026-10-12_live_pairing_setup.md) establish staging Pairing,
email display, reload, ordinary sign-out, cross-browser sign-out everywhere,
three read-only 200 / JSON-object probes, and a user-reported HTTPS-station
relay audio/title smoke check. They do not establish rights to relay that audio,
production Pocket Casts compatibility, full JSON schemas, live token refresh,
HTTP-origin playback, hour-long continuity, or deployed resource usage.

The phone uses `api.pocketcasts.net`. Keep `PC_API_ENVIRONMENT=staging` for this
test; a production `.com` code cannot be approved by that build. A Cloudflare
Pages “production” deployment environment can still be an upstream-staging
experiment. Do not confuse these two meanings of production.

## Terms findings

This is an engineering release-gate review, not a legal opinion. Public terms
were fetched directly from the vendors. Account-specific agreements, billing
status and separately negotiated permissions were not inspected.

### SomaFM: do not continue this relay test

The [SomaFM terms](https://somafm.com/legal/tos.html), also linked from its site
at [the contact-page terms](https://somafm.com/contact/tos.html), display
“Last Updated Sep 4, 2026, clarifying third-party and app use”. Both pages state:

> We can't grant permission for third-party SomaFM clients or applications, even noncommercial ones.

The third-party-use section says its music licences do not permit it to authorize
these standalone uses, that new clients are not being approved, and that old
general-purpose tuner exceptions are not being expanded. The streaming-content
section separately requires explicit prior written permission for embedding,
restreaming, retransmitting or broadcasting. It also restricts branding and
metadata use.

**Consequence:** the two allowed SomaFM hosts are an egress security boundary,
not a rights clearance. Do not use them for further relay listening/endurance
checks or a deployed demo without applicable permission. The user was asked to
stop any continuing SomaFM relay. No automatic stop was performed or confirmed.
A private or noncommercial app is not a documented exception in the cited
wording. This is not a legal classification of the user's personal one-to-one
relay or a claim that it is public broadcasting. HTTP-only transport does not
itself answer the third-party-client permission question.

For future tests, prefer original generated audio and synthetic ICY titles from
an origin we control. This removes the third-party music dependency, not the
Cloudflare hosting question. Provisioning that origin and integrating it into
the restricted resolver require separate approval; neither exists yet.

### Cloudflare: content hosting permission is not a specific relay clearance

The [Developer Platform terms](https://www.cloudflare.com/service-specific-terms-developer-platform/)
list Workers, Pages and Durable Objects and display “Last updated: September
28, 2026”. They say:

> Unlike most Cloudflare products, the Developer Platform can be used to host content.

They also permit temporary restrictions when usage burdens the network and
require compliance with documentation and third-party terms.

The [Application Services terms](https://www.cloudflare.com/service-specific-terms-application-services/),
with the same displayed date, restrict disproportionate audio/large-file delivery
through the ordinary Free/Pro/Business CDN without the specified paid services.
They name the Developer Platform among those paid services. They do not expressly
classify this uncached continuous Pages/DO audio relay or approve it on Workers
Free. A CDN Pro/Business subscription alone is not the stated exception.

The [Self-Serve Subscription Agreement](https://www.cloudflare.com/terms/),
displaying “Last Updated September 12, 2025”, adds two independent constraints:

- **§2.2.1(j):** absent express written permission, no use to provide “a virtual
  private network or other similar proxy services”. Whether our narrow,
  authenticated, fixed-station relay falls within “similar” is unresolved; do
  not claim either a blanket ban on all Worker fetches or an exemption for this
  relay. Ask Cloudflare to classify it.
- **§2.5.2, §2.5.4 and §2.7:** necessary content rights and permissions must be
  held, and infringing content must not be transmitted.

The [agreement index](https://www.cloudflare.com/legal/terms/) says applicable
terms depend on the subscription and services. Paying for Workers does not
itself resolve the proxy classification or station rights. `no-store`, private
access and low traffic are controls, not legal exemptions.

**E5 result:** unresolved Cloudflare classification plus a concrete SomaFM
restriction. Do not mark audio relaying permitted or close M1 on this evidence.

### Clarification request — draft only, not sent

Ask Cloudflare support to confirm in writing whether a personal radio player may
use Pages Functions and a SQLite Durable Object to forward a continuous,
authenticated audio response from a fixed, rights-cleared origin. Explain:

- No VPN, arbitrary destination URL, public proxy or stored/cached audio.
- One upstream connection per listener; ICY blocks stripped from that connection
  and titles delivered through same-origin SSE.
- Initial test: one approved tester, one stream at a time, two 62-minute runs,
  one HTTP upstream and one HTTPS upstream, up to 256 kbit/s.
- Confirm treatment under §2.2.1(j), the CDN provision and Developer Platform
  terms, required Free/Paid plan, and any traffic restrictions.

Use owned test audio in this request, not a claim that SomaFM is licensed.
For 256 kbit/s, two 62-minute runs transfer about 238 MB of audio, excluding
protocol overhead. This is a test estimate, not a public-service traffic cap.

## Runtime and cost constraints

Current sources: [Workers limits](https://developers.cloudflare.com/workers/platform/limits/),
[Workers pricing](https://developers.cloudflare.com/workers/platform/pricing/),
[Durable Object limits](https://developers.cloudflare.com/durable-objects/platform/limits/),
and [DO pricing](https://developers.cloudflare.com/durable-objects/platform/pricing/).

- HTTP-triggered Workers have no hard wall-time cutoff while the client remains
  connected. This is not an uninterrupted-playback guarantee. The current limits
  page, updated 2026-10-12, describes **up to 20 minutes** of draining during
  routine runtime updates; crashes and resource pressure can interrupt earlier.
  This updates the earlier report's 30-second runtime-update grace statement.
- Free ordinary Worker requests have **10 ms CPU**; Paid defaults to **30 seconds**
  and supports up to **300,000 ms**. Network waiting is not CPU, but streaming
  parsing/copying is. Measure the deployed Pages and DO invocations separately.
  DO documentation still mixes a 30-second default with per-plan wording; do not
  infer a Free DO allowance from that ambiguity.
- The current [Pages configuration reference](https://developers.cloudflare.com/pages/functions/wrangler-configuration/#limits)
  explicitly supports `limits` like Workers. This resolves the earlier report's
  uncertainty about a documented Pages setting; it does not prove a deployed
  setting or account allowance. No CPU configuration was changed here.
- Workers Paid has a **$5 USD/month account minimum**, not a spending cap. The
  reviewed pricing says no additional egress/bandwidth charge, but CPU, requests,
  active DO duration and storage remain metered. Other providers may charge.
- A streaming DO is active, not a hibernated free connection. Paid DO pricing
  includes 400,000 GB-s/month, then $12.50 per million GB-s with the documented
  rounding. Using the documentation's 128 MB allocation arithmetic, one active
  object-hour is approximately 460.8 GB-s. Allowances are account-wide; this is
  not an invoice prediction. Free DO duration is limited to 13,000 GB-s/day.
- The implementation's two-relays/account and five-starts/minute bounds do not
  impose a global spend cap. Session checks every 12 seconds also create database
  traffic. No account quota, existing usage, Supabase price or Access plan was
  inspected. Do not create paid resources or upgrade plans without approval.

**Plan choice:** try auth-only testing on the existing approved plan first.
For a permitted continuous relay, Workers Paid is the recommended candidate
because Free CPU is tight, but only after clarification, a cost check and
explicit billing approval. Do not describe $5 as the total cost or a permission.

## Isolation design

Proposed names are placeholders; availability has not been checked.

| Resource | Auth-only test | Later audio test |
|---|---|---|
| Pages | Dedicated `pocket-radio-web-m1-auth` project; same-origin page and Functions | Same isolated lab, after audio gates |
| Pocket Casts | Explicit `PC_API_ENVIRONMENT=staging` | Remains staging for this phone |
| Database | New, empty, dedicated Supabase test project; web-only migration | Same isolated test store |
| Relay binding | **No `RELAY_HUB` binding**, in either Pages environment | Dedicated `pocket-radio-relay-m1-staging` Worker and SQLite namespace |
| Previews | No untrusted automatic builds or shared production credentials | Separate preview namespace/credentials, or leave audio unavailable |
| Access | Approved tester only on primary, hash and branch-alias hosts | Same restrictions; no public radio service |

The current root config is **not** this isolation design: it names
`pocket-radio-web` and binds production and preview to the same
`pocket-radio-relay` Worker. Do not run `make deploy` with it for this experiment.
A separate auth-only config must omit that binding entirely. Current relay routes
check for a missing binding before station lookup/DO calls and fail closed with
503 after session validation. This is source evidence; prove it in regression
and deployed negative tests. Hide or label the inactive UI as well, but hiding
controls is not the security boundary.

Use a separate Supabase project rather than copying the existing PocketRadio
service-role key into the lab. The current secret tables do not namespace tokens
by upstream environment, and service-role access has a project-wide blast
radius. Do not reset the current project, migrate its unrelated tables, copy its
tokens, or silently reuse it as a production `.com` token store. New-project free
capacity and any charges must be confirmed before creation.

[Pages previews](https://developers.cloudflare.com/pages/configuration/preview-deployments/)
are public by default. The preview Access toggle protects previews **only**, not
the primary `project.pages.dev` host. Follow the
[primary-host Access instructions](https://developers.cloudflare.com/pages/platform/known-issues/#enable-access-on-your-pagesdev-domain)
and verify separate protection of the primary and preview hosts, including hash
and branch aliases. `noindex` is not access control. Keep custom domains out of
M1. Edge Access supplements, not replaces, application session/origin checks.

## Execution order — all cloud steps await approval

1. **Prepare locally.** Checkpoint the tested web changes and explicit shell
   documentation paths; leave unrelated agent/platform files alone. Add a separate
   auth-only Pages configuration with explicit staging vars for production and
   preview, no DO binding, and no production secrets. Add tests proving every
   audio entry route cannot reach station/upstream/DO work without a binding.
   Label audio unavailable in this deployment. Do not change the accepted
   all-station relay architecture to a fallback without a user decision.
2. **Run hermetic verification.** Run `make test typecheck build`, validate the
   auth-only configuration and inspect bundle output for secrets. Record the
   exact source revision and artifact/config used. No deploy command or remote
   dev session belongs in this step.
3. **Request a scoped provisioning approval.** Name the Cloudflare account,
   dedicated Pages project and dedicated Supabase project; state available free
   capacity or actual quoted charges and permitted testers. Approval must cover
   project creation, the web-only migration on that empty project, server-secret
   installation and the auth-only upload. It must not authorize billing changes,
   migration of the existing project, a relay Worker, or audio traffic.
4. **Provision the isolated store and private site.** After approval, create the
   empty test database and apply only `20261011000008_web_auth.sql`. Verify RLS,
   client table/RPC denial and absence of non-web data. Create the Pages project
   without a public functional preview; configure Access before authenticated
   application traffic. Disable untrusted build/preview access. Confirm account
   and resource identifiers without printing credentials.
5. **Configure and upload auth-only.** Install only the dedicated test database
   URL/service-role key as server bindings and explicitly select staging. Never
   use `VITE_` values or copy local `.dev.vars` into an artifact. Verify no DO
   binding exists in either environment. Upload only to the dedicated project
   using the reviewed config; no default deployment target or git push.
6. **Validate from Safari and Chrome.** Check Access on every hostname, then
   health, phone Pairing, email, reload, both sign-outs and cross-browser
   revocation. Confirm forged headers cannot change identity and client database
   access is denied. Attempt relay start/audio/events with a valid web session:
   expect unavailable, with no station/upstream connection. Do not start SomaFM.
   Record any CPU-limit errors instead of silently enabling Paid.
7. **Open a separate audio approval gate.** Obtain Cloudflare clarification,
   rights-cleared test audio, origin/hosting costs, approved egress/resolver
   changes and plan choice. Integrate an exact-host, server-owned fixture ID;
   never expose arbitrary URL input or loosen SSRF defenses for convenience.
   Do not publish the private fixture in radio-browser. Deploy the separate
   SQLite DO Worker first, configure its own database secrets, then bind Pages
   with its exact `script_name`. Do not share with production/untrusted preview.
8. **Run a measured audio experiment.** After that approval, use one stream at a
   time. Establish same-upstream audio/title provenance in the deployed binding,
   then run 62 minutes with a genuine HTTP origin and 62 with HTTPS, within the
   current 65-minute relay lifetime. Record audible continuity, title behavior,
   sanitized CPU/wall time/outcomes, DO usage and cleanup. Test stop, EOF,
   cancellation, revoked-session delivery and stale-handle rejection. A redirect
   immediately upgrading HTTP to HTTPS does not prove sustained HTTP transport.

Auth-only progress would validate part of E1/E2/E3/E6, not E4/E5 or production
`.com` Pairing. Identity comparison, refresh, remaining endpoint/schema checks,
and the milestone decision gate still need explicit evidence.

## Stop and rollback rules

- Stop on any host that bypasses Access, cross-environment database/DO binding,
  unexpected billing, secrets in output, a rights complaint, or unexpected audio
  egress. Re-block access first; do not broaden permissions to make a test pass.
- For auth-only rollback, keep Access closed and remove/roll back only this lab's
  application. Revoke/rotate only its dedicated secrets and sessions as needed.
  Do not delete the shared PocketRadio project or invalidate phone credentials.
- For later audio rollback, remove the Pages relay binding/disable entry routes
  and stop the dedicated relay Worker as necessary to terminate existing streams.
  Removing a binding alone is not proof that existing streams stopped. Confirm
  upstream closure and database/DO lease cleanup before declaring shutdown.
- Retain sanitized evidence. Resource deletion and database cleanup require
  explicit approval; neither was performed here.

## Decisions to request next

1. **Recommended: prepare the auth-only staging configuration and its tests.**
   This advances deployed cookie/Pairing checks without serving radio audio.
   Cloud resource creation still waits for the separate scoped approval above.
2. **Alternative: pause cloud preparation until audio hosting/rights are settled.**
   This avoids lab setup work but delays otherwise independent authentication
   checks. Do not replace the unresolved relay with direct HTTPS playback and
   claim equivalent ICY-title behavior; that would change the accepted design.

## Verification of this review

Only documentation changed. No deploy, push, account inspection, service upgrade,
secret installation, migration, permission request or audio connection was made.
The prior implementation run passed 192 Vitest tests, 41 SQL/handler tests, two
offline workerd checks, typechecks and builds; those are prior results, not a new
run in this documentation-only review. Whitespace and local Markdown links were
checked. M1 remains IN PROGRESS.
