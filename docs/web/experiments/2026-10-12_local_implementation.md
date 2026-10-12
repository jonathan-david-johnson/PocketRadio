# Web M1 local implementation evidence

**Result:** local contracts and runtime integration pass. E1–E6 live acceptance
and the milestone's decision gate remain open. No production deployment,
Supabase migration application, live audio connection, or phone action occurred.

## Tested revisions and commands

- Shell planning base: `e05b49f` on `main`, following original plan `88ebd62`.
  Additive migration and verification docs were present during tests and are
  committed with this report.
- Web bootstrap: `9ea6c56` on `main`.
- Web implementation: `25f9933`; default handler/SQL suite wiring: `2ce9a87`,
  on `feature/m1-spikes`.
- Node `24.15.0`, Wrangler `4.149.0`, Vitest `5.0.3`; locked package versions.

`make web-test web-typecheck web-build` passed. The default suite now runs
**177 Vitest unit/UI tests**, **41 PostgreSQL/WASM contract/handler tests**
(including two parent tests), and two offline real-workerd integration checks.
The final database-suite wiring was rerun with `npm run test:db` after its
commit; no production code changed in that follow-up.

Both runtime checks intercept every outbound fetch. The first exercises the
actual relay class with SQLite storage. The second uses the compiled Pages
router, a separate relay Worker, ephemeral SQL, synthetic Pocket Casts approval,
and a deterministic ICY stream. It checks cookies/session restoration,
authenticated audio/SSE, single-upstream byte stripping, URL rejection and sign-out.
Neither uses real Pocket Casts, Supabase, radio-browser or station traffic.

Local multi-worker HTTPS dev startup also returned 200 for `/`, `/api/health`,
and signed-out `/api/session`. No browser gesture was performed. Relay build
used Wrangler `--dry-run`; no upload occurred. Hooks, whitespace checks, the
production dependency audit (zero vulnerabilities), and a browser-bundle scan
for secret table/key/device-code names passed. The scan is not a proof against
all possible credential leaks.

## Findings and regressions

Independent review reproduced approval/sign-out and refresh races with real
handlers and isolated SQL. Fixes add atomic pairing/session cancellation,
persistent account revocation fences, and compare-and-swap refresh persistence
for surviving sessions while denying the revoked caller. Tests cover delayed
approval cookies and stale grants after fresh Pairing.

Relay fixes add service-only persistent admission, nonrolling revocation checks,
fail-closed timeouts and bounded object retention. Host/redirect allowlisting
remains deliberately restricted. Native workerd testing found that Worker fetch
rejects `redirect: "error"`; manual redirect handling made the runtime checks pass.

A final UI review reproduced a cookie-order race during initial restoration.
Two UI tests failed before the fix and passed after auth transitions were
serialized. The focused reviewer accepted that same-tab path. Cross-tab account
switching and production browser-cookie behavior were not established.

## Experiment boundaries

| Experiment | Local/source evidence | Still required |
|---|---|---|
| E1 Pairing | Source-backed JSON fields, server-only device codes/tokens, hashed browser binding, leases, one-time consume, synthetic approval through real Pages | Worker calls to real Pocket Casts; phone approval; matching iOS account UUID |
| E2 QR route | Existing iOS `/pair`/`pktc` source wiring; QR generated locally in browser code | Actual camera scans, prefill, app-scheme collision and approval |
| E3 JSON endpoints | Allowlisted probes expose status/format only; write-capable endpoints remain manual | Real authenticated responses; protobuf determination; safely approved write probe |
| E4 relay | ICY fixtures, same-connection audio/SSE in workerd, limits and revocation tests | HTTP and HTTPS 60+ minute deployed runs, CPU, cancellation, memory and listening |
| E5 terms | Current official clauses and runtime/deployment constraints in the discovery report | Cloudflare clarification and station redistribution rights; plan decision |
| E6 sessions/storage | Rolling expiry, both sign-outs, client-role permission denial, forged UUID rejection and sanitized browser response tests | Applied migration, production Safari/Chrome cookie reload/sign-outs, live forged-key read |

## Restrictions and risks

- Pages needs a separately deployed SQLite Durable Object Worker, with secrets
  configured for both runtimes. Local tests do not verify those production bindings.
- Only `ice1.somafm.com` and `ice2.somafm.com` pass the stream allowlist.
  Operator DNS is trusted; general DNS/IP pinning is absent. Curated-ID and
  arbitrary Browse-host support remain unimplemented. ADR 0004 is not superseded.
- Admission bounds one account, not global traffic or spend. Timer/abort bounds
  and 24-hour object cleanup are tested locally, not measured on Cloudflare.
- PostgreSQL/WASM serializes queries. It tests explicit interleavings and SQL
  behavior, not real multi-connection lock contention under production load.
- Titles are received on the listener's connection, but browser buffering still
  separates receipt from audible playback. No measured alignment is claimed.

No decision-gate choice or manual milestone checkbox was marked passed.
