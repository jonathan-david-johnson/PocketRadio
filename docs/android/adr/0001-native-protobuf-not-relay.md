# ADR-0001 — Android speaks Pocket Casts protobuf natively (no `pc-relay`)

**Status:** Accepted (2026-08-23)
**Applies to:** `pocket-radio-android`, `core/pocketcasts`

## Context

The Roku channel cannot read binary protobuf: `roUrlTransfer` truncates
responses at the first NUL byte and BrightScript has no `AsyncPostToFile`
(proven in `docs/roku/spikes.md`, Spike 1). That forced the `pc-relay`
Supabase Edge Function — a JSON↔protobuf translator at
`supabase/functions/pc-relay/` — and Roku speaks only JSON.

`pc-relay` now exists and works. The tempting move is to reuse it for Android
and skip all wire-format work.

## Decision

**Android talks to `api.pocketcasts.com` directly, encoding and decoding
protobuf itself.** It does not depend on `pc-relay`.

Wire code is **hand-rolled** — varint/length-delimited encode + decode over
`ByteArray` — with **no protobuf runtime dependency and no `.proto` files**.
This matches menubar (`APIService.swift`) and console
(`internal/pocketcasts/protobuf.go`) exactly.

## Rationale

- **The Roku constraint does not exist on Android.** OkHttp returns a real
  `ByteArray` via `ResponseBody.bytes()`. There is no NUL truncation and no
  binary-safety problem. `pc-relay` solves a problem Android does not have.
- **The relay is a liability, not an asset, for a client that doesn't need
  it.** It adds a network hop, a second failure domain, cold-start latency,
  and couples Android releases to relay schema changes. Roku accepts that cost
  because it has no choice.
- **The port is small and already proven twice.** Console's `protobuf.go` is
  ~130 lines total and was written from the Swift original. Android is the
  third port of the same 130 lines, not a research project.
- **No `.proto` files, because we don't have the schema.** Pocket Casts'
  `.proto` definitions aren't published; menubar and console both reverse-
  engineered field numbers from observed traffic. Generating Kotlin stubs
  would require first inventing a `.proto` that encodes those guesses —
  strictly more work and more drift surface than porting the 130 lines that
  already encode them correctly.
- **Keeps `:core:pocketcasts` a pure Kotlin/JVM module.** A hand-rolled
  encoder has no Android dependency, so the whole API layer unit-tests on the
  JVM with no emulator.

## Consequences

- Field numbers are duplicated in a fourth place (Swift, Go, Deno, Kotlin). A
  Pocket Casts wire-format change now breaks four surfaces independently.
  Mitigation: the byte-level fixtures in `core/pocketcasts` tests are ported
  from console's `protobuf_test.go` so a change fails loudly and identically
  on both.
- Android carries login credentials and talks to Pocket Casts directly, so it
  needs its own token storage and refresh handling rather than inheriting the
  relay's. Covered in M2.
- If Pocket Casts ever adds request signing or attestation that only a server
  can satisfy, this decision reverses and Android moves onto `pc-relay`. The
  `:core:pocketcasts` module boundary is drawn so that swap is a single
  implementation change behind the existing interface.

## Related

- `docs/roku/spikes.md` — the spike that forced the relay for Roku
- `docs/roku/README.md` § Architecture decision (2026-05-31)
- `pocket-radio-console/internal/pocketcasts/` — the port blueprint
