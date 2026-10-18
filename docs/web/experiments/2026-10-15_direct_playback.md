# Direct HTTPS playback — local implementation evidence

**Status:** implemented and tested locally, 2026-10-15; user-reported direct
playback smoke check recorded 2026-10-16 UTC. The user subsequently reported
20 minutes of successful playback. A 60+ minute run and cloud acceptance remain
pending. The user chose this route;
[ADR 0006](../adr/0006-direct-https-playback-without-an-audio-relay.md) supersedes
the relay decision. No deployment, billing, migration, permission request or
database cleanup occurred.

## Implemented

- Same-origin authenticated `GET /api/playback?stationId=<UUID>` performs a
  fixed, bounded radio-browser metadata lookup. It returns only the validated
  public HTTPS URL and station ID. It never opens or probes station audio.
- Shared initial URL validation rejects HTTP, credentials, fragments, literal
  IPs, local/reserved names, nondefault ports and malformed addresses. The browser
  checks again and rejects our own origin as an audio target. DNS answers and
  later browser redirects are not pinned.
- The native audio element uses the station URL, controls, no autoplay and
  `preload="none"`; no CORS attribute, JavaScript audio fetch, SSE or second
  metadata stream. Preload is a browser hint, not a no-connection guarantee.
- Stop/switch/error/local sign-out/unmount pause and release the source.
  Sign-out everywhere revokes sessions, not a public URL already playing in
  another browser. No generic Track titles or lyrics are displayed.
- All four retired relay entry handlers return uncached 410 without touching
  request bindings, the database or network. Normal config/build/dev has no
  relay Worker/DO. Legacy source/tests and existing applied relay SQL remain.
- Static no-referrer/CSP headers suppress the app referrer, restrict media to
  HTTPS, and restrict JavaScript connections to our origin.

## Automated evidence

`make test typecheck build` passed: **247 unit/UI tests**, **41 isolated
SQL/handler tests**, and **one real offline Pages runtime integration**.
The integration uses synthetic phone approval and ephemeral PostgreSQL/WASM,
intercepts every outbound fetch, rejects any relay RPC/audio request, and runs
without a DO binding. It checks session creation/restoration/sign-out, HTTPS
resolution, HTTP rejection and retired routes. UI regressions cover source
assignment, lack of a title subscription, cleanup and replacement lookup timing.

The initial direct-path regressions failed before implementation. Table-driven
test fixtures were corrected, and the final complete suite passed.
Optional `npm run test:legacy-relay` also passed offline; that does not enable
the relay or establish listening evidence.

## Local runtime check

The previous multi-worker dev server was stopped and replaced by Pages-only
HTTPS at `https://127.0.0.1:8788`. Initial startup revealed that Pages rejects a
custom config flag; removing it uses the standard root `wrangler.jsonc`.
Health, the rebuilt direct-playback bundle, no-referrer/CSP headers and all four
410 entry routes were then verified. No station audio or authenticated upstream
was requested by this check. Existing database sessions/secrets were not cleared.

## User-reported playback — 2026-10-16 UTC

After receiving the Radio Paradise Global station UUID
`566476bf-d03c-4cac-b5d3-468f99a874b8`, the user reported **“played”**. This
establishes a local direct-playback smoke check, not a timed run, browser matrix,
Linux installability, measured codec/transport behavior or station-rights review.
The user identified the browser/platform as **Chrome on macOS**; browser and
OS versions and listening duration were not supplied. The user also confirmed
that **Stop playback** audibly stops the stream. This does not independently
measure release of the network connection. After restarting playback, the user
also confirmed that **Sign out / cancel Pairing** stops the audio. This verifies
local sign-out's audible-stop behavior, not cross-browser audio revocation.
The user then reloaded and confirmed **Ready to pair**, verifying that the
browser remained signed out after reload.

The user subsequently reported that **all of those checks also worked in Safari
on macOS**: direct playback, Stop, local sign-out stopping audio, and remaining
signed out after reload. Safari/macOS versions and listening duration were not
supplied. This is local smoke evidence, not deployed-cookie or endurance evidence.

## Subsequent duration report and deployment preflight

The user reported **20 minutes of successful playback**, then requested
deployed-site testing. The browser for that specific run was not separately
identified; this is user-reported duration, not instrumented 60+ minute endurance.

Initial preflight found Wrangler signed out; after the user's login, read-only
verification confirmed one signed-in Cloudflare account with Pages access and
no existing Pages projects. The OAuth grant does not include Access-management
permissions; private-host policy setup needs a dashboard step or separately
approved scoped credentials. No credentials were printed or requested here.

Supabase CLI access works in one organization, but no dedicated web M1 staging
project was found. Organization plan and available free-project capacity are
not verified; active/paused project counts alone do not prove either. Proposed
Pages/database name: `pocket-radio-web-m1-staging`. Confirm creation of the private
site, dedicated database, web-only migration and server-secret installation,
using staging `.net`, with no paid plan changes. Stop if zero-cost capacity or
privacy cannot be verified. Those read-only checks created nothing.

The user then approved this Free-only setup and upload. Pages and the dedicated
Free database now exist, and the web-only migration/security checks passed.
The [provisioning checkpoint](2026-10-16_staging_deployment.md) records the details.
Cloudflare privacy/plan verification still needs a dashboard step; no app upload,
Cloudflare secret installation, billing change or existing database change
occurred.

## Still to observe

Record Chrome/macOS versions, station-switch/error behavior and a 60+ minute
HTTPS run. Record Safari/macOS versions as well; Linux browser/installability and
cloud-origin checks remain separate and pending.
Confirm HTTP-only rejection without a fallback. Do not substitute the historical
relay smoke check or the synthetic tests for this evidence. Direct playback is
not a waiver of station/client terms, including SomaFM's published restrictions.

PWA installability remains planned M3 work, especially Chromium on Linux without
a native helper. M1 and cloud deployment remain open.
