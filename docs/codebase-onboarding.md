# Pocket Casts iOS — Full Codebase Onboarding

> Written for a senior developer assuming full ownership. Last updated: 2026-05-20.

---

## 1. Project Overview

**PocketRadio** is a fork of Automattic's `pocket-casts-ios` (MPL 2.0 licensed). The fork adds live radio streaming capabilities (the "Radio" feature set) to the existing podcast player. The upstream repo is `Automattic/pocket-casts-ios`.

- **~837 Swift files** total across all targets
- **287 files** in the `Modules/` shared package
- **iOS 16+** deployment target, watchOS 9+, macOS 10.15+, tvOS 17+
- **Swift 5.10** toolchain with Xcode 16

### Target Architecture

The Xcode project contains multiple targets, all under `podcasts.xcodeproj`:

| Target | Purpose |
|--------|---------|
| `podcasts` (main) | The iOS app — all UI, playback, Radio, widgets |
| `Pocket Casts Watch App` | watchOS companion app |
| `Pocket Casts App Clip` | iOS App Clip (lightweight version) |
| `Pocket Casts TV App` | tvOS app |
| `WidgetExtension` | iOS home/lock screen widgets |
| `NotificationExtension` | Rich notification content |
| `NotificationContent` | Notification service extension |
| `PodcastsIntents` / `PodcastsIntentsUI` | Siri Shortcuts intents |
| `Share Extension` | Share sheet extension |

The "Pocket Casts Staging" scheme is the one you actually use for development (`build_sim`, `run_sim` in the Makefile).

---

## 2. Module Architecture (Shared Code)

The `Modules/` directory is a **Swift Package Manager** package containing shared libraries used by all targets. This is how Automattic shares code across the main app, watch, widgets, and app clip.

### Package Structure

```
Modules/
├── Package.swift          # Central manifest
├── Sources/
│   ├── PocketCastsUtils/       # Foundation-level utilities, logging, feature flags
│   ├── PocketCastsDataModel/   # GRDB database layer, models, query builder
│   ├── PocketCastsServer/      # REST API client, sync engine, subscriptions
│   ├── PocketCastsDependencyInjection/  # DI container (lightweight)
│   ├── EndOfYear/              # Year-end wrapped experience (SwiftUI)
│   ├── GRDBMacros/             # Swift macros for GRDB column definitions
│   ├── GRDBMacrosPlugin/       # Compiler plugin for the macros
│   ├── Modules/                # Umbrella module re-exporting everything
│   └── XcodeSupport/           # Per-target dependency shims (one per Xcode target)
└── Tests/
    ├── PocketCastsUtilsTests/
    ├── PocketCastsDataModelTests/
    ├── PocketCastsServerTests/
    ├── PocketCastsDependencyInjectionTests/
    ├── GRDBMacrosTests/
    └── ModulesTests/
```

### Key Package Design Detail: `XcodeSupport`

The `Package.swift` defines a clever pattern: each Xcode target gets a thin Swift package target (`XcodeTarget_podcasts`, `XcodeTarget_WidgetExtension`, etc.) that re-exports its dependencies. This lets Xcode project targets depend on SPM packages without SPM directly managing the Xcode project.

**Why this matters for you**: When you add a new third-party dependency, you add it to `Package.swift` under the relevant `xcodeTarget(...)` entry. The `podcasts` target dependency list is where you'd add anything the main app needs.

### Dependency Graph (Simplified)

```
PocketCastsUtils  (leaf — no internal deps)
    ↓
PocketCastsDataModel  (depends on Utils + GRDB)
    ↓
PocketCastsServer  (depends on DataModel + Utils)
    ↓
EndOfYear  (depends on DataModel + Server + Utils)
```

---

## 3. Third-Party Dependencies

Full list from `Package.swift`:

| Dependency | Purpose | Notes |
|------------|---------|-------|
| **GRDB.swift 7.x** | SQLite ORM | Core data layer. Entire app state lives in GRDB. |
| **Kingfisher 7.x** | Image loading/caching | All artwork, station logos, track art |
| **Firebase 10.x** | Analytics, Remote Config, Performance | AnalyticsWithoutAdIdSupport variant (privacy) |
| **Google Cast SDK** | Chromecast streaming | Automattic fork `google-cast` |
| **Google Sign-In** | OAuth provider | SSO login option |
| **Supabase Swift 2.x** | Radio favorites storage | Added by PocketRadio. User-scoped via `x-user-uuid` header. |
| **Automattic Tracks** | Event tracking | Automattic's own analytics pipeline |
| **EventHorizonSDK** | Binary framework | Closed-source analytics/SDK from Automattic |
| **Lottie 4.x** | Animation | Onboarding animations, loading states |
| **DifferenceKit** | Diffable data sources | Smooth list updates |
| **Fuse** | Fuzzy search | Podcast search in Intents |
| **SwipeCellKit** | Swipe actions | Episode list swipes |
| **JLRoutes** | URL routing | Deep link handling |
| **SwiftProtobuf** | Protocol Buffers | Server sync protocol |
| **SwiftSubtitles** | Transcript parsing | SRT/VTT subtitle parsing |
| **Swime** | MIME type detection | File type sniffing |
| **WrappingHStack** | SwiftUI layout | Tag/filter chip layouts |
| **Agrume** | Image viewer | Full-screen artwork viewer |
| **Fingerprint** | Device fingerprinting | Automattic's fork |

