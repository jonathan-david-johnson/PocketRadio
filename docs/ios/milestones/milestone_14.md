# iOS M14 — KCRW playback alignment (port from menubar)

**Status**: IN PROGRESS — updated 2026-10-29. 14.1–14.3 are closed (`archive/ios-m14.1`, `archive/ios-m14.2`, `archive/ios-m14.3`; ADRs 0004, 0005 and 0008). 14.3 passed its device checkpoint on 2026-10-10 and merged to `trunk` at `e550b26b9`. Continue the later timing work on `experiment/unified-skew` at `eba2c9977`, as approved by the user on 2026-10-21. The navigation-lifetime fix is committed (`eba2c9977`, approved 2026-10-23) and passed its manual check. The 14.4 preflight passed (238 focused tests; 128 CarPlay output tests with existing expected failures), but manual Bluetooth and speaker runs exposed stream stalls ([bug 15](../bugs/bug_15.md)). The cause is KCRW's two HLS servers behind rotating DNS; a Debug fix that pins each session to its server is committed at `56a7ecf21` ([ADR 0011](../adr/0011-kcrw-hls-pins-each-session-to-its-server.md)) and played about 21 minutes on the phone without a stall. Route acceptance can resume on that build; Bluetooth, wired CarPlay and background validation remain. The user selected the pin-and-backstop path for Release after those checks pass on 2026-10-29. It remains Debug-only until a separate Release change is tested and approved. M14 remains open.
**Depends on**: Menubar M11-A/M11-B/M12, accepted. `Modules/Package.swift` still uses `../../pocket-radio-menubar/Packages/StreamSession`; dependency checkout verified at menubar `8f71eb484` on 2026-10-21, including the additive `updateSelectionPolicy` API. The iOS `trunk` checkout is at `b58d5a168` and includes the CarPlay harness and output suite.
**Required by**: The later stream-presentation work in the [stream-monitoring review](../architecture/reviews/stream-monitoring-review-2026-09-16.md) §6 steps 2 and 5.
**Related**: [CarPlay output test boundary](../adr/0003-carplay-output-test-boundary.md) and the [maintained harness](../../../pocket-radio-ios/PocketCastsTests/Tests/CarPlayOutput/Harness/README.md). The accepted order is to close M13 first, then use its output suite for 14.2 and 14.4.

## Where the work happens

| | |
|---|---|
| Plan and reports | Shell `main`: this file, `docs/ios/experiments/`, `docs/ios/bugs/` |
| Code | iOS repo, branch `experiment/unified-skew`, HEAD `56a7ecf21` (session pinning, on top of `eba2c99772715193ad3faa189960e3a2ccea649f`). This is the approved continuation; `feature/kcrw-alignment` is not a current local branch. The lifetime fix (`eba2c9977`) is on top of `4a51372d3` and touches only `podcasts/Radio/StationDetailViewController.swift` and `PocketCastsTests/Tests/Radio/StationDetailLyricsTests.swift`. |
| Worktree | `/Users/jdj/code/PocketRadio/pocket-radio-ios-alignment/`, sibling of the main iOS checkout. `git worktree repair` from `pocket-radio-ios/` corrected the old `/Users/jdj/Documents/code/PocketRadio/` registration on 2026-10-21. HEAD and source files were preserved; the worktree was clean after repair and is no longer prunable. No branch was created or renamed. |
| Shell changes | Docs only, unless D1 moves the shared core into the shell |

**Goal:** On iPhone, an eligible KCRW Eclectic24 station shows the song that is audible, not the feed's newest row. Lock screen, Bluetooth, CarPlay, the full and mini players, station detail, and live lyrics all follow the player's own clock. The port reuses the menubar's selection core unchanged and adds iOS adapters. Other stations and podcasts keep today's behavior.

**User checkpoint:** Play KCRW on the phone with the screen locked. The title and artwork on the lock screen change when you hear the song change. Open live lyrics mid-song and across a transition. The highlighted line follows the audio, and a pause and resume keeps it right. Repeat on Bluetooth and CarPlay.

