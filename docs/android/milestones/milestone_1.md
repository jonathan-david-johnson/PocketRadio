# M1 — Playback core: `MediaSessionService` + hardcoded KCRW

**Goal:** Build `:core:player` — the Android "Engine" — around a Media3
`MediaSessionService` so audio survives backgrounding, app switching, and
rotation. Prove it against a single hardcoded stream URL (KCRW) with no auth,
no API, and no lists. This is the riskiest structural unknown on Android and
the one thing no sibling platform's source can be copied for, so it is
de-risked before any Pocket Casts work begins.

**User checkpoint:** Launch either app (TV or mobile) → press play → hear KCRW
→ press Home / switch apps → audio keeps playing → return to the app → the UI
still shows "playing" with correct elapsed time. On mobile, a media
notification appears with working play/pause; on TV, the D-pad play/pause key
works.

## Scope

### `:core:player` — the Engine
- `PlaybackService : MediaSessionService` — owns the single `ExoPlayer`
  instance and a `MediaSession`. Declared in `:core:player`'s manifest so both
  app modules inherit it via manifest merge. Foreground service type
  `mediaPlayback`; `FOREGROUND_SERVICE` + `FOREGROUND_SERVICE_MEDIA_PLAYBACK`
  permissions.
- `PlayerEngine` — the API the UI talks to. Wraps a `MediaController` future
  bound to the service. Exposes `load(source)`, `play()`, `pause()`,
  `seekTo()`, and a `StateFlow<NowPlaying>`.
- `NowPlaying` state in `:core:model`: source identity, title, artwork URL,
  position, duration, `isLive`, `isPlaying`, buffering/error. The single state
  object both UIs render around — the Android equivalent of console's
  `internal/library` and menubar's `PlayerViewModel`.
- **Live-vs-seekable gating.** A live radio stream has no meaningful duration
  or seek. `NowPlaying.isLive` drives whether the scrubber renders at all.
  Getting this into the model now avoids retrofitting it in M3/M4.
- `PositionTicker` — emits position updates on a ~1s cadence while playing,
  stops when paused. Position *saving* (throttled network writes) is M4; this
  milestone only produces the values.

### App modules
- Both `:tv` and `:mobile` bind to `PlayerEngine`, render `NowPlaying`, and
  offer play/pause. Near-identical shells (ADR-0002) — station name, a
  play/pause control, elapsed time.
- `:mobile` — `POST_NOTIFICATIONS` runtime permission request (API 33+),
  README hazard #2. Media notification comes free from `MediaSessionService`
  once the permission is granted; verify it does.
- `:tv` — handle `KEYCODE_MEDIA_PLAY_PAUSE` and D-pad center on the play
  control. No notification.

### Config
- KCRW stream URL as a constant in `:core:player` test fixtures / a debug
  constant. **Not** a hardcoded value that survives into M3 — M3 replaces it
  with resolved radio-browser URLs.
- Confirm the KCRW URL's scheme against `network_security_config.xml`. If it's
  cleartext `http://`, this is where hazard #3 gets its first real exercise.

## Behaviors to test (red → green, one at a time)

1. **`PlaybackService` starts as a foreground service and posts a media
   notification** when playback begins on mobile, with the correct foreground
   service type. Instrumented test.
2. **Audio continues playing after the Activity is destroyed.** Start
   playback, finish the Activity, assert the `ExoPlayer` in the service is
   still in `STATE_READY` and `isPlaying`. This is the milestone's whole
   point. Instrumented test.
3. **`PlayerEngine` reconnects to an already-playing session on rebind** and
   its `StateFlow<NowPlaying>` immediately emits the in-progress state
   (correct position, `isPlaying = true`) rather than a reset/idle state.
   Depends on 2.
4. **`NowPlaying.isLive` is true for the KCRW stream and the scrubber is not
   rendered.** Pure model + Compose test; no network needed if the duration
   signal is injected. Independent of 1–3.
5. **`PositionTicker` emits ~1 update/sec while playing and stops within one
   tick of pausing.** Pure JVM test in `:core:player` with a virtual-time
   coroutine dispatcher. Independent.
6. **Play/pause from the mobile media notification updates
   `StateFlow<NowPlaying>`** — i.e. the notification and the in-app UI never
   disagree. Depends on 1.
7. **`KEYCODE_MEDIA_PLAY_PAUSE` toggles playback on TV.** Instrumented test on
   the TV module. Depends on 2. Independent of 6.
8. **A stream URL that fails to resolve surfaces as `NowPlaying.error`** and
   does not crash or leave a stuck foreground service. Feed a bad URL; assert
   the service stops. Independent of 6/7.
9. **Cleartext (`http://`) stream URLs play**, or fail with a diagnosable
   error rather than a silent no-op — README hazard #3. Depends on the
   `network_security_config.xml` decision.

Behaviors 4, 5, and 8 are pure/near-pure and can fan out immediately in
parallel with the service work. 1→2→3 is the critical path and should land
first. 6, 7, and 9 fan out once 2 is green.

## Out of scope

- Any Pocket Casts API call, login, or protobuf byte — M2.
- Radio favorites, station search, or dynamic stream URLs — M3. The KCRW URL
  is hardcoded here on purpose.
- Position *persistence* or sync to Pocket Casts — M4. M1 produces position
  values but writes them nowhere.
- Artwork loading, tracklists, ICY metadata — M6.
- Audio focus / ducking against other apps, Bluetooth and Android Auto
  routing — M7. Media3 gives some of this by default; it is not tested or
  guaranteed here.
- Real 10-foot or touch-native UX (ADR-0002 keeps both app modules as shells
  until M7).