---

## 4. Data Layer — GRDB (SQLite)

### How It Works

`DataManager` (58,523 lines in `PocketCastsDataModel/Public/DataManager.swift`) is the **central data access layer**. It wraps GRDB's `DatabaseQueue` (single-writer serial queue) and provides:

- **Generated column accessors** via Swift macros (`@GrdbColumn` in `GRDBMacros/`)
- **Type-safe queries** via `PlaylistQueryBuilder` (41,020 lines)
- **Observed publishers** via GRDB's `ValueObservation` for reactive UI updates

### Key Models

All models live in `Modules/Sources/PocketCastsDataModel/Public/Model/`:

| Model | Purpose |
|-------|---------|
| `Episode` | Podcast episodes (GRDB-persisted) |
| `Podcast` | Subscribed podcasts |
| `BaseEpisode` | Protocol that both `Episode` and `RadioStation` conform to |
| `UserEpisode` | User-uploaded files |
| `PlaylistEpisode` | Junction table for playlists/filters |
| `EpisodeFilter` | Named filters (aka playlists) |
| `Folder` | Podcast folders |
| `Bookmark` | Episode bookmarks |
| `UpNextEpisode` | Up Next queue items |

### Important: `BaseEpisode` Protocol

This is the **polymorphism key** for PocketRadio. `RadioStation` conforms to `BaseEpisode`, which allows it to enter the existing playback stack (`PlaybackManager`, `PlaybackQueue`) without modifying the core data model. The trick:

```swift
// RadioStation.swift
downloadUrl = streamUrl     // EpisodeManager.urlForEpisode reads this
sizeInBytes = Int64.max     // DownloadManager cache guard always fails → no caching
duration = 0                // Mini player hides progress bar
played() → false            // Live stream is never "completed"
```

**Critical gotcha**: After `PlaybackManager.load(episode:)` saves a `RadioStation` to the SQL queue table, `currentEpisode()` returns an `Episode` shim (not `RadioStation`). This means `episode as? RadioStation` **always fails** after load. The fix in M7.1: `RadioStationRegistry` — an in-memory `[String: RadioStation]` dictionary that's the source of truth for "is this a radio station" lookups. Always use `RadioStationRegistry.shared.station(for: uuid)` not `as? RadioStation`.

---

## 5. Server / API Layer

### Architecture

`PocketCastsServer` module contains **all networking code**. It uses a custom URLSession-based stack (not Alamofire).

```
PocketCastsServer/Public/
├── API/
│   ├── ApiServerHandler.swift          # Main REST client (podcast search, subscriptions, etc.)
│   ├── ApiServerHandler+Account.swift  # Account management endpoints
│   ├── ApiServerHandler+SocialAuth.swift # Google/Apple sign-in
│   ├── ApiServerHandler+Suggestions.swift # Discovery suggestions
│   └── ...many more extensions
├── Sync/
│   ├── SyncManager.swift               # Full sync orchestration
│   ├── SyncTask.swift                  # Base sync task
│   ├── SyncTask+FullSync.swift         # Full sync implementation
│   ├── SyncTask+LocalChanges.swift     # Local→Server sync
│   ├── SyncTask+ServerChanges.swift    # Server→Local sync
│   ├── UpNextSyncTask.swift            # Up Next queue sync
│   ├── BackgroundSyncManager.swift     # BGTask-based background sync
│   └── ServerSyncDelegateProtocol.swift # Protocol for sync callbacks
├── Refresh/
│   └── RefreshManager.swift            # Podcast feed refresh
├── ServerSettings.swift                # Server-side persisted user settings (14,559 lines)
├── ServerPodcastManager.swift          # Podcast subscription management
├── SubscriptionHelper.swift            # IAP + subscription status
├── Upload/                             # User file upload pipeline
├── Discover/                           # Discover feed endpoint
├── Search/                             # Podcast search endpoint
└── Sharing/                            # Clip sharing endpoints

PocketCastsServer/Private/
├── API Tasks/                          # Individual API call implementations (~39 files)
│   ├── ApiBaseTask.swift               # Base class for all API calls
│   ├── RetrievePodcastsTask.swift      # Fetch subscribed podcasts
│   ├── RetrieveEpisodesTask.swift      # Fetch episode list
│   ├── MetadataTask.swift              # Podcast metadata refresh
│   ├── SubscriptionStatusTask.swift    # Check subscription status
│   └── ...40+ more task files
└── TokenHelper.swift                   # Auth token management (10,173 lines)
```

