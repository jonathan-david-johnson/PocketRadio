# M3: Up-Next Podcast Playback

**Status**: COMPLETED — 2026-05-21

## Goal

Show the user's top Pocket Casts up-next podcast in the menubar popover and play it.

## Done when

- After login, the player view shows the top episode from the up-next queue (title)
- A "refresh" button re-fetches the up-next queue
- Play button streams the episode's audio URL via AVPlayer
- Falls back to KCRW stream if no episode is available
- On relaunch (with existing Keychain token), up-next is fetched in background

## Architecture

```
Fetch: Bearer token → POST api.pocketcasts.com/up_next/sync
  Request: Api_UpNextSyncRequest { deviceTime(1), version=2(2), deviceID(6) }
  Response: Api_UpNextResponse { serverModified(1), episodes(4)[EpisodeResponse] }
  EpisodeResponse: { title(1), url(2), podcast(3), uuid(4), published(5) }
  Playback: AVPlayer with episode url field (MP3 remote URL)
```

## Files Changed

| File | Changes |
|------|---------|
| `Services/APIService.swift` | Added `fetchUpNext(token:)`, `UpNextEpisode` model, `encodeUpNextRequest()`, `decodeUpNextResponse()`, `decodeEpisodeResponse()`, Int64 varint helpers |
| `View Models/PlayerViewModel.swift` | `topEpisode`, `fetchUpNext()`, `nowPlayingTitle`/`nowPlayingSubtitle`, fetches on init + after login |
| `ContentView.swift` | Shows episode title, refresh button, now-playing subtitle |

## API Verified

```bash
$ POST api.pocketcasts.com/up_next/sync → HTTP 200
$ Response: 815 bytes, 3 episodes decoded
$ Episode 1: "The Thunder Get Physical to Take Game 2..."
$   url: https://pdst.fm/e/traffic.megaphone.fm/GLT4935759398.mp3 ✅
```

## Known Issue

macOS Keychain authorization dialog appears on first token read after fresh build. User must click "Always Allow" once to grant permanent access. This is expected macOS security behavior with `kSecAttrAccessibleAfterFirstUnlock`.

## Manual Smoke

1. Approve Keychain dialog (first run only)
2. Menubar → player view shows episode title from up-next
3. Click Play → audio streams from the episode URL
4. Click refresh icon → re-fetches up-next
5. Quit & relaunch → automatically shows up-next (no login needed)
