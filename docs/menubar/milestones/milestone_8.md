# M8 — Headphone / Media Key Remote Control

**Status**: DONE

## Goal

Respect hardware media controls (Bluetooth headphone play/pause/skip buttons, keyboard media keys) for playback in the menubar app. Currently the app has no `MPRemoteCommandCenter` / `MPNowPlayingInfoCenter` integration, so headphone buttons do nothing (or get routed to whatever app macOS considers "now playing", e.g. Music/Spotify).

## Changes

### 1. Now Playing Info Publishing
- Add `import MediaPlayer` to `PlayerViewModel`.
- Populate `MPNowPlayingInfoCenter.default().nowPlayingInfo` on every playback state change:
  - `MPMediaItemPropertyTitle` — `nowPlayingTitle`
  - `MPMediaItemPropertyArtist` — station name (radio) or podcast title (podcast)
  - `MPNowPlayingInfoPropertyElapsedPlaybackTime` / `MPMediaItemPropertyPlaybackDuration` — from `currentTimeSeconds` / `durationSeconds`
  - `MPNowPlayingInfoPropertyPlaybackRate` — `1.0` playing / `0.0` paused
  - `MPNowPlayingInfoPropertyIsLiveStream` — `true` for radio sources
- Update from `startPlayback()`, `pausePlayback()`, `stopPlayback()`, and the periodic time observer (`updateScrubTimes()`), throttled to avoid redundant writes.

### 2. Remote Command Handlers
- Register once (e.g. in `PlayerViewModel.init()` or app launch):
  - `playCommand` / `pauseCommand` / `togglePlayPauseCommand` → `togglePlayback()` / `pausePlayback()`
  - `nextTrackCommand` → `skipForward()`
  - `previousTrackCommand` → `skipBack()`
  - `changePlaybackPositionCommand` → `scrub(toSeconds:)`
- Toggle `isEnabled` on skip/seek commands based on `shouldUseMuteControls` (live radio streams aren't seekable — matches existing `showSkipControls` logic).

### 3. Central Hook
- Reuse existing `notifyNowPlayingChanged()` as the single point that refreshes `MPNowPlayingInfoCenter` alongside its current `NotificationCenter` post.

## Out of Scope
- Lock-screen / Control Center artwork (no artwork source for radio streams)
- iOS-side now-playing integration (separate app/target)

## Verification
1. Build + run menubar app, start podcast or radio playback.
2. Connect Bluetooth headphones; press play/pause button — playback should toggle.
3. Press skip-forward/back (where supported) on a podcast — should jump per `skipForwardSeconds`/`skipBackSeconds`.
4. For a live radio stream, confirm skip/seek controls are disabled/no-op (matches `shouldUseMuteControls`).
5. Check macOS Control Center "Now Playing" widget shows correct title and play state.
