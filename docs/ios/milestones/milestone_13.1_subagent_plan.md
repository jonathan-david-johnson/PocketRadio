# iOS M13.1 — subagent plan

**Status:** EXECUTED 2026-10-07, awaiting your checkpoint. See [Outcome](#outcome). The iOS repo's own rule still applies: nothing is committed until you have tested and approved.
**Scope:** [M13.1 — CarPlay output harness](milestone_13.1.md), with the lessons from the [M13 spike](milestone_13.md#findings-from-e3-to-e7).
**Route:** `anthropic` provider, Anthropic models only, Standard speed. No provider or billing-route changes.

## Freshness gate

| Check | Result |
|---|---|
| Active session | `anthropic/claude-sonnet-5-5`, reasoning `high` (from `PI_PROVIDER`, `PI_MODEL`, `PI_REASONING_LEVEL`) |
| Rate snapshot date | 2026-10-04 (UTC) |
| Runtime date | 2026-10-07 (UTC) |
| Stale after | 2026-11-04 (snapshot date plus one month) |
| Gate | **Passed.** The snapshot is fresh. |

## Decision and ownership

Run **one writer at a time**, each with its own files. Do not run writers in parallel. Every red-to-green loop needs the shared Xcode DerivedData and the one pinned simulator, so parallel writers would only queue behind each other and corrupt each other's builds. Disjoint files keep each handoff small and the review simple.

The lead (this session) integrates, owns the Makefile and shell-side files, and runs the final 20-run check. Writers do not commit, push, or delegate.

## Where the work happens

| Area | Location |
|---|---|
| Plan and reports | Shell `main`: this file, M13.1, experiment reports |
| Code | `pocket-radio-ios`, branch `feature/carplay-harness` from `trunk` `0751918f8` |
| Worktree | `pocket-radio-ios-carplay/`, reused. The spike's uncommitted files stay in place and carry across the branch switch. |
| Kept harness | `PocketCastsTests/Tests/CarPlayOutput/Harness/` (subfolders `FakeWorld/`, `Guard/`, `Probe/`, `Gherkin/`, `Reset/`) and `PocketCastsTests/Tests/CarPlayOutput/HarnessTests/` |
| Production seams | `#if DEBUG` only, in `PlaybackManager`, `NowPlayingHelper`, `TrackArtworkResolver`, `RadioTracklistService` (already present in the spike; the plan keeps them) |
| Shell changes | Additive: `contracts/features/README.md`, the smoke `.feature`, and a delegating `ios-test-carplay` target in the top-level `Makefile` |
| Spike code | `PocketCastsTests/Tests/CarPlayOutputSpike/` stays untouched during M13.1. The kept harness is **copied and renamed** from it (no `Spike` prefix), so E1 to E7 keep compiling. The lead proposes deleting the spike folder only at the end, with your approval. |

## Role agents

The existing `m12-sol` role is `openai-codex` and must not be reused. The user-level `researcher` and `image_reader` roles use Fireworks models and are not eligible. Create three project roles in the shell `.pi/agents/`, which is currently untracked:

| Role | Exact pin | Reasoning | Used for |
|---|---|---|---|
| `m13-sonnet` | `anthropic/claude-sonnet-5-5` | medium | All implementation slices |
| `m13-haiku` | `anthropic/claude-haiku-4-5` | low | The mechanical copy-and-rename slice only |
| `m13-opus` | `anthropic/claude-opus-5-5` | high | Upstream-seam review and the final review |

Every role brief must say: verify `PI_PROVIDER` and `PI_MODEL` before editing; never print credentials; no commit, push, or delegation; edit only assigned paths; use exact edits; bound build logs (`| tail -60` or a grep for `error:` and `Executed`); keep Wi-Fi and simulator settings alone; and report the effective provider and model. If the subagent tool cannot pin a role's model, stop and ask. Do not fall back silently.

## Slices, models, and soft budgets

Input budgets count aggregate uncached input, cache writes, and cache reads across all requests, including repeated history, mandatory instructions, tool schemas, file reads, and build output. Output budgets include provider-reported reasoning, without double counting. All budgets are advisory. The harness enforces nothing.

Why these sizes: each kept file is small (the spike's largest are about 160 lines), and the code already exists to promote, so contexts stay small per turn. Most of the cost is turns spent running `xcodebuild`, so build output must be bounded. For comparison, M12's single writer used about 87 turns and 5.5M cache-read tokens on a roughly 2,000-line view model. These slices are much smaller.

| # | Slice | Exact provider/model | Files and ownership | Acceptance check | Input | Output | Stop or escalate when | Est. cost (API list rate) |
|---|---|---|---|---:|---:|---:|---|---:|
| 0 | Lead: roles, branch, access checks | `anthropic/claude-sonnet-5-5` | Shell `.pi/agents/`, worktree branch | Roles load with the right models; access to Haiku and Opus confirmed | in lead total | in lead total | A model is unavailable on this route | in lead total |
| 1 | Mechanical copy and rename of spike types into the kept folder | `anthropic/claude-haiku-4-5` | New files only under `CarPlayOutput/Harness/`; **reads** `CarPlayOutputSpike/` | Build passes; spike tests still compile; no `Spike` prefix in the kept folder | 300k | 10k | Any change needed outside copy, rename, and import fixes | $0.12 |
| 2 | Fake world: ICY stream server, art server, tone script, control API | `anthropic/claude-sonnet-5-5` | `Harness/FakeWorld/` (stream and art servers, `tone_128k.mp3` and its generator script) and tests for **behavior 1** (ICY framing parsed back at exact offsets) | Behavior 1 red then green | 700k | 12k | Two failed fixes; any need to change production code | $0.43 |
| 3 | Network guard, fixtures, `FakeWorld` facade | `anthropic/claude-sonnet-5-5` | `Harness/Guard/` and the `FakeWorld` facade (`play`, `setTracklist`, `setLatency`, `fail`, `dropStream`, `sendAdFrame`); tests for **behaviors 2, 3, 4** | Fake KCRW tracklist parses through the real parser (including a null `albumImageLarge`); rewrite works; a non-fixture host fails and names the host. Loopback-only stream URLs enforced. Kingfisher timeout above any scripted delay. | 900k | 15k | Two failed fixes; a new network seam in production | $0.54 |
| 4 | Now Playing probe | `anthropic/claude-sonnet-5-5` | `Harness/Probe/` and tests for **behaviors 6, 7** | A red image samples as red and none samples as `nil`; a timed-out wait reports the last snapshot and a diff | 400k | 8k | Two failed fixes | $0.25 |
| 5 | Gherkin runner promotion | `anthropic/claude-sonnet-5-5` | `Harness/Gherkin/` (from the 156-line spike runner) and tests for **behavior 9** | An undefined step fails with its text, file, and line; scenarios are separate results and selectable with `-only-testing:` | 500k | 10k | The runtime-registration technique breaks on this Xcode; report before redesigning | $0.32 |
| 6 | Reset seams and order test | `anthropic/claude-sonnet-5-5` | `Harness/Reset/`; the four `#if DEBUG` seams in production files; test for **behavior 5** (X then Y equals Y then X) | Order independence over four orders; production behavior unchanged when not `DEBUG` | 1,000k | 15k | A seam needs more than one `#if DEBUG` block per upstream file; two failed fixes | $0.59 |
| 7 | Review of the two upstream-file seams | `anthropic/claude-opus-5-5` | **Read-only.** `PlaybackManager`, `NowPlayingHelper` diffs | No change to non-DEBUG behavior; smallest possible upstream diff; merge-conflict risk noted | 250k | 6k | Any production-visible change found | $0.29 |
| 8 | Lead: smoke scenario, Makefile, README, 20-run check, docs | `anthropic/claude-sonnet-5-5` | `Makefile` targets `test_carplay` (wrapped in `caffeinate -dimsu`) and `carplay_sim`; shell `contracts/features/`; harness README; **behavior 8** | Smoke passes 20 runs in a row; a faked 500 fails with the endpoint and last snapshot | 1,800k (includes slice 0) | 30k | Provider mismatch; two failed fixes; unresolved invariant | $1.08 |
| 9 | Final review of the whole diff | `anthropic/claude-opus-5-5` | **Read-only.** Harness, seams, Makefile, README | Matches M13.1 scope; no test-host state hazards; no credentials in logs | 300k | 8k | A defect that needs ownership transfer | $0.37 |
| | **Initial total** | | | **6,150k** | **114k** | | | **$3.99** |
| | **Reserve, not authorized** | Sonnet and Opus | Only for an explicitly reassigned failed slice | | 500k Sonnet, 200k Opus | 10k, 5k | Stop when exhausted | $0.56 |

Slices 2 to 6 run in that order. The whole plan runs 1, 2, 3, 4, 5, 6, 7, 8, 9. Slice 7 follows slice 6 and runs before slice 8, because the lead should know the seams are accepted before building on them.

## Cost, with assumptions

- **Unit:** USD at published API list rates (2026-10-04 snapshot): Sonnet $2.00 uncached input, $0.20 cache read, $2.50 cache write (5 minute), $10.00 output; Haiku $1.00, $0.10, $1.25, $5.00; Opus $4.00, $0.20, $5.00, $20.00, per million tokens.
- **Split assumed for every slice:** 8% uncached input, 4% cache write, 88% cache read. This is an estimate. Real usage reports will replace it.
- **Method:** `tokens ÷ 1,000,000 × rate`, per category, so categories never overlap.
- **No long-context surcharge.** Anthropic's 4.6 and later models carry long context at standard rates.

| Plan | Sonnet | Haiku | Opus | Total |
|---|---:|---:|---:|---:|
| **Proposed mix** (input 6,150k, output 114k) | $3.21 | $0.12 | $0.66 | **$3.99** |
| All Sonnet, same volumes | | | | $3.82 |
| All Opus, same volumes | | | | $6.56 |

**The mix does not save money against the all-Sonnet baseline.** It costs about $0.17 more. That buys an independent Opus review of the upstream-file seams and the final diff, the two places where a second view is worth the most. Haiku saves about one cent. Against all-Opus the mix saves about $2.57. Differences in tokenizers, reasoning effort, retries, and real task difficulty can erase any of these nominal gaps.

**Included subscription allowance impact: unknown.** This snapshot has no public conversion from tokens to Claude Pro or Max allowance. The dollar figures are not subscription-quota estimates.

## Execution order

1. **Lead (slice 0).** Create the three role files. Confirm the iOS repo's `trunk` state and switch the worktree to `feature/carplay-harness` without disturbing the uncommitted spike. Confirm access to Haiku and Opus with a minimal call before assigning slices.
2. **Slice 1 (Haiku).** Copy and rename. The lead looks at the diff before slice 2 starts.
3. **Slices 2 to 6 (Sonnet), one at a time.** Each starts with a red test for its numbered behavior, then goes green. Each hands back a diff summary, red and green evidence, test results, and remaining uncertainty. The lead reviews each handoff before releasing the next.
4. **Slice 7 (Opus).** Seam review. Findings go back to slice 6's owner, under explicit ownership transfer.
5. **Slice 8 (lead).** Integration, the 20-run loop, and the user checkpoint described in M13.1.
6. **Slice 9 (Opus).** Final review. The lead fixes what it reports.
7. **User checkpoint.** You turn Wi-Fi off and run `make test_carplay`. You approve commits (per `pocket-radio-ios/AGENTS.md`).

## Stopping rules

- Stop a slice after two unsuccessful fix attempts to the same check, an unresolved invariant, or a projected overrun of its budget. Report the overrun to the lead.
- Ask you before spending any reserve, raising a budget, or changing a model assignment.
- Prefer `medium` reasoning for implementation. Raise it only for a stuck check, and ask first.
- Use reported usage after each slice to revise the later forecasts. The harness enforces no hard cap.

## Invariants for every slice

- Real code under test stays real. Fake only the outside world (stream, tracklist, iTunes, artwork). Do not mock `PlaybackManager`, `NowPlayingHelper`, or `MPNowPlayingInfoCenter`.
- Stream URLs are loopback only, because AVPlayer traffic bypasses the network guard.
- Never write the real `UserDefaults.standard` keys, except through playback itself. The test host is the app.
- Seams are `#if DEBUG` and as small as possible. Upstream files get at most one block each.
- Run tests under `caffeinate -dimsu`, on the dedicated simulator `PocketRadio CarPlay Tests` only. One agent holds the simulator at a time. Never sign in on it.
- No credentials or auth headers in any log.
- Test our extensions, not upstream behavior, per the M13 test boundary.

## Unresolved checks before launch

1. **Billing route.** The provider is `anthropic`, but I did not inspect credentials to tell an API key from a subscription login. Dollar figures assume API list rates. Tell me which route applies and I will relabel the estimates.
2. **Model access.** The session proves Sonnet 5.5. Haiku 4.5 and Opus 5.5 appear in the local model registry, which does not prove account access. Slice 0 checks this.
3. **Role pinning.** Confirm the subagent tool honors the `model:` pin in each role file, and check the effective provider and model from runtime metadata.
4. **Your approval of:**
   - creating the three role files in the untracked `.pi/agents/`;
   - creating `feature/carplay-harness` in the existing worktree;
   - the copy-and-rename approach, with the spike folder deleted only at the end.

## Outcome

Executed in the planned order on `anthropic` models only. Role pins were checked from runtime metadata: Haiku 4.5, Sonnet 5.5 and Opus 5.5 all reported the expected provider and model.

| Slice | Model | Result |
|---|---|---|
| 1 Copy and rename | Haiku 4.5 | Done. Build passed, no `Spike` names in the kept folder. |
| 2 ICY stream server | Sonnet 5.5 | Blocked once, then done (see deviations). 4 tests. |
| 3 Guard, fixtures, `FakeWorld` | Sonnet 5.5 | Done. 10 tests. |
| 4 Probe | Sonnet 5.5 | Done. 9 tests. |
| 5 Gherkin runner | Sonnet 5.5 | Done. 15 tests, with a real red phase for 11 of them. |
| 6 Reset and order test | Sonnet 5.5 | Done. 2 tests. A temporary skip of two reset calls made the order test fail as predicted. |
| 7 Seam review | Opus 5.5 | No blockers. One should-fix (a delayed tracklist response could refill the cache after a reset), fixed by the lead with a generation counter in `NetworkGuard` and a test. |
| 8 Lead integration | Sonnet 5.5 | Smoke scenario, fault check, Make targets, READMEs, 20-run check. |
| 9 Final review | Opus 5.5 | No blockers. Five should-fix items; the first three and a few notes were fixed (see below). |

### Deviations from the plan

- **Slice 2 was blocked** by a name clash: the kept `tone_128k.mp3` and the spike's copy have the same name, and the synchronized test folder bundles files by name, so the build failed with "Multiple commands produce". The lead renamed the kept file to `carplay_tone_128k.mp3` and relaunched. The slice 1 brief should have said not to copy the mp3. Cost: one extra Sonnet launch.
- **No true red phase** in slices 3, 4 and 6 for behaviors that already existed in the spike. Each agent reported this honestly. Slice 6 proved the order test can fail by disabling reset calls.
- **Fixes from the Opus final review** (done by the lead): harness tests now skip themselves unless `TEST_RUNNER_CARPLAY_HARNESS=1` (set by `make test_carplay`), so a plain `make test_staging` on a developer simulator cannot end playback or wipe the art cache; teardown resets before it stops the guard; the fixture-class crash risk; art-server connections now close when the world stops; a probe test no longer leaks station state; the Kingfisher timeout-restore test now checks something.
- **Left as notes:** the phone UI state helper (deferred to M13.2); the guard covers `URLSession.shared` and Kingfisher only, not the roughly ten other `URLSession` instances in production code; behaviors 1 and 5 are tested somewhat loosely; the 500-fault message names the configured fault, not a request the app made; the simulator lookup matches by name only.
- **Shell Makefile:** `ios-test-carplay` is edited locally but **not committed**, because it fails on `main` until the iOS branch merges. Use `make ios-test-carplay IOS_DIR=pocket-radio-ios-carplay` until then.

### Usage

The subagent tool did not report token counts for most slices, so measured usage is unavailable. Agents estimated only slice 2's blocked attempt (about 15k in, 4k out). The $3.99 forecast is therefore unverified against actuals. Slice 7's finding and the slice 2 relaunch were the only budget-relevant surprises. No reserve was requested or spent.
