# M8: <one-line title>

**Status**: NOT STARTED
**Builds on**: M7.3 (committed at `3a23c22`).

## Goal

- New Widget this will be a 4x2 widget. two sections
- Top section: small icon of the palying track/pdocast, right of that the name in bold, artist under unbolded, right of that 3 buttons: back pause/play fwd 
- Bottom section: 4 icons, first icon: whatever podcast was last played, this is I believe at the top of the up/next list, next 3 icons are the top 3 favorite streams
- Middle of top seciton, the part wit hthe title and artist can be cut off with ... if it is larger than available space, but lets pick a small font
- play, pause fwd bcak buttons will need to respect what kind of track is playing. If mp3 or podcast play/back, if stream show a mute and a button to go to track list that would open teh app

## Done when

- A new WidgetKit widget kind `PocketRadio_Widget` (`.systemMedium`, 4x2) appears in the widget picker alongside the existing Now Playing / Up Next widgets.
- **Top row** renders a 1-line bold title + 1-line unbold artist that truncate with `…` at a small font (`.footnote` bold / `.caption` regular), with a 44x44 artwork tile on the left.
- **Top row controls** are context-aware:
  - Podcast / on-demand episode → `back 15s` · `play/pause` · `fwd 30s` (three `AppIntent` buttons).
  - Live radio (`shouldUseMuteControls == true`) → `mute toggle` · `open tracklist` (deep link), with the skip controls hidden. No skip controls ever shown for live streams.
- **Bottom row** shows exactly 4 tiles:
  1. Top-of-Up-Next episode artwork (deep-link → episode in app, mirrors existing `pktc://widget-episode/<uuid>`).
  2–4. Top 3 favorite radio stations (in `RadioFavoritesManager` `localOrder`), each tile is the station logo and deep-links to `pktc://station/<stationId>?source=widget` which routes to `StationDetailViewController`.
- If a favorite slot is empty (user has < 3 favorites), the tile renders a placeholder "Add favorites" prompt that opens `pktc://favorites`.
- Title/artist source: for live radio, pulled from `TrackArtworkResolver.bestResolveEntry` snapshot mirrored into the App Group; for podcasts, uses the existing `WidgetEpisode.podcastName` / `episodeTitle`.
- Tapping the artwork in the top row opens the player (existing `pktc://last_opened` URL).
- Widget refreshes on the same notifications as `WidgetHelper` (playback start/pause/track changed, up-next changed, plus new triggers for favorites changes and live-track changes).
- `make build_staging` and `make test_staging` pass. Manual smoke walkthrough completes with both a podcast and a live radio station in the player.

## Architecture

Mirror the existing widget patterns under `WidgetExtension/`:

- **Widget shell**: copy the shape of `WidgetExtension/Now Playing/NowPlayingWidget.swift` + `NowPlayingProvider.swift` + `NowPlayingEntry.swift` + `NowPlayingEntryView.swift`. Register the new widget in `WidgetExtension/PocketCastsWidgetBundle.swift` (currently lists `NowPlayingWidgetBold`, `UpNextWidgetBold`, `NowPlayingWidget`, `UpNextWidget`, `NowPlayingLockScreenWidget`, `AppIconWidget`, `UpNextLockScreenWidget`).
- **Supported families**: `[.systemMedium]` only (`.systemMedium` = 4x2). No small/large/lockscreen variants in this milestone.
- **App Group IPC**: the widget reads from `UserDefaults(suiteName: SharedConstants.GroupUserDefaults.groupContainerId)` exactly like `CommonWidgetHelper`. **All new state** (favorites snapshot, live-stream flag, current track title/artist/artwork-url) must be mirrored to this same suite by the main app — widgets cannot reach `RadioFavoritesManager`, `PlaybackManager`, or `TrackArtworkResolver` directly.
- **Tap actions**: use the existing iOS-17 `AppIntent` channel established by `podcasts/PlayEpisodeIntent.swift` + `AppPlayEpisodeIntentExtension.swift` (real impl) + `WidgetPlayEpisodeIntentExtension.swift` (widget-side stub that never runs). New intents (`SkipBackIntent`, `SkipForwardIntent`, `MuteToggleIntent`) follow the same split: declared in `podcasts/` so they're available to both the app target and the widget extension; a "real" extension lives next to `AppPlayEpisodeIntentExtension.swift` and a no-op stub lives next to `WidgetPlayEpisodeIntentExtension.swift`. The `OpenTracklistIntent` is replaced with a plain `widgetURL(...)` deep link since opening the host app does not need an intent.
- **Deep links**: extend the existing `pktc://` URL handler. New URLs:
  - `pktc://station/<stationId>?source=widget` — opens `StationDetailViewController` (favorites tile + open-tracklist button).
  - `pktc://favorites?source=widget` — opens the Favorites tab (placeholder tile).
  Existing `pktc://widget-episode/<uuid>` is reused for the Up Next tile and `pktc://last_opened` for the top-row artwork.
