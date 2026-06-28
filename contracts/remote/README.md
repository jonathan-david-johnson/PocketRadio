# Remote Protocol Contract Fixtures

Golden JSON fixtures for the PocketRadio cross-device remote control protocol.

## What these are

Each file is a canonical example of one inner JSON object exchanged between devices
over the Supabase Realtime channel. These fixtures are the **single source of truth**
for the wire contract — every platform's typed structs must round-trip through them.

## What these are NOT

These fixtures do **not** include the Phoenix / Supabase Realtime envelope:
```
[joinRef, ref, "realtime:remote:<userId>", "broadcast", {"event":"command","payload":<inner>}]
```
That envelope is a **transport** concern. Each platform's channel layer owns it.
The inner `<payload>` object is what these fixtures capture.

## File inventory

| File | Type | Notes |
|------|------|-------|
| `command_play.json` | `RemoteCommand` | No payload (play/pause/stop carry none) |
| `command_pause.json` | `RemoteCommand` | No payload |
| `command_stop.json` | `RemoteCommand` | No payload |
| `command_load_station.json` | `RemoteCommand` | Has `payload` with station fields |
| `presence_ios.json` | `RemotePresence` | role=sender, iOS device |
| `presence_macos.json` | `RemotePresence` | role=receiver, macOS device |

## Nil / absent fields

Swift `JSONEncoder` **omits** nil Optional properties (no `"key": null` emitted).
Fixtures likewise omit absent-optional fields so re-encode round-trips cleanly.
To document that a field *can* be absent, note it here — not as `null` in the JSON.

Optional fields that may be absent:
- `RemoteCommand.payload` — absent for play/pause/stop verbs
- `RemoteCommandPayload.station_id/url/name` — all present for `load_station`
- `RemotePresence.playback.station_id` / `.station_name` — absent when idle
- `RemotePresence.playback.artwork_url` — always absent in these fixtures (optional)

## Known verb set

`command` field: `play`, `pause`, `stop`, `load_station`

## Known playback state set

`playback.state` field: `playing`, `paused`, `idle`

## How each platform consumes these

- **iOS** (`pocket-radio-ios/`): `PocketCastsTests/Tests/Radio/RemoteCommandFixtureTests.swift`
  resolves path from `#filePath` → 5 × `deletingLastPathComponent()` → shell root → `contracts/remote/`
- **macOS menubar** (`pocket-radio-menubar/`): `PocketRadioTests/RemoteCommandFixtureTests.swift`
  resolves path from `#filePath` → 3 × `deletingLastPathComponent()` → shell root → `contracts/remote/`
- **Go console / Roku** — no fixture tests yet; corpus is ready for them.
