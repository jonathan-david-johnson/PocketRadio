# iOS M14.1 — KCRW playback clock feasibility

**Status**: PLANNED — plan prepared 2026-10-08. The plan is not approved yet, and no code exists. D6, D7, and D8 approved 2026-10-08. Implementation may start.
**Depends on**: [M14](milestone_14.md) (D1–D5 decided); iOS M13 closed; menubar `main` core verified on 2026-10-08 (see "Verified starting point").
**Required by**: M14.2 (titles and Now Playing). M14.2 starts only if this milestone's gate passes.

## Where the work happens

| | |
|---|---|
| Plan and reports | Shell `main`: this file; results in `docs/ios/experiments/2026-MM-DD_kcrw-clock-feasibility.md` |
| Code | `pocket-radio-ios`, branch `feature/kcrw-alignment` from `trunk` at `6d8e5a9aa` |
| Worktree | `pocket-radio-ios-alignment/`, sibling of `pocket-radio-ios/`. The main iOS checkout has uncommitted Xcode noise (reordered `project.pbxproj`, `podcasts-Info.plist`, a watch scheme), so do not build there. |
| Worktree extras | Copy these untracked files from the main checkout: `podcasts/Credentials/LocalApiCredentials.swift`, `podcasts/Strings+Generated.swift`, `podcasts/ThemeColor.swift`, `podcasts/ThemeStyle.swift`. Expect a full first build. |
| Shell changes | Docs only |

**Goal:** Learn, on a physical iPhone, whether KCRW's HLS stream gives the player a usable program-date clock, whether that monitoring keeps running with the screen locked, and whether radio stays at native speed. Change nothing the listener sees or hears except the stream endpoint, and only when the Debug Observe mode is on.

**User checkpoint:** With Observe on, play KCRW on "Jonathan iPhone" and lock the screen for 30 minutes. Afterward the log shows a valid clock, an unbroken stream of samples and feed polls, and a playback rate of 1.0 throughout.

## Verified starting point

Checked 2026-10-08 from the shell checkout.

| Check | Result |
|---|---|
| Menubar `main` | `e303f36`: M12 merge `8838df5` plus one docs-only commit. M12's dependency holds. |
| `Packages/StreamSession` | `swift test`: 23 tests pass. Foundation-only; declares `.iOS(.v16)`. |
| Menubar app unit tests | `make menubar-test`: all 22 `StreamSessionIntegrationTests`, 6 `RemoteCommandFixtureTests`, and 2 template tests pass. |
| Menubar UI tests | Did not run. `PocketRadioUITests-Runner` failed with "Timed out while enabling automation mode"; a second, unit-only attempt hung and was killed. This is a macOS UI-automation problem, not a core regression. It does not block this milestone. |
| iOS `trunk` | `6d8e5a9aa`, includes the closed M13 harness. |
| Physical device | `xcrun devicectl list devices` shows "Jonathan iPhone" as **unavailable** (not connected or locked). It must be connected and unlocked before step 3. |
| iOS item seam | `PlaybackItem.createPlayerItem` calls `EpisodeManager.urlForEpisode` and is the only path to the `AVPlayerItem`. |
| Native speed seam | `EpisodeManager.hasHLSStream` returns false for anything but an `Episode` with `hlsUrl`. A `RadioStation` therefore never sets `isStreamingHLS`, and `downloadParallelToStream` returns the plain item (`sizeInBytes = Int64.max` defeats the cache branch). Bug 3's neutral-effects fix is in place. Read from code; the device run confirms it. |

### Corrections to the M14 plan

1. **Feed decoding is not in `StreamSession`.** `FeedEntry` and `StationFeed` live in `Tools/StreamLab` (`StreamDiagnostics`), next to the recorder and privacy helpers. Do not depend on that package. Write a small iOS decoder that produces `StreamSession.OccurrenceInput` directly. It must keep `id` and `[BREAK]` rows, which `RadioTracklistService.parseKCRW` drops. The core needs both.
2. **`RadioPlaybackSession` is app code, not a package.** It lives in the menubar app target and is entangled with `StreamExperimentRecorder`. Port by copy, without the recorder, snapshot recording, and markers. Menubar's feed URL uses `page_size=5`; iOS's curated `tracklistUrl` uses `page_size=10`. Use the iOS curated URL for eligible stations and compare the core's behavior on both in a fixture.
3. **`podcasts/Radio/` is not a synchronized Xcode group.** New files there need `project.pbxproj` edits, which already churn on `trunk`. Adding the `StreamSession` package needs one pbxproj edit anyway. See D8.
4. **The endpoint override changes what the lock screen can show.** The measured HLS endpoint carries no ICY titles (M14 "must prove" item 4), and today's iOS path for KCRW uses ICY. Always overriding would silently degrade KCRW titles in 14.1, which contradicts "nothing is published". See D6.

## Hypotheses (not yet observed)

