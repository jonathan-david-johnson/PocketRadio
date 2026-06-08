# PocketRadio Menubar — Handoff

> Last updated: 2026-05-21 | Commit: `3fdea62`

## Goal

Build a macOS menubar companion app for PocketRadio that plays the user's top Pocket Casts up-next podcast and favorite radio streams. The iOS app is a fork of Automattic's `pocket-casts-ios` (MPL 2.0).

## Project Location

```
/Users/jdj/Documents/code/PocketRadio/pocket-radio-menubar/
```

GitHub: https://github.com/jonathan-david-johnson/pocket-radio-menubar

Top-level Makefile target: `make menubar` (from `/Users/jdj/Documents/code/PocketRadio/`)

## Current Progress

### Completed Milestones

| M# | What | Commit |
|----|------|--------|
| M1 | Skeleton menubar — NSStatusItem + NSPopover, plays KCRW stream | `eb7cb1d` |
| M2 | Pocket Casts login — email/password → protobuf → Bearer token → Keychain | `e2a1183` |
| M3 | Up-next podcast playback — fetch from `POST /up_next/sync` | `257c02e` |
| M4 | Radio favorites — Supabase → radio-browser.info metadata | `426e1ce` |
| M5 | Menubar scrolling title + quit button + polish | `4d1c70b` |
| Fix | NPR stream http→https upgrade (ATS compatibility) | `1e86767` |
| M6.1 | **Redesigned layout** — pill-based source selection + context-sensitive controls | `3fdea62` |

### M6 Sub-Milestones (defined in `docs/menubar/milestones/`)

| Sub-M | What | Status |
|-------|------|--------|
| [M6.1](docs/menubar/milestones/milestone_6.1.md) | Pill layout + controls (Podcast + 3 stream pills, ⋮, ⏪⏯️⏩/⏯️-only) | **DONE** |
| [M6.2](docs/menubar/milestones/milestone_6.2.md) | Up Next list — full episode queue when Podcast pill selected | PLANNED |
| [M6.3](docs/menubar/milestones/milestone_6.3.md) | Tracklist for enhanced streams (KCRW, KEXP) | PLANNED |
| [M6.4](docs/menubar/milestones/milestone_6.4.md) | Browse/Search + Favorites tabs + dark/light theming | PLANNED |

## Architecture

### File Structure

```
pocket-radio-menubar/
├── PocketRadio.xcodeproj/
├── PocketRadio/
│   ├── PocketRadioApp.swift           # @main + AppDelegate (NSStatusItem, NSPopover, menubar scrolling)
│   ├── ContentView.swift              # SwiftUI UI (pill layout, login form, controls)
│   ├── View Models/
│   │   └── PlayerViewModel.swift      # All state: auth, playback, pills, favorites, up-next
│   ├── Services/
│   │   └── APIService.swift           # PocketCastsAPI (login, up-next), KeychainManager,
│   │                                  #   RadioStation model, Supabase, radio-browser, protobuf codec
│   ├── Utils/
│   │   └── Constants.swift            # KCRW fallback URL + Notification.Name extension
│   ├── Model/                         # Placeholder files (Song.swift, Station.swift) — unused
│   └── Assets.xcassets/               # App icon
├── docs/menubar/
│   ├── README.md                      # Architecture overview
│   └── milestones/                    # All milestone docs
└── Makefile target: make menubar
```

### Data Flow

```
User logs in ──→ POST api.pocketcasts.com/user/login (protobuf)
                   ↓ Bearer token + userId
              Keychain (persists across launches)
                   ↓
         ┌────────┴────────┐
         ↓                  ↓
  POST /up_next/sync    Supabase REST
  (protobuf)            GET /radio_favorites
         ↓              x-user-uuid header
   [UpNextEpisode]            ↓
         ↓              [station_id list]
   AVPlayer plays             ↓
   episode.url          radio-browser.info
                        GET /stations/byuuid/{id}
                              ↓
                        [RadioStation: name, streamURL, logoURL]
                              ↓
                        AVPlayer plays streamURL
```

### Control Detection (M6.1)

Same logic as iOS `PlaybackManager.shouldUseMuteControls`:
```swift
var shouldUseMuteControls: Bool {
    guard currentSource?.isRadio == true else { return false }
    guard let duration = audioPlayer.currentItem?.duration,
          duration.isValid, !duration.isIndefinite else {
        return true  // indefinite → live stream → mute controls
    }
    return false  // finite → seekable → skip controls
}
```
- Default controls: ⏪ ⏯️ ⏩ (skip back 10s, play/pause, skip forward 45s)
- Swaps to ⏯️-only when AVPlayer duration resolves to indefinite
- Duration observed via Combine `publisher(for: \.currentItem?.duration)`

### APIs & Credentials

| Endpoint | Method | Auth |
|----------|--------|------|
| `https://api.pocketcasts.com/user/login` | POST | protobuf body (email, password, scope) |
| `https://api.pocketcasts.com/up_next/sync` | POST | Bearer token |
| `https://brvtspdculqyvdrmdtef.supabase.co/rest/v1/radio_favorites` | GET | `apikey` + `x-user-uuid` headers |
| `https://de1.api.radio-browser.info/json/stations/byuuid/{id}` | GET | User-Agent: PocketRadio/1.0 |