- **Live vs on-demand decision** is computed in the main app inside `WidgetHelper` (which already runs on playback notifications) and mirrored as a bool `pocketRadioIsLiveStream` into the App Group. The widget never re-derives it.
- **Favorites snapshot shape**: serialize as JSON `[{ stationId, name, logoUrl }]` taking `prefix(3)` of `RadioFavoritesManager.shared.order(...)` resolved to Supabase `FavoriteStation` rows. Logo images cached to `Application Support/widget_images/station_<stationId>.jpg` in the App Group container, exactly mirroring `WidgetEpisode.urlForItem` for episode images.

The 4x2 layout is a single `VStack(spacing: 8)` with a `HStack` top section (artwork · title/artist · controls) and a `HStack` bottom section of 4 equal tiles. Title uses `lineLimit(1)` + `truncationMode(.tail)`; both lines use `.footnote` (bold) / `.caption2` (regular) to keep things compact.

## Files

### NEW

- `WidgetExtension/Pocket Radio/PocketRadioWidget.swift` — `Widget` declaration, `supportedFamilies = [.systemMedium]`, kind `PocketRadio_Widget`.
- `WidgetExtension/Pocket Radio/PocketRadioProvider.swift` — `TimelineProvider`; reads `WidgetData` + new favorites/live-track helpers.
- `WidgetExtension/Pocket Radio/PocketRadioEntry.swift` — `TimelineEntry` carrying `nowPlaying: WidgetEpisode?`, `isLive: Bool`, `liveTrack: WidgetLiveTrack?`, `isPlaying: Bool`, `isMuted: Bool`, `favorites: [WidgetFavoriteStation]`.
- `WidgetExtension/Pocket Radio/PocketRadioEntryView.swift` — SwiftUI view: top row (artwork, title/artist, 3 controls) + bottom row (4 tiles).
- `WidgetExtension/Pocket Radio/PocketRadioControls.swift` — control button subviews; switches between podcast (back/play/fwd) and live (mute/tracklist) variants.
- `WidgetExtension/Data/WidgetFavoriteStation.swift` — App-Group-decodable favorite station snapshot (mirrors `WidgetEpisode` pattern).
- `WidgetExtension/Data/WidgetLiveTrack.swift` — Snapshot of `{ stationId, title, artist, artworkUrl }` from `TrackArtworkResolver`.
- `podcasts/SkipBackIntent.swift` — `AudioPlaybackIntent` for `-15s`.
- `podcasts/SkipForwardIntent.swift` — `AudioPlaybackIntent` for `+30s`.
- `podcasts/MuteToggleIntent.swift` — `AudioPlaybackIntent` toggling `PlaybackManager.shared.isMuted` (or equivalent live-stream mute path used by `MiniPlayerViewController`).
- `podcasts/AppSkipBackIntentExtension.swift`, `podcasts/AppSkipForwardIntentExtension.swift`, `podcasts/AppMuteToggleIntentExtension.swift` — real `perform()` bodies (app target).
- `podcasts/WidgetSkipBackIntentExtension.swift`, `podcasts/WidgetSkipForwardIntentExtension.swift`, `podcasts/WidgetMuteToggleIntentExtension.swift` — no-op widget stubs (mirror `WidgetPlayEpisodeIntentExtension.swift`).
- `PocketCastsTests/Tests/Widget/PocketRadioProviderTests.swift` — exercises the provider against synthesized App Group state for podcast / live-stream / no-favorites scenarios.

