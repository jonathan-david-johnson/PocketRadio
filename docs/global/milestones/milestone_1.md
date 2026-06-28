# Global M1 — Remote Playback Control: Plumbing (iOS → menubar)

**Status**: IN PROGRESS
**Platforms**: iOS (`pocket-radio-ios/`) + menubar (`pocket-radio-menubar/`)
**Depends on**: nothing (both already log into the same Pocket Casts account)

---

## Feature (the whole arc, not just M1)

Like Spotify Connect: be playing on one device, control playback on another — across
networks. Final goal **bidirectional**; both players show the active output device. This
milestone is **plumbing only**: establish the cross-network channel and prove an iOS
command moves menubar playback. No real UI yet.

### Roadmap

| Milestone | Scope |
|-----------|-------|
| **M1 (this)** | Transport + protocol. iOS sends, menubar receives & executes. Debug logging only, no UI. |
| M2 | Device picker + presence-driven wiring (debug-grade), end-to-end testable. |
| M3 | Spotify-style UI in both players: device button + "Playing on {device}". |
| later | Bidirectional (menubar controls iOS), Roku/console receivers, RLS hardening. |

---

## Why this is cheap (findings from the code)

- **Shared identity already exists.** iOS scopes by `ServerSettings.userId`; menubar logs
  into the same account (`APIService.login` → `uuid`) and already sends it as the
  `x-user-uuid` header (`APIService.swift:828`). Same account UUID on both ends → **no
  pairing UX needed**.
- **Stable per-install device id already exists** on menubar:
  `getOrCreateDeviceID()` (`APIService.swift:224`, UserDefaults key `pocketradio-device-id`).
  Mirror the same on iOS.
- iOS already depends on `supabase-swift` (`RadioSupabase.swift`). Menubar does **not** —
  it talks raw protobuf to `api.pocketcasts.com`. Adding the SDK is the one new dependency.

---

## Architecture — Supabase Realtime, zero new tables

Three Realtime primitives map cleanly to the feature:

| Primitive | Use in this feature |
|-----------|---------------------|
| **Presence** | Live device list + each device's current playback state → Spotify device picker & "Playing on X" |
| **Broadcast** | Transport commands (play/pause/stop/load_station). Ephemeral, instant, fire-and-forget. |
| Postgres Changes | *Not used in MVP.* Reserved for a future durable Roku/console poll. |

**No SQL tables for MVP.** Ephemeral broadcast is *correct* for playback control — a stale
command replaying on reconnect would be a bug, not a feature.

- **Channel topic**: `remote:{accountUserId}` — one private-by-obscurity channel per account.
- **Roles (MVP)**: iOS = sender, menubar = receiver. Both publish Presence (cheap; sets up
  bidirectional later).

### Protocol

**Presence payload** (each device tracks this; updated on playback change):

```json
{
  "device_id": "stable-per-install-uuid",
  "device_type": "ios" | "macos",
  "device_name": "Jonathan's iPhone",
  "role": "sender" | "receiver",
  "playback": {
    "state": "playing" | "paused" | "stopped" | "idle",
    "station_id": "...",
    "station_name": "...",
    "artwork_url": "..."
  },
  "updated_at": "iso8601"
}
```

**Broadcast command** (event name `command`):

```json
{
  "command_id": "uuid",
  "from_device_id": "...",
  "target_device_id": "...",
  "command": "play" | "pause" | "stop" | "load_station",
  "payload": { "station_id": "...", "station_url": "...", "station_name": "..." },
  "sent_at": "iso8601"
}
```

Receiver ignores any message where `target_device_id != myDeviceId`. `command_id` gives
idempotency (drop duplicates). `payload` only present for `load_station`.

**Command set (MVP)**: `play`, `pause`, `stop`, `load_station`. No volume/seek this round.

`load_station` carries `station_id` + `station_url` + `station_name` so the receiver can
play a station even when it isn't in its favorites — do **not** assume a favorites index.

---

## New files / changes

