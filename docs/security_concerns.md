# Security Concerns

## Supabase data unprotected against UUID spoofing

**Tables affected**: `radio_favorites`, `custom_streams`, `listen_time`, `donations`

**Status**: Known, accepted for MVP.

**The problem**: All Supabase writes/reads are scoped by `user_uuid` = `ServerSettings.userId` from Pocket Casts. RLS is disabled (migration 004). A malicious client that knows or guesses another user's UUID could read or overwrite their data.

**Why we can't fix it properly**: Pocket Casts is the auth authority. We have no independent way to verify that a request actually came from a valid PC session for a given UUID. Even with Supabase Auth JWTs, we'd still be trusting the UUID the client reports — we can't validate it against PC's backend without a server-to-server call.

**The real fix** (if warranted): Add a thin backend service that validates the PC session server-to-server before writing to Supabase under the service role key. This is architecturally significant and not justified for the current data sensitivity.

**Risk assessment**: Low. Exposed data is radio station favorites and self-reported donation amounts — not financial data, credentials, or PII beyond what PC already holds. Requires knowing a target's UUID (not publicly exposed).
