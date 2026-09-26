# M10 handoff — Stream Lab execution status

**Updated:** 2026-09-25  
**Branch:** menubar `feature/stream-monitoring-lab` at `a995f06`, Stream Lab package still untracked  
**Status:** Phases 1–3 are complete and a first unattended KCRW capture has run. Phase 4 still needs an attended session with human markers; no audible marker has been recorded yet.

This file tracks execution of [M10](milestone_10.md) without changing the milestone's scope after work began. The design and evidence model remain in the [stream-monitoring review](../../ios/architecture/reviews/stream-monitoring-review-2026-09-16.md).

## Current checkpoint

The Foundation-only package builds and its existing suite passes:

```bash
swift test --package-path pocket-radio-menubar/Tools/StreamLab
```

Last verified result: **42 tests, 0 failures** on 2026-09-25 (22 `StreamDiagnosticsTests`, 20 `StreamLabTests`).

This does not satisfy the M10 user checkpoint. KCRW has now been captured and replayed, but the run was muted and unattended, so no human marker exists and nobody confirmed what was audible.

## Execution plan

| Phase | Exit condition | Status |
|---|---|---|
| 1. Trace contract | Persisted events round-trip exactly; reducer failures, date policy, and privacy guarantees have regression coverage | Complete |
| 2. Executable wiring | `capture` and `replay` dispatch from the command line and report failures clearly | Complete |
| 3. Network-free integration | A local synthetic audio session produces a complete trace that replays offline | Complete |
| 4. Live observation | Short KCRW and KEXP captures include audible markers and replay without network access | Partial — KCRW transport observed unattended; markers and KEXP outstanding |
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

## Live observations (2026-09-25)

### Session: KCRW unattended transport check

- Stream: `https://streams.kcrw.com/e24_mp3` (from `curated_stations.json`); feed: station default.
- Muted, unattended, `--duration 150`. 145 events, ended `duration`, replayed offline cleanly.
- 136 playback observations, 5 feed responses, 0 feed failures, 0 markers.

**Finding 1 — KCRW delivers no usable timed metadata.** One metadata event arrived at
4.26s with an empty `values` array, and nothing after it. This independently confirms the
2026-06-03 `tools/stream-probe.py` finding ("KCRW ICY StreamTitle is permanently empty")
from the AVPlayer path rather than from a raw ICY reader. For KCRW, the tracklist feed is
the only title source, so lyric alignment cannot key off player metadata at all.

**Finding 2 — monotonic elapsed time freezes across a system suspend.** The Mac slept
during the run. `wallTime` advanced 201.905s while `elapsedSeconds` advanced 133.813s: a
68.094s gap, entirely in one step. The reducer accepted the trace, because the sequence
stayed ordered and elapsed time stayed non-decreasing. Nothing in the trace flagged it.

This qualifies decision 2 below. `elapsedSeconds` derives from `ProcessInfo.systemUptime`,
which does not advance while the system is suspended. It remains the right axis for
intervals *within* continuous playback, but any interval spanning a suspend under-reports
real time and must be read as a lower bound.

`ReplayReport` now prints a `clock` section comparing the two spans and naming every gap
over 2s, so a slept-through capture can no longer pass as a clean shorter one. Regression
coverage is in `ReplayReportTests`.

**Not established by this session:** audible behavior, song-boundary timing, feed-to-audio
lag, and anything about KEXP. The capture was muted and no one was listening.

## Decisions recorded

1. **Persisted UTC dates:** `wallTime`, `programDate`, and parsed `playedAt` use millisecond resolution for stable, language-neutral JSON round trips.
2. **Timing precision:** `elapsedSeconds`, media time, and metadata ranges retain full `Double` precision and are authoritative for interval analysis *within continuous playback*. Monotonic time freezes across a system suspend; see Finding 2 above and the `clock` section of a replay.
3. **Wall-clock correction:** replay allows wall time to move backward. Sequence and monotonic elapsed time define event ordering.
4. **Privacy guarantee:** standalone and embedded HTTP(S)/file URLs are redacted. Redaction remains defense in depth; review traces before sharing.

## Next bounded slice

Run Phase 4 as an attended session; this is the M10 user checkpoint and needs a person listening.

1. Run an unmuted KCRW capture on the intended output route, long enough for at least five
   song transitions, marking each one with `1`.
2. Exercise one pause/resume cycle with real time between them.
3. Repeat for KEXP, whose ICY metadata does carry track titles and so exercises a path KCRW cannot.
4. Disconnect the network and replay both traces.
5. Check the `clock` section first. If it reports untracked time, keep the machine awake and re-run
   before drawing any timing conclusion.
6. Compare human marker, feed receipt, and (for KEXP) metadata arrival on the elapsed axis.
   Report the distribution and worst case, not a single transition.

Keep the machine awake for the whole capture. `caffeinate -i` is the simplest guard.

## Evidence limits

- The 42 passing tests establish the synthetic trace contract, command dispatch, and clock-gap detection. They do not establish live station behavior.
- The regressions close the reproduced serialization and embedded-file-URL gaps; they do not establish audible drift or exhaustive privacy coverage.
- The local fixture and the KCRW session establish that the capture-to-replay path works against real audio. Neither establishes what a listener heard: both were muted and unattended.
- The local fixture's pause/resume markers were piped on stdin and landed 0ms apart, so no pause was ever observed in the playback samples. The KCRW session had no markers at all. Phase 4 still has to exercise a real pause.
- No account access or credential use has occurred. The only network contact was the public KCRW stream and tracklist endpoints.
- Feed timestamps, AVPlayer program dates, metadata arrivals, and human markers are observations with different uncertainty. None is automatically a song boundary.

## Repository guardrails

- The Stream Lab package is still untracked under `pocket-radio-menubar/Tools/`.
- The shell milestone/review documents are tracked on root `feature/stream-monitoring-lab`. Stage only explicit paths when recording status changes.
- iOS configurable-tab-bar work is merged and pushed: local and remote `trunk` are at `0751918f8`. M10 does not modify iOS or manage cleanup of the remaining feature-branch refs.
- Do not commit, merge, push, or delete Stream Lab branches until the manual checkpoint and explicit user approval.
- Do not edit `docs/menubar/current_milestone.md` through its symlink.
- Never place ACR credentials, signed URL parameters, account data, or unredacted local paths in docs, traces, tests, or logs.
