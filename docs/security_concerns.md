# Security Concerns

## Supabase data unprotected against UUID spoofing

**Tables affected**: `radio_favorites`, `custom_streams`, `listen_time`, `donations`

**Status**: Known, accepted for MVP.

**The problem**: Direct clients scope Supabase writes/reads by `user_uuid` = `ServerSettings.userId` from Pocket Casts. Migration `20260512000005_reenable_rls.sql` re-enables RLS in source, but its policies trust the caller's `x-user-uuid` header. A malicious client holding the extractable anon key can forge that header if it knows another user's UUID. The live migration state was not checked here.

**Why direct clients remain vulnerable**: Pocket Casts is the auth authority. A UUID header alone does not prove the caller holds that account's session. A trusted server must derive identity from a Pocket Casts response instead of accepting the client assertion.

**The stronger boundary**: Use a trusted backend that verifies the Pocket Casts account and derives the UUID before reaching Supabase. The web implementation adds this boundary for its own requests and secret storage. Direct iOS and other client access remains unchanged.

**Risk assessment**: Low. Exposed data is radio station favorites and self-reported donation amounts — not financial data, credentials, or PII beyond what PC already holds. Requires knowing a target's UUID (not publicly exposed).

## Web credentials and direct playback

The web implementation follows [Web ADR 0002](web/adr/0002-cloudflare-hosts-web-player-supabase-is-database.md)
and [Web ADR 0003](web/adr/0003-sign-in-by-phone-pairing.md). The additive migration
`supabase/migrations/20261011000008_web_auth.sql` was applied with user approval
to the linked PocketRadio Supabase project on 2026-10-12. Live metadata checks
confirmed RLS and revoked client privileges; forged anon-key reads against all
five secret tables returned permission denied.

- `pc_tokens`, `web_sessions`, `web_pairings`, `web_account_revocations`, and
  `web_relays` enable RLS without client policies. Table privileges and RPC
  execution are revoked from `PUBLIC`, `anon`, and `authenticated` and granted
  only to `service_role`. A forged `x-user-uuid` cannot grant access.
- Workers keep tokens and device codes server-side. Sessions and browser-bound
  Pairing handles are hashed. Origin checks, poll leases, account revocation
  fences, and atomic sign-out protect approval and refresh races.
- Pages needs server-only database secrets. Service-role compromise still
  exposes secret tables. No keys are bundled in the page (checked in the build
  artifacts on 2026-10-18). The private staging Pages project has the staging
  database's three secrets in its production environment only, behind email-only
  Cloudflare Access; a production deployment's secrets have not been configured
  or verified. Retained legacy Worker secrets are not
  required or used by normal direct playback.
- [ADR 0006](web/adr/0006-direct-https-playback-without-an-audio-relay.md) replaces
  the audio relay with station-to-browser HTTPS playback. A bounded fixed
  radio-browser lookup returns a public URL, never station audio. It does not
  forward app credentials or arbitrary client-supplied URLs. Old relay/SSE/stop
  routes return 410 without network or binding access; no DO binding remains.
- Initial public-looking DNS URLs are checked in browser/server and restricted
  to HTTPS/443, without credentials, literal IPs, local/reserved names or
  fragments. This is not DNS pinning or validation of browser redirects.
  The station sees the listener's IP. Browser network/security/codec rules still
  apply. Suppress referrers and do not attach app secrets to media requests.
- Stop/switch/error/local sign-out/unmount release the audio source. Global
  session revocation does not revoke a public URL already playing in another
  browser. Historical relay admission, 15-second revocation and lifetime
  controls are not guarantees of the direct path.
- The prior Cloudflare continuous-relay classification was unresolved, not a
  finding that personal listening or every private relay is unlawful. That
  question is no longer an audio deployment gate because this backend carries
  no audio. It must be revisited if a relay is ever proposed again.
- [SomaFM's terms](https://somafm.com/legal/tos.html) restrict new third-party
  clients and embedding/restreaming. Direct playback is not an established
  exemption from client/metadata terms; no permission has been obtained. Use
  permitted test sources. The earlier relay smoke check proves no rights.
- Cloud deployment remains separately gated on private access, an isolated
  database and explicit approval. Secret tables are not environment-namespaced;
  do not share staging/production token stores. No cloud resource or already
  applied database relay table was deleted as part of the playback switch.

The earlier shared-table discussion above describes the direct-client risk;
web secret storage must never inherit that header-trust design. The linked
project's migration history includes `20260512000005_reenable_rls.sql`, which
still trusts the caller's UUID header. This does not establish that every
shared-table policy is identical to source; the live privilege checks here
were limited to the new web secret tables.
