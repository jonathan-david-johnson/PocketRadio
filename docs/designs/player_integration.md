# Player Integration Design

## RadioStation: BaseEpisode conformance

Live radio streams must conform to `BaseEpisode` to enter the PC playback stack.

### Required PC source changes (minimal)

#### 1. `podcasts/EpisodeManager.swift` — `urlForEpisode(_:streamingOnly:)` (~line 435)

Add a fallback case before `return nil`:

```swift
// Fallback: any BaseEpisode whose downloadUrl is a direct stream URL (e.g. RadioStation)
if let url = episode.downloadUrl {
    return URL(string: url)
}
return nil
```

This is the only required PC core change. RadioStation.downloadUrl = streamUrl.

#### 2. No DownloadManager changes needed

To skip the parallel-download-while-streaming logic, set `RadioStation.sizeInBytes = Int64.max`.
DownloadManager guard: `(FileManager.deviceRemainingFreeSpaceInBytes ?? 0) > episode.sizeInBytes`
→ free space never exceeds Int64.max → guard fails → returns `playbackItem` directly (no caching). Clean.

---

## RadioStation model

File: `podcasts/Radio/RadioStation.swift`

```swift
import Foundation
import PocketCastsDataModel

/// Conforms to BaseEpisode so RadioStation can enter PC's playback stack.
/// Stream plays via AVPlayer with no download/caching side effects.
@objc class RadioStation: NSObject, BaseEpisode {

    // MARK: - Radio-specific

    let stationId: String
    let streamUrl: String
    let donateUrl: String?
    let tracklistUrl: String?
    let city: String?

    init(stationId: String, name: String, streamUrl: String, donateUrl: String? = nil,
         tracklistUrl: String? = nil, city: String? = nil) {
        self.stationId = stationId
        self.streamUrl = streamUrl
        self.donateUrl = donateUrl
        self.tracklistUrl = tracklistUrl
        self.city = city
        self.uuid = stationId
        self.title = name
        self.downloadUrl = streamUrl
        self.sizeInBytes = Int64.max   // prevents DownloadManager parallel-cache logic
    }

    // MARK: - BaseEpisode stored properties

    var uuid: String
    var title: String?
    var downloadUrl: String?
    var sizeInBytes: Int64

    var addedDate: Date? = nil
    var publishedDate: Date? = nil
    var cachedFrameCount: Int64 = 0
    var autoDownloadStatus: Int32 = 0
    var fileType: String? = "audio/mpeg"
    var contentType: String? = nil
    var playbackErrorDetails: String? = nil
    var downloadErrorDetails: String? = nil
    var lastDownloadAttemptDate: Date? = nil
    var downloadTaskId: String? = nil
    var playingStatusModified: Int64 = 0
    var playedUpToModified: Int64 = 0
    var archived: Bool = false
    var keepEpisode: Bool = false
    var wasDeleted: Bool = false
    var episodeStatus: Int32 = 0
    var playingStatus: Int32 = 0
    var playedUpTo: Double = 0       // always 0 — live stream has no position
    var duration: Double = 0         // 0 = unknown; mini player hides progress bar when 0
    var deselectedChapters: String? = nil
    var deselectedChaptersModified: Int64 = 0
    var hasBookmarks: Bool = false
    var hasOnlyUuid: Bool = false

    // MARK: - BaseEpisode methods

    func displayableTitle() -> String { title ?? stationId }
    func parentIdentifier() -> String { stationId }

    func downloaded(pathFinder: FilePathProtocol) -> Bool { false }
    func bufferedForStreaming() -> Bool { false }
    func downloadFailed() -> Bool { false }
    func downloading() -> Bool { false }
    func queued() -> Bool { false }
    func waitingForWifi() -> Bool { false }
    func exemptFromAutoDownload() -> Bool { true }
    func pathToDownloadedFile(pathFinder: FilePathProtocol) -> String { "" }
    func pathToTempFile(pathFinder: FilePathProtocol) -> String { "" }

    func inProgress() -> Bool { playingStatus == PlayingStatus.inProgress.rawValue }
    func played() -> Bool { false }    // live stream is never "played"
    func unplayed() -> Bool { true }
    func playbackError() -> Bool { playingStatus == PlayingStatus.error.rawValue }

    func videoPodcast() -> Bool { false }
    func mayContainChapters() -> Bool { false }

    var isUserEpisode: Bool { false }
}
```

---

## Playing a stream

```swift
// In RadioStationDetailViewController or RadioPlayerIntegration
func playStation(_ station: RadioStation) {
    PlaybackManager.shared.load(episode: station, autoPlay: true, overrideUpNext: false)
}
```

`overrideUpNext: false` — stream does NOT enter Up Next queue. It plays immediately and is cleared when user stops or switches.

### "No Up Next" enforcement

Streams must not persist in Up Next. After playback ends (network loss, user stop):
- Listen for `Constants.Notifications.playbackEnded`
- If current episode is a `RadioStation`, call `PlaybackManager.shared.clearUpNextQueue()`

---

## Mini player behavior for live streams

Mini player reads from `PlaybackManager.shared.currentEpisode()`.
When current episode is `RadioStation`:
- Progress bar: hidden (duration == 0 → PC already hides it)
- Station name shown as episode title
- No "skip 30s" controls (they no-op on live streams anyway)
- Donate button: add to mini player only if `donateUrl != nil`

No mini player code changes required for basic operation. Donate button is additive.

---

## Listen time tracking

`ListenTimeTracker.swift` observes `Constants.Notifications.playbackTrackChanged` and a 10s timer.

```swift
// Pseudocode
if let station = PlaybackManager.shared.currentEpisode() as? RadioStation {
    accumulatedSeconds[station.stationId, default: 0] += 10
    if accumulatedSeconds[station.stationId]! % 60 == 0 {
        syncToSupabase(stationId: station.stationId, seconds: 60)
    }
}
```

Syncs to `listen_time` table in 60s increments. Flushes on app background.
