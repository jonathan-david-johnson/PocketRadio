# M6: macOS Menubar App

**Status**: NOT STARTED

## Goal

Standalone menubar app plays favorites, shows now-playing track.

## Done when

- Menubar icon appears
- Click → popover with favorites list
- Tap station → stream plays via AVPlayer
- KCRW/KEXP show current track title
- Media keys (play/pause) work

## What to build

Everything in `PocketRadioMenubar/` — see `docs/designs/menubar.md`:
- `PocketRadioMenubarApp.swift` — `MenuBarExtra` entry point (macOS 13+)
- `MenubarContentView.swift` — SwiftUI popover
- `MenubarAudioPlayer.swift` — AVPlayer + MPRemoteCommandCenter
- `MenubarStation.swift` — lightweight station model (no BaseEpisode)
- `MenubarSupabaseClient.swift` — direct REST (URLSession, no SDK)
- `MenubarTracklistPoller.swift` — KCRW/KEXP API polling

## Notes

- Scan `other_apps/PocketCastsOSX` before starting — see `docs/todo.md` open question
- Menubar auth MVP: manual UUID paste in Settings popover — see open question in `docs/todo.md`
- Decide scrolling title behavior (see todo.md) before UI implementation
- No shared Swift package with iOS for MVP — duplicate the ~3 overlapping files
- Restore Watch app embed in xcodeproj before App Store submission
