# M1: Player Integration Proof

**Status**: COMPLETE — 2026-05-10

## Goal

A hardcoded KCRW stream plays inside PC's existing player with no crashes.
No UI, no Supabase, no navigation changes. Just audio.

## Done when

- `RadioStation("kcrw", streamUrl: "https://streams.kcrw.com/e24_mp3")` conforms to `BaseEpisode`
- `PlaybackManager.shared.load(episode: station, autoPlay: true)` starts audio
- Mini player appears, shows "KCRW", play/pause works
- Backgrounding the app → audio continues
- No crashes, no "urlForEpisode returned nil" failure

## What was built

1. `podcasts/Radio/RadioStation.swift` — BaseEpisode conformer
2. `podcasts/Radio/RadioStationRegistry.swift` — in-memory UUID→station map
3. `podcasts/Radio/StreamsHostViewController.swift` — M1 test harness (3 play buttons)
4. `podcasts/EpisodeManager.swift` — `else if let url = episode.downloadUrl` fallback
5. `podcasts/PlaybackQueue.swift` — registry check before UserEpisode stub
6. `podcasts/DefaultPlayer.swift` — re-trigger playback on readyToPlay
7. `podcasts/Main/MainTabBarController.swift` + `podcasts/AnalyticsHelper.swift` — `.streams` tab wired up

## Lessons learned

### PlaybackQueue reloads episodes from SQLite by UUID

The biggest surprise. After `PlaybackManager.load(episode:)`, the queue serializes the episode UUID to SQLite (`PlaylistEpisode` Core Data entity) and immediately calls `refreshList → cacheTopEpisode → episodeAt(index:)` which reloads the episode from the DB. RadioStation is not in the DB, so the queue replaced it with a dead `UserEpisode` stub (no stream URL). Fixed via `RadioStationRegistry` — an in-memory map keyed by stationId that `episodeAt(index:)` checks before falling back to the stub.

**Implication for M2+**: every time a RadioStation enters `PlaybackManager.load`, it must be registered first via `RadioStationRegistry.shared.register(station)`.

### AVPlayer rate must be set after readyToPlay for live streams

PC sets `player?.rate = 1.0` to start playback synchronously during `play()`. For podcasts this is fine because they use `seekTo(playedUpTo)` and restart in the seek completion handler. RadioStation has `playedUpTo = 0` and `currentTime() = 0` → no seek triggered → rate set before item is ready → AVPlayer ignores it → silence.

Fixed by adding a readyToPlay check in `DefaultPlayer.playerStatusDidChange`: if `shouldKeepPlaying && rate == 0`, call `performSetPlaybackRate()`. This is a general fix that benefits any future live-stream-like episode type.

### Xcode file location vs xcodeproj group path

When adding files to Xcode project, the xcodeproj group `path` property determines where on disk Xcode looks for the file relative to the parent group. A group at the project root with `path = Radio` resolves to `<repo>/Radio/`, not `<repo>/podcasts/Radio/`. Changed group path to `podcasts/Radio` to match where files live.

### App Clip target shares PlaybackQueue.swift

`Pocket Casts App Clip` compiles `PlaybackQueue.swift` too. `RadioStationRegistry` isn't available to App Clip, so the lookup needed `#if !APPCLIP` guard.

### Embed Watch Content build phase

The `podcasts` target embeds the Watch app via a `PBXCopyFilesBuildPhase`. Without the watchOS SDK installed, this phase fails at run time even on iPhone simulators. Removed the Watch app from the embed phase files list in xcodeproj for local dev. **Note**: restore this for production builds / CI when watchOS SDK is available.

## Commits

- `89dd5d0` — M1: RadioStation BaseEpisode conformer + Streams tab stub
- `681497b` — M1 working: all three streams play audio
- `3591b1b` — Remove stale StreamsHostViewController.swift from repo root
