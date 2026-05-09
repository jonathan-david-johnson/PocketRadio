# macOS Menubar App Design

## Overview

Standalone SwiftUI target in the same Xcode project. `NSStatusItem` icon in menubar → click → popover with player controls + favorites.

No shared Swift package with iOS for MVP. Direct Supabase calls, AVFoundation audio.

## Xcode target

- Name: `PocketRadioMenubar`
- Bundle ID: `com.pocketradio.menubar`
- Minimum deployment: macOS 13 (Ventura) — SwiftUI `MenuBarExtra` available
- Use `MenuBarExtra` (SwiftUI, macOS 13+) not `NSStatusItem` directly — simpler

```swift
@main
struct PocketRadioMenubarApp: App {
    var body: some Scene {
        MenuBarExtra("PocketRadio", systemImage: "radio") {
            MenubarContentView()
        }
        .menuBarExtraStyle(.window)  // popover-style window, not plain menu
    }
}
```

## Popover layout

```
┌────────────────────────────────┐
│ PocketRadio            [⚙]    │
├────────────────────────────────┤
│ NOW PLAYING                    │
│  [logo]  KCRW                  │
│          Floating Points — ... │
│  [  ◀◀  ]  [  ▶ / ‖  ]       │
│  [ Donate to KCRW ↗ ]         │
├────────────────────────────────┤
│ FAVORITES                      │
│  KCRW          ▶              │
│  KEXP          ▶              │
│  NPR Hourly    ▶              │
├────────────────────────────────┤
│ [ Browse all stations... ]     │
│ (opens iOS app or web — defer) │
└────────────────────────────────┘
```

Width: 280pt fixed. Height: dynamic (≤ 400pt, scrollable).

## Audio

`MenubarAudioPlayer.swift` — thin wrapper around `AVPlayer`.

```swift
class MenubarAudioPlayer: ObservableObject {
    private var player: AVPlayer?
    @Published var isPlaying = false
    @Published var currentStation: MenubarStation?

    func play(station: MenubarStation) {
        guard let url = URL(string: station.streamUrl) else { return }
        player = AVPlayer(url: url)
        player?.play()
        isPlaying = true
        currentStation = station
    }

    func pause() {
        player?.pause()
        isPlaying = false
    }
}
```

Media keys: `MPRemoteCommandCenter` — register play/pause commands. Works with keyboard media keys.

```swift
let commandCenter = MPRemoteCommandCenter.shared()
commandCenter.playCommand.addTarget { [weak self] _ in self?.player.play(); return .success }
commandCenter.pauseCommand.addTarget { [weak self] _ in self?.player.pause(); return .success }
```

Now Playing info (lock screen / Control Center):
```swift
MPNowPlayingInfoCenter.default().nowPlayingInfo = [
    MPMediaItemPropertyTitle: station.name,
    MPMediaItemPropertyArtist: "PocketRadio"
]
```

## Tracklist (now playing song)

Same KCRW + KEXP API calls as iOS. Poll every 60s while playing. Display in popover.

## Favorites sync

Direct Supabase REST calls — same schema, same `user_uuid` logic.

Auth: user_uuid stored in `UserDefaults` (macOS). MVP: manual entry in Settings popover. Post-MVP: shared keychain with iOS via App Groups if both apps are signed under same team.

## Settings popover (⚙ button)

- User UUID field (manual paste from iOS app for MVP)
- Supabase URL field (defaults to prod, overridable for dev)
- Quit button

## Tracklist in menubar icon (optional, post-MVP)

Menubar icon can show current song ticker. Defer — complex, low-value for MVP.

## Files

```
PocketRadioMenubar/
  PocketRadioMenubarApp.swift     # App entry, MenuBarExtra setup
  MenubarContentView.swift        # SwiftUI popover content
  MenubarAudioPlayer.swift        # AVPlayer + MPRemoteCommandCenter
  MenubarStation.swift            # Lightweight station model (no BaseEpisode)
  MenubarSupabaseClient.swift     # Direct REST client (URLSession, no SDK needed)
  MenubarTracklistPoller.swift    # KCRW/KEXP API polling
```

## Sharing code with iOS

No shared framework for MVP. Duplicate the ~3 files that overlap (station model, Supabase client, tracklist APIs). Refactor into a shared Swift package post-MVP if both apps grow.
