# iOS M13.2 — subagent plan

**Status:** IN PROGRESS — automated verification passed; user CarPlay exercise recorded with discrepancies (2026-10-08 UTC). The user accepted the recorded discrepancies and approved baseline commits; iOS commit `12c3cfb60`. Integration remains separate. User approved execution, both testability exceptions and baseline commits. No app-bug fixes or device runs.
**Scope:** [M13.2 — CarPlay Now Playing output suite](milestone_13.2.md). S1–S7 remain approved and unchanged.
**Route:** `openai-codex` OAuth, OpenAI models only, Standard speed.
**Budgeting:** Omitted at the user's request on 2026-10-07. No token budgets, cost forecasts, subscription-impact estimates, or budget-based stopping rules.

Build the suite on the existing harness. Use Sol 6.1 for specification, expected-failure semantics, asynchronous state transitions, and independent review. Use Luna for bounded step additions and test wiring. Run one writer and one simulator user at a time.

This plan replaces M13.2's original Opus/Sonnet model assignments, not its behavior spec. Planning does not authorize implementation, commits, or device runs.

## Verified starting point

| Check | Result on 2026-10-07 |
|---|---|
| Active session | `openai-codex/gpt-6.1-sol`, reasoning `high` |
| Authentication | `pi auth check --provider openai-codex --json --no-refresh`: ready, OAuth. No credentials read. |
| Skill snapshot | 2026-10-04; fresh against runtime UTC date 2026-10-07. Rates are not used. |
| Worktree | `pocket-radio-ios-carplay/`, branch `feature/carplay-harness`, commit `2358aab83` |
| Current baseline | `make test_carplay`: 43 tests, 0 failures, 91.2 s of test execution |
| Simulator | `PocketRadio CarPlay Tests`, `6565636E-BB8D-4C34-A9EB-56F2BB638400` |
| Existing edits | Both shell and iOS-worktree Makefiles have unrelated uncommitted edits. Preserve them. |
| Active milestone pointer | `docs/ios/current_milestone.md` still points to M13 experiments. Repoint it to M13.2 when execution starts; do not overwrite its target. |

The harness is committed but not merged to `trunk`. Continue in its worktree; do not branch from the main iOS checkout. The prior 20-run smoke check and device sign-off are recorded in [M13.1](milestone_13.1.md). Today's baseline is a simulator run, not a new offline or device check.

## Execution checkpoint

[Final automated verification](../experiments/2026-10-08_m13_2_verification.md) records
results and remaining limits. [Unmarked baselines](../experiments/2026-10-07_m13_2_baselines.md)
retain the earlier evidence. iOS code is committed as `12c3cfb60`; companion contracts/docs are approved for shell `main`. Pre-existing Makefile cleanup remains uncommitted.

| Slice | Current state |
|---|---|
| 0 | Effective Sol/Luna pins and OAuth verified; milestone pointer safely repointed |
| 1 | Strict per-output-check expected/unexpected/unrelated-failure semantics self-tested |
| 2 | Ordinary steps, request evidence and query-specific artwork fixtures verified |
| 3 | Real retained detail-controller lifecycle, cleanup and all five artwork scenarios verified |
| 4 | Lifecycle and absent-album steps verified; approved barrier gives causal cached-start reproduction |
| 5 | Three real delayed-artwork scenarios verified; station/podcast identity failures mapped to new bug 6 |
| 6 | Ad, live/music/audio and S7 policy scenarios verified; actual disconnect restoration independently checked |
| 7 | All 15 scenarios discoverable once; 9 strict checks across 7 scenarios; default Makefile selection wired |
| 8 | Fresh-context Sol review finding fixed and re-reviewed; formatting passed; three final full runs passed 128 tests each; ordinary-run skips and Release exclusion verified |
| 9 | Docs/ADR reconciled; four-song manual exercise recorded. User accepted discrepancies and approved baseline commits; iOS `12c3cfb60`; no merge/closure |

Both approved exceptions are implemented without app-bug fixes. The startup barrier
captures/releases the actual continuation for one identity; the real disconnect callback
and tests share its unchanged cleanup/restoration body. No unsupported CarPlay object
construction or fabricated passing display was used.

The reset's cache-completion wait/main-queue fence improved observed isolation, but does
not prove completion of unobservable background startup work. No final-run readiness/reset
failure occurred. Host sleep invalidated an earlier race run; no sleep occurred during the
three final runs. Only one writer/simulator user ran at a time; reviewers remained read-only.

## Models and roles

Dedicated role definitions were created under shell `.pi/agents/` after execution approval.

