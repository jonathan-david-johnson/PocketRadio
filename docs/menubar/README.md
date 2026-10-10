# PocketRadio Menubar App

macOS menubar companion app for PocketRadio. Plays the user's top up-next podcast and favorite radio streams from a lightweight NSStatusItem panel.

## Architecture

```
pocket-radio-menubar/
├── PocketRadio Menubar.xcodeproj
├── PocketRadio/
│   ├── PocketRadioApp.swift          # @main; NSStatusItem + floating NSPanel (KeyablePanel)
│   ├── ContentView.swift             # Panel UI: pills, controls, lists, lyrics
│   ├── View Models/PlayerViewModel.swift   # AVPlayer, source, queue, lyrics, favorites state
│   ├── Services/
│   │   ├── APIService.swift          # Pocket Casts protobuf, Supabase, radio-browser, Keychain
│   │   ├── LyricsService.swift       # lrclib lookup + LRC parsing
│   │   ├── RadioFeedClient.swift, RadioPlaybackSession.swift,
│   │   │   StreamExperimentConfiguration.swift, StreamExperimentRecorder.swift
│   │   │                             # KCRW alignment and Stream Lab capture
│   │   ├── TrackFingerprinter.swift  # ACRCloud
│   │   └── RemoteControlService.swift, RemoteDebugLogger.swift
│   ├── Model/                        # Station, Song, RemoteCommand
│   └── Utils/Constants.swift         # URLs, keys, PocketCastsTheme palette
├── Packages/StreamSession/           # Foundation-only alignment core
└── Tools/StreamLab/                  # capture and offline replay
```

### Data Flow

1. **Auth**: Email/password → `POST api.pocketcasts.com/user/login` (protobuf, hand-encoded) → Bearer token → Keychain
2. **Up-Next**: Bearer token → `POST api.pocketcasts.com/up_next/sync` (protobuf) → episode list with audio URLs; `playedUpTo` and `duration` come from the sync records
3. **Favorites**: Bearer token → extract userId → `x-user-uuid` header → Supabase `radio_favorites` table
4. **Station Metadata**: station_id → `radio-browser.info` API → name, logo, stream URL
5. **Playback**: AVPlayer with stream URL (radio) or episode URL (podcast)
6. **Now-playing titles**: KCRW and KEXP tracklist APIs, polled every 30 s; ICY metadata for other stations

### Key Dependencies

- **SwiftUI + AppKit**: `NSStatusItem` and a floating `NSPanel`
- **AVFoundation**: AVPlayer for audio playback
- **MediaPlayer**: `MPNowPlayingInfoCenter` and `MPRemoteCommandCenter`
- **Security framework**: Keychain for the token. After a fresh build, macOS asks once to authorize the Keychain read. Click "Always Allow".
- No third-party packages. Protobuf is encoded and decoded by hand, and artwork loads through `AsyncImage`.

### Gotchas

- **Protobuf `apiVersion` is the string `"2"`**, not `"2.0"`. The API answers `"2.0"` with a 400.
- **Stream URLs.** Some stations (NPR Hourly) publish `http` URLs whose servers also speak HTTPS. `upgradeToHTTPS()` rewrites them, because App Transport Security blocks plain http.
- **No standalone `Info.plist`.** The project generates it from build settings. `LSUIElement` is set in the `.pbxproj`.
- **Keychain items** use the Security framework with `kSecAttrAccessibleAfterFirstUnlock`.
- **Testing the panel.** Simulated clicks on the status item are unreliable, because other menubar icons shift its position. Test by hand.

### How the panel behaves

- **Window.** The app is an agent (`LSUIElement`, no Dock icon). The status item shows the Pocket Casts icon when idle and a scrolling title (about 22 characters visible) while playing. A click opens a floating `NSPanel`, pegged to the right of the status item. Because it is a panel and not a popover, its position doesn't depend on the status item's width.
- **Pills.** One podcast pill plus three stream pills (the first three favorites), shown as artwork. A tap stages a source and play starts it: [ADR 0001](./adr/0001-pill-tap-stages-play-starts.md). Empty stream slots show a radio icon and do nothing. `⋮` opens the Favorites/Browse panel.
- **Controls.** Skip back, play/pause, skip forward. Skip amounts default to 10 s and 45 s and are replaced by the account's synced values after login (`fetchSkipSettings`). For a radio source the controls swap to play/pause only once AVPlayer reports an indefinite duration. The scrubber shows for seekable sources only. Pausing keeps the `AVPlayerItem`.
- **Podcast area.** Two tabs, Up Next and New Releases. Up Next lists the full queue. Tapping an episode plays it and moves it to the top. Each row shows time left (`58m` if unplayed, `22m left` if started, `Finished` if done), and a header shows the total time left. Playback resumes at `playedUpTo`. The Pocket Casts dark palette is in `PocketCastsTheme`.
- **Stream area.** For KCRW and KEXP, a tracklist with title, artist, album and artwork, refreshed every 30 s. Other stations show a now-playing card. Lyrics: [ADR 0002](./adr/0002-radio-lyrics-sync.md).
- **Favorites/Browse panel.** Favorites come from Supabase and can be removed or reordered by dragging. Order is stored per user in `UserDefaults` under `radio_favorites_order_<userId>`, matching iOS. Browse shows radio-browser top-voted stations, or search results after a 300 ms debounce. Tapping a result adds it to favorites and plays it.
- **Hardware keys.** `notifyNowPlayingChanged()` is the single point that refreshes `MPNowPlayingInfoCenter`. Play, pause, toggle, next, previous and seek commands map to the player. Skip and seek are disabled while a live stream plays.