- **H1.** `AVPlayerItem.currentDate()` is non-nil on iOS within a few seconds of `.playing` for `https://streams.kcrw.com/e24_aac/playlist.m3u8`, as on macOS.
- **H2.** A `Task`-based 30 s poller and a periodic time observer keep running while the screen is locked and audio plays, because the app has the `audio` background mode. This is the least proven part: today's feed polling runs only while the station detail screen is visible, so no background feed poll exists yet. Treat H2 as something E2 must show, not something to assume. Lock screen and CarPlay Now Playing are written by the same background process, so a failure here would also stop them from updating.
- **H3.** Radio runs at rate 1.0, and media time advances at wall-clock speed.

## Scope

All new code is `#if !os(watchOS) && !APPCLIP && !os(tvOS)`. Edits to existing files stay a few lines each.

- **Core dependency (D1).** Add local package `../pocket-radio-menubar/Packages/StreamSession` to the app target only.
- **Eligibility.** New `KCRWAlignmentConfiguration`: port of `StreamExperimentConfiguration` (`ineligibilityReason`, `measuredEndpoint`, selection, history, and clock policies), taking a `RadioStation`'s `title` and `streamUrl`.
- **Endpoint override.** In `PlaybackItem.createPlayerItem`, use the measured endpoint when the episode is an eligible `RadioStation` **and** Observe is on (D6). Leave `EpisodeManager.urlForEpisode` alone so Cast and chapters are untouched. Never rewrite the saved URL.
- **Feed client and decoder.** New iOS feed client with the body, row, and timeout limits from the menubar client, no cookies, no cache. It returns `OccurrenceInput` rows including breaks and ids.
- **Session.** New iOS `RadioPlaybackSession`: one `AVPlayerItem`, a generation id, a same-item guard, a periodic time observer (1 s, main queue) for paired samples, and one in-flight 30 s feed poller owned by the session. `DefaultPlayer` creates it for an eligible station in Observe mode and calls `stop()` wherever it tears down the item. The session has no publishing dependency: it cannot write `MPNowPlayingInfoCenter` or any title.
- **Monitor log (D4).** `FileLog` lines prefixed `[align]`: session start/stop with generation, a sample line every 10 s, every feed poll result, every clock-validity change, every stall or rate change, and a run summary on stop. Log the host and path of the endpoint, never credentials or query strings.
- **Monitor summary.** A pure function over the recorded samples that reports: samples, first-valid-clock delay, longest gap between samples, longest gap between polls, clock-invalid intervals, min/max rate, and media-seconds-per-wall-second per 5-minute window excluding stalls. The readout and the stop-time log line both use it.
- **Observe readout and switch.** A Debug-only panel for the eligible station: Off / Observe switch, plus the live fields (clock state, program date, media time, rate, last poll, feed top, candidate selection, reason). Place it where the diff is smallest (D8). The switch is stored in an injected `UserDefaults(suiteName:)`-backed store, defaulting to Off.

## Order of work inside this milestone

1. Worktree, package wired in, empty build on the simulator.
2. **Early probe, red first.** Eligibility and override tests, then a minimal sample logger only. Run on the simulator for a cheap sanity check, then on the device for two minutes. If `currentDate()` is nil on the device, **stop** and report; nothing else is built. A simulator result does not satisfy the gate.
3. Feed decoder, session, poller, summary, readout.
4. Full unit pass, then the M13.2 CarPlay output suite as a regression check for the default-Off path.

## Behaviors to test (red -> green, one at a time)

Use the `PocketCastsTests` host. Inject the clock, feed, and defaults store. Never touch `UserDefaults.standard`.

1. **Eligibility.** A table of station names and URLs: the three known Eclectic24 variants are eligible; other KCRW streams, other hosts, URLs with credentials, queries, or fragments, and non-KCRW names are not. Each rejection has a stable reason.
2. **Endpoint resolution.** Eligible station with Observe on resolves to the measured endpoint; with Observe off, or ineligible, resolves exactly as before; the saved `streamUrl` is unchanged; a podcast `Episode` is untouched.
3. **Feed decoding.** A KCRW fixture with an id, a `[BREAK]` row, a null-title row, and fractional-second timestamps decodes to ordered `OccurrenceInput` values with the right kinds. A wrong shape, an oversize body, and too many rows are rejected.
4. **No early selection.** A feed response alone yields no selection. Only a paired player sample can.
5. **Clock unavailable is explicit.** A nil `currentDate()` produces a stated reason, never a selection or a feed-top fallback.
6. **Same-item and generation guards.** A sample from another item, and a feed result that returns after `stop()`, are dropped.
7. **Lifecycle.** `stop()` cancels the poller and clears callbacks. A new session has a new generation and starts with an empty clock. At most one request is in flight.
8. **Monitor summary.** Synthetic samples give correct gap, rate, and speed-ratio results, including a stall window and a clock-invalid interval.
9. **Nothing published.** An Observe session never calls the now-playing writer; legacy title, artwork, and lyrics paths behave as before.
10. **Default-Off regression.** With the switch off, KCRW and every other station resolve and play as on `trunk`; the M13.2 output suite passes.

## Experiments (device, step 3 of the overall plan)

Run on "Jonathan iPhone", StagingDebug build, Observe on, KCRW Eclectic24 playing over Wi-Fi. Record results in the experiment report with the `[align]` log excerpts.

