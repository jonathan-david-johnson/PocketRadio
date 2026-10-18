# Direct HTTPS playback without an audio relay

Status: accepted (2026-10-15). Supersedes
[ADR 0004](0004-every-station-plays-through-the-stream-relay.md) and the audio-relay
part of [ADR 0002](0002-cloudflare-hosts-web-player-supabase-is-database.md).
Cloudflare still hosts the page, Pairing, sessions and data/API functions.

## Decision

The standalone web player sends station audio directly from the station to the
browser's native audio element over HTTPS. It does not forward audio through
Cloudflare, Supabase, a local helper, or another backend.

The user chose direct playback after considering browser restrictions and the
goal of a Linux-installable browser app without a separate native installation.
PWA installation remains planned work; installation does not bypass browser
mixed-content/CORS restrictions.

## Consequences

- Support known HTTPS stream URLs. Do not silently rewrite HTTP URLs to HTTPS,
  tunnel them through a relay, or attempt an HTTP fallback. Report HTTP-only
  stations as unsupported. The same no-relay policy applies to episode audio.
- Keep station selection by ID. The authenticated server may resolve a
  radio-browser UUID through a fixed, bounded metadata lookup, but must not GET,
  HEAD, probe or follow the station's audio URL. The browser receives only the
  public station ID/stream URL, never Pocket Casts or database credentials.
- Validate initial URLs on both server and browser: HTTPS, no credentials,
  fragment, literal IP, local/reserved hostname or nondefault port. This
  conservative first implementation supports public-looking DNS hosts on 443.
  Syntax validation does not pin DNS or validate browser-followed redirects.
  Browser HTTPS/CSP and transport rules still apply; do not claim universal
  reachability, private-network protection or codec support.
- Use a native audio element, no autoplay, and no explicit JavaScript stream
  fetch or ICY request. Do not set a CORS mode that unnecessarily requires
  station CORS support for ordinary media playback. A preload hint is not proof
  that a browser never connects before Play.
- Generic ICY track titles, same-connection metadata timing and radio lyrics are
  unavailable in the initial direct path. Do not keep a second audio connection
  merely to collect metadata. Station-supported metadata feeds or browser-side
  ICY parsing may be investigated later, subject to permission, CORS and playback
  support. Feed observation time is not the listener's audio position.
- The station receives the listener's IP and may apply its own cookies and
  browser policies. Suppress the app's referrer. Our host-only app cookies and
  server-held tokens must not be sent as station request headers.
- Stop, switch, errors, local sign-out and unmount must release the media source.
  Sign-out everywhere revokes web sessions, but cannot revoke a public station
  URL already loaded in another browser. Do not carry forward the relay's
  15-second revocation or 65-minute lifetime claims.
- Remove the DO binding and relay Worker from normal build/dev/deployment paths.
  Old relay/audio/SSE/stop routes return 410 without network or binding access.
  Retained relay source/tests are legacy offline fixtures, not an enabled
  capability. Do not delete already-applied database tables/RPCs or remote
  resources as part of this change.
- Cloudflare audio-proxy permission, DO residency and audio-forwarding cost are
  no longer prerequisites for this design because our backend carries no audio.
  This is not a blanket clearance of station/client/metadata terms. In
  particular, direct playback is not an established exception to SomaFM's
  published third-party-client restrictions. Use permitted sources for tests.

## Considered options

- **Direct HTTPS playback (chosen):** standalone browser installation and no
  server audio path; HTTP-only stations and universal titles are sacrificed.
- **Hosted one-to-one relay:** preserves HTTP/ICY access, but adds streaming
  infrastructure, costs and unresolved provider/station terms.
- **Native playback helper:** handles HTTP and metadata locally but requires
  another installation, contrary to the standalone Linux browser-app goal.
- **Browser-side ICY parsing:** potentially possible with station cooperation
  and CORS, but not a universal baseline.

## Verification and roadmap

M1 checks direct HTTPS media wiring, unsupported HTTP behavior, cleanup and
absence of a server audio path, then live browser playback and deployment.
M3 implements installability and the finished player. M4 must establish explicit
per-station metadata/lyrics sources before promising lyrics. M5 must not restore
an HTTP episode relay. None of these future milestones is completed by this ADR.
