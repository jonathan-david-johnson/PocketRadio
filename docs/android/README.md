# PocketStreams for Android

Android companion to PocketRadio, shipped to **two form factors from one
codebase**: Android TV / Google TV (10-foot, D-pad) and phone/tablet (touch).
Plays the user's Pocket Casts **Up Next** queue (with resume + progress sync)
and **favorite radio streams** (Supabase → radio-browser.info).

Target: **feature parity with the macOS menubar app** (not the full iOS app) —
same bar the Roku channel and console app are held to.

The macOS menubar app remains the canonical spec:
`../pocket-radio-menubar/PocketRadio/Services/APIService.swift` for the API +
protobuf wire format, `PocketRadio/View Models/PlayerViewModel.swift` for
playback/state logic.

> **Closest existing reference: the console app.**
> `../pocket-radio-console/internal/pocketcasts/` is a from-scratch,
> non-Swift, hand-rolled-protobuf port of that same spec. It is the blueprint
> for `:core:pocketcasts` — read `protobuf.go`, `client.go`, and `lists.go`
> before writing any Kotlin wire code.

## Architecture decisions

Two ADRs record where Android deliberately diverges from sibling platforms:

- [ADR-0001](./adr/0001-native-protobuf-not-relay.md) — Android speaks Pocket
  Casts **protobuf natively**, and does **not** use the `pc-relay` Edge
  Function the Roku channel depends on.
- [ADR-0002](./adr/0002-shared-core-two-app-modules.md) — one `:core:*` stack,
  two thin app modules (`:tv`, `:mobile`).

## Module graph

```
pocket-radio-android/
├── settings.gradle.kts             # module registry
├── gradle/libs.versions.toml       # version catalog (single source of dep truth)
├── core/
│   ├── model/                      # pure Kotlin/JVM — Episode, Station, NowPlaying. No Android deps.
│   ├── pocketcasts/                # protobuf wire + OkHttp client (port of console internal/pocketcasts)
│   ├── radio/                      # Supabase favorites, radio-browser resolver, KCRW/KEXP tracklists
│   ├── auth/                       # token store (DataStore + EncryptedSharedPreferences)
│   ├── player/                     # Media3/ExoPlayer + MediaSessionService — the "Engine"
│   └── designsystem/               # Compose theme + tokens shared by both app modules
├── tv/                             # app module — Compose for TV (androidx.tv), D-pad, leanback launcher
└── mobile/                         # app module — Compose Material3, touch, media notification
```

`core/model`, `core/pocketcasts`, and `core/radio` are **pure Kotlin/JVM
modules** — no Android framework dependency. That keeps the whole API + wire
layer testable on the JVM with no emulator, which is where the bulk of the
test suite lives.

## Backend surface

| Service | Transport | Auth | Used for |
|---------|-----------|------|----------|
| `api.pocketcasts.com` | **protobuf** over HTTPS POST | `Bearer <token>` | `/user/login`, `/up_next/sync`, `/user/podcast/episodes`, `/user/podcast/list`, `/sync/update_episode`, `/user/named_settings/update` |
| `cache.pocketcasts.com` | JSON | none | `/mobile/podcast/full/<uuid>` — full episode lists + show notes |
| `brvtspdculqyvdrmdtef.supabase.co` | JSON (PostgREST) | `x-user-uuid` header | `radio_favorites` |
| `de1.api.radio-browser.info/json` | JSON | none | station search + stream URL resolution. **Requires `User-Agent: PocketRadio/1.0`.** |
| `tracklist-api.kcrw.com`, `api.kexp.org/v2/plays` | JSON | none | now-playing tracklists while those stations are active |

All request bodies for `api.pocketcasts.com` are hand-encoded protobuf — no
protobuf runtime dependency, matching menubar and console. See ADR-0001.

## Platform notes (vs menubar / Roku)