**Current branch differs from the original port:** [ADR 0008](../adr/0008-kcrw-lyrics-follow-the-media-clock-in-apply.md) records accepted 14.3 behavior. [ADR 0010](../adr/0010-timing-is-one-skew-per-station-healed-with-shazamkit.md) supersedes its in-memory lyric correction and the fixed `+160 s` policy: KCRW now uses one saved skew per stream, seeded at 160 s, shared by titles, artwork and lyrics. Alignment is Debug-only **Off / On**, not Off / Observe / Apply. The branch also contains KEXP profiles, per-song offsets and an optional automatic anchor loop; those experiments are not part of KCRW's 14.4 acceptance. The original decisions below remain historical context, not instructions to restore the older controls.

## What carries over, and what does not

The menubar work separates cleanly into a core and its adapters.

| Piece | iOS status |
|---|---|
| `Packages/StreamSession` (`SessionState`, `MediaClock`, `OccurrenceHistory`, `OccurrenceSelector`) | Reused through the local package dependency. Foundation-only, declares `.iOS(.v16)`; the current core also supports selection-policy updates. |
| Exact endpoint `https://streams.kcrw.com/e24_aac/playlist.m3u8`, initial `+160 s` offset, history/clock limits | Ported in `KCRWAlignmentConfiguration`. The endpoint and limits remain; 160 s is now a seed, replaced by the device's saved stream skew after a heal or nudge (ADR 0010). |
| Eligibility predicate (`StreamExperimentConfiguration.ineligibilityReason`) | Ported in 14.1 (`KCRWAlignmentConfiguration`). |
| `RadioPlaybackSession` (item generation, paired samples, 30 s feed poller, stale-callback guards) | Ported in 14.1 without the recorder, Observe only. 14.2 adds publication. |
| Lyric clock, shared line index, correction isolated from legacy lyric offsets | Delivered in 14.3 (ADR 0008). The later unified-skew work changes aligned nudges to move the stream skew; legacy saved lyric offsets remain for stations that are not aligned (ADR 0010). |
| `StreamDiagnostics` recorder, replay and feed decoder (`Tools/StreamLab`) | Not a dependency. iOS has its own KCRW decoder and `[align]` `FileLog` lines (D4). |
| Menubar `PlayerViewModel` wiring | Do not port. iOS has different owners. |

The iOS owners that the port touches:

- **Item creation:** `PlaybackItem.createPlayerItem` calls `EpisodeManager.urlForEpisode`. Radio stations reach it through a shim whose `downloadUrl` is the stream URL. This is the endpoint-override seam, and it leaves the saved station URL alone. Radio HLS is not the podcast `hasHLSStream` path, so `isStreamingHLS` stays false and the podcast buffer settings do not apply. Confirm that, because [bug 3](../bugs/bug_3.md) says radio must stay at native speed.
- **Player and metadata:** `DefaultPlayer` creates the `AVPlayer` and attaches `RadioMetadataObserver` for radio. The session attaches here too.
- **System Now Playing:** `PlaybackManager` and `NowPlayingHelper` write title, artist, album, and artwork from several paths. These are the "last writer wins" problem in the review.
- **Titles and lyrics:** The aligned session polls independently of station detail. `LyricSyncController` reads its song position; full-screen `LyricsViewController` subscribes to that controller's tick. Only the non-aligned path uses wall time and a separate full-screen timer.
- **Identification:** ACR Identify was removed in favor of timing recalibration ([ADR 0009](../adr/0009-acr-identify-button-removed-for-timing-recalibration.md)). A ShazamKit match measures timing; it does not replace the aligned title writer.

## What iOS must prove first

The menubar numbers came from macOS AVPlayer. Treat each as a hypothesis until a device run confirms it.

1. **`AVPlayerItem.currentDate()` is non-nil on iOS for this HLS endpoint.** Proven in 14.1 ([ADR 0004](../adr/0004-kcrw-playback-clock-on-ios.md)).
2. **Feed-to-program timing transfers.** The original 160 s policy passed the speaker title checkpoint in 14.2 (ADR 0005), but 14.3 exposed lyric lag. The later experiments replaced that constant with a saved skew and ShazamKit calibration (ADR 0010). Validate the current skew-based behavior on each route in 14.4, without treating a successful heal as a measurement of output delay.
3. **Polling survives lock, background, and route changes.** Lock proven in 14.1 for about 30 minutes on Wi-Fi ([ADR 0004](../adr/0004-kcrw-playback-clock-on-ios.md)). Background without lock and route changes remain for 14.4.
4. **HLS gives no ICY titles.** On the aligned endpoint the feed is the only title source. Every ICY or feed-top title path must be off for an eligible station, or it will overwrite the aligned title.
5. **Route latency is separate.** Bluetooth and CarPlay add output delay on top of player time. Measure it separately; do not fold it into the stream skew. ShazamKit hears the phone's own playback before output, not the room (ADR 0010), so its anchor cannot establish the listener's route delay.

