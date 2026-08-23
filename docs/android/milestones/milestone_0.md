# M0 — Project skeleton + CI

**Goal:** Stand up the `pocket-radio-android` repo as a Gradle multi-module
Kotlin project with the module graph from ADR-0002 in place, two installable
placeholder app modules (TV and mobile), a JVM test task that actually runs,
and a Makefile that the top-level `PocketRadio/Makefile` can delegate to. No
product behavior — this milestone exists so that every later milestone has a
place to put code and a green build to break.

**User checkpoint:** From the PocketRadio repo root, `make android-tv` installs
and launches an app on an Android TV emulator that shows "PocketStreams" on a
10-foot placeholder screen; `make android-mobile` does the same on a phone
emulator with a touch placeholder. `make android-test` runs and passes.

## Scope

### Repo + build
- New git repo `jonathan-david-johnson/pocket-radio-android`, cloned to
  `pocket-radio-android/`.
- `settings.gradle.kts` registering all eight modules from ADR-0002.
- `gradle/libs.versions.toml` — version catalog as the single source of
  dependency truth. Pin: Kotlin, AGP, Compose BOM, `androidx.tv`, Media3,
  OkHttp, kotlinx-serialization, kotlinx-coroutines, DataStore, JUnit5, MockK.
- Root `build.gradle.kts` with shared convention config (compile SDK, JVM
  target, Kotlin compiler options) applied to subprojects.
- `.gitignore` (Android/Gradle/IDEA), `gradle.properties` (AndroidX, JVM args,
  configuration cache on).

### Module stubs
- `core/model` — Java library module (`kotlin("jvm")`), no Android plugin.
  Contains a single placeholder type so the module compiles.
- `core/pocketcasts`, `core/radio` — `kotlin("jvm")` modules. Empty but wired
  and test-capable. **These must not apply the Android plugin** (ADR-0002).
- `core/auth`, `core/player`, `core/designsystem` — Android library modules.
- `tv/` — Android application module. `applicationId`
  `com.pocketradio.streams`, TV flavor via its own manifest:
  `<uses-feature android:name="android.software.leanback" android:required="true">`,
  `<uses-feature android:name="android.hardware.touchscreen" android:required="false">`,
  `LEANBACK_LAUNCHER` intent filter, `android:banner`.
- `mobile/` — Android application module. Same `applicationId` base with a
  `.mobile` suffix so both can be installed on one device during development.
  Standard `LAUNCHER` intent filter.
- Both app modules depend on `:core:designsystem` and render a placeholder
  Compose screen. Nothing else.

### Assets + config
- App icon, TV banner (320×180), and adaptive icon for mobile.
- `network_security_config.xml` in both app modules with a cleartext
  allowlist placeholder — see README hazard #3. Referenced from the manifest
  now so M3's radio streams don't hit it as a surprise.

### Tooling
- `pocket-radio-android/Makefile` — real targets: `build`, `test`, `tv`,
  `mobile`, `log`, `lint`, `clean`. Device selection via `ANDROID_TV_SERIAL` /
  `ANDROID_MOBILE_SERIAL`, defaulting to the single connected device.
- ktlint (or Spotless) wired to `make lint`.
- GitHub Actions workflow: assemble both app modules + run JVM unit tests on
  push. No instrumented tests in CI (no emulator) — that stays local.

### Meta-repo integration
- Top-level `Makefile`: `ANDROID_REPO`, `ANDROID_DIR`, the `android-*`
  delegating targets, `android` in `SUBMODULES`, a clone block in `checkout`,
  and a help section. Delegation only — no build logic at the top level.

## Behaviors to test (red → green, one at a time)

1. **`./gradlew build` succeeds on a clean clone** with all eight modules
   registered and no module missing from `settings.gradle.kts`.
2. **`:core:model`, `:core:pocketcasts`, and `:core:radio` compile without the
   Android Gradle plugin.** Assert via a build check that these modules'
   configurations contain no `com.android.*` plugin — this is the ADR-0002
   invariant and the thing most likely to silently rot. Depends on 1.
3. **A JVM unit test in `:core:model` runs and passes under `make android-test`**,
   proving the test source set, JUnit5 wiring, and Make target work end to
   end. Depends on 1.
4. **`:tv` assembles and its merged manifest contains the leanback
   `uses-feature` (required=true), touchscreen `uses-feature` (required=false),
   and a `LEANBACK_LAUNCHER` intent filter.** Manifest assertion, not a
   screenshot — README hazard #4. Depends on 1.
5. **`:mobile` assembles and its merged manifest contains a standard
   `LAUNCHER` intent filter** and an `applicationId` distinct from `:tv`, so
   both install side by side on one device. Depends on 1.
6. **Both app modules resolve `:core:designsystem` and render a placeholder
   Compose screen showing "PocketStreams".** Instrumented or Compose-preview
   smoke check. Depends on 4 and 5.
7. **`make android-tv` and `make android-mobile` from the PocketRadio root
   reach the correct nested Makefile target**, verified with `make -n`
   (dry-run) so it doesn't need a device attached. Depends on the top-level
   Makefile edit.
8. **CI workflow assembles both app modules and runs JVM tests on push.**
   Green run on the first pushed commit. Depends on 1 and 3.

Behaviors 2–5 are independent once 1 lands and can fan out in parallel.
Behavior 7 depends only on the two Makefiles and can run alongside all of them.

## Out of scope

- Any network call, protobuf byte, or credential — M2.
- Any real playback; `:core:player` is an empty module here. Media3 wiring is
  **M1**, deliberately the first real milestone (README § Ordering rationale).
- Supabase or radio-browser clients — M3.
- Real 10-foot or touch-native UX. Placeholders only; both app modules stay
  near-identical shells until M7 (ADR-0002).
- Play Store signing config, release build types, ProGuard rules. Debug builds
  and `adb install` only until there's something worth shipping.
- Instrumented tests in CI — needs an emulator runner, revisit if the
  `:core:player` suite grows past what's comfortable to run locally.
