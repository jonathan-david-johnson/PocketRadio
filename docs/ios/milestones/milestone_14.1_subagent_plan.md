# iOS M14.1 subagent plan — KCRW playback clock feasibility

**Status**: IN PROGRESS — approved 2026-10-09 (UTC). Slices 0–5 and gate G1 are done, plus a slice 3 fix. Slices 6–7 remain. Actual usage is not yet totalled; slice reports show no budget stop.
**Scope**: [M14.1](milestone_14.1.md). Decisions D6–D8 are approved there.
**Route**: Anthropic only, matching the active session (`PI_PROVIDER=anthropic`, `PI_MODEL=claude-sonnet-5-5`).

## Gate checks

- **Rate snapshot:** last updated 2026-10-04. Today is 2026-10-09, so it is fresh (limit is 2026-11-04).
- **Billing mode:** not established from session metadata. Costs below are API list-price references only. Subscription-quota impact is **unknown**, and I make no savings claim.
- **Model access:** `claude-opus-5-5` and `claude-sonnet-5-5` were used by the M13.1 agent definitions. Slice 0 re-checks access with a one-line probe per role before any slice runs. Haiku is not used. Nothing here is mechanical enough to justify it.

## Decision and ownership

M14.1 is small in code but has two hard stops (the `currentDate()` gate and the locked run). The plan therefore runs **serially behind the gate** and splits the work by file ownership. No two writers ever touch the same file.

- The lead (this session) owns the worktree, `project.pbxproj`, every `xcodebuild` and device command, and all shell docs.
- Delegates write only the files named for their slice. They do not build for the device, commit, push, or edit `project.pbxproj`.
- D8 puts new app files under `podcasts/Main/` and new tests under `PocketCastsTests/Tests/`. Both are auto-registered, so delegates never need the project file.
- One build or test run at a time in the worktree. Delegates run `make test_staging ONLY_TESTING=...` for their own tests. The lead serializes them, so slices never run concurrently.
- Nothing is committed until you have tested and approved, per `pocket-radio-ios/AGENTS.md`.

## Where the work happens

| Area | Location |
|---|---|
| Plan and report | Shell `main`: this file, M14.1, `docs/ios/experiments/` |
| Code | `pocket-radio-ios`, branch `feature/kcrw-alignment` from `trunk` `6d8e5a9aa` |
| Worktree | `pocket-radio-ios-alignment/` |
| New agent files | `.pi/agents/m14-sonnet.md` (`anthropic/claude-sonnet-5-5:medium`), `m14-sonnet-high.md` (`anthropic/claude-sonnet-5-5:high`), `m14-opus.md` (`anthropic/claude-opus-5-5:high`, read-only). Created in slice 0 from the `m13-*` files, with M13 paths replaced by M14.1 paths. Not created yet. |
| Shell changes | Docs and the three role definitions only |

## Slices

Token figures are **advisory** aggregates, not enforced caps. Input counts all uncached input plus cache reads and writes across turns, including repeated context, file reads, and test output. Output includes reasoning. Past runs overshot forecasts, so each slice reports its actual usage and any overrun.