| Aspect | Menubar (Swift) | Roku (BrightScript) | Android (Kotlin) |
|--------|-----------------|---------------------|------------------|
| UI | SwiftUI / AppKit | SceneGraph XML | Compose (`androidx.tv` on TV, Material3 on mobile) |
| Network | URLSession async | `roUrlTransfer` on Task nodes | OkHttp + coroutines |
| Protobuf | manual encode/decode | ❌ impossible — uses `pc-relay` | manual encode/decode over `ByteArray` |
| Token store | Keychain | `roRegistrySection` | DataStore + `EncryptedSharedPreferences` |
| Audio | AVPlayer | `Audio` SceneGraph node | Media3 ExoPlayer + `MediaSessionService` |
| Background play | n/a | n/a | **foreground service required** — biggest new-platform risk |
| Testing | Xcode | sideload + telnet, no emulator | JVM unit tests for `:core:*`; instrumented only for player/UI |

### Android-specific hazards

1. **Playback must live in a `MediaSessionService`**, not a ViewModel. An
   Activity-scoped player dies on backgrounding/rotation and takes the audio
   with it. This is the single largest structural difference from every other
   PocketRadio surface and is why `:core:player` is M1, before any API work.
2. **`POST_NOTIFICATIONS` runtime permission** (API 33+) gates the media
   notification on mobile. TV does not need it.
3. **Cleartext is disabled by default** — some radio-browser stream URLs are
   plain `http://`. Needs an explicit `network_security_config.xml` allowlist
   or stream-URL upgrade, or those stations silently fail to play.
4. **TV app needs `<uses-feature android:name="android.software.leanback">`**
   and a `LEANBACK_LAUNCHER` intent filter, or it won't appear on the TV home
   screen. Mobile must declare `android.hardware.touchscreen` non-required for
   the TV build to pass Play validation.
5. **Protobuf bytes ≥ 0x80** — same trap as Roku, different mechanism. Never
   round-trip response bodies through `String`; read `ByteArray` off
   `ResponseBody.bytes()` directly.

## Milestones

| Milestone | What | User checkpoint |
|-----------|------|-----------------|
| [M0](./milestones/milestone_0.md) | Project skeleton + CI | `make android-tv` and `make android-mobile` both install and launch a placeholder |
| [M1](./milestones/milestone_1.md) | Playback core — `MediaSessionService` + hardcoded KCRW | Launch either app → hear audio → survives backgrounding |
| M2 | Auth — protobuf primitives + `/user/login` + token store | Log in → force-stop → relaunch → still logged in |
| M3 | Radio favorites + browse/search (tracer bullet) | See favorites → play → add/remove → search radio-browser |
| M4 | Up Next — list + play + resume + position save | See queue → play → resumes at `playedUpTo` → position syncs |
| M5 | Up Next lifecycle + New Releases + show notes | Finish → advance; playNow; last-14d list; episode notes |
| M6 | Polish — skip settings, scrub, tracklist, Now Playing | Scrub seekable, tracklist shows, artwork/title correct |
| M7 | Form-factor divergence | TV: full 10-foot browse. Mobile: media notification + Android Auto |

**Ordering rationale** — two deliberate departures from the Roku order:

- **Playback (M1) comes before auth (M2).** On Roku the `Audio` node is
  trivial; on Android the foreground-service/`MediaSessionService` structure
  is the riskiest unknown and dictates how `:core:player` is shaped. De-risk
  it against a hardcoded stream URL before any credentials exist.
- **Radio (M3) still precedes Up Next (M4/M5)**, same as Roku — it's all JSON,
  and it builds the generic list UI, dynamic-URL playback, and
  live-vs-seekable gating on the easy path. Up Next then layers resume, sync,
  and lifecycle onto proven UI.

Form-factor divergence is deferred to M7 on purpose: M1–M6 build both app
modules as thin, near-identical shells over `:core:*`, which keeps parity
honest by construction. Real 10-foot and touch-native UX lands only once the
shared core is proven.

## Repo

`pocket-radio-android/` — own git repo
(`jonathan-david-johnson/pocket-radio-android`), **not yet scaffolded**.
`make checkout` clones it once it exists.

## Build & run

```bash
# from repo root — delegates to pocket-radio-android/Makefile
make android-build      # assemble both app modules (debug)
make android-test       # JVM unit tests across :core:*
make android-tv         # install + launch on TV device/emulator
make android-mobile     # install + launch on phone device/emulator
make android-log        # adb logcat filtered to the app
make android-lint       # ktlint + android lint
```

TV device targeting uses `ANDROID_TV_SERIAL`; mobile uses
`ANDROID_MOBILE_SERIAL`. Both default to the single connected device.
