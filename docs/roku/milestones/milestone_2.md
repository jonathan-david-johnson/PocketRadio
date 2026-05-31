# M2: Login + Persistence (Protobuf)

**Status**: NOT STARTED

## Goal

Pocket Casts login over manual protobuf (file-based POST), token persisted in `roRegistrySection`, auto-login on launch, 401 handling. First real protobuf round-trip on the device.

## Done when

- Login screen accepts email/password (keyboard node)
- `POST /user/login` succeeds: token + userId + email decoded from the protobuf response
- Token + userId + email written to registry section `"auth"` (`.Flush()` after write)
- On relaunch, channel auto-logs-in from stored token (no re-entry)
- 401/403 → clear stored token, return to login screen
- Logout clears the registry section

## What to Build

### Protobuf helpers (HANDOFF §5)
Implement over `roByteArray`: `encodeVarint`, `encodeStringField`, `encodeVarintField`, `encodeLenDelimField`, and a decode walker (tag → fieldNumber `>>3`, wireType `and 7`; wt0=varint, wt2=len-delimited, wt1 skip 8, wt5 skip 4, skip unknown). Put in `source/protobuf.brs`.

### Login Task node (`components/tasks/LoginTask`)
- Build `Api_UserLoginRequest`: `f1=email`, `f2=password`, `f3="mobile"` → `roByteArray`.
- **Binary-safe POST**: `bytes.WriteFile("tmp:/req.bin")`; `xfer.AsyncPostFromFile("tmp:/req.bin")`; capture response to file (`AsyncGetToFile`/file variant) → `ba.ReadFile`. Headers: `Content-Type: application/octet-stream`, `Accept: application/octet-stream`, `User-Agent: PocketRadio/1.0`.
- Decode response: `f1=token`, `f2=userId`, `f3=email`. Write output field; scene observes.

### Persistence (`source/registry.brs`)
```brightscript
sec = CreateObject("roRegistrySection", "auth")
sec.Write("token", token) : sec.Write("userid", userId) : sec.Write("email", email)
sec.Flush()
```
Read on boot; if token present → skip login. On 401 → delete keys + flush.

### Device ID
Persist a UUID once in the registry (or `roDeviceInfo().GetChannelClientId()`) — needed for Up Next in M3.

## Implementation Strategy

1. Write + unit-eyeball protobuf encode/decode against the login round-trip (print hex on telnet).
2. Wire login Task + keyboard screen.
3. Add registry read/write + auto-login + 401 path.

## User Checkpoint

Log in → quit channel → relaunch → still logged in (lands past login). Wrong password → error, stays on login.

## Commit
TBD.
