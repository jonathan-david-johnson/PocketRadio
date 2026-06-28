# Global M3 — Spotify-style Output Device UI

**Status**: PLANNED (stub — flesh out when M2 lands)
**Platforms**: iOS + menubar
**Depends on**: M2 (working picker + presence wiring)

---

## Goal

Promote the debug-grade M2 picker to the real product surface: a Spotify-Connect-style
**output-device control living in the player**, on both iOS and menubar.

- **Device button** in each player (iOS now-playing + menubar player), styled to theme.
- Tapping opens a polished device list (icon per `device_type`, current-state subtitle,
  selected-state highlight).
- **"Playing on {device}"** indicator in the player chrome — the signature Spotify cue —
  themed, not debug text.
- Transitions/affordances when output moves between devices.

---

## Likely work (provisional)

- iOS: device button in `NowPlayingPlayerItemViewController` chrome; themed picker
  (`AppTheme.colorForStyle` for UIKit).
- Menubar: device button + indicator in `ContentView` player; SwiftUI theming.
- Per-`device_type` iconography (phone / laptop / later tv).
- Empty/solo state (only this device present) handled gracefully.

## Done when (provisional)
- [ ] Device button present and themed in both players.
- [ ] Picker shows icon + name + state per device; selected device highlighted.
- [ ] "Playing on {device}" indicator themed and correct in both players.
- [ ] Looks right in light/dark + at least one non-default theme.
- [ ] Solo-device state hides or disables the control cleanly.

## Out of scope (M3)
- Menubar → iOS control direction.
- Roku / console receivers.
- Volume / seek commands.