| # | Slice and owner | Model | Files owned | Acceptance check | Input | Output | Stop or escalate |
|---|---|---|---|---|---:|---:|---|
| 0 | **Setup.** Lead | `claude-sonnet-5-5` (this session) | Worktree; the four untracked files copied in; `project.pbxproj` (add the `StreamSession` package, app target only); three `.pi/agents` files; brief for each slice | Worktree on `feature/kcrw-alignment`; `../contracts` and `../.githooks` resolve; empty simulator build passes; `StreamSession` imports in the app; each role answers a provider/model probe; seam for the Debug readout chosen (D8) | 600k | 8k | Package will not link; model access fails. Ask before changing route. |
| 1 | **Probe.** Writer | `m14-sonnet-high` | `podcasts/Main/Alignment/KCRWAlignmentConfiguration.swift`, `.../AlignmentProbeLog.swift`, `.../ObserveSwitchStore.swift` (all new); the `createPlayerItem` override in `PlaybackItem.swift` (a few lines); a minimal sample hook in `DefaultPlayer.swift`; tests `PocketCastsTests/Tests/Alignment/EligibilityTests.swift`, `EndpointResolutionTests.swift` | Behaviors 1 and 2 red then green. Probe logs `[align]` lines with `currentDate()`, media time, rate, and status once per second. With the switch off, resolution matches `trunk`. | 700k | 14k | Two failed fixes on one check; need for any file outside this list; unclear seam in `DefaultPlayer`. |
| **G1** | **Device probe.** Lead and you | none | none | Two-minute run on "Jonathan iPhone". `currentDate()` non-nil within 15 s of `.playing`. Rate 1.0. | 150k | 3k | **If nil: stop.** Report. Slices 2–6 are cancelled. You decide next steps. |
| 2 | **Feed decoder and client.** Writer | `m14-sonnet` | `.../KCRWFeedDecoder.swift`, `.../KCRWFeedClient.swift` (new); `Tests/Alignment/KCRWFeedDecoderTests.swift`; a fixture under `Tests/Alignment/Fixtures/` | Behavior 3. Ids, breaks, null titles, fractional seconds decode. Wrong shape, oversize body, and too many rows reject. No network in tests. | 350k | 7k | Fixture shape in doubt; compare to the menubar `StationFeed.swift` (read only) and ask. |
| 3 | **Monitor summary.** Writer | `m14-sonnet` | `.../AlignmentMonitorSummary.swift` (new); `Tests/Alignment/AlignmentMonitorSummaryTests.swift` | Behavior 8. Sample and poll gaps, attempt counts, clock-invalid intervals, min/max rate, and per-5-minute speed ratio excluding stalls. Counts poll **attempts** and reports failures separately (D7). | 300k | 6k | Ambiguity about what counts as a stall; return the question. |
| 4 | **Session, poller, wiring.** Writer | `m14-sonnet-high` | `.../RadioPlaybackSession.swift` (new, ported by copy without the recorder); small teardown and create calls in `DefaultPlayer.swift`; `Tests/Alignment/RadioPlaybackSessionTests.swift` | Behaviors 4–7 and 9. No early selection; explicit unavailable state; same-item and generation guards; one in-flight request; `stop()` cancels; no write to `MPNowPlayingInfoCenter`. Poller is an injectable scheduler, so the fallback (drive from the 1 s observer) can be swapped in without a rewrite. | 1,200k | 25k | Any invariant in behaviors 4–7 unresolved after two tries; need to edit `PlaybackManager` or `NowPlayingHelper` (out of scope). |
| 5 | **Debug readout and switch.** Writer | `m14-sonnet` | `.../AlignmentObserveView.swift` (new); one-line hook at the seam chosen in slice 0 | Off / Observe switch and live fields. Hidden in Release. Default Off. Uses the injected defaults store, never `UserDefaults.standard`. | 500k | 10k | Seam needs more than a few lines in an existing file; stop and ask. |
| 6 | **Independent review.** Reviewer | `m14-opus` (read-only) | None. `git diff`, `grep`, `ls` only | Reviews behaviors 1–10 against M14.1: guards, lifecycle, nothing published, D6 gating, no `UserDefaults.standard`, no change outside the file lists. Reports defects with file and line. | 450k | 9k | Defect needing ownership transfer: report, do not fix. |
| 7 | **Integration and device runs.** Lead and you | `claude-sonnet-5-5` | Fixes the reviewer finds; report in `docs/ios/experiments/` | Full unit pass; M13.2 CarPlay suite with the switch off (behavior 10); then E1–E4 on the device, including 30 minutes locked. | 900k | 12k | Any gate G1–G3 failure: stop, write the report, decide with you. |
| | **Total** | | | | **4,700k** | **94k** | |
| | **Reserve, not authorized** | `m14-opus` for a failed slice | One reassigned slice | Needs your approval | 600k | 12k | Stop when spent |

## Order and why

1. Slice 0, then slice 1, then **G1**. Nothing else is built until the clock proves usable on the phone. If it fails, I have spent about 1.5M input tokens, not 4.7M.
2. After G1: slices 2 and 3 are pure and independent, so they could run in parallel. I run them one after the other, because they share one worktree and one build. The saving is minutes, and it removes the risk of build collisions.
3. Slice 4 follows slice 2 because it consumes the decoder and client types. Slice 5 follows slice 4 because it reads session fields.
4. Review comes after all writers finish, with no implementation overlap.
5. E2 (30 minutes locked) is your hand-run and cannot be sped up.

## Model choices

- **Writers use Sonnet, not Opus.** Slices 2, 3, and 5 are narrow, well-specified, and test-driven, so `medium` is enough. Slices 1 and 4 get `high` because the probe sits in `DefaultPlayer` and the session carries the concurrency invariants.
- **Review uses Opus.** It is a separate, stronger pass, and read-only. It does not run builds.
- **No Haiku.** The slices have no purely mechanical copy work. The one near-copy (the session port) still needs adaptation to iOS.
- **No Fable.** At $10 per million input tokens and $50 per million output tokens, I cannot justify it for a diff this size.
- **Everything on Opus** would roughly double the writer cost for slices 2, 3, and 5 with no clear accuracy gain. When in doubt, we escalate a failed slice to Opus through the reserve.

## Cost reference (API list price only)

**Assumptions:** billing mode unknown; about 90 % of aggregate input is cache read; cache writes ignored; Sonnet is $2.00 uncached, $0.20 cached, $10.00 output per million tokens; Opus is $4.00, $0.20, $20.00. These are **not your actual cost**. Subscription-quota impact is unknown.

| Group | Input | Output | List-price reference |
|---|---:|---:|---:|
| Sonnet slices 0–5, 7 | 4,250k | 85k | about $2.5 |
| Opus review (slice 6) | 450k | 9k | about $0.45 |
| **Total** | **4,700k** | **94k** | **about $3, plausibly up to $6 if caching is weaker or the work overshoots** |

The G1 stop would cap spending at about $1.

## Completion check

- Rate snapshot is fresh (2026-10-04 vs. 2026-10-09).
- Every delegate is Anthropic, matching the active provider. Access is re-verified in slice 0.
- Every slice has a file list, token budget, acceptance check, and stopping condition.
- Costs name their units and assumptions. Quota impact is marked unknown.
- Implementation, commits, and device testing stay behind your approval, per `pocket-radio-ios/AGENTS.md`.
