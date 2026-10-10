# iOS M14.3 subagent plan — KCRW lyrics on the media clock

**Status**: IN PROGRESS — approved 2026-10-10 (UTC). Slice 0 done: the pending iOS work is committed and on `trunk`, and `feature/kcrw-lyrics` exists.
**Scope**: [M14.3](milestone_14.3.md), with decisions D12–D14 and extrapolation made on 2026-10-10.
**Route**: Anthropic only (`PI_PROVIDER=anthropic`, `PI_MODEL=claude-sonnet-5-5`, reasoning high). The rate snapshot in the `subagent-plan` skill is dated 2026-10-04, six days old, so it is fresh. Billing mode is unknown, so the costs below are API list-price references and the quota impact is unknown. Both model IDs were used for M14.1 and M14.2; I haven't re-verified access today.
**Agents** (new, `.pi/agents/`, briefs name the 14.3 files): `m143-sonnet-high` (implementation, `anthropic/claude-sonnet-5-5:high`) and `m143-opus` (read-only review, `anthropic/claude-opus-5-5:high`). The M14.1 agents are not reused, because their briefs forbid lyric and Now Playing work.

## Before slice 1 (lead, needs your approval at each commit)

1. Commit the bug 9 fixes, the clock-fault hold and the lock-screen Stop work in `pocket-radio-ios-alignment`, then fast-forward `trunk`. Nothing is pushed.
2. Create `feature/kcrw-lyrics` from `trunk` in the same worktree. Record the shell commit hash in the milestone's verification notes.

## How lyric position works today, and what changes in Apply

| Reader | Source today | 14.3 change in Apply |
|---|---|---|
| `LyricSyncController` (station detail) | Wall clock: `Date() − playedAt + saved offset`, a 1 s `Timer` | Song seconds from the aligned state, sampled by the same 1 s timer; correction held per occurrence |
| `LyricsViewController` (full screen) | Its own `Timer` and `initialOffset`, rebuilt from `Date() − elapsed` after navigation | Reads the same position and the same line index; no second timer |
| `StationDetailViewController.viewDidDisappear` | Stops `LyricSyncController` and zeroes its offset, including when full screen is pushed | Leaving for full screen changes neither the clock nor the correction |
| `RadioFavoritesManager.lyricOffsets` | Read on load, debounced upsert on nudge | Not read, not written |
| `LyricsService.currentLine(in:at:)` | Binary search used by the controller | Becomes the shared line index, used by both screens |
| Album-field write (`didUpdateNowPlayingAlbum`) | Already skipped in Apply (D11 b′) | Unchanged |

## Shared interface (written in slice 1, used by slices 2 and 3)

```swift
/// Pure. Injected clock. Song seconds between player samples.
struct SongPositionEstimator {
    init(holdLimit: TimeInterval = 5, now: @escaping () -> Date)
    mutating func record(occurrenceID: String, songSeconds: Double, playing: Bool)   // a valid player sample
    mutating func recordFault()                                                       // clock invalid: stop re-anchoring
    func position(forOccurrence id: String) -> Double?   // nil: wrong occurrence, no sample, or a fault older than holdLimit while playing
}
// AlignedNowPlayingState gains one reader; AlignedConsumers exposes it.
static func lyricPosition(stationId: String) -> (occurrenceID: String, seconds: Double)?   // nil unless applying
// RadioPlaybackSession feeds the estimator from every sample() and from clock-invalid decisions.
```

While the player plays, the position is the last anchor plus the time since it. While it is paused or buffering, the position holds. A clock fault holds the position for the same 5 s as the title (ADR 0005), then it is nil: no timed highlight, no wall-clock fallback.

## Slices

Token figures are advisory aggregates, including repeated context and tool output.

| # | Owner, model | Files owned | Acceptance | Input | Output | Stop when |
|---|---|---|---|---:|---:|---|
| 0 | Lead, Sonnet | Commits, branch, briefs, this plan | Branch `feature/kcrw-lyrics` from `trunk`; interface above | 300k | 6k | — |
| 1 | `m143-sonnet-high` | `podcasts/Main/Alignment/` (new `SongPositionEstimator.swift`; `AlignedNowPlayingState.swift`, `AlignedNowPlayingConsumers.swift`, `RadioPlaybackSession.swift`); tests `PocketCastsTests/Tests/Alignment/` | Behaviors 1 (session position, no wall clock), 2 (pause holds), 8 (unavailable is explicit); fault hold | 700k | 15k | Two failed fixes; any other file needed |
| 2 | `m143-sonnet-high` | New `podcasts/Main/Alignment/LyricLineIndex.swift`; `podcasts/Radio/LyricSyncController.swift`; `podcasts/Radio/LyricsService.swift` (`currentLine` delegates to the index); tests `PocketCastsTests/Tests/Radio/` | Behaviors 3 (same index, equal timestamps), 5 (correction per occurrence), 6 (saved offsets untouched in Apply, unchanged in Off and Observe), 7 (late results dropped; a repeat play reloads), 9 | 1,200k | 25k | Same; any visible change with the mode Off |
| 3 | `m143-sonnet-high` | `podcasts/Radio/LyricsViewController.swift`; `podcasts/Radio/StationDetailViewController.swift` (lyric and `viewDidDisappear` parts only); tests as in slice 2 | Behavior 4 (navigation keeps clock and correction; no second timer; full-screen buttons adjust the same correction) | 900k | 18k | Same; any change to the tracklist poll or Now Playing writes |
| 4 | `m143-opus`, read-only | none | Review behaviors 1–10 and the invariants in its brief, Off and Observe safety, bug 7 not widened, upstream diff size | 500k | 10k | Two unresolved questions |
| 5 | Lead with you | Fixes from the review; docs from Docs impact | Behavior 10: full unit suite and CarPlay suite (no new album-field write in Apply); the eight hand-performed interactions on the phone | 800k | 12k | Any lyric line you hear or see out of step |
| | **Total** | | | **4,400k** | **86k** | |

Slices 1, 2 and 3 run one after another, not in parallel. They share the lyric state, the build, and the simulator, and slice 3 depends on slice 2's interface.

**List-price reference** (Sonnet $2.00 uncached, $0.20 cached, $10.00 output; Opus $4.00, $0.20, $20.00; per million tokens):
- At about 90 % cache reads: Sonnet ≈ $2.2 (3,900k input, 76k output), Opus ≈ $0.5. About **$2.7** in all.
- At about 50 % cache reads: about **$6**.
- Subscription-quota impact is unknown.

## Gates

- **Approval:** this plan, then each commit, per `pocket-radio-ios/AGENTS.md`. Nothing is committed until you have tested it on the phone.
- **Device:** the lead installs over the cable or, with your say-so, the network. Agents never touch the phone or the CarPlay simulator.
- **Docs impact:** when 14.3 closes, ADR 0005 is extended or superseded for lyrics, and the iOS README, `test-architecture.html` and the menubar ADR 0002 pointer are updated. See the milestone.
