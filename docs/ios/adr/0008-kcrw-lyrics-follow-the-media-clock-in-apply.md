# 0008 — KCRW lyrics follow the media clock in Apply

**Status:** Accepted (2026-10-10). Supersedes the lyric part of [ADR 0005](0005-kcrw-aligned-now-playing-single-writer.md) (D11 b′: "lyrics stay on today's wall clock").

## Context

Live lyrics were positioned from broadcast wall time: `Date() − playedAt + a saved station offset`, on a 1 s timer in station detail and a second timer in full-screen lyrics. A pause, a stall, or opening full-screen lyrics put the line out of step. Pushing full-screen lyrics also stopped the station-detail controller and zeroed its offset. In Apply the screen loaded lyrics for the feed's newest row, which is about 160 s newer than the aligned song, so the lyrics were for the wrong song.

## Decision

In Apply, lyrics read the player's own clock. Off and Observe keep the wall-clock path unchanged.

- **One position source.** `SongPositionEstimator` keeps the last valid player sample's song seconds and extrapolates from it while the player plays. It holds while the player is paused or buffering. `AlignedConsumers.lyricPosition(stationId:)` reads it. It is nil for another occurrence, before any sample, and once the session stops applying.
- **One 5 s rule.** A brief clock fault keeps the position extrapolating. The estimator has no timer of its own: when the title hold in `AlignedNowPlayingPublisher` ends and publishes unavailable, that resets the estimator. The title and the lyric position let go at the same moment.
- **Right song.** Station detail loads the aligned entry (`AlignedConsumers.entry(for:)`) with its occurrence id, not the feed top, and reloads on every aligned post, including a repeat play.
- **One line index.** `LyricLineIndex.index(in:at:)` returns the last line whose timestamp is at or before the position. `LyricsService.currentLine` delegates to it. Both screens use it.
- **One correction.** The `+` and `−` correction is in memory, keyed to the current occurrence, and shared by both screens through `LyricSyncController`. A new occurrence (including a repeat), a station change, and a real exit from station detail reset it.
- **No second timer.** Full-screen lyrics subscribes to the controller's 1 s tick (`observeTicks`). Leaving station detail for full-screen lyrics does not stop the controller (`AlignedLyricsPolicy.shouldStopOnDisappear`).
- **Saved offsets are ignored.** In Apply nothing reads or writes `lyric_offsets`. Those values compensated for the wall-clock error and would double-correct. In Off and Observe they are read on load and written on a debounced 800 ms nudge, as before.
- **Unavailable is explicit.** With no valid position, the lyrics show no timed highlight and the station name. There is no wall-clock fallback.
- **Unchanged on purpose.** In Apply the controller never writes the lock screen's album field (D11 b′, and bug 7). CarPlay and Bluetooth lyric display stay out of scope.

## Consequences

- **Position error is the title's error.** Lyrics and title share the `+160 s` feed-to-program offset, so any error in it shows in both. On the device the lyric line ran about 3 s behind the audio, and a `+3` nudge fixed it. Calibrating that offset is a separate piece of work (the ShazamKit experiment).
- **The correction survives only a push to full-screen lyrics (D13 a).** Leaving station detail for good resets it. Whether it should survive other navigation is for the 14.4 review.
- **Full-screen lines come from the same cached lookup** as station detail, both through the controller's loader, so the two get the same lines.
- **`lyricPosition` can move slightly between samples,** because it extrapolates and a new sample replaces it. The line index tolerates a small step in either direction.

## Rejected alternatives

- **Wall-clock lyrics in Apply** (ADR 0005's D11 b′). The line disagrees with the aligned title and the audio after any pause or stall.
- **Each screen subscribes to session snapshots itself.** That gives two owners and lets a screen start or stop the monitor. A read on the aligned state keeps one owner (D12 a).
- **A session-level lyric controller** that outlives the screens (D13 b). The reset bug came from the clock and the correction, not from who owns the fetch. Revisit if 14.4 shows leaving station detail still drops lyrics.
- **Read saved `lyric_offsets` as a starting correction** (D14 b). They are tuned to the wall-clock path and would double-correct.
- **A timer inside the estimator for the 5 s fault hold.** The review found it disagreed with the publisher's hold when a pause fell inside the window. One copy of the rule is enough.

## Verification

| Behavior | Covered by |
|---|---|
| Session position; no wall clock; pause holds; fault hold; unavailable is explicit | `SongPositionEstimatorTests`, `AlignedNowPlayingTests`, `AlignedConsumersTests` |
| Same line everywhere; equal timestamps | `LyricLineIndexTests`, `LyricsServiceTests` |
| Correction per occurrence; saved offsets untouched in Apply and unchanged in Off and Observe; late results dropped; repeat play reloads; Off and Observe characterized | `LyricSyncControllerTests`, `LyricSyncControllerSharedClockTests` |
| Navigation keeps clock and correction; no second timer; shared correction; load target; stop policy | `AlignedLyricsNavigationTests`, `StationDetailLyricsTests`, `LyricsViewControllerTests` |
| Full `PocketCastsTests` (1,280 tests, 101 skipped) and the CarPlay output suite (128) | 2026-10-10 |
| The eight checks on the device | User, 2026-10-10 |

Evidence: `archive/ios-m14.3:docs/ios/milestones/milestone_14.3.md` and `archive/ios-m14.3:docs/ios/milestones/milestone_14.3_subagent_plan.md`.
