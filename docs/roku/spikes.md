# Roku Spikes — De-risk Before Milestones

**Status**: NOT STARTED

Throwaway-ish experiments that answer the project's pivotal unknown — **can Roku speak Pocket Casts protobuf natively, or do we need a translation relay?** — before committing real milestone work. Run in order; each isolates ONE unknown and is gated. Bail to the relay the moment a gate fails.

The relay idea (a hosted service that speaks protobuf to Pocket Casts and exposes JSON to Roku) is **parked behind these spikes**. Spike 1/2 outcomes decide native-vs-relay. Do not design the relay until a gate forces it.

---

## Prereq — Capture golden bytes (off-Roku)

Before any encode/decode on Roku, capture known-good wire bytes from the **menubar app** (working SwiftProtobuf).

- Capture real `POST /user/login` **request** + **response** bytes — via mitmproxy/Charles, or add a temporary hex `print` in `../pocket-radio-menubar/PocketRadio/Services/APIService.swift`.
- Save as fixtures (hex dumps) in this repo under `spikes/fixtures/` (login req + login resp). **Scrub creds** — login request contains the password; use the dev test account only and do NOT commit a real password. Prefer capturing with the throwaway test account from HANDOFF §4.

**Learns:** the exact bytes Roku's encoder must reproduce and decoder must parse. Without this you debug blind.

---

## Spike 0 — Toolchain + Task HTTP (no protobuf) ✅ DONE (2026-05-31)

**Result: PASS.** On-device chain confirmed: `main` → MainScene → `HttpGetTask` (roUrlTransfer) → 200 / 5967 bytes from radio-browser topvote → `ParseJSON` → 5 station names printed (telnet 8085) + rendered. Dev loop works: `make install` (sideload) + ECP `launch/dev` + scripted socket capture of port 8085.

---

### Original plan

Prove the dev loop and the Task-node networking pattern in isolation.

- Sideload a minimal channel; confirm `Install Success` + launch + telnet `8085` output.
- One `Task` node does a JSON `GET https://de1.api.radio-browser.info/json/stations/topvote?limit=5` (`User-Agent: PocketRadio/1.0`), writes result to an output field, scene observes + prints names.

**Learns:** sideload/telnet loop works; `Task` + `roUrlTransfer` + `observeField` round-trip works; JSON parse works — all without protobuf muddying it.
**Cost:** hours. **Gate:** none (foundational). Scaffold is reusable as the generic HTTP Task.

---

## Spike 1 — Binary byte-fidelity (THE pivotal test)

The unknown HANDOFF §3 hand-waves: Roku has **no `AsyncPostToFile`**; a POST that returns binary comes back only via `roUrlEvent.GetString()`, and `roByteArray.FromAsciiString()` round-trip may corrupt bytes ≥0x80.

- **1a — request side:** build a `roByteArray` of all 256 values `0x00`–`0xFF` → `WriteFile("tmp:/req.bin")` → `AsyncPostFromFile` → `https://httpbin.org/post`. Confirm the echoed body shows all 256 bytes intact (httpbin returns base64 in `data` for non-UTF8 — decode + compare).
- **1b — response side:** `GET` a known binary blob with high bytes (host a small fixture, or hit a known file), read it back via the POST-response path (`GetString()` → `roByteArray`), compare a hash/length to the original.

**Learns:** whether binary survives Roku's POST request path AND the response path.
**Cost:** ~half day.
**🚦 Gate:** if response bytes corrupt and unrecoverable → **relay is mandatory**. Stop native protobuf; un-park the relay design.

### ❌ RESULT: GATE FAILED (2026-05-31) → relay mandatory

On-device (`httpbin.org`, firmware as of test):

```
T1 RESPONSE (GetString binary): FAIL — file=8090 bytes vs str=8 bytes, first diff @ byte 8
T2 REQUEST  (POST binary):      PASS — round-tripped all 256 bytes (0x00–0xFF)
```

