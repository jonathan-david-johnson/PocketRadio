# M10 handoff — Stream Lab execution status

**Updated:** 2026-09-30
**Branch:** menubar `feature/stream-monitoring-lab` at `a995f06`, Stream Lab package still untracked  
**Status:** Phases 1–3 and short attended captures on both stations are complete. Four unattended MP3 and two attended AAC/HLS KCRW captures, plus one attended KEXP AAC capture, are retained. KCRW's nine identified audible changes support a ~160s media-date-to-feed mapping for that HLS endpoint. KEXP supplies ICY titles, but the first arrival can precede audibility and its feed can lag or lead this listener. KEXP has only three marked song changes plus an airbreak, so no KEXP timing policy is established. User approval to commit and push Stream Lab and the M10/M11 docs was received on 2026-09-30; merge approval remains separate. See Findings 7–9.

This file tracks execution of [M10](milestone_10.md) without changing the milestone's scope after work began. The design and evidence model remain in the [stream-monitoring review](../../ios/architecture/reviews/stream-monitoring-review-2026-09-16.md).

## Current checkpoint

The Foundation-only package builds and its existing suite passes:

```bash
swift test --package-path pocket-radio-menubar/Tools/StreamLab
```

Last verified result: **52 tests, 0 failures** on 2026-09-30 (22 `StreamDiagnosticsTests`, 30 `StreamLabTests`). The new synthetic regression covers untitled KEXP airbreak transitions; this suite does not test the proposed M11 selection policy.

The user ran and annotated two unmuted KCRW AAC/HLS sessions and one KEXP AAC session with real pause/resume cycles. All three traces replay offline without a clock gap. KCRW has nine identified song changes; KEXP has three song markers and an airbreak marker, with pre-roll and a stall. The short two-station capture checkpoint has been exercised; KEXP has not met the five-song threshold for a timing distribution. User approval to commit and push was received on 2026-09-30; merge approval remains separate.

## Execution plan

| Phase | Exit condition | Status |
|---|---|---|
| 1. Trace contract | Persisted events round-trip exactly; reducer failures, date policy, and privacy guarantees have regression coverage | Complete |
| 2. Executable wiring | `capture` and `replay` dispatch from the command line and report failures clearly | Complete |
| 3. Network-free integration | A local synthetic audio session produces a complete trace that replays offline | Complete |
| 4. Live observation | Short KCRW and KEXP captures include audible markers and replay without network access | Complete for the short two-station capture; KEXP has only three song transitions, not a timing distribution |
| 5. Measurement report | Results separate player, feed, wall-clock, media-clock, and human-marker evidence; limitations and next policy decision are recorded | KCRW and preliminary KEXP reports recorded; selection-policy validation is proposed separately in M11 |
| 6. Manual checkpoint | User runs the documented scenario and approves the result before any commit or merge | Two-station scenario exercised by user; commit/push approval received 2026-09-30; merge approval remains separate |

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
- `ReplayReport` renders a deterministic offline timeline, per-kind counts, and the evidence boundary. Its feed-transition summary preserves untitled KEXP airbreaks (regression added 2026-09-30).
- Failures are one line with a nonzero status: `2` for usage, `1` otherwise.
- The whole path ran end to end offline: `capture` against a missing local fixture wrote a complete trace, and `replay` rendered it. Stream URL redaction held (`file:///<local-audio>`).
- A trace hand-written in Python replayed correctly, which checks the language-neutral JSON contract from outside the Swift encoder.
- A network-free local fixture played and replayed; its piped pause/resume markers were simultaneous, so real pause behavior was tested instead in the attended KCRW HLS sessions.
- Two user-attended KCRW HLS sessions captured audible markers and real pauses and replayed offline. Feed-top and heard changes are reported separately.

**Still required:**

- Obtain separate user approval before any merge or production playback change.
- In the separate approved M11 offline slice, validate an HLS media-clock selection rule against replay fixtures and the intended production playback route. Obtain five or more named KEXP song transitions in a later session **only if** selecting a KEXP timing policy; the present short KEXP capture does not support one.

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

**Finding 4 — the KCRW tracklist feed publishes after an entry's own stated airtime.** *(The 29–60s bracket below is uncorrected for cache age; Finding 6 supersedes it with an upper bound only.)*
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

