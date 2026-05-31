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

## Spike 0 — Toolchain + Task HTTP (no protobuf)

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

---

## Spike 2 — Real protobuf round-trip

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
| 1 or 2 fails | Build relay (JSON↔protobuf). Roku M2/M3/M5 collapse to JSON; revisit relay statefulness/scope/hosting decisions. |

Spikes 0+1 are throwaway test scaffolds (httpbin, hash compare). Spike 2 code graduates into M2 login.
