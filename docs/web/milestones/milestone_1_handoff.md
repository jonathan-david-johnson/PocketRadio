# Web M1 handoff — local implementation verified

**Status:** M1 remains IN PROGRESS. The plan was executed through local
implementation, independent review, regression fixes, and commits. External
experiments and the user decision gate are pending. Nothing was pushed.

## Commits and location

| Repo | Revision / branch | Contents |
|---|---|---|
| Shell | `e05b49f`, `main` | Updated shell guidance, approved subagent plan, pinned Codex role |
| Web | `9ea6c56`, `main` | First commit: Vite/React/TS, Pages Functions, tests, Makefile and instructions |
| Web | `25f9933`, `feature/m1-spikes` | Pairing/sessions, probes, restricted relay and bare experiment page |
| Web | `2ce9a87`, `feature/m1-spikes` | Default handler/SQL interleaving test wiring |
| Shell | Commit containing this handoff, `main` | Additive auth migration, web targets, status/security docs and reports |

Worktree: `pocket-radio-web/`. No merge or milestone close occurred.
Unrelated untracked `.pi/agents/` definitions were left untouched.

## Verification

- `make web-test web-typecheck web-build`: 177 unit/UI tests, 41 isolated
  database/handler checks (including two parent tests), two offline workerd
  integration checks, typechecks, browser/Functions build and relay dry run.
- `make hooks-check`: passed for all repos/worktrees.
- Local HTTPS multi-worker server: page, health and signed-out session returned 200.
- Production dependency audit: zero vulnerabilities. Browser bundle secret-schema
  name scan and whitespace checks passed.
- Independent review findings were fixed. Final focused review accepted the
  same-tab cookie-restoration serialization. No verified blocking code finding
  remains from those reviews; external checks below are not waived.

Detailed methods and limits:
[local implementation evidence](../experiments/2026-10-12_local_implementation.md)
and [platform constraints](../experiments/2026-10-11_platform_constraints.md).
All roles used `openai-codex/gpt-6.1-sol` with OAuth. Exact delegated usage and
included subscription consumption were unavailable, so no measured cost is claimed.

## What exists

- Browser-bound Pairing with expiring server-side device grants; source-backed
  identity validation; hashed rolling 90-day sessions and both sign-outs.
- Service-only SQL storage/RPCs, account revocation fences, rate limits and
  approval/refresh/sign-out race tests. Migration is written, **not applied**.
- Sanitized JSON probes; write-capable `up_next/sync` and `sync/update_episode`
  remain manual/pending, not automatically called.
- One listener-owned SQLite Durable Object joins audio and SSE through Pages.
  Default Worker ingress denies public requests. Revocation/admission/cleanup
  tests and true separate-Worker local integration pass.
- Bare QR/account/relay/probe page. Auth transitions wait for restoration before
  issuing new cookie-changing requests. This is not M2's navigation shell.

## Next actions and gates

1. **User/lead:** clarify permission with Cloudflare and establish station
   redistribution rights before enabling production audio. Current terms do
   not explicitly establish this relay's permission. Workers Paid is a candidate,
   not an approved choice or verified exception.
2. **User:** explicitly approve applying the migration and deploying Pages plus
   the separate relay Worker. Configure server-only database secrets in both
   runtimes, and verify production/preview binding isolation. No such approval
   or external action occurred in this session.
3. **User/lead:** run E1/E2/E3/E6 with the deployed origin and real account.
   Confirm phone approval and account UUID, JSON endpoints, Safari/Chrome cookie
   reload, both sign-outs and denied forged-key reads. The user performs camera
   gestures with and without Automattic's app installed.
4. **User/lead after permission:** run E4 for 60+ minutes on HTTP and HTTPS
   stations; record CPU/quotas, native chunk sizes, disconnects, cancellation,
   titles and audible continuity. Local synthetic fixtures cannot replace this.
5. **User:** decide M1's gate from the resulting evidence. Do not close M1 or
   start M2 on the assumption that these unperformed experiments passed.

## Known restrictions

The relay allows only exact `ice1.somafm.com` / `ice2.somafm.com` hosts and trusts
operator DNS. It does not yet resolve curated IDs or safely serve arbitrary
Browse hosts. Broadening requires a reliable approved egress defense and actual
curated-table schema. This fail-closed spike restriction does not change ADR 0004.

Two live relays and five starts/minute are per-account limits, not a global cost
cap. Session delivery bounds and retention are deterministic local evidence;
production scheduling and PostgreSQL lock contention still need validation.
Browser receipt timestamps are not measured audible alignment. Cross-tab account
switching, real phone routing and production cookie persistence are unverified.

Menubar M12 and all other platform work were left unchanged.