| Role | Exact model pin | Assignment |
|---|---|---|
| Lead | `openai-codex/gpt-6.1-sol:high` | Spec wording, integration, ownership, final verification and docs |
| `m13-2-sol` | `openai-codex/gpt-6.1-sol:high` | Strict expected failures; UI lifecycle; rebuilds; delayed callbacks; lyric/CarPlay boundary |
| `m13-2-luna` | `openai-codex/gpt-6-luna:high` | Straightforward fixture/step additions and scenario-class wiring after the lead defines exact checks |
| `m13-2-review` | `openai-codex/gpt-6.1-sol:high` | Fresh-context, read-only review; no simulator commands |

Sol access is established by the active session. Luna access and its effective model pin were confirmed by a minimal read-only admission call before its first slice. Before assigning Luna a slice, make a minimal read-only access check on the same OAuth route and verify its effective provider/model. If unavailable, stop and ask to reassign its slices to Sol. Do not silently change models or providers.

Do not reuse `m13-haiku`, `m13-sonnet`, or `m13-opus`: they are Anthropic roles. Do not reuse `m12-sol` unchanged: it contains M12-specific instructions and an execution-specific budget waiver. Verify that the delegation tool honors each exact model pin before edits begin.

## Ownership and execution order

Paths below are relative to the shell unless prefixed by `CarPlayOutput/`, which means `pocket-radio-ios-carplay/PocketCastsTests/Tests/CarPlayOutput/`.

The lead owns shared contracts, milestone docs, role definitions, and Makefile integration. Delegates receive only their assigned harness/test files. Hand overlapping files to the next writer explicitly. No parallel builds: writers share Xcode DerivedData, singleton state, and one simulator.

| Order | Slice and model | Allowed files | Acceptance check | Stop or escalate when |
|---|---|---|---|---|
| 0 | Admission and scenario wording — lead Sol | Role definitions; this plan; M13.2; `contracts/features/now_playing/`; shared features README | Provider pins work; approved S1–S7 map to 15 core scenarios; stretch work excluded; scenario names fixed before adding known-bug entries | Model access fails; wording changes approved policy; a requested behavior cannot be observed within scope |
| 1 | Strict expected-failure support — Sol | `CarPlayOutput/Harness/Gherkin/FeatureRunner.swift`; new iOS-side known-bugs table; runner self-tests and fixtures | Known output defect is expected; unexpected pass fails; unrelated step/setup/network errors still fail; feature and Swift locations retained | Matcher cannot distinguish the intended output defect from a harness failure |
| 2 | Ordinary steps and fixture controls — Luna | `CarPlayOutput/Harness/Gherkin/NowPlayingSteps.swift`; narrowly scoped `FakeWorld.swift` additions; focused step/fixture tests | Multiple rows, explicit albums, null art, iTunes hit/miss, logo comparison, ad frames, and sustained output assertions work; behavior 1 remains green; 5, 6, 11, 13 run without undefined steps | A change involves asynchronous ownership, UI lifecycle, or production code; return it to Sol |
| 3 | Station-detail path and mismatched feed — Sol | New retained station-detail helper under `CarPlayOutput/Harness/`; steps and helper self-tests; fixture extensions if needed | Behavior 3 uses the real controller lifecycle and observes a tracklist refresh; 2 and 4 exercise distinct stale/mismatched cases; helpers stop tasks and observers at teardown | UI opens unguarded network paths; controller lifecycle cannot be modeled without a new production seam |
| 4 | Rebuild, cached start, stop/replay — Sol | Lifecycle steps under `CarPlayOutput/Harness/Gherkin/`; focused tests; known-bugs table | Behavior 7 and bug 5 symptoms B/C reproduce independently inside their own scenarios; setup passes before the narrowly matched output failure | A scenario only fails because an earlier test polluted state; startup ordering cannot be made repeatable without fixing app code |
| 5 | Delayed artwork across song/station/episode changes — Sol | Race steps; fake-world/art-server controls; supporting local episode fixture; focused tests | Behaviors 8–10 prove the old request started, the identity changed, and the old result finished; the observation window catches any stale publication | A second fake station needs a competing global guard; podcast playback leaks off-loopback; negative assertions run before the old result arrives |
| 6 | CarPlay lyric boundary and write-path markers — Sol | CarPlay/lyric steps and fixtures; focused tests; small reset/helper extensions within the test target | Behavior 12 drives the relevant real album-write path; connected state blocks lyrics; disconnection restores the real album; behavior 13 checks initial, metadata, artwork, and rebuild writes | The helper writes the expected output itself; disconnect semantics need a spec change; production changes would be required |
| 7 | Scenario registration and selection — Luna | New suite classes under `CarPlayOutput/`; runner-discovery self-tests | Each scenario is a separate XCTest result and individually selectable; exactly 15 core scenarios including the existing first-song smoke; no duplicate smoke | Dynamic registration or scenario identity needs redesign; hand that issue to Sol |
| 8 | Integration and verification — lead Sol | Worktree Makefile CarPlay test list; harness/shared README; contracts; bug docs; milestones; explicitly returned fixes | Existing 43-test baseline remains green; full suite includes all core scenarios; strict markers name bugs; repeated runs remain stable; production diff unchanged | New failures lack bug evidence; tests are flaky; a proposed fix changes production behavior |
| 9 | Independent review — fresh Sol | Read-only diff, assigned source paths, feature specs, evidence | Approved policies covered; no false expected failures, state leaks, vacuous holds, skipped scenarios, or hidden production changes | A finding needs another owner or changes the approved spec |