**Finding 5 — WITHDRAWN. Read Finding 6 instead.** *This claimed publish lag was variable and*
*that a fixed-offset policy was ruled out. Both conclusions were wrong: they came from treating*
*stale cached responses as current observations. The table below is kept because the raw receipt*
*times are real; the inference drawn from them was not.*
Tightening the poll interval to 10s produced three more brackets, and they do not agree:

| Transition | Poll interval | Published, relative to claimed airtime |
|---|---|---|
| Comes Back to You | 30s | +29.4s to +59.6s |
| Breathless | 10s | **+7.4s to +17.7s** |
| Every Single Weekend | 10s | +33.2s to +43.5s |
| Don't You Want Me (with Cat Power) | 10s | +29.2s to +39.4s |

~~The intersection of all four brackets is empty, so no single lag value explains them.~~ This
reasoning assumed each poll's response described the feed at the moment it was received. It did
not: the responses were cached and often stale. See Finding 6.

**Finding 6 — the feed is cached with a ~60s refresh, which explains the apparent variability.**

Every feed response carries `cache-control: max-age=15, public, must-revalidate`, and the `age`
header cycles 0 → ~51s and then resets. So the effective refresh is about 60s, not the advertised
15s. In all four transitions across s2 and s3, the new entry was first seen on a cache-fresh
response (`age` header absent), and the preceding poll's response was already 30–51s stale.

That invalidates every lower bound in Finding 5's table. A response that is 51s stale cannot show
an entry published 40s ago, so its failure to show the entry proves nothing about publication
time. Correcting each bound for `age` gives only upper bounds:

| Transition | Origin held the entry by |
|---|---|
| Breathless | claimed airtime **+17.7s** |
| Don't You Want Me (with Cat Power) | +39.4s |
| Every Single Weekend | +43.5s |
| Comes Back to You | +59.6s |

A single constant publish lag anywhere in 0s..+17.7s is consistent with all four. **The
fixed-offset policy is therefore not ruled out** — Finding 5 said it was, and that was wrong.

**What does survive, and is actionable.** A client's *feed receipt* delay is publish lag *plus*
up to ~60s of cache staleness, and it cannot do better by polling harder: a cached feed cannot
reveal a change sooner than it refreshes. The s3 run made 89 requests to learn what roughly 15
would have. The original claim that this necessarily bounds **playback-aligned title timing** was
too broad: later attended HLS sessions found entries available well before this listener heard
them. A measured player-media clock mapping can defer selection until that buffered audio reaches
the entry, provided the mapping is valid. See Findings 7–8 below.

**What this does not establish.** Only upper bounds; the publish lag itself is unmeasured and this
endpoint cannot reveal it, because the cache floor exceeds the quantity of interest. Measuring it
needs a cache-bypassing request or a station-side answer. The meaning of KCRW's `datetime` field
remains unverified and the whole interpretation rests on it. Every session was muted and
unattended, so the offset between any of these timestamps and what a listener hears is still
entirely unmeasured *by those unattended MP3 sessions*; the later attended HLS measurements are
reported in Finding 7.

**Process note.** Finding 5 was committed before the `age` header was examined, and the header was
already being captured in the trace the whole time. The evidence to catch the error was in hand
before the wrong conclusion was published.

### Attended KCRW AAC/HLS sessions (2026-09-26)

Full setup, replayable traces, nine paired transitions, a missed marker, and pause/commercial
annotations: [attended-session record](../experiments/2026-09-26_kcrw_hls_attended.md). This uses
`https://streams.kcrw.com/e24_aac/playlist.m3u8` with a five-entry feed and does **not** calibrate
the earlier `e24_mp3` endpoint or an unrecorded output route. Both runs replay with zero player
timed-metadata events, zero feed failures, and no clock gap.

**Finding 7 — the listener's HLS media clock provides a stable estimated feed-to-audio mapping.**
Across nine identified song changes in two unmuted sessions, the nearest sampled AVPlayer
`currentDate()` was **158.863–163.171s** after the matched entry's `playedAt` timestamp. Four
pre-pause markers in the first run were ~165–168s after `playedAt` by wall clock; the post-11s-pause
marker was ~178s. In the second run, pre-pause markers were ~165–169s by wall clock; the
post-31.367s-pause marker was ~196s. The **media-date** difference remained near 160s in both
post-pause cases. Human markers and 1s player sampling limit precision; the timestamp's station
semantics remain unverified. This is a candidate calibration for this HLS path, not a universal
KCRW constant or proof of lyric-level sync.

