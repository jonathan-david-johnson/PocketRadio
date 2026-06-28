# Global M1.1 — Remote Protocol: One Home (golden fixtures + typed menubar decode)

**Status**: PLANNED
**Platforms**: iOS (`pocket-radio-ios/`) + menubar (`pocket-radio-menubar/`)
**Depends on**: M1 (transport + receiver proven end-to-end)
**Source**: architecture review candidate #1 ("give the remote protocol one home")

---

## Why

The remote protocol — command verbs, presence fields, snake_case wire keys — is the contract
between the two players. After M1 it has **no single home**: iOS expresses it as typed
`Codable` structs (`RemoteCommand.swift`); menubar re-expresses it as hand-built
`[String:Any]` dictionaries (`RemoteControlService.handleCommand` / `sendPresence`). The
contract is asserted twice and checked nowhere.

Every bug debugged during M1 lived in exactly this gap:
- the `realtime:` topic prefix (transport envelope, not contract — but undocumented),
- the nested `payload` shape,
- loose dictionary keys on the menubar receiver.

Each was found by hand. A small executable contract would have failed loudly instead.

**Principle:** the wire is JSON, so the contract stays JSON-shaped (golden fixtures), not
binary. Codegen reduces hand-typing; only **fixtures verify** the hand-typed mirrors didn't
drift. Because Roku (BrightScript) and console (Go) will hand-mirror regardless, the fixture
corpus is the load-bearing piece — it is the contract; the typed structs are conveniences
that must conform to it.

**Prior art on iOS:** `PocketCastsTests/Tests/Radio/RemoteCommandTests.swift` already exists
and round-trips the structs (encode → decode) plus asserts snake_case keys. But it is
**self-anchored** — it encodes an in-memory struct and decodes its own output, so it proves
iOS is internally consistent, NOT that iOS matches a shared external contract. The new
fixture tests are anchored to on-disk JSON that *every* platform checks against; that shared
anchor is the new guarantee. Keep both: `RemoteCommandTests` (self-consistency) and
`RemoteCommandFixtureTests` (cross-platform contract) are complementary, not duplicate.

---

## Decisions (locked)

| Decision | Choice |
|----------|--------|
| Fixture home | **Shell repo** at `contracts/remote/*.json`. Sub-project tests load via relative path (`../contracts/remote/...`). Single source, no duplication. |
| Scope | Fixtures + round-trip tests on **iOS + menubar**, **and** refactor menubar `handleCommand`/`sendPresence` from `[String:Any]` to typed `Codable` structs mirroring iOS. |
| Out (this milestone) | Go console + Roku fixture tests (no receivers yet); JSON-Schema/codegen (premature); shared SPM package for the two Swift apps (later — see M1.2 candidate). |

**Contract unit = the inner `RemoteCommand` / `RemotePresence` JSON object** (snake_case),
NOT the Phoenix envelope. The envelope (`realtime:` prefix, `event=broadcast` wrapper) is a
**transport** concern owned by each side's channel layer, documented but not fixtured here.

---

## Fixture corpus

New directory at the **monorepo shell root**: `contracts/remote/`

```
contracts/remote/
  README.md              # what these are, how each platform consumes them
  command_play.json
  command_pause.json
  command_stop.json
  command_load_station.json
  presence_ios.json      # role=sender
  presence_macos.json    # role=receiver
```

Each command fixture is one canonical `RemoteCommand` object, e.g.
`command_load_station.json`:

```json
{
  "command_id": "11111111-1111-1111-1111-111111111111",
  "from_device_id": "AAAAAAAA-0000-0000-0000-000000000000",
  "target_device_id": "BBBBBBBB-0000-0000-0000-000000000000",
  "command": "load_station",
  "payload": {
    "station_id": "kcrw",
    "station_url": "https://kcrw.streamguys1.com/kcrw_192k_mp3_on_air_internet_radio",
    "station_name": "KCRW"
  },
  "sent_at": "2026-06-28T00:00:00Z"
}
```

`presence_macos.json`:

```json
{
  "device_id": "BBBBBBBB-0000-0000-0000-000000000000",
  "device_type": "macos",
  "device_name": "Test Mac",
  "role": "receiver",
  "playback": {
    "state": "playing",
    "station_id": "kcrw",
    "station_name": "KCRW"
  },
  "updated_at": "2026-06-28T00:00:00Z"
}
```

These literals double as documentation of the protocol — the only place the full shape is
written down once.

**No explicit `null` keys in fixtures.** Swift `JSONEncoder` **omits** a nil optional (it
does not emit `"key": null`). If a fixture carried `"artwork_url": null`, the re-encode step
in the round-trip test would drop the key and the order-insensitive key-set compare would
fail — even though iOS already conforms. So absent-optional fields are **omitted** from
fixtures (e.g. `artwork_url` left out above), and decoders must treat a missing key as
`nil`. To document that a field *can* be null without breaking round-trip, note it in
`contracts/remote/README.md`, not as a literal `null` in the corpus.

---

## Approach

### A. iOS — round-trip tests (no production code change)

- New `PocketCastsTests/Tests/Radio/RemoteCommandFixtureTests.swift` (auto-discovered).
- For each command fixture: load JSON → `JSONDecoder().decode(RemoteCommand.self)` → assert
  typed fields → assert `command` ∈ known verb set (`play/pause/stop/load_station`) → re-encode
  → assert key-equal to the fixture (order-insensitive compare; fixtures omit nil fields so
  re-encode matches — see corpus note).