## Scope

New iOS code goes in `podcasts/Main/Alignment/`, a synchronized Xcode group ([ADR 0004](../adr/0004-kcrw-playback-clock-on-ios.md)). Edits to `DefaultPlayer`, `PlaybackManager`, `NowPlayingHelper`, and `EpisodeManager` stay small. This is a fork of Automattic's repo, and small diffs keep upstream merges cheap.

- **Shared core wiring.** Done in 14.1 through `Modules/Package.swift` (D1 kept on `trunk`; see ADR 0004 for the version-pin risk).
- **Eligibility and endpoint.** `KCRWAlignmentConfiguration` holds KCRW eligibility, endpoint and seed policy. `AlignmentProfiles` selects the current experiment's profile when alignment is On. Eligible KCRW playback uses the measured HLS endpoint; saved station URLs, favorites, Supabase rows and `curated_stations.json` stay unchanged.
- **Playback session.** Done in 14.1 for Observe. `DefaultPlayer` creates it with the item for an eligible station and stops it at item teardown. Stopping tears the item down and a restart joins a fresh clock; a plain pause keeps the session (corrected 2026-10-09, see ADR 0004). Sample from a periodic time observer, not from a UI timer.
- **Feed client.** Delivered in 14.1; the current client is `AlignmentFeedClient`, with `KCRWFeedDecoder` preserving ids and break rows. The poller is one in-flight request, owned by the session, and independent of any screen.
- **Single publication point.** One adapter owns the radio writes to `MPNowPlayingInfoCenter`. For an eligible station it writes from the selected occurrence only. It never borrows album or artwork from the feed-top row. This also fixes the artwork rebuild bug for this station. KCRW is the acceptance target here; the current branch also reuses the adapter for the separate KEXP experiment.
- **UI consumers.** Full player, mini player, and station detail read the session snapshot. History rows stay in feed order and highlight the selected occurrence, not row zero.
- **Lyrics.** Delivered in 14.3: position is song seconds from the session clock; both screens use the same line index and one tick. Pushing full-screen lyrics keeps the controller running. On the current branch a nudge moves KCRW's saved stream skew, not a per-occurrence lyric offset; aligned lyrics never read or write legacy `lyric_offsets`.
- **Debug mode.** Alignment is Off / On, default Off and forced Off in Release. The separate Auto anchor control is Off / Measure / Apply. For the 14.4 baseline leave Auto anchor Off. After Bluetooth, wired CarPlay, and locked/background checks pass, implement the selected production path: enable only KCRW session pinning and its replacement backstop in Release. That change needs its own test, manual validation, and approval to merge; the decision does not enable the current Debug code. Existing ShazamKit calibration sends a signature to Apple; it does not use the microphone or record audio files. Do not run the separate microphone diagnostic as part of this checkpoint.

## Sequence

| Step | Delivers | Gate |
|---|---|---|
| **14.1 Feasibility** — closed (`archive/ios-m14.1`) | Core wired in. Eligibility, endpoint override, session, and an Observe-only readout on device. Nothing is published. | Passed 2026-10-09; see [ADR 0004](../adr/0004-kcrw-playback-clock-on-ios.md). |
| **14.2 Apply: titles and Now Playing** — closed (`archive/ios-m14.2`, ADR 0005) | Single publication adapter. Full player, mini player, detail, and lock screen follow the selected occurrence. ICY, ACR, and feed-top title paths are off for the station. | Listener confirms title changes match audio on the speaker and the lock screen. Pause and resume work. |
| **14.3 Lyrics on the media clock** — closed (`archive/ios-m14.3`, ADR 0008) | Shared lyric index. Full-screen lyrics uses the session clock. Offset-reset bug fixed. | Eight device checks accepted 2026-10-10; merged at `e550b26b9`. Current-branch regression results are below. |
| **14.4 Routes and background** — started; stall fix in place | Automated preflight passed. Manual runs reproduced audio stalls (bug 15); session pinning (ADR 0011) fixed them in phone runs on speaker. Bluetooth, wired CarPlay and background checks remain. | Listener confirms titles and phone lyrics on each route. Route delay stays separate from skew. |