### iOS (`pocket-radio-ios/`)
- `podcasts/Radio/RemoteControl/RemoteCommand.swift` — `Codable` command + presence structs (shared schema).
- `podcasts/Radio/RemoteControl/RemoteControlManager.swift` — long-lived `SupabaseClient`,
  channel subscribe, presence track, `send(command:to:)`. Note: existing `RadioSupabase.client()`
  is **per-operation**; Realtime needs one **long-lived** client/channel — new code, not a reuse.
- Stable device id helper (mirror menubar's `getOrCreateDeviceID()`), UserDefaults key
  `pocketradio-device-id`.
- **`project.pbxproj` registration** for both new files (mirror `StreamsHostViewController.swift`).

### Menubar (`pocket-radio-menubar/`)
- Add **`supabase-swift` SPM** dependency to `PocketRadio.xcodeproj`.
- `PocketRadio/Services/RemoteControlService.swift` — channel subscribe, presence track,
  receive `command`, dispatch to `PlayerViewModel`.
- **Config**: add `SUPABASE_URL` + `SUPABASE_ANON_KEY` (menubar has no Supabase config today;
  match how iOS reads them from Info.plist).
- Dispatch map: `load_station` → play arbitrary `RadioStation` (existing `selectStream(_:)`
  is favorites-index based — add/locate a "play this station object" entry point);
  `play`/`pause`/`stop` → existing transport toggle (`isPlaying` is published at
  `PlayerViewModel.swift:91`; wire to its play/pause path).

---

## Security (flag, not a blocker)

Channel scoped only by account UUID in `x-user-uuid` + anon key = trust-the-client, the
**same posture as existing favorites sync**. Anyone who knew your account UUID could send
commands. Acceptable for MVP because it matches current posture. RLS on `realtime.messages`
+ private channels = a later hardening milestone. Note it; don't gate M1 on it.

---

## Done when

### Transport & config
- [x] Menubar uses raw Phoenix WebSocket (no SDK needed — matches existing raw HTTP pattern). Hardcoded Supabase URL/key (same as iOS staging values in Info.plist).
- [x] Both ends derive a stable `device_id` via UserDefaults key `pocketradio-device-id`.
- [x] iOS reads `accountUserId` from `ServerSettings.userId`; menubar passes via `login()`.

### Channel & presence
- [x] Both ends subscribe to `remote:{accountUserId}` on launch (when logged in).
- [x] Both publish Presence on join and log presence diffs.
- [x] Presence updates when local playback state changes (iOS: notification observers; menubar: `didSet` on `isPlaying`/`currentSource`).

### Commands (iOS → menubar)
- [x] iOS exposes `RemoteControlManager.shared.send(command:to:payload:)` (callable from debug console / future UI).
- [x] Menubar receives commands, filters by `target_device_id`, drops duplicate `command_id`, drives `PlayerViewModel` for all four commands.
- [x] `load_station` constructs `RadioStation(id:name:streamURL:logoURL:)` from command payload and calls `playStation(_:)`.

### Verification
- [ ] Two-device manual test on **different networks** (e.g. iOS on cellular, Mac on wifi): each command moves menubar playback within ~1s.
- [x] iOS unit tests: `RemoteCommandTests` — 3 tests pass (round-trip + snake_case key verification).
- [x] `make build_staging` iOS green. Menubar: pbxproj registered (build verify pending Xcode install).

---

## Pending on merge

- **Re-add CarPlay entitlement** to both `podcasts/podcasts.entitlements` and `podcasts/podcastsDebug.entitlements`:
  ```xml
  <key>com.apple.developer.carplay-audio</key>
  <true/>
  ```
  Backed out 2026-06-28 to allow device builds while awaiting Apple CarPlay Audio App capability approval. Restore when merging this branch back to main (or once approval lands, whichever comes first).

---

## Explicitly out of scope (M1)
- Any production UI / device picker (M2–M3).
- Menubar → iOS direction (later).
- Volume, seek (later).
- Roku / console receivers (later).
- RLS / private-channel hardening (later).