### Differences from KCRW Menubar App

| Aspect | KCRW Menubar | PocketRadio Menubar |
|--------|-------------|---------------------|
| Station data | Hardcoded 3 stations | Dynamic from Supabase + radio-browser |
| Auth | None | Pocket Casts email/password login |
| Podcast support | None | Up-next from Pocket Casts API |
| Metadata | KCRW/KEXP tracklist APIs | ICY metadata + up-next titles |
| Persistence | None | Keychain tokens + UserDefaults |
| Code sharing | N/A | May share protobuf defs + Supabase client with iOS |

---

## Milestones

| Milestone | What | User Checkpoint |
|-----------|------|-----------------|
| M1 (`archive/menubar-m1`) | Skeleton menubar plays hardcoded stream | Click icon → click play → hear audio |
| M2 (`archive/menubar-m2`) | Pocket Casts login + token persistence | Log in → quit → reopen → still logged in |
| M3 (`archive/menubar-m3`) | Up-next podcast in menubar | See top podcast → click play → hear it |
| M4 (`archive/menubar-m4`) | Radio favorites from Supabase | See favorites → play a station |
| M5 (`archive/menubar-m5`) | Now-playing metadata + polish | Track title scrolls, artwork shows, controls work |
| M6.1 (`archive/menubar-m6.1`) | Source pills and playback controls | Switch among podcast and stream sources and use the appropriate controls |
| M6.2 (`archive/menubar-m6.2`) | Full Up Next list | Browse the queue and start another episode |
| M6.2.5 (`archive/menubar-m6.2.5`) | Dark theme and remaining-time display | See per-episode and total remaining time in the styled queue |
| M6.3 (`archive/menubar-m6.3`) | Enhanced-stream tracklists | See KCRW/KEXP track history while that stream plays |
| M6.4 (`archive/menubar-m6.4`) | Browse, search, and favorites | Find, save, and play a station from the menubar |
| M6.5–M6.8 (commits `12c5bee`..`f9f4316` in `pocket-radio-menubar`) | Shipped without milestone docs: Pocket Casts idle icon and right-pegged panel, New Releases tab, NSPanel container, pill tap stages only | See [How the panel behaves](#how-the-panel-behaves) |
| M7 (`archive/menubar-m7`) | Synced radio lyrics | Follow the current lyric line for supported stations |
| M8 (`archive/menubar-m8`) | Headphone and media-key control | Control playback from hardware buttons and macOS Now Playing |
| M9 (`archive/menubar-m9`) | Lyric sync tuning and lookup fixes | Adjust station sync and see sensible between-track state |
| [M10](./milestones/milestone_10.md) | Stream Lab capture and replay *(complete; merged at `a3787ff`)* | Mark an audible change and replay the trace offline |
| [M11](./milestones/milestone_11.md) | KCRW playback-alignment experiment *(split plan)* | Review the offline proof before authorizing an app experiment |
| [M11-A](./milestones/milestone_11a.md) | Offline KCRW media-clock selection proof *(accepted; merged/pushed at `e6fa855`)* | Reproduce all retained-trace decisions and review their errors and exclusions |
| [M11-B](./milestones/milestone_11b.md) | Opt-in AAC/HLS menubar experiment *(qualitative prototype accepted; merged/pushed at `e6fa855`)* | Titles and lyrics align by listener report; Off works; formal numerical targets remain unverified |
| [M12](./milestones/milestone_12.md) | KCRW alignment in normal playback *(accepted; merged/pushed at `8838df5`; bugs 2 and 3 open)* | Play KCRW with aligned titles/lyrics without Debug Apply or automatic recording |

## Build & Run

```bash
cd pocket-radio-menubar
xcodebuild -project "PocketRadio Menubar.xcodeproj" -scheme "PocketRadio Menubar" -destination "platform=macOS" build
```

Or open in Xcode and press Cmd+R.