Each step ends at a user checkpoint. Per `pocket-radio-ios/AGENTS.md`, nothing is committed until the user has tested it and approved. Acceptance is qualitative, as in M11-B and M12. Formal ±5 s title and ±2 s lyric targets stay unverified unless the user asks for them.

## Current-branch verification — 2026-10-21

Reviewed `SongPositionEstimator`, `AlignedNowPlayingState`, `AlignedNowPlayingPublisher`, `AlignedConsumers`, `AlignedLyricsNavigation`, `LyricLineIndex`, `LyricSyncController`, and both lyric screens at `4a51372d3`.

- Player samples anchor the song position. Playing status permits extrapolation; pause and buffering hold it. The publisher owns the transient-clock hold and clears both title and lyric position when it expires.
- Station detail loads the selected occurrence, not the feed top. Full-screen lyrics subscribes to the same tick and line-index rule, with no aligned timer of its own. A stale occurrence has no position and cannot nudge the new song.
- The navigation policy preserves the controller while full-screen lyrics is pushed. KCRW nudges now move its saved stream skew (ADR 0010); they do not restore the old per-occurrence correction or touch legacy lyric offsets.

The focused run used Xcode 27.1, scheme **Pocket Casts Staging**, `StagingDebug`, simulator `F0042A02-0973-4694-B267-49A1CC21FE19`, and `-parallel-testing-enabled NO`. Selected classes: `SongPositionEstimatorTests`, `LyricLineIndexTests`, `AlignedLyricsNavigationTests`, `AlignedConsumersTests`, `AlignedNowPlayingTests`, `RadioPlaybackSessionTests`, `LyricsServiceTests`, `LyricSyncControllerWallClockTests`, `LyricSyncControllerApplyTests`, `LyricSyncControllerApplyStateTests`, `LyricSyncControllerSharedClockTests`, `LyricsViewControllerTests`, and `StationDetailLyricsTests`.

| Run | Result |
|---|---|
| Initial build/test attempt | No tests ran: ignored `BuildTools/.build` artifact metadata still pointed to the old checkout location. Preserved the entire cache at `/tmp/pocketradio-m14-verification.h9pZ6B/BuildTools.build-before-relocation`; the retry regenerated it at the current path. |
| Focused selection | **236 passed, 1 failed** out of 237; no skips. Results: `/tmp/pocketradio-m14-verification-retry.jLABc4/results.xcresult`. |
| Failing test alone, without rebuilding | **Failed again**. Results: `/tmp/pocketradio-m14-navigation-reruns.E75Vwp/single.xcresult`. |
| Entire station-detail lyric class, without rebuilding | **14 passed, 1 failed**. Results: `/tmp/pocketradio-m14-navigation-reruns.E75Vwp/class.xcresult`. |

**Failure reproduced on 2026-10-21:** `StationDetailLyricsTests.testStationDetailDeallocationStopsTheClock`, assertion then at `PocketCastsTests/Tests/Radio/StationDetailLyricsTests.swift:270`. The fake tick scheduler remained running after the test released its navigation container and yielded. This reproduced outside the larger selection. Those runs did **not** establish a production timer leak: the test did not first prove that UIKit released the controller. Those verification runs changed no source or test assertions.

### Lifetime follow-up — 2026-10-22

**Cause confirmed:** Weak references showed the navigation container was released but station detail was still alive. Temporary logging showed its favorites request was still pending. `loadFavoriteState` promoted `weak self` to a strong reference before awaiting the real favorites lookup, retaining the controller and its lyric timer until the request completed. The old test therefore depended on ambient account/network state. Its attempt to open full-screen lyrics was also a no-op: no tracklist row was seeded.