- **Request side OK** — `roByteArray.WriteFile` + `AsyncPostFromFile` round-trips arbitrary bytes. Sending protobuf would work.
- **Response side BROKEN** — `roUrlEvent.GetString()` (→`FromAsciiString`) **truncates at the first NUL byte**. PNG = 8-byte signature then `00`, so the string was cut to 8. Roku has **no `AsyncPostToFile`**, so a POST's binary response can only be read via `GetString()`. Protobuf responses contain NUL bytes throughout → unreadable natively.
- `AsyncGetToFile` reads binary correctly (8090 bytes) but is **GET-only** — no help for POST responses.

**Decision: build a JSON↔protobuf relay for Pocket Casts.** Spike 2 (native protobuf encode) skipped — moot when the response can't be read. radio-browser + Supabase stay native JSON (Spike 0 proved that path). Relay scope = `api.pocketcasts.com` only.

---

## Spike 2 — Real protobuf round-trip — ⏭️ SKIPPED

Spike 1 response gate failed, so native protobuf is moot (can't read the binary response regardless of encode correctness). Not run.

### Original plan (only if Spike 1 had passed)

Only if Spike 1 passes. End-to-end against the live API.

- Implement minimal `encodeVarint`/`encodeStringField` over `roByteArray` (HANDOFF §5).
- Encode `Api_UserLoginRequest` (`f1=email`, `f2=password`, `f3="mobile"`); **byte-compare to the golden request fixture** before sending.
- `POST /user/login` (octet-stream headers, HANDOFF §6.1); decode response `f1=token`, `f2=userId`, `f3=email` from the real binary body.

**Learns:** encode matches Swift exactly; decode parses the real Pocket Casts binary response; the full native path is viable.
**Cost:** ~1 day.
**🚦 Gate:** pass → Roku does protobuf natively, **relay optional/deferred**; M2 reuses this login code. Fail → **relay**.

---

## Outcome → milestone path

| Spike result | Path |
|--------------|------|
| 0 ok, 1 ok, 2 ok | Native protobuf. Proceed M2–M6 as written. Relay shelved. |
| **1 fails (ACTUAL)** | **Built relay (JSON↔protobuf).** Roku M2/M3/M5 collapse to JSON. |

## ✅ Relay built + proven (2026-05-31)

Spike 1 forced the relay. Built and validated same day:

- **`pc-relay`** — Supabase Edge Function (Deno/TS), `supabase/functions/pc-relay/` in the meta repo. Stateless proxy: Roku holds the token, passes it per call. Shared-secret header (`x-relay-secret`, env `RELAY_SECRET`), `verify_jwt = false`. Reuses the manual-protobuf wire logic from menubar `APIService.swift`, but in Deno where binary is NUL-safe.
- **Endpoints** (full Pocket Casts surface, HANDOFF §6): `login`, `upNext`, `podcastEpisodes`, `updateEpisode`, `upNextChange`, `namedSettings`, `podcastList`.
- **Validated**: local Deno round-trip (login + upNext, 19 episodes) → deployed → live curl (login/upNext/403 gate) → **on-device Roku E2E**: `RelayTask` (JSON POST) → relay → Pocket Casts → JSON → 19 episodes rendered. Telnet-confirmed.

**Decisions locked:** Supabase Edge Functions (zero new infra, ~$0 for one user) · stateless proxy · shared-secret + TLS · relay scope = Pocket Casts only (radio-browser + Supabase stay native JSON from Roku).

**Roku gotchas learned:** `source/` globals aren't visible in component scope — include shared `.brs` via `<script>` in each component. Re-running one Task node from inside its own field observer doesn't refire — create a fresh Task per call.

**Next:** M2+ now hit the relay (JSON), not protobuf. Update milestone bodies accordingly. Relay secret + URL live in `pocket-radio-roku/SECRETS.local.md` and the gitignored `source/secrets.brs`.