Every slice stops after two unsuccessful fixes to the same check or an unresolved invariant. The lead asks before changing a model assignment, adding a production seam, expanding scope, or launching a device run. Budget overruns are not a stopping condition in this plan.

## Core scenario coverage

Reuse the first-song smoke for behavior 1. Add 14 scenarios: behaviors 2–13 and bug 5 symptoms B/C. Favourite/mute buttons and KEXP remain stretch goals, outside this execution.

| Scenario | Behavior or rule | Expected status before implementation |
|---|---|---|
| First song: title, artist, album, matching artwork | 1 | Existing passing smoke; its deliberate tracklist latency remains explicit |
| Second song, station detail never opened | 2, S1 | Bug 4 expected failure after reproduction |
| Second song, station detail open | 3, S1 | Not yet baselined |
| Feed one song behind: neither wrong album nor wrong art | 4, S2 | Not yet baselined; do not assume the bug 4 marker applies |
| Matching row lacks artwork: iTunes fallback | 5 | Not yet baselined |
| No matching artwork anywhere: station logo | 6, S1/S6 | Not yet baselined; use a previous-song setup to test stale-art removal |
| Pause/resume preserves resolved art | 7, S3 | Bug 5 symptom A expected failure after reproduction |
| Slow song-A art never publishes during song B | 8, S4 | Passing E7 hypothesis H3; strengthen the timing proof |
| Station switch drops old art | 9, S4 | Not yet baselined |
| Podcast switch drops radio art | 10, S4 | Not yet baselined; assert only our radio extension's interference, not upstream podcast behavior |
| Ad frame leaves title, artist, artwork unchanged | 11, S5 | Not yet baselined |
| CarPlay connection suppresses lyric album; disconnect restores album | 12, S7 | Not yet baselined; tag `@ios-only` where appropriate |
| Live/music markers survive every relevant write path | 13 | Not yet baselined |
| Cached tracklist at playback start preserves art | Bug 5 B, S3 | Expected failure after deterministic reproduction |
| Stop and replay same song resolves art again | Bug 5 C, S3 | Expected failure after reproduction |

The lead replaces the draft `carplay_artwork.feature` with approved scenario wording and adds files if that improves readability. Keep wording platform-neutral and preserve existing implemented vocabulary. Put `@ios @carplay` on each core scenario; the current parser does not propagate feature-level tags. Known-bug markers belong only in iOS code, never in shared tags.

## Expected-failure contract

- Key the iOS table by a unique, stable scenario name, not its generated line-number selector. Reject duplicate names and stale table entries.
- Associate each marker with a bug doc, symptom, and intended failing output check. Do not wrap the whole test in a catch-all expected failure.
- Use strict XCTest expected-failure semantics. A passing marked scenario must fail the run as unexpectedly passing.
- Keep playback readiness, undefined/ambiguous steps, feature loading, reset, and unexpected-network failures outside the accepted defect. Teardown must remain an ordinary failure path.
- For a scenario with several assertions, identify which approved-policy failure reproduces the bug and make that expectation explicit. Do not suppress later checks or classify all failures in that scenario as the same defect.
- Self-test expected failure, unexpected pass, unrelated failure, and stale/duplicate mapping behavior with synthetic fixtures. No production fix is needed to prove unexpected-pass handling.
- Baseline each new scenario without a marker first. For a newly reproduced app defect, record evidence in a bug doc before adding its marker. A flaky or broken harness is never a known app bug.

## Test boundary and lifecycle invariants

