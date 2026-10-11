# Web M1 subagent plan

**Status:** APPROVED TO EXECUTE — user requested plan, commit, then execution.
**Scope:** [M1 feasibility experiments](milestone_1.md), not the first-release UI.
**Route:** `openai-codex/gpt-6.1-sol:high`, Codex OAuth. The active session
establishes model access; `pi auth check --provider openai-codex --json
--no-refresh` reported ready on 2026-10-11. No provider or auth-route change.

## Outcome and limits

Create and test the smallest deployable experiment page for Pairing, sessions,
Pocket Casts JSON probes, and the Stream relay. Record what the code proves and
which experiments still require accounts, deployment, or human observation.
Do not turn mocked responses into evidence that an ADR holds.

The user authorized implementation and commits. This does not authorize a
public deployment, applying a migration, pushing commits, modifying iOS, or
spending an hour listening automatically. Stop at those external checkpoints.
Keep M1 open until the user performs its gestures and decides from E1–E6.

## Locations and ownership

| Area | Location / owner |
|---|---|
| Coordination | Lead; shell `main`: this plan, M1 status, reports and handoff |
| Bootstrap | Setup delegate; `pocket-radio-web/` on unborn `main` |
| Experiment code | `pocket-radio-web/`, `feature/m1-spikes` after first commit |
| Session and Pairing | Auth delegate; `functions/_lib/auth/`, `functions/api/pair/`, `functions/api/session/`, `functions/api/signout/`, `functions/api/probes/`, `tests/auth/` |
| Relay | Relay delegate; `functions/_lib/relay/`, `functions/api/relay/`, `functions/api/relay-events/`, `tests/relay/` |
| Shared wiring and page | Lead only; package/config files, shared types, bindings and `src/` after bootstrap |
| Migration | Auth delegate; one new `supabase/migrations/` file, no edits to existing migrations |
| Review | Independent delegate; read-only code and reports, no production edits |
| Agent definition | `.pi/agents/web-m1-sol.md`; all roles use the same pinned route |

Auth and relay run in parallel only after the lead freezes their shared
interfaces. They may not edit shared config, page, other agents' files, or
existing migrations. Request an ownership transfer if a shared interface must
change. Lead reviews and commits each completed slice with explicit paths.
No other platform's code or unrelated untracked agent files are in scope.

## Model choice, budgets, and stopping rules

Use Sol for all slices. It is the verified active model, and security-sensitive
cross-runtime code warrants it. Do not claim a cheaper model is available
without checking its access through this exact provider. No quota-saving claim.

The skill's 2026-10-04 rate snapshot is fresh against runtime UTC 2026-10-11.
Codex OAuth uses the subscription route, not API-dollar billing. Included
allowance consumption and any actual purchased-credit charge are unknown.
The following token forecasts are soft planning budgets, not harness caps.
Input includes repeated context, cached reads, instructions, and tool output;
output includes reasoning where reported. Actual usage may differ.

| Slice | Exact provider/model | Aggregate input | Output/reasoning | Completion check |
|---|---|---:|---:|---|
| Lead: instructions, plan, interfaces, integration and evidence | `openai-codex/gpt-6.1-sol:high` | 700k | 20k | Explicit commits, full verification, pending external checks recorded |
| Setup | `openai-codex/gpt-6.1-sol:high` | 250k | 10k | Vite/React/TS, Functions, Vitest, Makefile, reproducible lockfile; build and tests pass |
| Auth: E1/E3/E6 implementation | `openai-codex/gpt-6.1-sol:high` | 900k | 25k | Browser-bound Pairing, verified identity, secret storage, rolling session, two sign-outs; hermetic tests |
| Relay: E4 implementation | `openai-codex/gpt-6.1-sol:high` | 900k | 25k | Arbitrary ICY chunk boundaries, safe station resolution, authenticated same-connection title channel, cleanup/backpressure tests |
| Discovery: E2/E5 and deployment constraints | `openai-codex/gpt-6.1-sol:high` | 300k | 10k | Source-backed QR routing and current terms/runtime limits; unknowns labeled |
| Independent review | `openai-codex/gpt-6.1-sol:high` | 500k | 15k | Security and runtime review, findings mapped to tests or pending checks |
| **Total forecast** | | **3,550k** | **105k** | |

For reference only, the fresh snapshot lists Sol at 50 uncached-input,
2.5 cached-input, and 250 output credits per million tokens for eligible
credit billing. If all forecast input were uncached, that would be 203.75
credits; if all were cached, 35.125 credits. These are illustrative bounds
under those assumptions, not an estimate of included subscription usage or
an actual bill. No API-dollar conversion is applied.

Every slice stops on provider/model mismatch, missing required permissions,
unsafe identity/proxy behavior, two unsuccessful fixes to the same failing
check, projected budget overrun, or a needed edit outside its assigned paths.
Report the blocker before expanding scope. The lead may reassign ownership
within this plan; provider changes or scope expansion require the user.

## Execution order

1. **Lead:** update shell and platform instructions; commit the shell plan and
   pinned role before starting implementation. Leave unrelated files alone.
2. **Setup delegate:** scaffold the empty repo using current third-party docs.
   Keep the page minimal and secrets absent. Lead verifies and makes the
   first `main` commit, then creates `feature/m1-spikes` and wires hooks.
3. **Lead:** define a shared environment and session-validation interface.
   Decide on a same-connection relay event transport supported by Pages;
   durable cross-isolate coordination cannot be replaced by module globals.
4. **Auth and relay delegates:** implement their assigned paths red-to-green
   with injected fetch, persistence, clock, and streams. Auth writes the
   additive migration but never applies it. Relay never accepts a URL or
   obtains titles from a second upstream connection.
5. **Discovery delegate:** inspect the existing iOS route without changing
   it; retrieve current Cloudflare terms and limits. Record quoted clauses,
   source dates, and remaining uncertainty. No phone launch or audio capture.
6. **Lead:** integrate the bare page and bindings. Add shell `web-*` delegates;
   update repo status docs and security notes only for verified facts. Run
   unit tests, type checking, build, local Functions smoke tests and hooks.
7. **Independent reviewer:** review the completed diff for credential leaks,
   forged identity, Pairing takeover, origin checks, SSRF/redirects,
   cross-isolate state, abort cleanup and false experiment claims. Lead
   resolves findings under explicit ownership and reruns verification.
8. **Lead:** commit completed code and additive shell docs; record revisions,
   test counts, delegated usage when available, and external blockers in the
   M1 handoff. Do not push, merge, close M1, or mark manual checks complete.

## Evidence checklist

- **E1:** unit tests prove request/response handling, not Pocket Casts JSON
  support. Live Worker approval and matching iOS UUID remain separate.
- **E2:** source inspection identifies the fork's route. Camera scans with
  and without Automattic installed require the user.
- **E3:** test probes must label each endpoint pending until a live
  authenticated call returns usable JSON or an identified protobuf format.
  Do not mutate the user's episode state as part of an automatic probe.
- **E4:** fixtures prove byte stripping and event association. A deployed
  60+ minute run, audible continuity and CPU measurement require an external
  checkpoint for both HTTP and HTTPS stations.
- **E5:** distinguish a cited permission, a restriction, and silence in the
  terms. No legal-permission claim from an uncited inference.
- **E6:** mocked and local tests prove session behavior only. Safari/Chrome
  reload, both sign-outs, and a forged anon-key read against the applied
  migration remain pending until performed on the deployed origin.
