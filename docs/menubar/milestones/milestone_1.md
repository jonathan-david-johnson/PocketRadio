# M1: Menubar Skeleton — Play a Hardcoded Stream

**Status**: COMPLETED — 2026-05-21

## Goal

A native macOS menubar app that plays one hardcoded radio stream via AVPlayer.
No auth, no API calls, no favorites — just a menubar icon that opens a popover with a play/stop button.

## Done when

- `PocketRadio Menubar.app` launches and shows an icon in the macOS menubar
- Clicking the icon opens an NSPopover below it
- Popover shows a play button
- Clicking play starts streaming `https://streams.kcrw.com/e24_mp3` through AVPlayer
- Clicking stop (same button toggles) stops playback
- Popover can be dismissed by clicking elsewhere (`.transient` behavior)
- App does NOT show in Dock (LSUIElement = YES)
- Sandbox entitlements include network client

## What to Build

### Project Setup

Create new macOS SwiftUI app in `pocket-radio-menubar/`:

```
pocket-radio-menubar/
├── PocketRadio Menubar.xcodeproj/
├── PocketRadio/
│   ├── PocketRadioApp.swift          # @main app entry
│   ├── AppDelegate.swift             # NSStatusItem + NSPopover (from KCRW template)
│   ├── ContentView.swift             # Popover UI (play/stop button)
│   ├── ViewModels/
│   │   └── PlayerViewModel.swift     # AVPlayer wrapper, @Published isPlaying
│   ├── Utils/
│   │   └── Constants.swift           # Hardcoded stream URL
│   ├── Assets.xcassets/              # App icon
│   └── Info.plist                    # LSUIElement=YES, sandbox
└── README.md
```

### Source Files

#### `PocketRadioApp.swift`
```swift
@main
struct PocketRadioApp: App {
    @NSApplicationDelegateAdaptor(AppDelegate.self) private var appDelegate
    var body: some Scene {
        Settings { EmptyView() }
    }
}
```

#### `AppDelegate.swift`
Copy from KCRW `KCRW_MenuBar_PlayerApp.swift` but simplified:
- `NSStatusBar.system.statusItem` with variable length
- Icon from Assets.xcassets
- `NSPopover` with `.transient` behavior, 300x150 size
- `togglePopover()` with right-edge anchor (same as KCRW)
- No polling, no scrolling title, no stream switching

#### `ContentView.swift`
Minimal SwiftUI view:
- Play/stop button (toggles `playerViewModel.isPlaying`)
- Stream starts/stops on toggle

#### `PlayerViewModel.swift`
```swift
@MainActor
class PlayerViewModel: ObservableObject {
    @Published var isPlaying = false
    let audioPlayer = AVPlayer()
    
    func togglePlayback() {
        if isPlaying {
            audioPlayer.replaceCurrentItem(with: nil)
            isPlaying = false
        } else {
            guard let url = Constants.streamURL else { return }
            let item = AVPlayerItem(url: url)
            audioPlayer.replaceCurrentItem(with: item)
            audioPlayer.play()
            isPlaying = true
        }
    }
}
```

#### `Constants.swift`
```swift
enum Constants {
    static let streamURL = URL(string: "https://streams.kcrw.com/e24_mp3")
}
```

### Build Configuration
- Target: macOS 14.0+
- Bundle ID: `com.jdj.pocketradio.menubar`
- Scheme: PocketRadio Menubar
- Swift 5.10 toolchain

## Implementation Strategy

The KCRW Menubar Player project already has a working menubar app pattern. We start by copying that project and simplifying it:

1. Copy KCRW project to `pocket-radio-menubar/`
2. Rename target, bundle ID, scheme
3. Strip out KCRW/KEXP/NPR-specific code (station picker, tracklists, NPR skip controls, scrolling title)
4. Reduce to single stream with play/stop toggle
5. Build and verify

## Commit
TBD — after build succeeds.
