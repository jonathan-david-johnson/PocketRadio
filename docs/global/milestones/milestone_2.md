# Global M2 — Device Picker + Presence Wiring (debug-grade)

**Status**: PLANNED (stub — flesh out when M1 lands)
**Platforms**: iOS + menubar
**Depends on**: M1 (transport + protocol)

---

## Goal

Make the feature usable end-to-end from real player controls, driven by live Presence —
not the M1 debug trigger. Functional, not yet polished (that's M3).

- iOS shows a **device list** built from Presence (every device on the account channel).
- User **picks a target device**; selection persists for the session.
- iOS player transport controls (play/pause/stop) and station selection route as
  `command` broadcasts to the selected target instead of (or alongside) local playback.
- Basic **"Playing on {device}"** text indicator when a remote target is active.
- Menubar surfaces that it's under remote control (minimal affordance).

Still **one direction** (iOS → menubar). Reverse is a later milestone.

---

## Likely work (provisional)

- iOS: `RemoteDevicePickerView` (SwiftUI sheet) bound to `RemoteControlManager` presence list.
- iOS: session-scoped "active target device_id"; nil = play locally.
- iOS: route existing player actions through target when set.
- Presence freshness: drop devices stale > N seconds (define N).
- Menubar: minimal "remote controlling" state from received commands.

## Done when (provisional)
- [ ] iOS device picker lists all present devices with name + type + current state.
- [ ] Selecting a target routes play/pause/stop/station to it; deselect → local.
- [ ] "Playing on {device}" shows while a target is active.
- [ ] Stale devices disappear from the list within N seconds.
- [ ] Two-device cross-network test: pick menubar from iPhone, drive it from the iOS player UI.

## Out of scope (M2)
- Final visual polish / animation (M3).
- Menubar → iOS direction.
- Volume / seek, Roku / console.