**Finding 8 — feed-top and audible audio are independent, including during an unreported break.**
In the first run, a scheduled feed request reported “Wanderlust” 0.338s after the user paused;
AVPlayer remained paused on “Things Take Time.” In the second run the user heard a station-ID
commercial at 246.879s and “Fools in Love” at 304.635s. The feed showed “Fools in Love” from
180.726s onward and reported no `[BREAK]` in its five-entry responses. The 246.879s marker is
**not** a song-start marker. The user prioritizes the AAC playback path and does not require ad
identification in this slice. Do not derive audibility from feed row zero or treat the commercial
as evidence of a track boundary in the feed.

A separate browser HAR showed KCRW's page polls five-entry history every 30s, its player title
polls `/Music` every 60s, and the web player fetches AAC/HLS. The website does not prove
sample-synchronous metadata; the full HAR remains local in Downloads, not in the repository.

### Attended KEXP AAC session (2026-09-27)

Full timeline, trace, and limits: [KEXP attended-session record](../experiments/2026-09-27_kexp_aac_attended.md).
The unmuted `https://kexp.streamguys1.com/kexp160.aac` session ended cleanly at 737.777s
with no clock gap: 25 feed responses, 11 timed-metadata events, a pre-roll metadata event,
one playback stall, three named song markers, an airbreak marker, and a 39.030s recorded pause.
This is AAC/ICY, not KCRW's HLS path; `AVPlayerItem.currentDate()` was unavailable in all
724 playback samples. The listener output route was not recorded.

**Finding 9 — KEXP has title metadata, but first arrival is not a universal audible boundary.**
The first `StreamTitle` for “Good to Go” arrived 15.972s before the user's marker and repeated
2.394s after it. First titles for “The Day That's Just Begun” and “Sea Of Heartbreak” arrived
1.499s and 1.623s before their markers; those titles also repeated later. The matching feed
rows first appeared 22.226s, 27.773s, and 31.690s **after** the respective markers. A KEXP
`airbreak` row appeared 35.089s **before** the listener marked the break. Pre-roll carried
`insertionType=preroll` at 4.647s; the first song title arrived at 19.388s, with no audible
first-song marker. Thus player title, feed row, and listener have distinct timing and content
semantics. These three songs do not establish a stable station lag. The raw trace preserved the
airbreak, but replay initially omitted it because it lacked a title. A synthetic regression and
fix on 2026-09-30 make the unchanged trace report five feed-top transitions, including the
`airbreak` at 694.536s. Do not count the airbreak as a fifth song.

## Decisions recorded

1. **Persisted UTC dates:** `wallTime`, `programDate`, and parsed `playedAt` use millisecond resolution for stable, language-neutral JSON round trips.
2. **Timing precision:** `elapsedSeconds`, media time, and metadata ranges retain full `Double` precision and are authoritative for interval analysis *within continuous playback*. Monotonic time freezes across a system suspend; see Finding 2 above and the `clock` section of a replay.
3. **Wall-clock correction:** replay allows wall time to move backward. Sequence and monotonic elapsed time define event ordering.
4. **Privacy guarantee:** standalone and embedded HTTP(S)/file URLs are redacted. Redaction remains defense in depth; review traces before sharing.
5. **KCRW playback direction:** the user prefers the AAC HLS stream for quality and does not require ad identification for this slice. The ~160s mapping is a candidate for that exact endpoint, not yet a saved station offset or an approved production change.

## Next bounded slice

The [approved M11 offline plan](milestone_11.md) now defines the offline selection tests and a later
opt-in menubar AAC/HLS experiment, including separate calibration/lyric corrections and both
pause paths. Approval covers committing and pushing the plan and starting offline validation; it
does not approve merge, production playback changes, or a default endpoint switch. M10's short KEXP
observation is recorded. A five-song KEXP timing policy would need a longer independent attended
run, but is not a prerequisite for KCRW's M11 plan.

**Prototype and validate, without a production playback change yet:** select the latest feed
occurrence only when the current AVPlayer media/program date passes that occurrence's `playedAt`
plus a measured, HLS-endpoint-specific ~160s estimate. Build deterministic fixtures from the two
attended traces; cover early feed arrival, two pauses, the missed marker, the unreported commercial,
cache freshness, a missing media date, reconnects, and correction of a feed entry. Keep feed
history distinct from the selected audible candidate. Lyrics must use player media time rather
than `Date.now` and must not double-apply the existing saved KCRW manual offset.

