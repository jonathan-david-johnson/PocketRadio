# M10 handoff — Stream Lab execution status

**Updated:** 2026-09-25  
**Branch:** menubar `feature/stream-monitoring-lab` at `a995f06`, Stream Lab package still untracked  
**Status:** Phases 1–3 are complete. Four unattended KCRW captures have run, yielding five findings; the headline is that KCRW feed publish lag is variable and cannot be corrected with a fixed offset. Phase 4 still needs an attended session with human markers; nothing yet ties any observation to audible reality.

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

### Session: KCRW caffeinated 7-minute capture

- Same stream and feed. Muted, unattended, `caffeinate -is`, `--duration 420`, `--feed-interval 30`.
- 420.009s monotonic against 420.005s wall: **no clock gap**. `caffeinate -is` is sufficient, and
  the `clock` section confirms a clean run rather than leaving it assumed.
- 410 playback observations, 14 feed responses, 0 failures, no stalls or time jumps.

**Finding 3 — zero timed-metadata events across the whole run.** The two earlier KCRW runs each
produced exactly one metadata group with an empty `values` array; this one produced none at all.
So KCRW player metadata is not merely empty but inconsistent between sessions. Any design that
waits on an AVPlayer metadata callback for KCRW can wait forever. This strengthens Finding 1.

**Finding 4 — the KCRW tracklist feed publishes well after an entry's own stated airtime.** *(Refined by Finding 5 below: the lag is variable, not a fixed 29–60s.)*
One transition was observed with a 30s poll interval:

| Evidence | Wall time relative to the new entry's stated airtime |
|---|---|
| Entry's own `datetime` (`2026-09-25T18:16:36-07:00`) | +0s by definition |
| Last poll that did **not** yet contain the entry | +29.4s |
| First poll that **did** contain the entry | +59.6s |

The publish therefore happened between +29.4s and +59.6s. The 30s poll interval is what leaves a
30s window; a 10s interval would tighten it to ~10s.

This is the most consequential observation for the lyric-alignment policy M10 exists to inform.
For KCRW there is no player metadata at all, so the feed is the only title source, and that source
lags its own stated airtime by at least half a minute. Feed arrival cannot be used as a song-start
signal without correcting for that lag.

**What this does not establish.** One transition is not a distribution. The semantics of KCRW's
`datetime` field are unverified: it may be a logging or scheduling time rather than the audible
start, which would change the interpretation entirely. The capture was muted and unattended, so
the listener's buffered audio position was never tied to any of these timestamps. Nothing here
measures the offset between broadcast and what a listener hears.

### Session: KCRW 15-minute capture at a 10s poll interval

- Same stream and feed. Muted, unattended, `caffeinate -is`, `--duration 900`, `--feed-interval 10`.
- 900.025s monotonic against 900.090s wall: no clock gap. 874 playback observations,
  89 feed responses, 0 failures, 3 feed transitions.
- One metadata event, again with an empty `values` array. Across four KCRW sessions the count
  has been 1, 0, 1, 1 and the array has been empty every time. Findings 1 and 3 hold.

**Finding 5 — publish lag is variable, not a fixed offset. This supersedes Finding 4.**
Tightening the poll interval to 10s produced three more brackets, and they do not agree:

| Transition | Poll interval | Published, relative to claimed airtime |
|---|---|---|
| Comes Back to You | 30s | +29.4s to +59.6s |
| Breathless | 10s | **+7.4s to +17.7s** |
| Every Single Weekend | 10s | +33.2s to +43.5s |
| Don't You Want Me (with Cat Power) | 10s | +29.2s to +39.4s |

The intersection of all four brackets is empty, so no single lag value explains them. Three
pairs are provably disjoint: "Breathless" published no later than +17.7s, while the other
three published no earlier than +29.2s. The lag genuinely differs between transitions, across
an observed range of roughly 7s to 60s.

**Consequence for the alignment policy.** KCRW offers no player metadata at all, so the feed is
the only title source; and the feed's publish lag cannot be corrected with a constant offset,
because it is not constant. A fixed-offset correction was the obvious cheap policy and these
four transitions rule it out. Any KCRW alignment either tolerates tens of seconds of error,
or needs a signal other than feed arrival.

**What this still does not establish.** Four transitions from one stream variant on one evening
is not a distribution; it is enough to disprove a constant, not to characterise the variation.
The meaning of KCRW's `datetime` field remains unverified and the whole interpretation rests on
it. Every session was muted and unattended, so the offset between any of these timestamps and
what a listener hears is still entirely unmeasured.

## Decisions recorded

1. **Persisted UTC dates:** `wallTime`, `programDate`, and parsed `playedAt` use millisecond resolution for stable, language-neutral JSON round trips.
2. **Timing precision:** `elapsedSeconds`, media time, and metadata ranges retain full `Double` precision and are authoritative for interval analysis *within continuous playback*. Monotonic time freezes across a system suspend; see Finding 2 above and the `clock` section of a replay.
3. **Wall-clock correction:** replay allows wall time to move backward. Sequence and monotonic elapsed time define event ordering.
4. **Privacy guarantee:** standalone and embedded HTTP(S)/file URLs are redacted. Redaction remains defense in depth; review traces before sharing.

## Next bounded slice

**Run the attended session (the M10 user checkpoint).** This is now the only remaining blocker
on a policy decision, and it cannot be automated:

1. Unmuted KCRW capture on the intended output route, long enough for five or more transitions.
2. Mark each clearly heard song change with `1`; use `2` only for a recognizable lyric landmark.
3. Exercise one pause/resume cycle with real time between the two.
4. Repeat for KEXP, whose ICY metadata does carry titles and so exercises a path KCRW cannot.
5. Disconnect the network and replay both traces.
6. Compare the human marker against the feed transition bracket the replay already prints.

`caffeinate -is` for the whole capture, and read the `clock` section before trusting any timing.

The attended session is what converts Finding 5 from "the feed lags its own claimed airtime by a
variable amount" into "the feed lags what the listener hears by X", which is the number an
alignment policy actually needs. Until then the feed-to-audio offset is unmeasured.

Also still unresolved: what KCRW's `datetime` field means. Findings 4 and 5 both depend on it.
Worth a direct check against the station's API documentation or a maintainer before Phase 5.

## Evidence limits

- The 47 passing tests establish the synthetic trace contract, command dispatch, clock-gap detection, and publish-lag bracketing. They do not establish live station behavior.
- The regressions close the reproduced serialization and embedded-file-URL gaps; they do not establish audible drift or exhaustive privacy coverage.
- The local fixture and the four KCRW sessions establish that the capture-to-replay path works against real audio and a live station. None establishes what a listener heard: all were muted and unattended.
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
