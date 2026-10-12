# Security Concerns

## Supabase data unprotected against UUID spoofing

**Tables affected**: `radio_favorites`, `custom_streams`, `listen_time`, `donations`

**Status**: Known, accepted for MVP.

**The problem**: Direct clients scope Supabase writes/reads by `user_uuid` = `ServerSettings.userId` from Pocket Casts. Migration `20260512000005_reenable_rls.sql` re-enables RLS in source, but its policies trust the caller's `x-user-uuid` header. A malicious client holding the extractable anon key can forge that header if it knows another user's UUID. The live migration state was not checked here.

**Why direct clients remain vulnerable**: Pocket Casts is the auth authority. A UUID header alone does not prove the caller holds that account's session. A trusted server must derive identity from a Pocket Casts response instead of accepting the client assertion.

**The stronger boundary**: Use a trusted backend that verifies the Pocket Casts account and derives the UUID before reaching Supabase. The web implementation adds this boundary for its own requests and secret storage. Direct iOS and other client access remains unchanged.

**Risk assessment**: Low. Exposed data is radio station favorites and self-reported donation amounts — not financial data, credentials, or PII beyond what PC already holds. Requires knowing a target's UUID (not publicly exposed).

## Web credentials and relay

The web implementation follows [Web ADR 0002](web/adr/0002-cloudflare-hosts-web-player-supabase-is-database.md)
and [Web ADR 0003](web/adr/0003-sign-in-by-phone-pairing.md). The additive migration
`supabase/migrations/20261011000008_web_auth.sql` is written and tested in an
isolated PostgreSQL/WASM database, **not applied to Supabase**.

- `pc_tokens`, `web_sessions`, `web_pairings`, `web_account_revocations`, and
  `web_relays` enable RLS without client policies. Table privileges and RPC
  execution are revoked from `PUBLIC`, `anon`, and `authenticated` and granted
  only to `service_role`. A forged `x-user-uuid` cannot grant access.
- Workers keep tokens and device codes server-side. Sessions and browser-bound
  Pairing handles are hashed. Origin checks, poll leases, account revocation
  fences, and atomic sign-out protect approval and refresh races.
- Pages and the separate relay Worker each need server-only database secrets.
  Service-role compromise still exposes the secret tables. No keys are bundled
  in the page; production secret configuration has not been verified.
- Relay admission limits an account to two active relays and five starts per
  minute. Nonrolling session checks fail closed and bound ongoing delivery
  after revocation to 15 seconds in deterministic tests; deployed cancellation
  and scheduling still need verification. Ended object state expires after
  24 hours. These controls are not a global cost or denial-of-service guarantee.
- The restricted spike resolves radio-browser UUIDs and accepts only exact
  `ice1.somafm.com` / `ice2.somafm.com` hosts, with each redirect revalidated.
  It trusts operator DNS, not general DNS/IP pinning. Arbitrary Browse hosts
  must stay blocked until a reliable egress defense is approved.
- Cloudflare's current terms do not explicitly establish permission for this
  continuous third-party audio relay. Cloudflare clarification and station
  redistribution rights are production gates, separate from implementation
  tests. See [Web ADR 0004](web/adr/0004-every-station-plays-through-the-stream-relay.md).

The earlier shared-table discussion above describes the original MVP risk;
web secret storage must never inherit that header-trust design. Migration
`20260512000005_reenable_rls.sql` re-enables shared-table RLS in source, but
still trusts the caller's UUID header. This document does not establish which
migrations are deployed to the live database.