### How API Calls Work

All API calls subclass `ApiBaseTask` and follow a pattern:

1. Construct a `URLRequest` with auth headers
2. Execute via `URLConnection.sendAsync(request:completion:)`
3. Parse the response (JSON or protobuf)
4. Call completion handler

The `ApiServerHandler` public class exposes a clean Swift API that internally creates and executes these task objects.

### Sync Engine

The sync engine uses **Protocol Buffers** for efficiency. The flow:

1. **Pull**: `SyncTask+ServerChanges` requests changes since last sync timestamp → receives protobuf of modified/added/deleted records → applies to GRDB
2. **Push**: `SyncTask+LocalChanges` finds locally modified records → encodes as protobuf → sends to server
3. **Full Sync**: Resets the sync timestamp and re-downloads everything

**Playback position sync** is separate: `PositionSyncTask` sends `playedUpTo` values to the server periodically (every 30 seconds during playback, see `PlaybackManager.updatesPerSave`).

### Auth & Tokens

- Authentication is handled by the persistent Pocket Casts account system
- `ServerSettings.userId` is the user UUID — this is what PocketRadio uses for Supabase scoping
- `TokenHelper` manages refresh tokens, OAuth flows, and password auth
- Google Sign-In and Apple Sign-In are supported via `ApiServerHandler+SocialAuth.swift`

---

## 6. Playback Architecture

### PlaybackManager (2,722 lines)

`PlaybackManager` is a **singleton** (`PlaybackManager.shared`). It's the central coordinator for all audio playback:

- Manages the `PlaybackQueue` (current episode + up next list)
- Creates and swaps player implementations (`PlaybackProtocol`)
- Handles audio session lifecycle (`AVAudioSession`)
- Manages `MPNowPlayingInfoCenter` (lock screen / Control Center)
- Coordinates `MPRemoteCommandCenter` (headphone controls, CarPlay)
- Tracks sleep timer, chapters, effects

### Player Implementations

`PlaybackProtocol` has multiple implementations:

| Player | Use Case |
|--------|----------|
| `DefaultPlayer` | Standard `AVPlayer`-based playback |
| `EffectsPlayer` | `AVPlayer` with effects (trim silence, volume boost, speed) |
| `GoogleCastManager` | Chromecast streaming |
| `StreamingPlayer` | HTTP live streaming via `AVPlayer` |

Radio stations use `DefaultPlayer` with an AVPlayer connected to the stream URL.

### Key PlaybackManager Methods for Radio

```swift
// M7.1 additions:
func isLiveStream(_ episode: BaseEpisode? = nil) -> Bool  // Uses RadioStationRegistry
func shouldUseMuteControls(for episode: BaseEpisode? = nil) -> Bool  // Live + unseekable
func toggleMute()  // Toggles AVPlayer.isMuted, fires .playbackMuteChanged notification
func stopRadioPlayback()  // Tears down playback entirely
var isMuted: Bool  // Mute state, resets on item change

// Added in M7.2:
func liveStation(for episode: BaseEpisode? = nil) -> RadioStation?  // Registry lookup
handleRadioTrackChanged(_:)  // Per-track artwork resolution (lock screen)
handleRadioTracklistRefreshed(_:)  // Tracklist-based artwork
```

### Audio Session Management

`PlaybackManager` activates/deactivates the `AVAudioSession` on play/pause. Key detail: deactivation is **delayed by 3 seconds** (`deactiveAudioSession`) because iOS gets "cranky" if you deactivate while audio is still playing out. There's a `shouldDeactivateSession` atomic flag to cancel scheduled deactivation if playback resumes.

---

## 7. Radio System (PocketRadio Additions)

**19 files** in `podcasts/Radio/`. This is entirely your team's code.