### EDIT

- `WidgetExtension/PocketCastsWidgetBundle.swift` — register `PocketRadioWidget()` in the `WidgetBundle`.
- `podcasts/SharedConstants.swift` — add new keys: `pocketRadioFavorites`, `pocketRadioIsLiveStream`, `pocketRadioLiveTrack`, `pocketRadioIsMuted`. Existing keys stay.
- `podcasts/WidgetHelper.swift` — extend `publishUpNextInfo` (or add a sibling `publishPocketRadioInfo`) to mirror favorites + live-stream flag + live-track snapshot to the App Group. Hook new observers: `RadioFavoritesManager` change notification, `TrackArtworkResolver` updates, mute-state notification. Add `PocketRadio_Widget` kind to the `updateAllWidgets` reload list.
- `podcasts/Radio/RadioFavoritesManager.swift` — post a `Notification.Name.radioFavoritesChanged` after `setOrder`, `addFavorite`, `removeFavorite` so `WidgetHelper` can republish (only if no equivalent notification exists; check first).
- `podcasts/Radio/TrackArtworkResolver.swift` — emit a notification when `bestResolveEntry` result changes for the currently-playing station, OR (preferred) have `WidgetHelper` poll on `playbackTrackChanged` + a new ICY-metadata-changed notification. Wire whichever path already exists; do not invent new pub/sub if `NowPlayingHelper` / lock-screen update path already broadcasts.
- `podcasts/Main/NavigationManager.swift` (or wherever `pktc://` URLs are parsed — confirm in reference sweep) — handle `pktc://station/<stationId>` and `pktc://favorites`.
- `podcasts/AppDelegate.swift` (or scene delegate URL handler — confirm in sweep) — route new URLs to `NavigationManager`.
- `podcasts/Analytics/AnalyticsEvent.swift` — add `pocketRadioWidgetInteraction` event (mirror existing `widgetInteraction`).
- `podcasts/en.lproj/Localizable.strings` — strings for "Add favorites" placeholder, tracklist button accessibility label, mute button accessibility label.

### NO CHANGE

- `WidgetExtension/Now Playing/*` — existing widget unchanged; new widget is a parallel kind.
- `WidgetExtension/Up Next/*` — same.
- `WidgetExtension/Common/CommonWidgetHelper.swift` — reused as-is for App Group access patterns; do not add Pocket-Radio-specific helpers here, keep them in the new `Pocket Radio/` subdir to keep the upstream-shared helper clean.
- `podcasts/PlayEpisodeIntent.swift` — existing intent unchanged; new widget reuses it for the Up Next tile if we ever add play-on-tap there (out of scope this milestone — Up Next tile is a deep link only).

## Risks / Edge cases

- **Stale App Group data on cold widget render**: the widget can render before `WidgetHelper` has run. Mitigation: provider returns a placeholder entry when keys are missing; do not crash on nil. Match `NowPlayingProvider`'s nil-tolerant pattern.
- **`shouldUseMuteControls` flips mid-render**: between the time the widget timeline was generated and the user taps, the stream could have ended. Mitigation: each intent re-checks `PlaybackManager.shared.shouldUseMuteControls()` server-side and no-ops if the state no longer matches.
- **Favorites < 3**: fewer than 3 favorited stations → render "Add favorites" placeholders. Do not crash, do not show empty boxes.
- **Tile image fetch on widget process**: widgets cannot use async loaders. Mitigation: `WidgetHelper` writes pre-downsized JPEGs to the App Group container (`widget_images/station_<id>.jpg`) — same trick `WidgetEpisode` already uses for UserEpisode artwork.
- **iOS < 17**: `AppIntent`-driven `Toggle`/`Button` requires iOS 17. Below that, the existing widgets degrade to non-interactive labels (see `playToggleOrPlaybackLabel` in `NowPlayingEntryView`). Mirror the same `if #available(iOS 17, *)` fallback — top-row buttons render as static glyphs that open the app on tap.
- **Mute state divergence**: the widget shows the last-published `isMuted`; if the user mutes via in-app, the widget must refresh. Mitigation: `WidgetHelper` reloads the `PocketRadio_Widget` kind on `Constants.Notifications.playbackTrackChanged` and a new mute-state notification posted from `PlaybackManager` (check if one exists before adding — `MiniPlayerViewController` already reads `shouldUseMuteControls`, so the trigger likely exists).
- **Deep-link race**: tapping a favorite tile while the app is mid-launch needs the URL queued. The existing `pktc://widget-episode/<uuid>` path already handles this — follow the same queue-and-replay mechanism in `NavigationManager`.
- **Curated vs ad-hoc station**: `pktc://station/<stationId>` must work for both seeded/curated stations and user-added ones. Resolve via the same path Favorites uses (`FavoriteStation.stationId` → Supabase row → `StationDetailViewController`).

