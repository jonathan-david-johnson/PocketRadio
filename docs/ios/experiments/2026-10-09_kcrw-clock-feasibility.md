# KCRW playback clock feasibility — G1 probe (iOS M14.1)

**Date:** 2026-10-09. **Device:** "Jonathan iPhone" (iPhone 15, iOS 26.6.2). **Build:** `feature/kcrw-alignment` (slice 1 probe), StagingDebug, Observe on via launch argument. **Network:** Wi-Fi. **Screen:** on, app foreground.
**Raw evidence:** [`traces/2026-10-09_kcrw-g1-probe.log`](traces/2026-10-09_kcrw-g1-probe.log) (the `[align]` lines from `main.log` and `old.log`).

## Result: G1 passes

| Check | Criterion | Observed |
|---|---|---|
| `currentDate()` on iOS | Non-nil within 15 s of `.playing` | Non-nil on the first `.playing` sample, 6.5 s after probe start |
| Valid samples while playing | At least 95 % | 275 of 275 `.playing` samples had a program date |
| Program date tracks media time | Within 2 s per step | Largest per-sample difference between program-date step and media-time step: 0.004 s |
| Media tracks wall time | Within 1 % | 273.0 s of media over 273.1 s of elapsed time |
| Rate | 1.0 | 1.00 on every sample, no `waiting` after the first `.playing` sample |
| Sample continuity | No gap over 5 s once playing | 277 samples over 280 s; the only gap over 1 s was the 6.4 s before playback began |

## Notes

- The program date runs a constant **5.0 s behind the phone's wall clock** (range 5.000–5.037 s). This is the stream's own delay, not the feed-to-stream offset. The `+160 s` offset relates the *feed's* `playedAt` to program time and is unverified on iOS until 14.2.
- The first sample is logged twice at `t=0.1` and again at `t=6.5`: the periodic observer fires once when installed and once at the start of playback. Harmless.
- The run lasted about 280 s, longer than the planned two minutes. It does not replace E1 (five minutes, readout), E2 (30 minutes locked), or E3 (podcast speed set first).
- No stop line was in the log. The last lines were flushed at the buffer threshold; the item had not been torn down.
- Locked-screen behavior, the feed poller, and background suspension are **not** tested here.

## Automated regression with Observe off (slice 7)

Run 2026-10-09 on `feature/kcrw-alignment` after the review fixes, iOS repo uncommitted, shell `main` at `3e8c47f`.

| Suite | Command | Result |
|---|---|---|
| Full unit suite | `make test_staging ONLY_TESTING=PocketCastsTests` (iPhone 17 simulator) | 1,080 tests, 0 failures, 101 skipped (harness tests skip outside `make test_carplay`) |
| M13.2 CarPlay output suite | `make test_carplay` (dedicated "PocketRadio CarPlay Tests" simulator) | 128 tests, 0 unexpected failures |

Behavior 10 (default-Off regression) passes on the simulator. E4 checks it on the device.

## E1 and E2 — five minutes on screen, then 30 minutes locked

Run 2026-10-09 16:36:20–17:12:05 (35.7 minutes), session `B730E710`, Observe on, Timer poll driver, Wi-Fi, build with the review fixes. The user watched the readout for about five minutes, locked the phone without pausing, unlocked after 30 minutes and paused. **Raw evidence:** [`traces/2026-10-09_kcrw-e1-e2-locked.log`](traces/2026-10-09_kcrw-e1-e2-locked.log).

| Check | Criterion | Observed |
|---|---|---|
| E1 clock | Non-nil within 15 s of playing; ≥ 95 % of playing samples valid | Valid at the first playing sample (6.4 s after start); 2,139 of 2,139 playing samples dated; no clock-invalid interval |
| E1 readout | Candidate appears | Candidate shown at 6.5 s; the user confirmed it matched the audible song and changed to the next song "at the appropriate time" |
| E2 sample gaps | ≤ 5 s from first playing sample | Longest 1.1 s |
| E2 poll attempts | ≥ 58, gaps ≤ 45 s | 72 attempts, 0 failures, longest gap 30.4 s |
| E2 liveness | Session alive, audio never stopped before the pause | Both true; 2,141 samples to the pause |
| E2 verdict | `kind=at-pause` passes | `verdict passed=true failures=0 kind=at-pause` |
| E3 rate and speed | Rate 1.0; each 5-minute window within ±1 % | Rate 1.00 on every playing sample; all eight windows ratio 1.000; 2,137 s of media over 2,137 s elapsed |

Recomputing gaps, rates, poll count and the overall speed ratio from the raw `probe` and `poll` lines gives the same numbers as the in-app summary.

### Notes

- **Lock period is from the user's report.** The log has no lifecycle lines, so it cannot show when the screen locked. Continuity held for the whole 35.7 minutes, which covers any lock period in it.
- **Pausing radio tears the session down.** The `stop` verdict one second after the pause fails with "audio stopped", by design; the `at-pause` verdict decides E2.
- **Checkpoint summaries count an in-flight poll as a failure.** The first checkpoint showed `pollFailures=1`; later summaries show 0 after the response arrived. Cosmetic.
- **Selection timing is qualitative.** Eleven song changes were selected. The user heard the first change land at the right time; the `+160 s` offset is checked formally in 14.2.
- Not yet observed: E3's podcast-speed check and E4 (Observe off on the device).

## Decision

Proceed with slices 2–5 of the [subagent plan](../milestones/milestone_14.1_subagent_plan.md).
