# PocketRadio Menubar App

macOS menubar companion app for PocketRadio. Plays the user's top up-next podcast and favorite radio streams from a lightweight NSStatusItem popover.

## Architecture

```
pocket-radio-menubar/
├── PocketRadio Menubar.xcodeproj
├── PocketRadio/
│   ├── PocketRadioApp.swift          # @main SwiftUI App entry
│   ├── AppDelegate.swift             # NSStatusItem + NSPopover lifecycle
│   ├── ContentView.swift             # Main popover UI
│   ├── ViewModels/
│   │   ├── PlayerViewModel.swift      # AVPlayer + playback state
│   │   ├── AuthViewModel.swift        # Login/logout + token management
│   │   ├── UpNextViewModel.swift      # Pocket Casts up-next fetch
│   │   └── FavoritesViewModel.swift   # Supabase favorites + radio-browser
│   ├── Services/
│   │   ├── PocketCastsAPI.swift       # Login + up-next protobuf calls
│   │   ├── SupabaseClient.swift       # Radio favorites CRUD
│   │   ├── RadioBrowserAPI.swift      # radio-browser.info metadata
│   │   └── KeychainManager.swift      # Token storage
│   ├── Models/
│   │   ├── UpNextEpisode.swift        # Pocket Casts up-next episode
│   │   ├── RadioStation.swift         # Radio station model
│   │   └── AuthResponse.swift         # Login response model
│   ├── Utils/
│   │   └── Constants.swift            # API URLs, keys
│   └── Assets.xcassets/               # App icon, logos
└── README.md
```

### Data Flow

1. **Auth**: Email/password → `POST api.pocketcasts.com/user/login` (protobuf) → Bearer token → Keychain
2. **Up-Next**: Bearer token → `POST api.pocketcasts.com/up_next/sync` (protobuf) → episode list with audio URLs
3. **Favorites**: Bearer token → extract userId → `x-user-uuid` header → Supabase `radio_favorites` table
4. **Station Metadata**: station_id → `radio-browser.info` API → name, logo, stream URL
5. **Playback**: AVPlayer with stream URL (radio) or episode URL (podcast)
6. **ICY Metadata**: Poll stream metadata endpoint (Shoutcast/Icecast) for now-playing track info

### Key Dependencies

- **SwiftUI + AppKit**: NSStatusItem, NSPopover for menubar UI
- **AVFoundation**: AVPlayer for audio playback
- **SwiftProtobuf**: Pocket Casts API protobuf serialization (shared from iOS modules or vendored)
- **Kingfisher**: Station logo / podcast artwork loading (optional — can use AsyncImage for MVP)
- **Security framework**: Keychain for token storage

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
| [M1](./milestones/milestone_1.md) | Skeleton menubar plays hardcoded stream | Click icon → click play → hear audio |
| [M2](./milestones/milestone_2.md) | Pocket Casts login + token persistence | Log in → quit → reopen → still logged in |
| [M3](./milestones/milestone_3.md) | Up-next podcast in menubar | See top podcast → click play → hear it |
| [M4](./milestones/milestone_4.md) | Radio favorites from Supabase | See favorites → play a station |
| [M5](./milestones/milestone_5.md) | Now-playing metadata + polish | Track title scrolls, artwork shows, controls work |
| [M6.1](./milestones/milestone_6.1.md) | Source pills and playback controls | Switch among podcast and stream sources and use the appropriate controls |
| [M6.2](./milestones/milestone_6.2.md) | Full Up Next list *(planned)* | Browse the queue and start another episode |
| [M6.2.5](./milestones/milestone_6.2.5.md) | Dark theme and remaining-time display | See per-episode and total remaining time in the styled queue |
| [M6.3](./milestones/milestone_6.3.md) | Enhanced-stream tracklists *(planned)* | See KCRW/KEXP track history while that stream plays |
| [M6.4](./milestones/milestone_6.4.md) | Browse, search, and favorites *(planned)* | Find, save, and play a station from the menubar |
| [M7](./milestones/milestone_7_lyrics.md) | Synced radio lyrics | Follow the current lyric line for supported stations |
| [M8](./milestones/milestone_8.md) | Headphone and media-key control | Control playback from hardware buttons and macOS Now Playing |
| [M9](./milestones/milestone_9.md) | Lyric sync tuning and lookup fixes | Adjust station sync and see sensible between-track state |
| [M10](./milestones/milestone_10.md) | Stream Lab capture and replay *(complete; merged at `a3787ff`)* | Mark an audible change and replay the trace offline |
| [M11](./milestones/milestone_11.md) | KCRW playback-alignment experiment *(split plan)* | Review the offline proof before authorizing an app experiment |
| [M11-A](./milestones/milestone_11a.md) | Offline KCRW media-clock selection proof *(accepted; merged/pushed at `e6fa855`)* | Reproduce all retained-trace decisions and review their errors and exclusions |
| [M11-B](./milestones/milestone_11b.md) | Opt-in AAC/HLS menubar experiment *(qualitative prototype accepted; merged/pushed at `e6fa855`)* | Titles and lyrics align by listener report; Off works; formal numerical targets remain unverified |
| [M12](./milestones/milestone_12.md) | KCRW alignment in normal playback *(proposed; requires default-behavior approval)* | Play KCRW with aligned titles/lyrics without Debug Apply or automatic recording |

## Build & Run

```bash
cd pocket-radio-menubar
xcodebuild -project "PocketRadio Menubar.xcodeproj" -scheme "PocketRadio Menubar" -destination "platform=macOS" build
```

Or open in Xcode and press Cmd+R.