| File | Purpose |
|------|---------|
| `RadioStation.swift` | `BaseEpisode` conforming model for live streams |
| `RadioStationRegistry.swift` | In-memory UUID→Station lookup (survives SQL round-trip) |
| `RadioBrowserAPI.swift` | radio-browser.info REST client |
| `RadioSupabase.swift` | Supabase client factory (per-user scoped) |
| `RadioFavoritesManager.swift` | CRUD for radio favorites in Supabase |
| `RadioFavoritesSeeder.swift` | First-launch curated station seeding |
| `RadioMetadataObserver.swift` | ICY metadata polling (Shoutcast/Icecast `metadata.xsl` endpoint) |
| `RadioTracklistService.swift` | KCRW-style JSON tracklist parsing |
| `TracklistEntry.swift` | Tracklist entry model (artist, title, imageUrl) |
| `TrackArtworkResolver.swift` | Per-track artwork resolution (tracklist→iTunes→logo fallback chain) |
| `CuratedStation.swift` | Curated station JSON model |
| `CuratedEnhancement.swift` | Enhancement decoration struct (logo, tracklistUrl) |
| `curated_stations.json` | Bundled curated station definitions (KCRW, KEXP, NPR) |
| `FavoritesViewController.swift` | Favorites tab UI |
| `BrowseViewController.swift` | Browse/search tab UI |
| `StreamsHostViewController.swift` | Container for Favorites + Browse tabs |
| `StationDetailViewController.swift` | Station detail screen (logo, bitrate, tracklist, donate) |
| `RadioStationCell.swift` | Station list cell |
| `TracklistCell.swift` | Tracklist row cell |

### Radio Station Lifecycle

1. **Discovery**: User browses radio-browser.info or sees curated seeded stations
2. **Favoriting**: `RadioFavoritesManager` writes to Supabase `radio_favorites` table
3. **Playback**: `RadioStation` is loaded via `PlaybackManager.load(episode:)` → enters the standard podcast playback stack
4. **Metadata**: `RadioMetadataObserver` polls the stream's ICY metadata endpoint every N seconds
5. **Tracklist**: `RadioTracklistService` fetches/enriches from KCRW-style JSON APIs
6. **Artwork**: `TrackArtworkResolver` resolves per-track album art (M7.2)

### RadioBrowserAPI

Talks to `https://de1.api.radio-browser.info/json`:
- `topStations(limit:)` — top voted stations
- `search(query:limit:)` — search by name
- `station(uuid:)` — lookup by UUID

No rate limiting implemented yet (noted as open question). Uses `URLSession.shared` with a custom `User-Agent: PocketRadio/1.0`.

### RadioSupabase

Factory that creates a `SupabaseClient` per operation. Key detail: reads `SUPABASE_URL` and `SUPABASE_ANON_KEY` from `Info.plist` (secrets not in source). Sets `x-user-uuid` header from `ServerSettings.userId` — this is how Supabase scopes data, but RLS is disabled (see `security_concerns.md`).

---

## 8. Error Handling Patterns

### Playback Errors

`PlaybackManager.PlaybackError` is a well-structured error enum:

```swift
enum PlaybackError: Error {
    case internetConnection(logMessage: String?)
    case episodeNotAvailable(errorCode: Int, logMessage: String?)
    case fileCorrupted(logMessage: String?)
    case chromecastError(logMessage: String?)
    case playbackError(logMessage: String?, isLocalFile: Bool)
}
```

Each case provides:
- `userMessage`: Long-form localized string for UI
- `shortUserMessage`: Short form for mini player
- `shortUserAttributedMessage`: Rich text with "Learn More" link
- `userAction`: Support URL for the specific error
- `logMessage`: Debug details sent to `FileLog`

### Fallback Player

When playback fails, the system tries to fall back from `EffectsPlayer` to `DefaultPlayer`:

```swift
if fallbackToDefaultPlayer, let episode = currentEpisode() {
    fallbackToPlayer = DefaultPlayer.self
    load(episode: episode, autoPlay: true, overrideUpNext: false)
}
```

### File Corruption Heuristic