## Reference sweep

Before declaring the file list complete, run:

```bash
# Confirm where pktc:// URLs are parsed today
grep -rn 'pktc://' podcasts/ WidgetExtension/ Modules/

# Confirm widget kind strings are unique
grep -rn 'PocketRadio_Widget\|Now_Playing_Widget\|Up_Next_Widget' podcasts/ WidgetExtension/

# Make sure all WidgetBundle entries are listed
grep -rn 'WidgetBundle\|Widget()' WidgetExtension/

# Find every place that broadcasts a favorites change today
grep -rn 'RadioFavoritesManager\|radioFavoritesChanged\|favoritesChanged' podcasts/ Modules/

# Find every place that mirrors data to the App Group so we mirror the new state next to it
grep -rn 'GroupUserDefaults\|groupContainerId\|suiteName: SharedConstants' podcasts/ WidgetExtension/ Modules/

# Confirm intent split pattern (real vs widget-stub) is mirrored for every new intent
grep -rn 'intentPlayback\|AppPlayEpisodeIntent\|WidgetPlayEpisodeIntent' podcasts/

# Confirm live-stream predicates and mute path
grep -rn 'shouldUseMuteControls\|liveStation(for\|isLiveStream' podcasts/ WidgetExtension/

# Confirm TrackArtworkResolver emits a change signal we can hook
grep -rn 'TrackArtworkResolver\|bestResolveEntry' podcasts/
```

Address every hit in the plan or note why it is intentionally skipped before declaring file list complete.

## Automated tests

Per AGENTS.md test layout — files under `PocketCastsTests/Tests/Widget/` are auto-picked up by the `PBXFileSystemSynchronizedRootGroup`, no pbxproj edit needed.

- `PocketCastsTests/Tests/Widget/PocketRadioProviderTests.swift`
  - `test_podcast_state_yields_back_play_fwd_controls()` — seed App Group with `isLiveStream=false` + a `WidgetEpisode`, assert entry uses podcast control set.
  - `test_live_state_yields_mute_and_tracklist_controls()` — seed App Group with `isLiveStream=true` + a `WidgetLiveTrack`, assert entry uses live control set and tracklist URL.
  - `test_favorites_under_three_pads_with_placeholders()` — seed 1 favorite, assert 3 placeholder tiles.
  - `test_no_now_playing_renders_idle_state()` — empty App Group, provider returns nil-now-playing entry without crashing.
- `PocketCastsTests/Tests/Widget/WidgetHelperPocketRadioTests.swift`
  - `test_publish_favorites_writes_three_to_app_group()` — drive `WidgetHelper` with a stub favorites list and assert encoded JSON in the App Group suite has exactly 3 entries in order.
  - `test_publish_live_flag_tracks_playback_manager_state()` — toggle `PlaybackManager.shared` stub between podcast/live, assert `pocketRadioIsLiveStream` reflects current state.

Use the existing `XCTest + @testable import podcasts` pattern (instantiate, call into the helper directly, assert on `UserDefaults(suiteName:)` contents — same shape as any test that pokes at shared state).

## Manual smoke

