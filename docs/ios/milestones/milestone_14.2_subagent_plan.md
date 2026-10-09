# iOS M14.2 subagent plan — KCRW aligned titles and Now Playing

**Status**: IN PROGRESS — approved 2026-10-09 (UTC) with "go" after D9–D11.
**Scope**: [M14.2](milestone_14.2.md).
**Route**: Anthropic only (`PI_PROVIDER=anthropic`, `PI_MODEL=claude-sonnet-5-5`). Rate snapshot 2026-10-04 is fresh. Billing mode unknown: costs are API list-price references, quota impact unknown. Agents `.pi/agents/m14-sonnet-high.md` and `m14-opus.md` are reused; their briefs name the 14.2 files.

## How radio Now Playing is written today

| Writer or reader | Source today | 14.2 change in Apply |
|---|---|---|
| `RadioMetadataObserver` → `.radioStationNowPlayingDidChange` | ICY / in-band ID3 | Not attached for an Apply session |
| `PlaybackManager.handleRadioTrackChanged` → `NowPlayingHelper.setRadioTrackInfo` and artwork resolve | ICY title, tracklist top fills artist/album | Only aligned posts are honored; album never borrowed from the tracklist top |
| `PlaybackManager.handleRadioTracklistRefreshed` | Tracklist top artwork | Resolves to the aligned song (via `bestResolveEntry`) |
| `TrackArtworkResolver.bestResolveEntry` (used by the lock screen, full and mini player artwork, and full-player labels) | ICY match, else **tracklist top** | Returns the aligned song, or nil when unavailable; never the tracklist top |
| `NowPlayingHelper.setAllNowPlayingInfo` rebuild | Station logo artwork | Keeps the aligned song's artwork |
| `StationDetailViewController.refetchTracklist` → `setRadioTrackInfo` | Tracklist top | Skipped |
| Lyric album line → `setRadioAlbumTitle` | Feed-top lyrics | Skipped (D11 b′); lyrics stay on screen |
| ACR Identify button | Second stream | Hidden for the station |

## Shared interface (written in slice 1, used by slice 2)

```swift
enum AlignmentMode { case off, observe, apply }   // ObserveSwitchStore → AlignmentModeStore, key PocketRadio.alignment.mode
struct AlignedSong: Equatable { stationId; occurrenceID: String; title; artist; album: String?; artworkURL: URL?; generation: UUID }
enum AlignedNowPlaying: Equatable { case song(AlignedSong); case unavailable(stationId: String, reason: String) }
@MainActor final class AlignedNowPlayingState {
    static let shared
    func isApplying(stationId:) -> Bool           // true while an Apply session for that station is live
    var current: AlignedNowPlaying?               // nil when no Apply session
    func entry(for stationId:) -> TracklistEntry? // the aligned song as a TracklistEntry, nil if unavailable
    var artwork: (occurrenceID: String, image: UIImage)?
}
```

The adapter posts `.radioStationNowPlayingDidChange` with the existing keys plus `RadioMetadataNotificationKey.aligned = true` when the selected song or the available state changes.

## Slices

Token figures are advisory aggregates, including repeated context and tool output.

| # | Owner, model | Files owned | Acceptance | Input | Output | Stop when |
|---|---|---|---|---:|---:|---|
| 0 | Lead, Sonnet | Branch, briefs, this plan | `feature/kcrw-apply` from `trunk` `d29d7fad4`; map above | 300k | 6k | — |
| 1 | `m14-sonnet-high` | `podcasts/Main/Alignment/*` (mode store, state, adapter, session wiring, readout picker); `RadioMetadataObserver.swift` (one key); `DefaultPlayer.swift` (pass mode, skip ICY observer in Apply); Alignment tests | Behaviors 1, 2, 3, 6 (state), 7 | 1,000k | 20k | Two failed fixes; need for any other file |
| 2 | `m14-sonnet-high` | `TrackArtworkResolver.swift`, `PlaybackManager.swift` (radio handlers only), `NowPlayingHelper.swift` (radio rebuild artwork only), `StationDetailViewController.swift`, `NowPlayingPlayerItemViewController+Update.swift` and `MiniPlayerViewController.swift` (unavailable/label reset only if needed); tests under `PocketCastsTests/Tests/Alignment/` | Behaviors 4, 5, 6 (display), 8 | 1,200k | 25k | Same; any change visible with the mode Off |
| 3 | `m14-opus`, read-only | none | Review behaviors 1–9, mode-Off safety, single writer, upstream diff size | 500k | 10k | Two unresolved questions |
| 4 | Lead with you | Fixes from review; experiment report | Full unit suite and CarPlay suite with Off; device checkpoint by ear | 800k | 12k | Any title mismatch you hear |
| | **Total** | | | **3,800k** | **73k** | |

List-price reference (about 90 % cache reads, Sonnet $2.00/$0.20/$10.00 and Opus $4.00/$0.20/$20.00 per million): about $2.5–5. Not your actual cost.
