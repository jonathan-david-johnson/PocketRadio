# M10 handoff — Stream Lab execution status

**Updated:** 2026-09-17  
**Branch:** menubar `feature/stream-monitoring-lab` at `a995f06`  
**Status:** Trace-contract hardening in progress. The executable and live experiment are not ready.

This file tracks execution of [M10](milestone_10.md) without changing the milestone's scope after work began. The design and evidence model remain in the [stream-monitoring review](../../ios/architecture/reviews/stream-monitoring-review-2026-09-16.md).

## Current checkpoint

The Foundation-only package builds and its existing suite passes:

```bash
swift test --package-path pocket-radio-menubar/Tools/StreamLab
```

Last verified result: **7 tests, 0 failures** on 2026-09-17.

This does not satisfy the M10 user checkpoint. `Sources/StreamLab/StreamLab.swift` is still a stub, no capture or replay command has run end to end, and live AVPlayer behavior has not been measured.

## Execution plan

| Phase | Exit condition | Status |
|---|---|---|
| 1. Trace contract | Persisted events round-trip exactly; reducer failures, date policy, and privacy guarantees have regression coverage | In progress |
| 2. Executable wiring | `capture` and `replay` dispatch from the command line and report failures clearly | Not started |
| 3. Network-free integration | A local synthetic audio session produces a complete trace that replays offline | Not started |
| 4. Live observation | Short KCRW and KEXP captures include audible markers and replay without network access | Not started |
| 5. Measurement report | Results separate player, feed, wall-clock, media-clock, and human-marker evidence; limitations and next policy decision are recorded | Not started |
| 6. Manual checkpoint | User runs the documented scenario and approves the result before any commit or merge | Not started |

## Milestone behavior status

### 1. Trace write, read, and replay

**Complete:**

- Happy-path trace write/read and snapshot replay.
- Explicit start/end requirement on replay.
- Millisecond normalization of root `TraceEvent.wallTime`.
- Exact root-event round trip for unaligned `Date()` inputs.
- Separate player-metadata and feed observations.

**Still required:**

- Regression tests for wrong session ID, backward sequence, backward elapsed time, unsupported schema, events after stop, and missing start/end.
- A failing regression for fractional `PlaybackObservation.programDate`; the root-date fix does not normalize nested dates.
- A decision and regression for backward wall-clock corrections. Recommendation: allow wall-clock adjustment while sequence and monotonic elapsed time remain authoritative.
- Review persisted `FeedEntry.playedAt` under the chosen nested-date policy.

### 2. Bounded, private trace files

**Complete:**

- Exclusive file creation; an existing trace is not overwritten.
- Owner-only `0600` file permissions.
- A 32 MiB default limit and explicit incomplete-trace failure.
- Standalone HTTP(S) and file URL redaction.
- Embedded HTTP(S) URL redaction in metadata.

**Still required:**

- Embedded `file://` URLs currently survive inside metadata. Add a failing regression and fix it before sharing captures.
- Recheck error paths so write or capacity failures cannot appear complete.

### 3. Station-feed observations

**Complete:**

- KEXP track, airbreak, provider ID, fractional timestamp, and artwork-URL coverage.
- Parser code preserves source order and does not declare feed-top audible.
- Parser code handles KCRW music and `[BREAK]` observations.

**Still required:**

- Add a synthetic KCRW regression. KCRW behavior is implemented but not covered by the package suite.
- Decide the persisted nested-date policy before claiming exact identity for `playedAt`.

### 4. Replay rejection and metadata ranges

**Complete:**

- The reducer implements schema, sequence, elapsed-time, session, lifecycle, and completion checks.
- Metadata observations retain media ranges and remain separate from feed candidates.

**Still required:**

- Lock each rejection behavior with the tests listed in behavior 1.
- Add multiple-metadata-item/range coverage.
- Record the approved wall-clock correction policy rather than assuming backward wall time is invalid.

### 5. Local and live capture

**Complete:**

- `CaptureSession`, argument parsing, AVPlayer observation, feed polling, markers, and shutdown paths compile.

**Still required:**

- Wire the executable entry point.
- Exercise capture and replay end to end.
- Run a network-free local fixture.
- Run manual KCRW and KEXP observations using explicit stream URLs.
- Compare evidence without treating feed-top or first metadata arrival as an audible boundary.

## Open decisions

1. **Root wall-time precision:** confirm that milliseconds are sufficient for external correlation. Use `elapsedSeconds` and media time for timing analysis.
2. **Nested persisted dates:** choose a policy for `programDate` and `playedAt` that preserves the required round-trip contract. Do not silently quantize every date field.
3. **Wall-clock correction:** decide whether replay permits wall time to move backward. The current reducer permits it; the recommendation is to preserve that behavior and document monotonic elapsed time as authoritative.
4. **Privacy guarantee:** fix embedded file-URL redaction or explicitly narrow the guarantee before traces leave the local machine.

## Next bounded slice

Complete Phase 1 before executable wiring:

1. Add the failing fractional-`programDate` round-trip and replay regression.
2. Fix the nested-date contract without weakening equality assertions.
3. Add reducer rejection tests and a regression for the approved wall-clock behavior.
4. Add and fix the embedded-file-URL privacy regression.
5. Add KCRW feed-parser coverage.
6. Rerun the complete package suite and record the result here.

Then wire `capture` and `replay` according to the package [runbook](../../../pocket-radio-menubar/Tools/StreamLab/README.md).

## Evidence limits

- The seven passing tests do not cover the gaps above.
- Synthetic probes established serialization and redaction contract failures, not audible drift or broad privacy coverage.
- No AVPlayer capture, station contact, account access, or credential use occurred during the review.
- Feed timestamps, AVPlayer program dates, metadata arrivals, and human markers are observations with different uncertainty. None is automatically a song boundary.

## Repository guardrails

- The Stream Lab package is still untracked under `pocket-radio-menubar/Tools/`.
- The shell milestone/review documents are also untracked or mixed with unrelated documentation changes. Stage only explicit paths.
- iOS configurable-tab-bar work is merged and pushed: local and remote `trunk` are at `0751918f8`. M10 does not modify iOS or manage cleanup of the remaining feature-branch refs.
- Do not commit, merge, push, or delete Stream Lab branches until the manual checkpoint and explicit user approval.
- Do not edit `docs/menubar/current_milestone.md` through its symlink.
- Never place ACR credentials, signed URL parameters, account data, or unredacted local paths in docs, traces, tests, or logs.