If playback fails near the end of an episode (within 3 minutes of duration, and we've listened to >1 minute), the app marks it as finished rather than erroring — handles corrupt file headers at the tail end of downloads.

### Logging

The app uses two logging systems:
1. **`FileLog`** — writes to a rolling log file on disk (used for debug and crash diagnosis)
2. **`SentryLogger`** — conforms to `ErrorLogger` protocol, sends errors to Sentry (`CrashLoggingAdapter`) in debug, or captures breadcrumbs-only in App Store builds

```swift
struct SentryLogger: ErrorLogger {
    func log(error: Error, context: [String: String]?) {
        if BuildEnvironment.current == .appStore {
            // Breadcrumb only — no error event
            let crumb = Breadcrumb()
            crumb.level = SentryLevel.info
            crumb.category = "grdb"
            crumb.message = error.localizedDescription
            SentrySDK.addBreadcrumb(crumb)
        } else {
            CrashLoggingAdapter.sharedManager?.crashLogging?.logError(error, ...)
        }
    }
}
```

DataManager and ServerConfig both set this as their error logger:
```swift
DataManager.logger = SentryLogger()
ServerConfig.shared.errorLogger = SentryLogger()
```

---

## 9. Memory Management

### Strong Reference Cycles

The codebase uses standard iOS patterns:
- **`[weak self]`** in closures extensively (see `PlaybackManager`'s many NotificationCenter blocks)
- **`unowned`** is rare — mostly avoided
- **Deinit** is consistently implemented with `NotificationCenter.default.removeObserver(self)`

### Caching Strategy

**ImageManager** uses multiple Kingfisher `ImageCache` instances:

| Cache | Purpose | Limit | Expiry |
|-------|---------|-------|--------|
| `subscribedPodcastsCache` | Podcast artwork | 400MB disk | 365 days |
| `networkImageCache` | General network images | Default | 56 days |
| `searchImageCache` | Search results | 10MB disk | Default |
| `userEpisodeCache` | User files | 10MB disk | Default |
| `discoverCache` | Discover feed | Default | Default |

**TrackArtworkResolver** (M7.2) adds an `NSCache<NSString, URL>` for artwork resolution results — this is the in-memory cache for track → artwork URL lookups, separate from the Kingfisher pixel cache.

### Thread Safety

- **`ThreadSafeDictionary`**: Used for `downloadEpisodesCache` and `downloadAndStreamEpisodes` caches (feature-flagged via `downloadsThreadSafeCache`)
- **`AtomicBool`**: Used for `aboutToPlay` and `shouldDeactivateSession` in PlaybackManager
- **GRDB's `DatabaseQueue`**: All database access is serialized through a single writer queue
- **DispatchQueue**: Several custom queues exist — `playerCleanupQueue` for player teardown, `DispatchQueue.global()` for background setup work

### Audio Session Cleanup

The `deactiveAudioSession` method has a deliberate 3-second delay to avoid deactivating while audio buffers are still draining. Uses `TimedActionHelper` with a weak self capture.

---

## 10. Widgets (WidgetExtension)

The widget extension is a **separate process** that communicates with the main app via **App Group UserDefaults**.

### Architecture

```
WidgetExtension/
├── PocketCastsWidgetBundle.swift   # @main WidgetBundle entry point
├── Data/
│   ├── WidgetData.swift            # ObservableObject, loads from App Group
│   └── WidgetEpisode.swift         # Episode model with sync image loading
├── Common/
│   ├── CommonWidgetHelper.swift    # Reads/writes App Group UserDefaults
│   ├── ArtworkViews.swift          # Shared artwork rendering
│   ├── PCWidgetColorScheme.swift   # Theme-aware colors
│   └── Widget+Accentable.swift     # iOS tint handling
├── Now Playing/                    # Now Playing widget (home + lock screen)
├── Up Next/                        # Up Next widget (home + lock screen)
└── App Icon/                       # App icon shortcut widget
```

### Data Flow

1. **Main App writes** → `WidgetHelper.publishUpNextInfo()` serializes `CommonUpNextItem` array to App Group UserDefaults
2. **Widget reads** → `CommonWidgetHelper.loadNowPlayingEpisodes()` deserializes from App Group UserDefaults
3. **Triggers**: `WidgetHelper` observes `playbackStarted`, `playbackPaused`, `playbackTrackChanged`, `upNextQueueChanged`, etc.
4. **Artwork**: Images are copied to `widget_images/` directory in the App Group container during publish (sync, not async — widget timeline can't do network)
5. **PocketRadio Widget**: Added in M8 — mirrors favorites, live stream status, mute state, and track info via `WidgetHelper.publishPocketRadio*` methods

### Key Implementation Detail

Widgets **cannot load images asynchronously** — the timeline provider must supply image data synchronously. So `WidgetEpisode.loadImageData()` does a synchronous `try? Data(contentsOf: imageUrl)` from the app group container during timeline snapshot:

```swift
func loadImageData() {
    guard let imageUrl else { return }
    imageData = try? Data(contentsOf: imageUrl)
}
```

---

## 11. Watch App (Pocket Casts Watch App)

~60 Swift files in the watch target. Uses **SwiftUI** (not WatchKit storyboards).

### Architecture

```
Pocket Casts Watch App/
├── UI/
│   ├── PocketCastsApp.swift           # @main App entry point
│   ├── ExtensionDelegate.swift        # Legacy WKExtensionDelegate (notifications)
│   ├── Main Page/                     # Main menu (podcasts, filters, files, downloads)
│   ├── Now Playing/                   # Now Playing screen + row controller
│   ├── Episode Lists/                 # Episode lists (up next, downloads, filters, files)
│   ├── Episode/                       # Episode detail screen + actions
│   ├── Podcasts/                      # Podcast list
│   ├── Folders/                       # Folder navigation
│   ├── Filters/                       # Filter/playlist list
│   ├── Effects/                       # Playback effects (speed, trim silence)
│   ├── Play Source/                   # Source selection (phone vs watch)
│   └── SwiftUI/                       # Shared SwiftUI components
├── Data & Communication/
│   ├── SessionManager.swift           # WCSession management
│   ├── SessionManager+Send.swift      # Message sending
│   ├── WatchDataManager.swift         # Local watch data cache
│   ├── WatchImageHelper.swift         # Artwork loading
│   └── WatchPlaylist.swift            # Filter data model
├── Complication/
│   └── ComplicationController.swift   # Watch face complications
└── Extensions/                        # Various Swift extensions
```

### How the Watch Communicates

Uses `WCSession` (Watch Connectivity framework):

- **SessionManager** manages the WCSession lifecycle
- Data is transferred via `sendMessage(_:replyHandler:errorHandler:)` for real-time and `transferUserInfo(_:)` for background
- `WatchSyncManager` syncs podcasts and episodes from the phone
- `WatchDataManager` caches data locally using GRDB (same database module as the phone)
- **Playback can happen on the watch itself** (local files synced from phone) or remotely on the phone

### Watch Playback Sources

The watch supports two playback sources:
- **PhoneSourceViewModel**: Controls playback on the paired iPhone (remote control)
- **WatchSourceViewModel**: Plays synced episodes locally on the watch

---

## 12. Build System

### Xcode Project

- **`podcasts.xcodeproj`** — single project, multiple targets
- **"Pocket Casts Staging" scheme** — the scheme used for development builds with your custom bundle ID (`com.jdj.pocketradio`)
- The upstream "pocketcasts" scheme uses Automattic's bundle ID and signing

### Makefile

The local `Makefile` provides convenience commands:

| Command | What It Does |
|---------|-------------|
| `make build_sim` | Build StagingDebug for iPhone 17 Pro simulator (ID `F0042A02...`) |
| `make run_sim` | Build + install + launch on simulator |
| `make build_device` | Build StagingDebug for physical iPhone (UDID `8119F0C0...`) |
| `make run_device` | Build + install + launch on device |
| `make test` | Run PocketCastsTests |
| `make test_staging` | Run tests against StagingDebug |
| `make lint` / `make format` | SwiftLint (auto-correct available) |
| `make generate_code` | Run SwiftGen for string/asset code generation |
| `make external_contributor` | Generate empty API credentials for open-source builds |

### Code Generation

- **SwiftGen**: Generates `Strings+Generated.swift` from string catalogs and asset catalogs. Run with `make generate_code` after adding new assets or localized strings.
- **GRDBMacros**: Custom Swift macro (`@GrdbColumn`) auto-generates GRDB column definitions from model properties.

### Feature Flags

`FeatureFlag` enum in `PocketCastsUtils/Feature Flags/`. Flags can be:
- **Compile-time**: Default value in the enum
- **Remote**: Overridden by Firebase Remote Config (fetched on launch)
- **Local override**: `FeatureFlagOverrideStore` for development/testing
- **Conditional**: `slumber` flag is active when promo code is present

Notable flags: `newSettingsStorage`, `playerIsReadyToPlay`, `downloadsThreadSafeCache`, `playlistsRebranding`, `upNextShuffle`, `enableLocalizationHeaders`, `earlyReloadSubscriptionStatus`.

### Secrets

API credentials are stored in `podcasts/Credentials/ApiCredentials.swift` (not committed). An `ApiCredentials.tpl` template exists. The `external_contributor` Makefile target fills it with empty values for open-source builds.

Supabase secrets are read from `Info.plist` (`SUPABASE_URL`, `SUPABASE_ANON_KEY`).

---

## 13. Notification System

The app uses `NotificationCenter` with `Constants.Notifications` for inter-component communication. Key notifications:

| Notification | Fired When |
|-------------|------------|
| `playbackStarted` | Playback begins |
| `playbackPaused` | Pause |
| `playbackEnded` | Playback ends |
| `playbackTrackChanged` | Track/episode changes |
| `playbackFailed` | Playback error |
| `playbackEffectsChanged` | Speed/trim/boost change |
| `playbackPositionSaved` | Progress saved (every 30s) |
| `playbackMuteChanged` | Radio mute toggled (M7.1) |
| `currentlyPlayingEpisodeUpdated` | Now playing info changed |
| `upNextQueueChanged` | Queue modified |
| `episodeDownloaded` | Download completed |
| `podcastUpdated` | Podcast metadata changed |
| `manyEpisodesChanged` | Bulk episode update |
| `sleepTimerChanged` | Sleep timer state change |
| `.radioStationNowPlayingDidChange` | ICY metadata tick (new song) |
| `.radioTracklistDidRefresh` | Tracklist API response received |
| `.radioFavoritesChanged` | Supabase favorites mutation |
| `.episodeEmbeddedArtworkLoaded` | Embedded artwork parsed |

### Custom Notification Names (Radio)

```swift
extension NSNotification.Name {
    static let radioStationNowPlayingDidChange = NSNotification.Name("radioStationNowPlayingDidChange")
    static let radioTracklistDidRefresh = NSNotification.Name("radioTracklistDidRefresh")
    static let radioFavoritesChanged = NSNotification.Name("radioFavoritesChanged")
}
```

---

## 14. Navigation System

The app uses a hybrid navigation approach:

1. **`MainTabBarController`** — Root tab bar (Podcasts, Filters, Discover, Profile, Streams)
2. **`NavigationManager`** — URL-like navigation with `navigateTo(_:data:)` and route constants
3. **`JLRoutes`** — Deep link routing (handles `pktc://` URLs)
4. **SwiftUI Navigation** — Newer screens (Profile, EndOfYear, Account) use SwiftUI with `NavigationStack`

The Radio feature added the "Streams" tab (6th tab) to the main tab bar. It contains a `StreamsHostViewController` with two sub-tabs: Favorites and Browse.

---

## 15. Theme System

`Theme` is a struct with static properties for all app colors. Themes support:
- **Light/Dark mode** (follows system)
- **Custom themes**: Default (light/dark), Classic, Electricity, Indigo, Rose, Radioactive, Contrast (dark/light), Gold
- **`Themeable*` views**: Subclasses of standard UIKit views that auto-update when the theme changes
- **`Themeable+SwiftUI`**: SwiftUI environment-based theming
- **`AppTheme`**: Enum listing all available themes with metadata

Colors are defined in `Styles.swift` and `Theme+AppColors.swift`.

---

## 16. Download Manager

`DownloadManager` is a singleton handling all episode downloads:

- **Multiple URLSessions**: WiFi-only background, cellular background, cellular foreground
- **Eager initialization**: `setupSessions()` called from `init()` to avoid lazy var race conditions
- **Thread-safe caches**: Uses `ThreadSafeDictionary` (feature-flagged) for episode and stream delegate caches
- **Retry logic**: `DownloadAttempt` struct tracks retry state
- **Progress tracking**: `DownloadProgressManager` publishes download progress
- **Downloaded file cleanup**: `checkIfRestoreCleanupRequired()` on launch finds episodes marked as downloaded where the file is missing

---

## 17. Key Patterns and Conventions

### Singleton Usage

Singletons are used heavily (Apple ecosystem convention):
- `PlaybackManager.shared`
- `DownloadManager.shared`
- `DataManager.sharedManager`
- `ImageManager.sharedManager`
- `WatchManager.shared`
- `WidgetHelper.shared`
- `WidgetData.shared`
- `SiriShortcutsManager.shared`
- `UserEpisodeManager.shared`
- `GoogleCastManager.sharedManager`
- `SubscriptionHelper.shared`

### Observer Pattern

Prefer `NotificationCenter` over delegate protocols for multi-consumer events. Most components add observers in `init()` and remove them in `deinit`.

### File Extensions Convention

Large classes split across files using `ClassName+Purpose.swift`:
- `PlaybackManager` has no direct extensions (huge single file)
- `AppDelegate+Analytics.swift`, `AppDelegate+Defaults.swift`, etc.
- `DownloadManager+Logging.swift`, `DownloadManager+SessionManagement.swift`
- `NowPlayingPlayerItemViewController+Seek.swift`, `+Shelf.swift`, `+Update.swift`, `+UpNextPan.swift`
- `PodcastManager+Cleanup.swift`, `PodcastManager+Delete.swift`

### Threading Convention

```swift
// UI work always on main
DispatchQueue.main.async { ... }

// Heavy work on global queue
DispatchQueue.global().async { [weak self] in ... }
DispatchQueue.global(qos: .userInitiated).async { ... }

// Post notifications on main thread
NotificationCenter.postOnMainThread(notification: ...)
```

### Async/Await Adoption

Newer code (Radio) uses `async/await` while older code uses completion handlers. `RadioBrowserAPI`, `RadioFavoritesManager`, `RadioTracklistService` all use async/await. `PlaybackManager` still uses completion handlers (callback-based).

---

## 18. How the Pieces Fit Together — End-to-End Flows

### Playing a Radio Station

1. User taps station in Browse or Favorites
2. `StationDetailViewController` → user taps "Play"
3. `RadioStation` is constructed with `stationId`, `streamUrl`, metadata
4. `PlaybackManager.load(episode:station, autoPlay:true, overrideUpNext:true)`
5. `RadioStationRegistry` stores the station in-memory
6. `PlaybackQueue` adds the episode to "currently playing" slot
7. AVPlayer is set up with the stream URL via `DefaultPlayer`
8. `RadioMetadataObserver` starts polling the stream's ICY metadata endpoint
9. On metadata tick: posts `.radioStationNowPlayingDidChange` → UI updates artist/title
10. If station has `tracklistUrl`: `RadioTracklistService` fetches tracklist JSON, posts `.radioTracklistDidRefresh`
11. M7.2: `TrackArtworkResolver` resolves artwork → Kingfisher loads → `MPNowPlayingInfoCenter` updates

### Syncing Favorites

1. User favorites a station → `RadioFavoritesManager.addFavorite(stationId:name:)`
2. Creates `SupabaseClient` with `x-user-uuid: ServerSettings.userId` header
3. Inserts row into Supabase `radio_favorites` table
4. Posts `.radioFavoritesChanged` notification
5. `FavoritesViewController` reloads from Supabase
6. `WidgetHelper` publishes updated favorites to App Group for widget mirroring

### App Launch Sequence

1. `main.swift` → `UIApplicationMain` → `AppDelegate`
2. `AppDelegate.didFinishLaunchingWithOptions`:
   - Configure Firebase, Sentry
   - Setup analytics, secrets
   - Create unique app ID (UUID)
   - Setup Google Cast, routes
   - Register for push notifications
   - On background queue: setup sync delegate, check defaults, log downloads, ImageManager cleanup, Widget cleanup, Siri setup, start queued downloads
   - Setup badge, Watch connectivity, shortcuts
   - Register background refresh task
   - Setup IAP, sign-out listener
   - **`RadioFavoritesSeeder.seedIfNeeded()`** — one-shot curated station seeding
3. `SceneDelegate.scene(willConnectTo:)`:
   - Creates `MainTabBarController` as root view controller
   - Makes window key and visible
   - Handles shortcut item, URL, or user activity from launch options

### Upstream Merge Considerations

The codebase is a fork of `Automattic/pocket-casts-ios`. Files that have been modified for PocketRadio:
- `podcasts/Radio/` — entirely new
- `podcasts/PlaybackManager.swift` — added mute/stop, live stream artwork
- `podcasts/DefaultPlayer.swift` — radio stream support
- `podcasts/Constants.swift` — Radio-related constants
- `podcasts/SceneDelegate.swift` — likely unchanged
- `Modules/Package.swift` — added Supabase dependency

For any upstream merge, the biggest conflict areas will be `PlaybackManager.swift` (heavily modified) and `DefaultPlayer.swift`.

---

## 19. Supabase / Backend

Located at `/Users/jdj/Documents/code/PocketRadio/supabase/`:

```
supabase/
├── migrations/     # SQL migrations for radio_favorites, listen_time, donations, etc.
├── config.toml     # Supabase project config
└── seed.sql        # Seed data
```

### Tables (migration-based):
- `radio_favorites` — user's favorited radio stations (scoped by `user_uuid`)
- `custom_streams` — user-added custom stream URLs
- `listen_time` — listening history
- `donations` — donation tracking

### Security Note
RLS (Row Level Security) is **disabled** (migration 004). Data scoping relies entirely on the `x-user-uuid` header from the client. A malicious client that guesses another user's UUID could read/write their data. Accepted risk for MVP.

---

## 20. Known Issues & Open Questions

From `docs/todo.md`:

- **WordPress.com OAuth**: Not yet registered for `dotcomSecret`
- **Account sync loading**: No loading state on first sync
- **Menubar app**: Architecture TBD (your next milestone)
- **iOS→macOS install flow**: Undecided
- **Podcast listen time**: Need to check if PC tracks this internally
- **Menubar auth**: Manual UUID paste MVP approach pending
- **radio-browser rate limits**: Single endpoint, no redundancy yet
- **Upstream merge cadence**: Undecided
- **Shared code iOS/menubar**: Currently duplicated, needs SPM extraction

---

## 21. Quick Reference: Key Files to Know

| File | Why It Matters |
|------|---------------|
| `podcasts/PlaybackManager.swift` | Central playback — heavily modified for Radio |
| `podcasts/Radio/RadioStation.swift` | Radio model conforming to BaseEpisode |
| `podcasts/Radio/RadioStationRegistry.swift` | Source of truth for "is this a radio station?" |
| `podcasts/Radio/RadioBrowserAPI.swift` | radio-browser.info client |
| `podcasts/Radio/RadioSupabase.swift` | Supabase client factory |
| `podcasts/Radio/RadioFavoritesManager.swift` | Favorites CRUD |
| `podcasts/DefaultPlayer.swift` | AVPlayer wrapper (radio plays through this) |
| `podcasts/DownloadManager.swift` | Episode downloads & streaming |
| `podcasts/ImageManager.swift` | All image caching (Kingfisher) |
| `podcasts/WidgetHelper.swift` | App Group bridge for widgets |
| `podcasts/Constants.swift` | All notification and UserDefaults keys |
| `Modules/Sources/PocketCastsServer/Public/API/ApiServerHandler.swift` | Main REST client |
| `Modules/Sources/PocketCastsServer/Public/Sync/SyncManager.swift` | Sync engine |
| `Modules/Sources/PocketCastsDataModel/Public/DataManager.swift` | Database layer (58K lines) |
| `Modules/Package.swift` | All dependencies + target wiring |
| `Makefile` | Build/test/run commands |
