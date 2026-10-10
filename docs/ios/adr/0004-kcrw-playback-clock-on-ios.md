# KCRW alignment on iOS uses the player's program-date clock, monitored per item

**Decision:** Accepted 2026-10-09. On iPhone, KCRW Eclectic24 alignment reads `AVPlayerItem.currentDate()` from the measured HLS endpoint and runs the shared `StreamSession` selector in a per-item session that owns its own sampler and feed poller. Through M14.1 the session is Debug Observe only and publishes nothing.

## What the device showed

Measured on "Jonathan iPhone" (iPhone 15, iOS 26.6.2), StagingDebug, Wi-Fi, screen on and then locked. Evidence: `archive/ios-m14.1:docs/ios/experiments/2026-10-09_kcrw-clock-feasibility.md` and its traces.

| Question | Result |
|---|---|
| Does `currentDate()` work on iOS for `https://streams.kcrw.com/e24_aac/playlist.m3u8`? | Yes. Non-nil on the first playing sample, about 6.5 s after the item was created, and on every later playing sample (2,139 of 2,139 in a 35.7-minute run). Program date stepped with media time within 0.004 s. It ran a constant 5.0 s behind the phone's wall clock. |
| Does monitoring keep running with the screen locked? | Yes. A `Task`-sleep poller and a 1 s periodic time observer ran continuously for 35.7 minutes, about 30 of them locked (lock timing is from the user's report; the log has no lifecycle lines). 72 poll attempts, 0 failures, longest poll gap 30.4 s, longest sample gap 1.1 s. |
| Does radio stay at native speed? | Yes. Rate 1.00 on every sample; media-per-wall ratio 1.000 in every 5-minute window. A podcast set to 1.5× kept its speed afterwards. |
| Does the `+160 s` feed-to-program offset carry over? | Not formally tested. The user heard the selected song match the audio and change at the right time. M14.2 checks it by ear. |

## Design choices

| Choice | Reason | Alternatives not selected |
|---|---|---|
| **Shared core by local path.** `Modules/Package.swift` adds `../../pocket-radio-menubar/Packages/StreamSession` to `XcodeTarget_podcasts`. Merged to `trunk` 2026-10-09 (`abc1b5063`). | One copy of the core; `project.pbxproj` stays unchanged; the shell's `make checkout` already places the menubar repo beside the iOS repo; no CI builds `trunk`. | **Copy into iOS:** copies drift. **Move to the shell now:** no second consumer needs it yet. **Edit `project.pbxproj` for a package reference:** churns a file that conflicts easily. |
| **Override the endpoint only while Debug Observe is on.** `PlaybackItem.createPlayerItem` uses the measured endpoint for an eligible station; `EpisodeManager.urlForEpisode` is unchanged, so Cast and chapters are untouched. Saved station URLs are never rewritten. | The HLS endpoint carries no ICY titles. Always overriding would degrade KCRW titles before M14.2 can replace them. | **Always override eligible stations:** loses lock-screen titles until publication is ported. |
| **Eligibility** is the menubar rule: name contains "kcrw"; `http`/`https`; host `streams.kcrw.com`; path `/e24_mp3`, `/e24_aac` or `/e24_aac/playlist.m3u8`; no query, fragment or credentials. The station is found by cast or by `RadioStationRegistry` uuid, because the player can receive a SQLite `Episode` shim. | Exact identity, not a name match. | Matching on name alone. |
| **Feed decoding is iOS code**, producing `StreamSession.OccurrenceInput` and keeping row ids and `[BREAK]` rows. | The menubar's decoder lives in `Tools/StreamLab` (`StreamDiagnostics`) with the recorder and privacy helpers. The legacy `RadioTracklistService.parseKCRW` drops ids and breaks, which the core needs. | Depending on `StreamDiagnostics`; reusing `RadioTracklistService`. |
| **Session owned by `DefaultPlayer`, one per `AVPlayerItem`.** Created only on the main thread; stopped at the top of `loadEpisode` and at the start of `endPlayback`, before its pause. Late samples and feed results from another item or a stopped session are dropped. A feed receipt never changes the selection; only a player sample can. | Same-item guarantees from the menubar. Stopping before the pause keeps teardown from looking like the listener stopping audio. | Sampling from a UI timer; polling from a screen (today's `StationDetailViewController`). |
| **New code under `podcasts/Main/Alignment/`**, tests under `PocketCastsTests/Tests/Alignment/`. | Both are synchronized Xcode groups, so new files need no `project.pbxproj` edit. | `podcasts/Radio/`, which needs a pbxproj edit per file. |
| **The Observe switch lives in `UserDefaults.standard`**, Debug only, and is an emptied private suite under XCTest. | A launch argument (`-PocketRadio.alignment.observe YES`) can set it; the test host is the app, so a switch left on in the simulator must not reach host tests. | A suite-backed store, which launch arguments do not reach. |
| **Pass/fail for a locked run is computed in the app** from the raw samples and poll attempts (`AlignmentMonitorSummary.evaluateLockedRun`) and logged as `[align] verdict … kind=checkpoint|at-pause|stop`. Criteria: no sample gap over 5 s after the first playing sample unless a logged stall covers it; no gap over 45 s between poll attempts; at least 58 attempts in 30 minutes, failures counted but reported separately; a clock-invalid run excused only within 5 s after a stall and no longer than 5 s; rate exactly 1.0; each judged 5-minute window within ±1 %. The `at-pause` verdict decides a run, because stopping radio tears the session down. A plain pause (lock screen or Control Center) keeps the session and its clock. | One-second `probe` lines let the verdict be recomputed from the raw log. Counting attempts, not successes, measures whether iOS ran the code, not the network. | A smoke check ("still alive at unlock"), which would miss throttling. |

## Consequences

- **No version pin.** A `trunk` commit does not record which `StreamSession` commit it built against. A menubar change to the package can change the iOS build or behavior without an iOS commit. Move the package to a shared location in the shell when it starts changing often or a third surface needs it.
- **Fallback if background polling ever fails.** The Debug poll-driver setting can start polls from the 1 s player observer instead of a sleeping `Task`. It was not needed.
- **Release is unchanged.** `ObserveSwitchStore` always returns Off in Release, and the readout (Settings > Developer > KCRW alignment (Observe)) compiles only in Debug.
- **Known limits carried into publication work:**
  - `isStreamingHLS` stays false for radio, so a stall on the HLS endpoint recovers through `play()` and `jumpToStartingPosition()` rather than the HLS path. Watch for a media-time jump after a stall.
  - Checkpoint summaries count an in-flight poll as a failure until it returns. Cosmetic.
  - The session does not log app lifecycle or device lock, so lock periods rely on the listener's report.
  - The `page_size=10` (iOS) versus `page_size=5` (menubar) feed difference was not compared.

## Verification

| Behavior | Covered by |
|---|---|
| Eligibility | `KCRWEligibilityTests` |
| Endpoint override only when Observe is on; saved URL unchanged; podcasts untouched | `KCRWEndpointResolutionTests` |
| Feed decoding keeps ids, breaks and order; size, row and shape limits | `KCRWFeedDecoderTests`, `KCRWFeedClientTests` |
| No early selection; explicit unavailable reason; same-item and generation guards; lifecycle; one request in flight; nothing published | `RadioPlaybackSessionTests` |
| Monitor summary and locked-run verdict | `AlignmentMonitorSummaryTests` |
| Debug switch and readout model | `AlignmentObserveViewModelTests` |
| Default Off is unchanged | Full `PocketCastsTests` (1,080 tests) and the CarPlay output suite (128) pass with Observe off; the user confirmed normal KCRW and other-station titles on the device |
| Clock, locked monitoring and speed on a real phone | Device runs in the evidence above; not automatable |
