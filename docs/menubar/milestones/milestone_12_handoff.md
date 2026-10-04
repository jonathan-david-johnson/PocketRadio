# M12 — normal KCRW playback verification handoff

**Status:** ACCEPTED AND MERGED — the user accepted the installed build on 2026-10-04. Menubar commit `fb1943d`, merged to `main` at `8838df5` and pushed. The text below records the pre-merge verification state.
**Next action:** None for M12. Bugs 2 and 3 remain open. The iOS port is planned separately under `docs/ios/`.
**Scope:** [M12](milestone_12.md), executed with the [all-Sol subagent plan](milestone_12_subagent_plan.md).

## Where the work is

| Area | State |
|---|---|
| Menubar | `feature/kcrw-normal-use` in `pocket-radio-menubar/`; base `464ca70ecad506d9f8c124030706bb87dd2b145e` plus uncommitted diff |
| Shell | `main`, tested coordination revision `878e771684ac18f6b6899e3a999c8349c4ae901e` plus uncommitted M12 documentation/role changes |
| Current milestone | `docs/menubar/current_milestone.md` now points to `milestones/milestone_12.md`; M11-B archive was not overwritten |
| Verified build | `/tmp/pocketradio-m12-build-verification/Build/Products/Debug/PocketRadio.app` |
| Release compile artifact | `/tmp/pocketradio-m12-build-verification/Build/Products/Release/PocketRadio.app` |
| Installed/running app | `/Applications/PocketRadio.app`, switched from the prior M11-B listener with user approval on 2026-10-04 |
| Previous installed app backup | `/tmp/pocketradio-pre-m12-install.aGHNyE/PocketRadio.app` |
| Prior running M11-B artifact | `/tmp/pocketradio-m11b-current-check/Build/Products/Debug/PocketRadio.app` remains available, but its process was stopped for the authorized switch |

Both final build artifacts and the installed app passed `codesign --verify --deep --strict`. The installed executable SHA-256 matches the verified Debug build (`46af5c4d31a817d24258d0b7eec45cb8b9e98e62ec59682126ef024901855618`); its running process was verified at the `/Applications` path. They use ad-hoc signing, not distribution signing. Tests launched temporary XCTest hosts, not attended radio playback. Unrelated untracked `Tools/StreamLab/.pi/` was left untouched. No shared contract, backend, station record, or frozen core policy changed.

## Implemented behavior

- Eligible KCRW source identities resolve to `https://streams.kcrw.com/e24_aac/playlist.m3u8` in ordinary playback. Existing name/host/path/scheme/query/credential restrictions remain exact. Saved source URLs stay unchanged. `+160s` and clock/history policies stay frozen.
- Ordinary alignment owns a same-item session without Debug Apply, an experiment recorder, or capture arming. Debug **Off** means ordinary alignment; Observe is the legacy-publication comparison override; Apply is the explicit aligned experiment path. Capture remains a separate explicit Debug action.
- Player samples, not feed receipt, publish the selected occurrence. Item/source/generation guards reject old callbacks. Pause tears down; resume joins a new item and valid clock. Active polling survives browsing other source pills.
- Menubar title, history selection, Now Playing, and LIVE lyric detail consume the selected playback state. Missing clock/history presents an ordinary alignment-unavailable reason instead of falsely aligned feed-top output.
- LIVE detail uses the view model's selected lyric resource/index rather than a second lookup. Historical detail remains independent and unhighlighted. Fuzzy, missing, invalid, or untimed resources cannot drive aligned highlighting. Exact text/catalog identity remains uncertain evidence of the recording heard.
- Lyric correction stays in memory, separate from `+160s` and saved station offsets, and resets for changed occurrence/revision/resource/generation. Equal-timestamp lines now choose one index for both text and highlight.
- Off and Release cannot arm a recorder, even through direct session/recorder calls. Normal playback and reconnect create no trace/sidecar files. Explicit Debug capture retains existing schema, owner-only exports, and privacy guarantees.
- Unsupported KCRW paths, other stations, podcasts, and remote JSON contract tests retain legacy behavior.

## Changed menubar paths

Paths are relative to `pocket-radio-menubar/`.

| Path | Change |
|---|---|
| `PocketRadio/Services/StreamExperimentConfiguration.swift` | Ordinary alignment predicate/resolution plus injected playback/feed/lyrics/storage/publication boundaries |
| `PocketRadio/Services/RadioPlaybackSession.swift` | Recorder factory seam; Debug-only non-Off capture/marker gate; unchanged selection core |
| `PocketRadio/Services/StreamExperimentRecorder.swift` | Off/Release rejection before file creation; existing recorder format preserved |
| `PocketRadio/Services/LyricsService.swift` | Catalog resource ID, aligned timing validity, shared last-eligible-line index |
| `PocketRadio/View Models/PlayerViewModel.swift` | Ordinary sessions/publication, lifecycle guards, shared LIVE lyric selection, unavailable state, offset isolation, offline test injection |
| `PocketRadio/ContentView.swift` | Normal unavailable reason, selected-history marker, shared LIVE detail result/highlight, cancellation-safe historical fetch |
| `PocketRadio/StreamExperimentView.swift` | Off/Observe/Apply and explicit capture descriptions |
| `PocketRadioTests/StreamSessionIntegrationTests.swift` | Updated endpoint behavior and twelve added VM/session/resource regression tests |
| `PocketRadioTests/RemoteCommandFixtureTests.swift` | Load unchanged shared JSON fixtures from the XCTest bundle |
| `PocketRadio.xcodeproj/project.pbxproj` | Copy six existing `../contracts/remote` fixtures into the test bundle |