- Same for `RemotePresence` against the presence fixtures; assert `playback.state` ∈ known
  state set.
- Fixture path resolved from `#filePath` → walk up to repo root → `../contracts/remote/`.
  (iOS repo is a direct child of the shell root.)

### B. menubar — typed decode refactor + round-trip tests

1. New `PocketRadio/Models/RemoteCommand.swift` — `RemoteCommand`,
   `RemoteCommandPayload`, `RemotePresence`, `RemotePlaybackState` as `Codable` structs with
   snake_case `CodingKeys`, **wire-mirroring iOS** (identical JSON bytes; the *Swift types*
   need not match). Add a `RemoteVerb` enum (`play/pause/stop/loadStation`, String raw values)
   and `PlaybackState` enum. Note iOS models `command`/`state` as plain `String`; menubar
   tightens to enums. Encoded bytes are identical, but decode strictness diverges (see Drift
   guard below) — that divergence is intentional, menubar is the strict receiver.
2. Refactor `RemoteControlService.handleCommand(_ raw:)` to decode the broadcast payload into
   `RemoteCommand` (one `JSONDecoder` call) instead of `raw["..."]` lookups. Switch on the
   typed verb enum (exhaustive). Keep dedup + target-filter in transport, before decode.
3. Refactor `sendPresence()` to build a `RemotePresence` struct and `JSONEncoder` it instead
   of the hand-built dictionary literal. **Impedance note:** the existing `send(...)` takes
   `payload: [String:Any]` and wraps it in the Phoenix envelope. Typed `send()` is deferred to
   M2 (out of scope #4), so this milestone the struct must bounce back to a dict:
   `RemotePresence` → `JSONEncoder` → `Data` → `JSONSerialization.jsonObject` → `[String:Any]`
   → `send(...)`. That round-trip is expected, not a smell — it isolates the typed model from
   the still-untyped transport boundary. Do not widen `send()` here.
4. New `PocketRadioTests/RemoteCommandFixtureTests.swift` — same round-trip assertions as iOS,
   fixtures via `../contracts/remote/`.
5. Add `make menubar-test` to the root Makefile
   (`xcodebuild test -project ... -scheme PocketRadio`), mirror `console-test`.

### C. pbxproj registration

- iOS: test file auto-discovered (synchronized group) — no edit.
- menubar: `PocketRadio.xcodeproj/project.pbxproj` has **zero** `PBXFileSystemSynchronizedRootGroup`
  (confirmed) → nothing in the menubar project auto-discovers. **Register both files** in
  pbxproj: `RemoteCommand.swift` in the main `PocketRadio` target, and
  `RemoteCommandFixtureTests.swift` in the `PocketRadioTests` target. No "verify early" — it's
  settled.

---

## Done when

### Contract corpus
- [ ] `contracts/remote/` exists at shell root with 4 command + 2 presence fixtures + README.

### iOS
- [ ] `RemoteCommandFixtureTests` round-trips all 6 fixtures; `make test_staging` green.
- [ ] No production-code change required (proves iOS already conforms).

### menubar
- [ ] `RemoteCommand.swift` typed model added + pbxproj-registered.
- [ ] `handleCommand` decodes typed `RemoteCommand`; verb switch is an exhaustive enum.
- [ ] `sendPresence` encodes a `RemotePresence` struct (no hand-built dict).
- [ ] `RemoteCommandFixtureTests` round-trips all 6 fixtures.
- [ ] `make menubar-test` target added and green.
- [ ] `make menubar-build` green; end-to-end re-verified (Supabase REST broadcast →
      menubar plays KCRW, as in M1).

### Drift guard
- [ ] A **key** rename in one fixture (e.g. `command_id` → `cmd_id`) fails **both** platforms'
      tests (manually confirm once) — both decode by snake_case `CodingKeys`, so a missing key
      throws on both.
- [ ] A **verb-value** drift (e.g. `load_station` → `loadStation`) fails menubar (enum,
      unknown case throws) but, by default, **not** iOS (`command: String` accepts any value).
      To close the gap, `RemoteCommandFixtureTests` on iOS asserts each decoded `command`
      against a known verb set (`play/pause/stop/load_station`) and each `playback.state`
      against a known state set — so verb drift fails iOS too.

---

## Risks / unknowns

- **Relative fixture path under `xcodebuild`**: the test's working directory is not the repo
  root. Resolve from `#filePath`, not `FileManager.currentDirectoryPath`.
- **Envelope vs contract confusion**: do NOT fixture the Phoenix `realtime:`/`broadcast`
  wrapper here — keep the corpus to the inner object. Add a one-paragraph note in
  `contracts/remote/README.md` pointing at where the envelope lives on each side.

---

## Out of scope (M1.1)

- Go console + Roku fixture tests (no receivers until later milestones; corpus is ready for them).
- JSON-Schema source-of-truth + quicktype codegen (revisit if a 3rd typed platform lands).
- Shared SPM package unifying the two Swift apps' types (candidate for a later M1.2).
- Typed `send()` enum interface (architecture review #4 — deferred to M2 when real callers appear).
- Connection-lifecycle state machine (architecture review #5 — deferred).