| # | Question | Method | Pass criterion | Feeds |
|---|---|---|---|---|
| E1 | Does the stream give a usable clock? | Play 5 minutes, screen on. Read the readout and the log. | `currentDate()` non-nil within 15 s of `.playing`; at least 95 % of later samples clock-valid; program date advances with media time within the core's 2 s tolerance. | Gate G1 |
| E2 | Does monitoring survive 30 minutes locked? | Press play, lock, leave for 30 minutes without touching the phone, unlock, copy the log. | No sample gap over 5 s and no gap over 45 s between poll **attempts** while locked; at least 58 attempts of the 60 expected (failed requests count as attempts, and are reported separately); clock stays valid except for logged stalls; session still alive at unlock; audio never stopped. | Gate G2 |
| E3 | Does playback stay at native speed? | Use E1 and E2 samples. Also set a non-1× podcast speed first, then play radio. | `rate` is 1.0 on every sample; each 5-minute window's media-per-wall ratio is within ±1 % excluding stalls; podcast speed is unchanged afterward. | Gate G3 |
| E4 | Is the default path unchanged? | Switch off, play KCRW and one other station; check lock screen title. | Same title behavior as `trunk`. | Regression |

Not measured here, on purpose: whether `+160s` is right on iOS (14.2), route latency (14.4), and Bluetooth or CarPlay behavior.

## Decision gate

The user decides from the E1–E3 results whether to proceed to M14.2. The outcomes:

| Outcome | Next |
|---|---|
| G1, G2, and G3 pass | Proceed to M14.2. |
| G1 fails (clock nil or invalid) | Stop. Write the report. M14 pauses for a decision on whether a different clock source (for example feed-only timing) is worth designing. |
| G2 fails (monitoring stops when locked) | Stop. Report where it stopped. The first fix to try is driving the feed poll from the 1 s playback time observer (for example every 30th tick) instead of a sleeping `Task`, because that observer is tied to audio. If that also fails, the decision is a different poller design or abandoning the iOS feed poll. |
| G3 fails (rate or speed drifts) | Stop. Find the source, which is likely the effects path, before any alignment work. |

Per `pocket-radio-ios/AGENTS.md`, nothing is committed to the iOS repo until the user has tested and approved.

## Decisions needed before implementation

| # | Question | Options | Recommendation |
|---|---|---|---|
| D6 (**decided: a**) | When does KCRW play the measured HLS endpoint in 14.1? | **(a)** Only while Debug Observe is on; default Off, so normal listening is unchanged. **(b)** Always for eligible stations, which loses ICY titles on the phone now and must wait until M14.2 can replace them. | **(a).** It keeps this milestone's promise to change nothing the listener sees. The cost is that Observe runs show degraded titles; that is expected for a diagnostic mode. |
| D7 (**decided: a, attempts counted**) | Is the 30-minute locked run a hard pass number or a smoke check? | **(a)** Hard criteria as in E2. **(b)** Only "monitoring still alive at unlock". | **(a).** The criteria come from the log, cost nothing extra, and tell us whether 14.2 can trust the poller. Count poll attempts, not successes, so the test measures whether iOS ran our code while locked, not the Wi-Fi. The numbers are estimates; if a run misses narrowly, inspect the log before declaring failure. |
| D8 (**decided: b**) | Where does new code go? | **(a)** `podcasts/Radio/` per M14, with pbxproj edits for each file. **(b)** A new directory under `podcasts/Main/`, which Xcode registers automatically, plus one pbxproj edit for the package. | **(b)** for 14.1. It limits the pbxproj diff to the package reference. Revisit the location before merging to `trunk`. |

## Out of scope

- Publishing any title, artwork, or lyric from the aligned selection (14.2, 14.3).
- Single publication adapter, ICY and ACR suppression (14.2).
- Apply mode, history UI, lyrics clock (14.2–14.3).
- Bluetooth, CarPlay, route latency (14.4).
- Audio capture, JSONL traces, replay, uploads (D4: `FileLog` only).
- Checking the `+160s` offset by ear.
- Fixing menubar bugs 2 and 3 (D5).

## Docs impact

- **Docs this changes or makes stale:** [M14](milestone_14.md) (status line, the `StreamDiagnostics` assumption in "What carries over", the `podcasts/Radio/` location); `docs/ios/README.md` roadmap; possibly `pocket-radio-ios/AGENTS.md` if a new radio-alignment test layout or Debug switch is added.
- **Questions this must settle:** whether iOS HLS gives a valid clock and survives lock (ADR input for M14); whether a path dependency on the menubar package stays acceptable past 14.2 (D1 revisit).

## Hand-performed interactions

- [ ] Connect and unlock "Jonathan iPhone"; `xcrun devicectl list devices` shows it available.
- [ ] E1: five minutes on screen, readout shows a valid clock.
- [ ] E2: 30 minutes locked, audio keeps playing, log copied after unlock.
- [ ] E3: podcast speed set to a non-1× value before the radio run; radio reads 1.0 and the podcast speed is intact afterward.
- [ ] E4: switch off; KCRW and one other station behave as on `trunk`.
