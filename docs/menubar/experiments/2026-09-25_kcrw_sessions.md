# Stream Lab session records — KCRW, 2026-09-25

Records for the unattended KCRW captures run during M10 Phase 3/4 groundwork, in the shape
prescribed by the [package runbook](../../../pocket-radio-menubar/Tools/StreamLab/README.md)
§ Results record. Findings and their current status live in
[the M10 handoff](../milestones/milestone_10_handoff.md).

**Every session here was muted and unattended.** None of them establishes what a listener
heard. Retained traces are in `traces/`, replayable with `stream-lab replay <file>`.

## Common to all sessions

- **Menubar commit / dirty state:** `a995f06`, with `Tools/` untracked (the Stream Lab package
  is not yet committed).
- **Test result:** 51 tests, 0 failures (`swift test --package-path pocket-radio-menubar/Tools/StreamLab`).
- **macOS:** Version 26.6.2 (Build 25G83).
- **Station:** KCRW.
- **Sanitized stream endpoint:** `https://streams.kcrw.com/e24_mp3` (Eclectic24), taken from
  `curated_stations.json` so it matches what the app plays.
- **Feed endpoint:** `https://tracklist-api.kcrw.com/Music/all/1` (query stripped by redaction).
- **Transport:** MP3 over HTTPS with ICY metadata *inferred* from the endpoint name and the
  existing `tools/stream-probe.py` notes. **Not verified in these sessions** — no ICY header
  inspection was performed on this connection.
- **Output route:** none. All captures ran `--muted`, which is why no marker evidence exists.

---

## Session s0 — reachability sanity check

- **Duration:** 12s, `--feed-interval 5`
- **Trace:** `traces/2026-09-25_kcrw_s0_sanity_12s.jsonl`
- **Clean end reason:** `duration`

Purpose was only to confirm the stream was reachable after a location change before spending
15 minutes on a capture. Feed-top was `Lejos de Más (feat. Helado Negro)` throughout.

---

## Session s1 — first live transport check

- **Duration:** requested 150s; trace shows 133.813s monotonic
- **Trace:** `traces/2026-09-25_kcrw_s1_transport_150s.jsonl`
- **Clean end reason:** `duration`

### Counts

- Heard-song-change markers: 0 (muted, unattended)
- Lyric-landmark markers: 0
- Metadata observations: 1, with an empty `values` array
- Feed responses / failures: 5 / 0
- Stalls, waits, or media-time jumps: none

### Result

- **Observed:** the stream plays, the feed polls cleanly, and the trace replays offline.
- **Observed:** wall time advanced 201.905s while monotonic time advanced 133.813s. The Mac
  suspended for ~68s mid-capture and nothing in the trace flagged it at the time.
- **Limits:** the suspend makes every interval in this trace a lower bound. Superseded as
  timing evidence by s2 and s3.
- **Follow-up:** added the `clock` section to replay so this cannot pass unnoticed again;
  use `caffeinate -is` for all later captures.

---

## Session s2 — caffeinated 7-minute capture

- **Duration:** 420s (`--feed-interval 30`), under `caffeinate -is`
- **Trace:** `traces/2026-09-25_kcrw_s2_caffeinated_420s.jsonl`
- **Clean end reason:** `duration`

### Counts

- Heard-song-change markers: 0 (muted, unattended)
- Lyric-landmark markers: 0
- Metadata observations: 0
- Feed responses / failures: 14 / 0
- Stalls, waits, or media-time jumps: none

### Comparisons

| Transition | Human marker elapsed | Metadata elapsed/range | Feed receipt and provider time | Notes/uncertainty |
|---|---:|---|---|---|
| 1 — Comes Back to You | none (muted) | none delivered | first seen elapsed 241.227; claimed airtime `18:16:36-07:00`; responding cache fresh, prior poll 30s stale | Origin held it by airtime +59.6s. No lower bound: the prior response predates the airtime. |

### Result

- **Observed:** 420.005s wall against 420.009s monotonic — no clock gap. `caffeinate -is` works.
- **Observed:** zero timed-metadata events across the whole run.
- **Not observed:** anything audible; anything about KEXP.
- **Limits:** one transition, and no marker to compare it against.

---

## Session s3 — 15-minute capture at a 10s poll interval

- **Duration:** 900s (`--feed-interval 10`), under `caffeinate -is`
- **Trace:** `traces/2026-09-25_kcrw_s3_lag_900s_poll10.jsonl`
- **Clean end reason:** `duration`

### Counts

- Heard-song-change markers: 0 (muted, unattended)
- Lyric-landmark markers: 0
- Metadata observations: 1, with an empty `values` array
- Feed responses / failures: 89 / 0
- Stalls, waits, or media-time jumps: none

### Comparisons

| Transition | Human marker elapsed | Metadata elapsed/range | Feed receipt and provider time | Notes/uncertainty |
|---|---:|---|---|---|
| 1 — Breathless | none (muted) | none delivered | first seen elapsed 182.430; responding cache fresh, prior poll 51s stale | Origin held it by airtime **+17.7s**; no lower bound |
| 2 — Every Single Weekend | none (muted) | none delivered | first seen elapsed 425.228; prior poll 51s stale | Origin held it by airtime +43.5s; no lower bound |
| 3 — Don't You Want Me (with Cat Power) | none (muted) | none delivered | first seen elapsed 607.082; prior poll 51s stale | Origin held it by airtime +39.4s; no lower bound |

### Result

- **Observed:** 900.025s monotonic against 900.090s wall — no clock gap.
- **Observed:** the feed sits behind a cache. `cache-control: max-age=15, public, must-revalidate`,
  but the `age` header cycles 0 → ~51s and resets, so the effective refresh is **~60s, not 15s**.
- **Observed:** all three transitions were first seen on a cache-fresh response (`age` absent).
  New entries only become visible when the cache refreshes.
- **Conflicting evidence:** the raw receipt times initially looked like a *variable* publish lag
  spanning 7–60s, and three brackets looked provably disjoint. Correcting for `age` voids every
  lower bound, and a single constant lag anywhere in 0s..+17.7s fits all four transitions across
  s2 and s3. The apparent variability was aliasing between the ~60s cache cycle and the poll
  interval, not station behavior. See Finding 6 in the handoff.
- **Limits:** upper bounds only. Measuring publish lag itself needs a cache-bypassing request
  or a station-side answer; this endpoint cannot show it.
- **Follow-up:** replay now corrects brackets for `age` and refuses a lower bound from a stale
  response. Polling faster than the refresh interval gains nothing — this run made 89 requests
  to learn what roughly 15 would have.

---

## Session — Phase 3 local audio fixture

- **Stream:** local `say`-generated AIFF, redacted in-trace as `file:///<local-audio>`. No
  station audio and no copyrighted material.
- **Duration:** 18s requested; ended `item_ended` at 15.605s
- **Trace:** `traces/2026-09-25_phase3_local_fixture_18s.jsonl`

### Result

- **Observed:** media time advanced 1:1 with elapsed time after a ~0.38s startup offset;
  playback samples, markers, and a clean end are all present and replay offline.
- **Limits:** the pause/resume markers were piped on stdin and landed 0ms apart, so **no pause
  was ever actually observed** in the playback samples. A real pause/resume cycle still owes
  a test in the attended session.