1. `make run_sim`
2. From the home screen, long-press, hit `+`, find "Pocket Radio" widget. Verify only the `.systemMedium` size offers. Add it to the home screen.
3. With nothing playing: widget shows idle artwork + "Add favorites" placeholders for empty favorite slots.
4. In-app, play a downloaded podcast episode. Widget top row shows podcast artwork, bold episode title, unbold podcast name, and `back/play/fwd` buttons. Tap play/pause — playback toggles, widget reflects.
5. Tap `back 15s` and `fwd 30s` — playback position jumps accordingly.
6. Add 3+ favorite radio stations (Favorites tab). Reorder them. Widget bottom row reflects the new top-3 order within ~5 seconds.
7. Play a live radio station (one where `shouldUseMuteControls == true`). Widget controls swap to `mute` + `tracklist`. Title/artist update with ICY metadata.
8. Tap `mute` — audio mutes, widget icon flips. Tap again — unmutes.
9. Tap `tracklist` — app foregrounds to the Station Detail tracklist tab for the currently-playing station.
10. Tap the top-of-Up-Next tile (bottom row, slot 1) — app foregrounds to that episode.
11. Tap a favorite tile (bottom row, slots 2–4) — app foregrounds to that station's `StationDetailViewController`.
12. Background the app, lock device, unlock — widget still renders correctly (no blank state, no stale "Now Playing" from a previous session).
13. With < 3 favorites total, verify placeholder tiles open Favorites tab.

## Agentic plan

Sequential phases. Each agent reads this file as ground truth.

### Phase 1 — App Group mirror + intents

- Agent: `general-purpose`, model: Sonnet 4.6
- Goal: extend `WidgetHelper` + `SharedConstants` to publish favorites, live-stream flag, and live-track snapshot to the App Group; add the three new `AppIntent`s with their app-side and widget-side extensions.
- Files allowed: `podcasts/SharedConstants.swift`, `podcasts/WidgetHelper.swift`, `podcasts/SkipBackIntent.swift`, `podcasts/SkipForwardIntent.swift`, `podcasts/MuteToggleIntent.swift`, `podcasts/App{SkipBack,SkipForward,MuteToggle}IntentExtension.swift`, `podcasts/Widget{SkipBack,SkipForward,MuteToggle}IntentExtension.swift`, `podcasts/Radio/RadioFavoritesManager.swift` (notification only), `podcasts/Analytics/AnalyticsEvent.swift`, `podcasts/en.lproj/Localizable.strings`, plus pbxproj registration for the new app-side Swift files.
- Verify: `make build_staging`

### Phase 2 — Widget UI

- Agent: `caveman:cavecrew-builder`, model: Sonnet 4.6
- Goal: build the widget itself in `WidgetExtension/Pocket Radio/` plus the App Group data adapters. Register in `PocketCastsWidgetBundle`. No tests yet.
- Files allowed: everything under `WidgetExtension/Pocket Radio/`, `WidgetExtension/Data/WidgetFavoriteStation.swift`, `WidgetExtension/Data/WidgetLiveTrack.swift`, `WidgetExtension/PocketCastsWidgetBundle.swift`, plus the WidgetExtension target's pbxproj registration.
- Verify: `make build_staging` and visually confirm the widget appears in the simulator widget picker.

### Phase 3 — Deep links + tests

- Agent: `general-purpose`, model: Sonnet 4.6
- Goal: wire `pktc://station/<stationId>` and `pktc://favorites` through `NavigationManager` + AppDelegate/SceneDelegate URL handler. Add unit tests under `PocketCastsTests/Tests/Widget/`.
- Files allowed: `podcasts/Main/NavigationManager.swift`, `podcasts/AppDelegate.swift` (or scene delegate — confirm via sweep), `PocketCastsTests/Tests/Widget/*`.
- Verify: `make test_staging ONLY_TESTING=PocketCastsTests/PocketRadioProviderTests` and `make test_staging ONLY_TESTING=PocketCastsTests/WidgetHelperPocketRadioTests`.

### Phase 4 — Review

- Agent: `caveman:cavecrew-reviewer`, model: Sonnet 4.6
- Focus: App Group key collisions with upstream, intent split correctness (app extension vs widget stub), live-stream predicate consistency (everything goes through `shouldUseMuteControls`), iOS-17 availability fallbacks, missing pbxproj entries for app-side files, accessibility labels on the new buttons, and any reference-sweep hits not addressed.

### Phase 5 — Manual smoke

- Human runs Manual smoke list. Sign off before commit.