**Fix (committed 2026-10-23 as `eba2c9977`):** `StationDetailViewController` captures the station id and lookup without retaining the controller across the await, then updates the UI weakly if still live. Deinitialization cancels the favorites task. A defaulted `FavoriteLookup` dependency lets the lyric tests supply immediate or suspended results without reading the real account or favorites service. Temporary diagnostic logging was removed.

**Stronger tests:** The original deallocation test now seeds the selected track, proves full-screen lyrics actually opened, and asserts that both navigation and detail weak references become nil before checking timer cleanup. A new suspended-lookup regression proves controller release, lyric shutdown and task cancellation before allowing the lookup to return. The original timer assertion remains.

| Run | Result |
|---|---|
| Suspended lookup before the production fix | New regression failed: controller retained, timer running and occurrence still set. The isolated, immediate-lookup/full-screen case passed. Evidence: `/tmp/pocketradio-m14-favorites-red.pwZzj5/results.xcresult`. |
| Entire station-detail lyric class after the fix | **16 passed, 0 failed**. Evidence: `/tmp/pocketradio-m14-favorites-green.3iZak9/results.xcresult`. |
| Original focused selection plus the new regression | **238 passed, 0 failed, no skips**, on the same pinned simulator, scheme and configuration. Evidence: `/tmp/pocketradio-m14-focused-fixed.lZ0ONC/results.xcresult`. |

`make format` and `git diff --check` completed. Formatter-only edits outside the two patch files were excluded. No branch change was made while the 238-test run was recorded.