The user prefers AAC for quality and is not prioritizing ad recognition. `curated_stations.json`
currently names KCRW's `e24_mp3` path; `PlayerViewModel` reads the station stream URL, immediately
selects feed row zero, and tears down live radio on pause. Do not transplant the HLS calibration
onto MP3 or silently change the production endpoint. Choose and validate the AAC production
endpoint in a separate, explicit implementation step with an audible menubar build. Preserve
fallback/uncertainty when `currentDate()` is unavailable or a stream/item changes. The output
route of the attended captures was not recorded, so route-specific validation remains necessary.

For the remainder of **M10**, do not treat the three KEXP song markers as a timing distribution or
transfer the KCRW HLS calibration to this AAC/ICY connection. The meaning of KCRW's `datetime`
remains unverified; its measured mapping is empirical, not station documentation. Merge remains a
separate approval gate.

## Evidence limits

- The 52 passing tests establish the synthetic trace contract, command dispatch, clock-gap detection, cache-age-corrected publish-lag bracketing, and an untitled KEXP airbreak transition. They do not establish live station behavior.
- The regressions close the reproduced serialization and embedded-file-URL gaps; they do not establish audible drift or exhaustive privacy coverage.
- The local fixture and four original KCRW MP3 sessions were muted and unattended; they cannot establish audibility. Two later AAC/HLS sessions were unmuted and listener-marked, with real observed 11s and 31s pauses. Markers remain coarse and the listener output route was not recorded.
- The local fixture's pause/resume markers were piped on stdin and landed 0ms apart, so no pause was actually observed there. The later attended sessions close that gap for Stream Lab, not for production menubar radio pause, which tears down its item.
- No account access or credential use has occurred in Stream Lab. Its only network contacts were the public KCRW/KEXP streams and tracklist endpoints. The separately captured website HAR includes browser request data and has not been copied into the repo.
- The KEXP AAC/Icecast item supplied ICY metadata but no player program date. The first ICY callback preceded one heard change by ~16s; the sole KEXP run has fewer than five named transitions and one stall. Its airbreak marker must not count as a song.
- Feed timestamps, AVPlayer program dates, metadata arrivals, and human markers are observations with different uncertainty. None is automatically a song boundary.

## Session records and retained data

Session records for [2026-09-25 unattended KCRW MP3](../experiments/2026-09-25_kcrw_sessions.md),
[2026-09-26 attended KCRW AAC/HLS](../experiments/2026-09-26_kcrw_hls_attended.md), and
[2026-09-27 attended KEXP AAC](../experiments/2026-09-27_kexp_aac_attended.md), plus the
retained traces, are in `docs/menubar/experiments/`. Traces live in
`docs/menubar/experiments/traces/` at mode `0600` and replay with `stream-lab replay <file>`.

They were moved there out of `/tmp`, which is not retention: every finding above traces back to
one of those files and a reboot would have lost them.

Privacy review of the retained traces (the runbook requires an explicit one before they leave the
local machine): no credentials, tokens, auth headers, cookies, usernames, or unredacted local
paths. Contents are the redacted public stream/feed URLs, the macOS version string, public album
artwork CDN links carried in the feeds, KCRW/KEXP track titles, KEXP provider IDs and ICY values,
source timestamps, and timing/buffer data.
Captured response headers are limited to `age`, `cache-control`, `content-type`, and `date`. The
residual consideration is that the traces are a record of what this machine streamed and when,
for a public station.

## Repository guardrails

- The Stream Lab package is still untracked under `pocket-radio-menubar/Tools/`.
- The shell milestone/review documents are tracked on root `feature/stream-monitoring-lab`. Stage only explicit paths when recording status changes.
- iOS configurable-tab-bar work is merged and pushed: local and remote `trunk` are at `0751918f8`. M10 does not modify iOS or manage cleanup of the remaining feature-branch refs.
- Manual checkpoint approval for commit/push was received on 2026-09-30. Do not merge or delete Stream Lab branches without separate explicit approval.
- Do not edit `docs/menubar/current_milestone.md` through its symlink.
- Never place ACR credentials, signed URL parameters, account data, or unredacted local paths in docs, traces, tests, or logs.
