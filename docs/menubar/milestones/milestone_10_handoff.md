# M10 handoff — Stream Lab execution status

**Updated:** 2026-09-25  
**Branch:** menubar `feature/stream-monitoring-lab` at `a995f06`, Stream Lab package still untracked  
**Status:** Phases 1 and 2 are complete. `capture` and `replay` dispatch and run; Phase 3 is a network-free local audio fixture. No live station has been observed.

This file tracks execution of [M10](milestone_10.md) without changing the milestone's scope after work began. The design and evidence model remain in the [stream-monitoring review](../../ios/architecture/reviews/stream-monitoring-review-2026-09-16.md).

## Current checkpoint

The Foundation-only package builds and its existing suite passes:

```bash
swift test --package-path pocket-radio-menubar/Tools/StreamLab
```

Last verified result: **40 tests, 0 failures** on 2026-09-25 (22 `StreamDiagnosticsTests`, 18 `StreamLabTests`).

This does not satisfy the M10 user checkpoint. Capture and replay now run, but every trace exercised so far is synthetic: no station has been contacted and no audible marker has been recorded against real audio.

## Execution plan

| Phase | Exit condition | Status |
|---|---|---|
| 1. Trace contract | Persisted events round-trip exactly; reducer failures, date policy, and privacy guarantees have regression coverage | Complete |
| 2. Executable wiring | `capture` and `replay` dispatch from the command line and report failures clearly | Complete |
| 3. Network-free integration | A local synthetic audio session produces a complete trace that replays offline | Next |
| 4. Live observation | Short KCRW and KEXP captures include audible markers and replay without network access | Not started |
| 5. Measurement report | Results separate player, feed, wall-clock, media-clock, and human-marker evidence; limitations and next policy decision are recorded | Not started |
| 6. Manual checkpoint | User runs the documented scenario and approves the result before any commit or merge | Not started |

## Milestone behavior status

### 1. Trace write, read, and replay

**Complete:**

- Happy-path trace write/read and snapshot replay.
- Explicit start/end requirement on replay.
- Millisecond normalization and exact round trips for `TraceEvent.wallTime`, `PlaybackObservation.programDate`, and parsed `FeedEntry.playedAt`.
- Full precision retained for monotonic elapsed time, media time, and metadata ranges.
- Separate player-metadata and feed observations.
- Regression coverage for wrong session, duplicate start, sequence gaps/reordering, backward elapsed time, invalid wall time, unsupported schema, events after end, and missing start/end.
- Corrupt JSON reports its line and a missing final newline is identified as possible truncation.
- Backward wall-clock corrections are explicitly allowed while sequence and monotonic elapsed time remain authoritative.

### 2. Bounded, private trace files

**Complete:**

- Exclusive file creation; an existing trace is not overwritten.
- Owner-only `0600` file permissions.
- A 32 MiB default limit and explicit incomplete-trace failure.
- Standalone HTTP(S) and file URL redaction.
- Embedded HTTP(S) and `file://` URL redaction in metadata.
- Regression coverage that size-limit failures leave a trace explicitly incomplete.

### 3. Station-feed observations

**Complete:**

- KEXP track, airbreak, provider ID, fractional timestamp, and artwork-URL coverage.
- KCRW music, `[BREAK]`, source-time, and artwork-URL coverage.
- Parser code preserves source order and does not declare feed-top audible.
- Parsed provider dates normalize to milliseconds and round-trip exactly.

### 4. Replay rejection and metadata ranges

**Complete:**

- The reducer's schema, sequence, elapsed-time, session, lifecycle, and completion checks have direct regression coverage.
- Multiple metadata items and their media ranges remain observable.
- Wall time is finite correlation evidence but not an ordering constraint.

### 5. Local and live capture

**Complete:**

- `CaptureSession`, argument parsing, AVPlayer observation, feed polling, markers, and shutdown paths compile.
- `LabDispatch.parse` separates command parsing from running, so dispatch is covered without opening a stream or contacting a feed.
- `capture`, `replay`, `help`, unknown commands, and missing or invalid options all dispatch and report correctly.
- `ReplayReport` renders a deterministic offline timeline, per-kind counts, and the evidence boundary.
- Failures are one line with a nonzero status: `2` for usage, `1` otherwise.
- The whole path ran end to end offline: `capture` against a missing local fixture wrote a complete trace, and `replay` rendered it. Stream URL redaction held (`file:///<local-audio>`).
- A trace hand-written in Python replayed correctly, which checks the language-neutral JSON contract from outside the Swift encoder.

**Still required:**

- Run a network-free local fixture that actually plays audio, with pause/resume markers.
- Run manual KCRW and KEXP observations using explicit stream URLs.
- Compare evidence without treating feed-top or first metadata arrival as an audible boundary.

## Decisions recorded

1. **Persisted UTC dates:** `wallTime`, `programDate`, and parsed `playedAt` use millisecond resolution for stable, language-neutral JSON round trips.
2. **Timing precision:** `elapsedSeconds`, media time, and metadata ranges retain full `Double` precision and are authoritative for interval analysis.
3. **Wall-clock correction:** replay allows wall time to move backward. Sequence and monotonic elapsed time define event ordering.
4. **Privacy guarantee:** standalone and embedded HTTP(S)/file URLs are redacted. Redaction remains defense in depth; review traces before sharing.

## Next bounded slice

Run Phase 3, the network-free local fixture, per the package [runbook](../../../pocket-radio-menubar/Tools/StreamLab/README.md) § Experiment protocol step 2:

1. Produce a local synthetic or rights-cleared audio fixture. Do not use station audio.
2. Capture it with `--no-feed`, exercising one pause/resume cycle and at least one marker.
3. Confirm the trace has one start, player state samples, both markers, and one explicit end.
4. Disable network access and confirm `replay` still succeeds.
5. Confirm replay snapshots match the captured event sequence.
6. Rerun the complete package suite and record the result here.

A plain local audio file validates the playback-signal path only. It cannot validate Icecast metadata interleaving, HLS program-date behavior, or live feed timing; those wait for Phase 4.

## Evidence limits

- The 40 passing tests establish the synthetic trace contract and command dispatch; they do not validate live AVPlayer or station behavior.
- The regressions close the reproduced serialization and embedded-file-URL gaps; they do not establish audible drift or exhaustive privacy coverage.
- The only AVPlayer run so far failed immediately on a deliberately absent local file (`AVFoundationErrorDomain -11800`). It proves the capture-to-replay path, not that audio playback was observed.
- No station contact, account access, or credential use has occurred.
- Feed timestamps, AVPlayer program dates, metadata arrivals, and human markers are observations with different uncertainty. None is automatically a song boundary.

## Repository guardrails

- The Stream Lab package is still untracked under `pocket-radio-menubar/Tools/`.
- The shell milestone/review documents are tracked on root `feature/stream-monitoring-lab`. Stage only explicit paths when recording status changes.
- iOS configurable-tab-bar work is merged and pushed: local and remote `trunk` are at `0751918f8`. M10 does not modify iOS or manage cleanup of the remaining feature-branch refs.
- Do not commit, merge, push, or delete Stream Lab branches until the manual checkpoint and explicit user approval.
- Do not edit `docs/menubar/current_milestone.md` through its symlink.
- Never place ACR credentials, signed URL parameters, account data, or unredacted local paths in docs, traces, tests, or logs.