Supabase anon key: `sb_publishable_1MRvFzvB6O7f2zDPfs2nkA_p18FSLUF` (publishable — safe)

### Protobuf (Manual — no SwiftProtobuf dependency)

All protobuf encode/decode is done manually in `APIService.swift`:
- `encodeVarint` / `encodeVarint64` — unsigned LEB128
- `encodeField(fieldNumber, string)` — wire type 2 (length-delimited)
- `encodeVarintField(fieldNumber, int64)` — wire type 0 (varint)
- Login request: fields 1(email), 2(password), 3(scope)
- Up-next request: fields 1(deviceTime), 2(version="2"), 6(deviceID)
- Up-next response: field 4(episodes[]) → field 1(title), 2(url), 3(podcast), 4(uuid)

### Keychain

Token stored via `KeychainManager` using Security framework:
- Service: `com.jdj.pocketradio`
- Keys: `pocketcasts-token`, `pocketcasts-userid`, `pocketcasts-email`
- Accessibility: `kSecAttrAccessibleAfterFirstUnlock`
- First run prompts macOS Keychain authorization dialog → user must click "Always Allow"

## What Worked

- Manual protobuf encode/decode — no dependency needed, handles all Pocket Casts API calls
- Copying the KCRW Menubar Player project as a template saved significant setup time
- The `apiVersion` is `"2"` (not `"2.0"`) — this was a 400 error until fixed
- NPR stream URL is HTTP but server supports HTTPS — added `upgradeToHTTPS()` helper
- Duration-based control detection lets MP3 streams (NPR hourly) get skip controls automatically
- Using `@Published` + Combine for reactive UI updates works well with SwiftUI

## What Didn't Work / Gotchas

- **Programmatic menubar clicking**: Tried `CGEvent` mouse clicks to screenshot the popover. Worked intermittently because menubar icon positions shift based on other icons. Manual testing is more reliable.
- **Screen recording**: `screencapture` requires permissions. Works after granting in System Settings.
- **`Info.plist` is auto-generated**: The project uses Xcode build settings (no standalone Info.plist). `LSUIElement` is set in pbxproj.
- **Keychain dialog**: macOS prompts "PocketRadio wants to access key..." on first token read. User must click "Always Allow". This is normal — not a bug.
- **Popover `.transient` behavior**: Popover closes when clicking elsewhere. Programmatic clicks often dismissed it before screenshot.

## Test Credentials

```
Email:    thuggler+pocketcasts@gmail.com
Password: cQU8@Nun6BQv.mFnzQ
```
DO NOT commit these to source. Use only for manual testing. The account has:
- Up-next queue with ~3 podcast episodes
- 3 favorite stations in Supabase: KCRW Eclectic 24, KEXP, NPR Hourly Newscast

## Next Steps

### Immediate: Finish M6

1. **M6.2 — Up Next List**: When Podcast pill is selected, show the full episode list in the bottom section. Already have `upNextEpisodes: [UpNextEpisode]` in the ViewModel. Need to build the list UI and wire tap-to-switch-episode.

2. **M6.3 — Tracklist for Enhanced Streams**: Copy `CuratedEnhancement` from iOS (`/Users/jdj/Documents/code/PocketRadio/pocket-casts-ios/podcasts/Radio/CuratedEnhancement.swift` + `curated_stations.json`). Implement KCRW/KEXP tracklist API clients. Show tracklist in bottom section when enhanced stream is playing.

3. **M6.4 — Browse/Search + Favorites Tabs**: ⋮ button opens Favorites/Browse tabs. Browse tab searches radio-browser.info. Favorites tab shows CRUD for favorites. Dark/light theming follows macOS.

### Build & Run

```bash
cd /Users/jdj/Documents/code/PocketRadio
make menubar
```

Or manually:
```bash
cd pocket-radio-menubar
xcodebuild -project PocketRadio.xcodeproj -scheme PocketRadio -configuration Debug build
open ~/Library/Developer/Xcode/DerivedData/PocketRadio-*/Build/Products/Debug/PocketRadio.app
```

### Key Files to Edit Next

- `PocketRadio/ContentView.swift` — main UI, needs M6.2/6.3/6.4 content in bottom section
- `PocketRadio/View Models/PlayerViewModel.swift` — already has `upNextEpisodes` array and favorites state
- `PocketRadio/Services/APIService.swift` — add browse search endpoint for M6.4

### iOS Codebase Reference

The iOS app source is at `/Users/jdj/Documents/code/PocketRadio/pocket-casts-ios/`. Key files for reference:
- `podcasts/Radio/RadioBrowserAPI.swift` — browse/search endpoints
- `podcasts/Radio/RadioTracklistService.swift` — KCRW/KEXP tracklist parsing
- `podcasts/Radio/CuratedEnhancement.swift` + `curated_stations.json` — enhanced stream config
- `podcasts/PlaybackManager.swift` — `shouldUseMuteControls` pattern (already replicated)
- `Modules/Sources/PocketCastsServer/Private/Protobuffer/api.pb.swift` — protobuf field numbers

### Available Subagents

- `researcher` (qwen3p6-plus via fireworks.ai) — deep codebase investigation
- `image_reader` (kimi-k2p6 via fireworks.ai) — screenshot/UI analysis
