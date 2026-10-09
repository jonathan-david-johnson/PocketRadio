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

## Decision

Proceed with slices 2–5 of the [subagent plan](../milestones/milestone_14.1_subagent_plan.md).