The fixture wiring prevents XCTest hosts from opening protected Documents paths at runtime. A transient host stall was sampled in `fixtureData -> Data.init(contentsOf:) -> __open`; bundled full runs subsequently passed. The reviewer compared all six bundled JSON files with shared source contracts; contents were unchanged. Production startup remains unchanged; default XCTest-host startup suppresses automatic authentication, and VM tests inject offline boundaries.

## Review finding and resolution

The independent reviewer left one verified failing test: accepted equal-timestamp lyric lines produced bar text from the last matching line but a highlight index from the first matching timestamp. The lead took production ownership after the reviewer stopped. `LyricsService.currentLineIndex(in:at:)` now selects once, and both the bar text and LIVE highlight use that index.

- Red: `/tmp/m12-review-equal-timestamp-red.log` and `/tmp/m12-review-tests.log` (30 tests, one failure).
- Focused green after the fix: `/tmp/m12-review-fix-green.log` (one test, zero failures).
- Final Debug and Release suites below both include the regression and pass.

Additional independently added tests cover pending/loaded lyrics while browsing supported and unsupported history pills, actual poller ownership and canceled receipt, same-title revision/later-occurrence callbacks, and stall/discontinuity/wrong-item recovery. Original implementation behaviors were developed sequentially with red/green logs at `/tmp/m12-b1-red.log` through `/tmp/m12-b6-green.log`.

## Final verification

These results include the final equal-timestamp fix and all reviewer tests.

| Check | Result | Log |
|---|---|---|
| Debug app unit tests | **30 passed, zero failures**: 22 integration, six remote fixtures, two template tests | `/tmp/m12-verified-debug-tests.log` |
| Release app unit tests | **26 passed, zero failures**: 18 integration, six remote fixtures, two template tests | `/tmp/m12-verified-release-tests.log` |
| StreamSession core | **23 passed, zero failures** | `/tmp/m12-verified-core.log` |
| StreamLab/Diagnostics | **63 passed, zero failures**: 41 plus 22 package tests | `/tmp/m12-verified-lab.log` |
| Debug app build | **BUILD SUCCEEDED** | `/tmp/m12-verified-Debug-build.log` |
| Release app build | **BUILD SUCCEEDED** | `/tmp/m12-verified-Release-build.log` |
| Deep/strict code-signature checks | Both artifacts passed | Command exit zero |
| `git diff --check` | Menubar and shell passed | Command exit zero |

Commands from the menubar root:

```sh
swift test --package-path Packages/StreamSession
swift test --package-path Tools/StreamLab
xcodebuild test -project PocketRadio.xcodeproj -scheme PocketRadio \
  -destination 'platform=macOS' -parallel-testing-enabled NO \
  -derivedDataPath /tmp/pocketradio-m12-signed \
  -only-testing:PocketRadioTests \
  CODE_SIGNING_ALLOWED=YES CODE_SIGN_IDENTITY=- DEVELOPMENT_TEAM=
```

The Release test command adds `-configuration Release`, uses `/tmp/pocketradio-m12-release`, and sets `ENABLE_TESTABILITY=YES ENABLE_HARDENED_RUNTIME=NO` **for XCTest only**. It skips the four old tests that deliberately create Debug captures:

- `testRecorderDoesNotOverwriteExistingSidecarOrClaimCompleteExport`
- `testApplyRecorderLabelsModeWithoutChangingObservedCaptureDefaults`
- `testItemTeardownExportsCompleteApplyCapture`
- `testSameItemRecorderExportsReplayableTraceAndDecisionSidecar`

The Release capture-isolation test still runs and verifies direct capture refusal. Full commands and result bundle paths are in each log. The final Debug/Release build commands use `xcodebuild build`, configuration-specific builds, `/tmp/pocketradio-m12-build-verification`, and the same ad-hoc signing arguments, **without** the XCTest-only testability/hardened-runtime overrides.

Existing Swift concurrency warnings remain in the legacy lyric timer and app delegate. No broad concurrency cleanup was attempted. The old development-certificate test route hung at host launch; serial ad-hoc signing passed. No system security or project production-signing settings were changed.

## Remaining uncertainty and user checkpoint

No UI suite or attended M12 normal-use playback has run. Tests exercise VM LIVE/history transitions and callback/resource boundaries, not actual SwiftUI `.task` execution/rendering or real speaker timing. Historical detail still fetches through `LyricsService.shared`. Ordinary eligible startup also retains the legacy browsing poller alongside the aligned session; its publication is guarded away. Neither observation was a demonstrated failing acceptance behavior.

The user has authorized the build switch, and the installed app is running. Remaining user checks:

1. Play an eligible KCRW favorite without opening Debug controls. Confirm title and live lyrics follow the audio; no capture should start.
2. Pause/resume and confirm reconnect joins current playback rather than retaining an old item/lyric anchor.
3. Open LIVE lyrics, browse another station's history, and return. Check matching bar/detail highlighting and unchanged playback.
4. Switch to another station or podcast and confirm existing behavior.

This is a short qualitative ordinary-use checkpoint, not a new long-capture protocol. M11-B qualitative evidence is retained; measured ±5s/±2s accuracy and recording identity remain unverified. Acceptance, commit/merge/push, and any rollout beyond the approved eligible menubar scope require separate decisions.

## Agent execution

The writer and independent reviewer both verified `openai-codex/gpt-6.1-sol`, OAuth ready. The writer owned production first; reviewer owned tests only; lead fixed the reported defect after transfer. No other publisher/model was used. Reported delegated usage and forecast overruns are recorded in the [execution plan](milestone_12_subagent_plan.md); subscription impact is not evaluated at the user's request.