Use real playback and ICY input for song changes. Fake only the outside world. Do not mock `PlaybackManager`, `NowPlayingHelper`, or `MPNowPlayingInfoCenter`, or call setters to fabricate a passing snapshot. Existing test seams may establish connection state or reset a scenario; pure output-policy checks must state their narrower boundary.

The station-detail helper must retain the real controller, model appearance/disappearance, and cancel timers/tasks and release observers before reset. Account and lyric requests triggered by that controller need deterministic fixtures or an explicit stop; do not tolerate arbitrary network leaks on the simulator.

Use distinct station identities and track them through `HarnessReset.track(stationId:)`. Keep a single guard owner; do not start two `FakeWorld` instances that overwrite each other's process-wide interception. Model the additional station within the existing guarded world. Keep all stream and media fixture URLs loopback.

Use unique artwork URLs for different songs, even if their colors match. Check the station logo against the actual bundled logo sample rather than an arbitrary `rgb` literal. For stale-result tests, prove the request occurred and observe its completion before declaring success. Poll throughout the critical window: checking only the final snapshot cannot establish that stale art never appeared.

Cache-at-start and stop/replay are transitions **within one scenario**. Do not reset the dedupe key between its two playback starts. Prefer warming the cache through the real parser/fetch path. Do not depend on another scenario's cache or dedupe state.

Production edits are limited to the two approved exceptions: a DEBUG-only startup/rebuild barrier with narrowly scoped fork-owned support, and extracting the existing CarPlay disconnect body into a callable shared handler. Keep the unarmed/Release startup path and normal disconnect behavior unchanged. Contradictory existing unit tests and all app-bug fixes stay in `fix/stream-presentation`. Stop for any further production access.

## Brief and handoff for every delegate

Provide only shell `AGENTS.md`, worktree `AGENTS.md`, M13.2, this plan, harness/shared README, and the assigned focused files. Do not copy the full lead conversation or repeat repository-wide discovery.

Each brief must require:

1. Verify `PI_PROVIDER`, `PI_MODEL`, and OAuth readiness before editing. Never read or print credentials.
2. Edit only assigned paths. Fetch current documentation before changing third-party API calls.
3. Run focused checks under `make test_carplay` on the dedicated simulator, with bounded logs. Do not change Wi-Fi, sign in, or touch another simulator.
4. Preserve guard/reset ordering, use `republishWidgetState: false`, and never write ambient defaults directly. Playback's existing simulator-side effects remain documented.
5. No commit, push, branch change, delegation, app-bug fixes, or device tests. Production edits require explicit ownership of one of the two approved exceptions.
6. Return changed paths, passing setup evidence, the exact intended failing/passing assertion, focused test results, remaining uncertainty, and effective provider/model. Report usage if readily available; it is not a budget gate.

## Completion and approval

The lead runs `make format`, reviews formatter changes, and runs `make test_carplay` after adding the new suite/self-test classes to the default selection. Use `CARPLAY_TESTS` to select individual scenarios during development. Preserve existing Makefile edits and review only the M13.2 delta.

Run the full suite three consecutive times after integration, including independent fresh launches. Repeat startup and delayed-result scenarios individually to confirm they are not dependent on suite order. Validate ordinary test runs still skip destructive harness tests. Capture scenario-level results, expected-failure messages, and representative timelines; do not promise a fixed test total beyond the current 43 until new self-tests are registered.

A fresh Sol reviewer checks both shell contracts and the iOS diff. The lead addresses findings under explicit ownership transfer, reruns affected checks, and records remaining limitations.

**User checkpoint:** Approve this plan to start. After automated verification, manually check Simulator CarPlay through three real KCRW song changes and compare the display with the suite's observed fields. Record that result in M13.2. Ask for explicit commit approval after manual testing, per the iOS repo rules. Physical-device tests require separate consent because the harness clears the phone's local Up Next and changes listening stats.

**Approval:** the user accepted the [recorded manual discrepancies](../experiments/2026-10-08_m13_2_manual_carplay.md) as follow-up work and explicitly approved baseline commits. The user subsequently authorized the external review's documentation corrections, integration and closure preparation; the harness branch is now merged to `trunk`. **Closure approved:** the user approved extraction/deletion and deferred investigation of the unresolved integration setup failure ([bug 8](../bugs/bug_8.md)) on 2026-10-08. The isolated scenario and follow-up full run passed without code changes; neither establishes that failure's cause. Original automated checks and both exception reviews passed, but the manual Carnival lyric line prevents claiming full real-world S7 verification ([bug 7](../bugs/bug_7.md)). Lyric timing remains deferred. No app fix, device test or push is authorized. No budget or billing clarification is required.
