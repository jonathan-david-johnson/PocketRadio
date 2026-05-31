# M2: Login + Persistence (via Relay)

**Status**: DONE

## Goal

Pocket Casts login through the `pc-relay` JSON endpoint, token persisted in `roRegistrySection`, auto-login on launch, 401 handling. No protobuf on the device — the relay does all of it (see [`spikes.md`](../spikes.md)).

## Done when

- Login screen accepts email/password (SceneGraph keyboard), with a **dev prefill** path so the test account isn't re-typed on every sideload
- `RelayTask` `login` returns token + userId + email (JSON); on success they're written to registry section `"auth"` (`.Flush()` after write)
- On relaunch, channel auto-logs-in from the stored token (skips login screen)
- A relay `401`/`403` → clear stored token, drop back to login with a message
- Logout clears the registry section
- Empty/failed states named: bad credentials → inline error; no network → retryable error, not a crash

## What to Build

### Relay call (already exists)
`POST` to `RelayUrl()` with `{ action:"login", email, password }` + `x-relay-secret` header → `{ token, userId, email }`. `RelayTask` (`components/tasks/RelayTask.brs`) already does the JSON POST. Reuse the fresh-task-per-call pattern.

### Persistence (`source/registry.brs`)
```brightscript
sec = CreateObject("roRegistrySection", "auth")
sec.Write("token", token) : sec.Write("userid", userId) : sec.Write("email", email)
sec.Flush()
```
Read on boot; token present → skip login. On relay 401 → delete keys + flush → login screen.

### Device ID
Use `CreateObject("roDeviceInfo").GetChannelClientId()` — stable per channel/device, no need to persist or generate a UUID. Needed as `deviceId` for Up Next (M4/M5).

### Dev prefill
Login screen pre-fills from `TestEmail()`/`TestPassword()` in the gitignored `source/secrets.brs` when present, so dev doesn't D-pad-type the password each cycle. Real users type it once; never commit credentials.

## Implementation Strategy

1. Boot path: read registry → token? → main : login screen.
2. Login screen (keyboard) → `RelayTask login` → store token → main.
3. Auto-login + 401 clear-and-return.
4. Logout.

## User Checkpoint

Log in → quit channel → relaunch → still logged in. Wrong password → inline error, stays on login.

## Commit
TBD.