**Part A manual check: passed 2026-10-23** on Jonathan iPhone, StagingDebug build, alignment On (build `4a51372d3` plus the uncommitted lifetime fix, installed over `localNetwork` at the user's request). The favorite heart loads and toggles. Full-screen lyrics open and go back. Five quick repeats of open and back worked. Reopening shows the current song. The user approved the iOS commit on 2026-10-23; it is `eba2c9977`, not pushed. The wider 14.4 device checkpoint and CarPlay regression preflight remain pending.

## 14.4 validation — Bluetooth, CarPlay and background

**State:** Manual checks started 2026-10-27 and stopped for [bug 15: KCRW HLS stalls on Bluetooth and speaker](../bugs/bug_15.md). The stall fix is committed at `56a7ecf21` (below). Resume the matrix on that build, starting with Bluetooth.

### Results — 2026-10-27

| Check | Result |
|---|---|
| Focused selection | **238 passed, zero failures**, rerun at `eba2c9977` on the dedicated signed-out **PocketRadio CarPlay Tests** simulator. |
| `make test_carplay` | **128 tests, zero unexpected failures** on that simulator, with the Mac kept awake. Nine existing known-failure scenario checks reproduced under their strict expected-failure markers. This is output regression evidence, not physical CarPlay certification. |
| Initial speaker baseline | User reported title, artwork and lyrics matching within a couple of seconds at skew **155.6 s**. Only a short qualitative check; the later sustained speaker run stalled. |
| IONIQ 5 Bluetooth, USB disconnected | “Moving to L.A.” appeared about **20 s late**; the next “Mama…” transition looked right, then audio remained silent for over a minute. Control Center showed Pause bars and IONIQ 5. Device logs show buffer starvation and terminal playback failure. **Not passed.** |
| Speaker control, same skew | User reported a dropout around **18:21** and confirmed automatic audible recovery. Device logs show an empty buffer, recovery-time media/program-date rewind of about **66 s**, and later discontinuities. Audible replay of old audio was not confirmed. **Not passed.** |
| Wired IONIQ 5 CarPlay; locked/background checks | **Not run** as acceptance checks. The user identified the same car and a wired CarPlay connection. |

Alignment stayed **On**, Auto anchor **Off**, and skew **155.6 s** for the manual comparisons. Do not tune that skew to hide a stall or infer route delay from the late title. The app first observed the late song's feed row at estimated song position 23.4 s; provider availability versus polling phase remains unresolved.

The speaker reproduction means the audio failure is not limited to Bluetooth. The existing no-seek recovery branch was selected, so do not assume the earlier saved-position seek bug has simply returned. Bug 15 retains the event times, uncertainties, raw-log locations and proposed diagnostics. The error after the user's later speaker pause is not counted as a second active-playback dropout.

Preflight logs and focused result bundle: `/tmp/pocketradio-m14-4-preflight.QbOw0I/`; the CarPlay result-bundle path is printed in `carplay.log`. Raw device logs were copied over wired USB and remain local, not committed. No playback policy, timing value or app code was changed. Next recommended action: prepare narrowly scoped Debug media-access/error and seek diagnostics, then obtain approval for a diagnostic install and a single speaker control run before resuming route acceptance.

### Stall fix — 2026-10-28 and 2026-10-29

The cause and the measurements are in [ADR 0011](../adr/0011-kcrw-hls-pins-each-session-to-its-server.md). `streams.kcrw.com` rotates in DNS between two servers, a listening session lives on one, and AVPlayer's new connections could reach the other, which answers segments with `404`. The fix rewrites the master's variant URL to the session's own server, with an item replacement as a backstop. Debug only, KCRW HLS profile only.

| Check | Result |
|---|---|
| Focused tests | **135 passed**: session pinning, the backstop watchdog and its budget, media diagnostics, stall recovery, the playback session, Now Playing and endpoint resolution. |
| Mac AVPlayer, new connection forced on every request, 15 min, 12 DNS changes | Pinned: **0 errors**, buffer full throughout. Unpinned: 54 errors, buffer empty from minute 5. |
| Phone, replacement backstop only (2026-10-28 afternoon) | Four replacements, each about 7 s of silence and about 7 s skipped, no replay. Each new session lost its loader again within 40–90 s. Not a fix on its own. |
| Phone, pinned (2026-10-28 evening, 2026-10-29 morning), speaker | About **21 minutes** across three sessions: Wi-Fi, cellular, a pause and resume, and a live Wi-Fi to cellular switch. **0 errors, 0 stalls, 0 replacements**; buffer 107–122 s after start. The user heard no drops. |

The build was installed over the local network at the user's request. Bluetooth, CarPlay, locked and background playback were not part of these runs.

**Prerequisites and safety**

- Ask the user to connect and unlock Jonathan iPhone before any install or launch. Confirm `Transport Type: wired` with `devicectl`; stop if it reports `localNetwork`. Build/install from the alignment worktree, not the older `trunk` checkout.
- Use Debug alignment **On** (launch argument `-PocketRadio.alignment.mode on`), then start KCRW Eclectic24. Leave **Auto anchor Off**. Record the initial saved skew; do not reset or tune it separately for each output route.
- Ask which Bluetooth output and real CarPlay head unit are available, and whether CarPlay is wired or wireless. Perform CarPlay interactions while parked. Phone lyrics are in scope; publishing lyric text on the head unit is not.
- Before the manual checkpoint, re-run the focused selection on its pinned simulator. Run `make test_carplay` separately on the dedicated, signed-out **PocketRadio CarPlay Tests** simulator, with the laptop awake. That suite covers MP3/ICY publication regressions, not aligned HLS transport or real scene connectivity (ADR 0003).
- Do not run `make test_carplay_device` without separate explicit approval: it replaces playback, clears local Up Next and changes listening stats. Manual route playback is a different check. Leave host Wi-Fi unchanged.

**Manual matrix** — procedure for the remaining checkpoint. Record each row as pending, pass, fail or unavailable; actual results and the current blocker are above.

| Check | Exercise | Evidence to record |
|---|---|---|
| Speaker baseline | Check one transition, phone titles/artwork and synced lyrics. Navigate into full-screen lyrics and back; exercise pause/resume and Stop/restart separately. | Build SHA, session generation, saved skew, audible transition markers, controls used and recovery. Do not confuse the station-detail button's stop behavior with a true pause ([bug 10](../bugs/bug_10.md)). |
| Bluetooth | Observe at least three transitions with the chosen output. Check phone full/mini player, lock-screen metadata and lyric navigation. Switch to speaker and back without a manual skew change. | Output model, connection changes, title/artwork agreement, lyric residual and its direction, clock validity, poll continuity and any session restart. |
| Locked and backgrounded | On speaker and Bluetooth, separately lock the phone and send the app to the background without locking. Leave station detail closed through at least one transition and two 30 s poll intervals in each state; reopen lyrics mid-song. | Session generation, poll/sample timestamps, feed age, title updates while the screen is closed, and whether lyrics recover immediately on return. |
| Real CarPlay | Observe at least three transitions on the head unit; check title, artist, artwork/LIVE and transport controls. Repeat locked and backgrounded, then disconnect/reconnect. Check phone lyrics only while safely parked. | Head-unit and connection type, actual scene connection/disconnection evidence, phone versus head-unit presentation, poll continuity, controls and reconnect recovery. A modeled connection flag or simulator pass is not sufficient. |
| Lifecycle/regression | Stop/restart from the lock screen; switch to a non-aligned station and a podcast, then back to KCRW. Open full-screen lyrics across a change of occurrence. | New generation on restart, no stale callbacks or lyric highlight/nudge for the old occurrence, saved KCRW skew retained, and ordinary playback unchanged. An old full-screen song does not automatically become the next song; return and open the newly selected row. |

Record device/iOS version, code/dependency SHAs, route and connection type, wall-time markers, session generation, skew before/after, and any nudges or heals. Flush `FileLog` before copying the logs; retain `[align]`, `[anchor]`, `[heal]` and any `[track]` evidence with the report. A fresh heal, if needed, is a separately labeled calibration check, not a substitute for route validation.

Record output delay separately from the stream skew, including the measurement method and uncertainty. A lyric mismatch alone mixes route delay, feed stamps and lyric-file timing; call it a residual, not a measured route latency. If output delay cannot be isolated, record **unmeasured** rather than inventing a number or saving it into the skew. Qualitative listener acceptance remains the checkpoint; formal timing bounds are still unverified.

**Completion:** The user reviews each available route's titles, artwork, phone lyrics, lifecycle and background results, with failures and unavailable routes explicit. The selected KCRW pin-and-backstop path then needs a Release configuration change and Release-build validation. Enabling alignment by default, KEXP acceptance and merging the experiment to `trunk` remain separate gates. No iOS commit without manual testing and explicit approval.

## Behaviors to test (red -> green, one at a time)

Tests use the `PocketCastsTests` host. Inject the clock, feed, lyrics, and publication boundaries. Never write real `UserDefaults.standard` keys. The test host is the app.

1. **Eligible source only.** An eligible KCRW radio shim resolves to the measured endpoint. The saved URL is unchanged. Other stations, unsupported KCRW paths, and podcasts resolve as before.
2. **No early publication.** A feed response alone cannot change the published title. Only a player sample can.
3. **Same-item guards.** Late feed, artwork, or lyric callbacks from an old item, station, or occurrence are rejected at the publication boundary.
4. **Lifecycle.** Stop tears the session down and a restart creates a new generation and a new clock; a plain pause keeps the session. Station and podcast switches cancel the poller. A hidden or never-opened detail screen makes no difference.
5. **One writer.** For an eligible station, `nowPlayingInfo` title, artist, album, and artwork come from one occurrence. A full rebuild keeps the selected artwork instead of the logo. ICY titles and ACR results do not reach the system info.
6. **Missing clock or history.** Show an explicit unavailable state and no timed highlights. Do not fall back to a feed-top title while claiming alignment. This is where menubar [bug 2](../../menubar/bugs/bug_2.md) applies: show the message only while this station is the active, playing item.
7. **Lyric clock.** Same line index in every consumer. Equal timestamps pick one line. Positions and callbacks remain occurrence-scoped. On the current branch, KCRW correction is its saved stream skew and survives a new occurrence; aligned lyrics never touch legacy lyric offsets (ADR 0010 supersedes the 14.3 reset rule).
8. **Regression.** Existing radio, CarPlay, tracklist, artwork, and lyrics tests pass. Some current tests require feed-top fallback on ICY mismatch. Change those only for the eligible station.

## Out of scope

- The 14.4 checkpoint does not expand to other stations, KEXP, MP3 or direct-AAC calibration. The existing KEXP experiment stays on the branch; this scope does not authorize deleting or reverting it.
- Rewriting saved station URLs, favorites, curated data, or Supabase rows. Deleting legacy lyric offsets.
- Removing the `+ / −` lyric controls. Hide them only after multi-route validation, per the review.
- Buffered pause, new continuous timing telemetry, app audio recording and new uploads. The existing optional ShazamKit signature flow and Debug anchor loop are separate experiments, not requirements for 14.4.
- Replacing the whole artwork pipeline. Only the single-writer rule for the eligible station.
- watchOS, tvOS, App Clip. Guard new code with `#if !os(watchOS) && !APPCLIP && !os(tvOS)`, as `DefaultPlayer` already does for the radio observer.

## Docs impact

Each sub-milestone has its own Docs impact section. This one covers what spans 14.2 to 14.4, or lands when M14 closes.

- **Docs this changes or makes stale:**
  - A shared KCRW alignment ADR for both platforms: the eligibility rule, the endpoint, the seed and calibrated skew policy, single-writer publication, and route delay kept separate. Write it when M14 closes, after iOS has tested the policy. [ADR 0004](../adr/0004-kcrw-playback-clock-on-ios.md) narrows to the iOS clock and package-pin details, or a newer ADR supersedes it.
  - The menubar M10–M12 bundle closes with M14 and feeds that ADR. The bundle is milestones 10, 11, 11a, 11b and 12, their handoffs and subagent plan, and the `docs/menubar/experiments/` reports. Traces that `Tools/StreamLab` replays move to the menubar repo; they aren't deleted. Until then, the cleanup leaves this bundle alone, because this port reads it.
  - The "KCRW alignment" section of `docs/ios/README.md` still describes Off / Observe / Apply and the fixed offset; update it to the accepted skew-based behavior when reconciling the experiment for merge. Do not describe Debug On as shipped Release alignment.
  - The `docs/menubar/README.md` roadmap rows for M10–M12 change to archive tags.
  - The StreamSession and alignment rows in `docs/test-architecture.html`.
  - The coverage map in the CarPlay harness README, if 14.2 or 14.4 adds aligned scenarios.
  - Code comments in `podcasts/Main/Alignment/` cite ADRs, never this file. The pre-commit hook enforces that.
- **Questions this must settle:**
  - The remaining items in "What iOS must prove first":
    - the offset by ear (14.2)
    - every ICY, ACR and feed-top title path off for the station (14.2)
    - polling in the background without lock, and across route changes (14.4)
    - delay measured per route (14.4)
  - Whether the StreamSession path dependency (D1) stays or moves to the shell, now that two platforms ship it.
  - Whether the single-writer adapter should serve every station (D3).
  - Whether the iOS offset differs enough to port the JSONL recorder (D4).

## Decisions (made 2026-10-04)

**D1 path dependency on the menubar package; D2 finish M13 first; D3 leave non-KCRW as is; D4 `FileLog` only; D5 defer menubar bugs 2 and 3.** Detail below keeps the options considered. Consequences: M14.1 starts after M13 closes, so M13.2 is available for 14.2 and 14.4. The menubar bugs stay open and are not blockers; iOS still follows behavior 6.

| # | Decision | Options | Recommendation |
|---|---|---|---|
| D1 | Where the shared core lives | (a) Path dependency on `../pocket-radio-menubar/Packages/StreamSession`. (b) Move it to a shared location in the shell. (c) Copy it into iOS. **(a)**, kept on `trunk` 2026-10-09 ([ADR 0004](../adr/0004-kcrw-playback-clock-on-ios.md)). It needs no move, and a fix lands in one place. A path outside the iOS repo is awkward for a fork, and a move to a shared location is easy then. Avoid (c): the copies will drift. |
| D2 | Order relative to M13 | (a) Start M14.1 in parallel. (b) Finish M13.1 and M13.2 first. | **(b), accepted 2026-10-04.** Close M13 first so the output suite is available for 14.2 and 14.4. |
| D3 | Does the iOS player stay on the feed-driven design for non-KCRW stations? | Leave as is, or apply the single-writer adapter to all stations later. | Leave as is now. Treat the adapter as ready for reuse. |
| D4 | Trace and replay on iOS | (a) `FileLog` lines only. (b) Port the bounded JSONL recorder and replay. | **(a).** M11-B and M12 were accepted on listener reports, and the offset is a feed-to-stream property. Do (b) only if 14.1 shows the iOS offset differs. |
| D5 | Carry the menubar bugs 2 and 3 into the port | Fix on menubar first, or design the iOS behavior around them. | Design iOS around bug 2 (behavior 6). Bug 3 is menubar UI and does not apply. Fix both on menubar separately. |
