# iOS M13 — CarPlay output harness: experiments

**Status**: COMPLETE as an experiment milestone — E1–E7 done and D1–D4 decided (2026-10-04). Implementation checkpoints: `archive/ios-m13.1:docs/ios/milestones/milestone_13.1.md` and `archive/ios-m13.2:docs/ios/milestones/milestone_13.2.md`. See [Progress](#progress).
**Depends on**: M12.3 (`trunk` at `0751918f8`)
**Required by**: M13.1 (harness), M13.2 (CarPlay output suite), and the later
`fix/stream-presentation` branch proposed in the
[stream-monitoring review](../architecture/reviews/stream-monitoring-review-2026-09-16.md) §6 step 2
**Model**: **mixed**. Experiment design and interpretation of results need
**Opus**. The spike servers and fixtures are **Sonnet** work.

---

## Where the work happens

| | |
|---|---|
| Plan and reports | Shell `main`: this file, `docs/ios/experiments/` |
| Code | `pocket-radio-ios`, branch `spike/carplay-harness` from `trunk`. Disposable; nothing merges. |
| Worktree | `PocketRadio/pocket-radio-ios-carplay/` (sibling of `pocket-radio-ios/`, so `../contracts` and `../.githooks` resolve) |
| Shell changes | Docs only. A draft `.feature` file for E6 stays uncommitted until D3. |

## Superseding checkpoint and integration

The user rejected the original Wi-Fi-off checkpoint on 2026-10-07 and accepted two clean device runs of the M13.1 harness instead. Leave Wi-Fi unchanged; offline operation was not validated and is not a remaining acceptance requirement.

The maintained M13.1 harness and M13.2 suite are merged into iOS `trunk` at `52dd7c1f7` (2026-10-08). The original spike was disposable, uncommitted experiment code; `spike/carplay-harness` has no unique commits beyond its original base. It is not the maintained implementation or a branch whose spike code must be merged. The original experiment plan/progress below is historical. The user approved extraction/deletion on 2026-10-08, deferring the intermittent setup failure. Close the child milestones before this parent.

## Test boundary

The suite tests **our extensions** to Pocket Casts: radio playback, stream
metadata, tracklists, artwork, lyrics, and the CarPlay radio integration.
Upstream podcast behavior is Automattic's to test. The harness runs upstream
code such as `PlaybackManager` and `NowPlayingHelper` only because it sits on
the path to our output. Scenarios never assert upstream-only behavior.

## Plan at a glance

| Milestone | Delivers | Gate |
|---|---|---|
| **M13** (this) | Evidence that an in-process, hermetic CarPlay-output test is viable; baseline of suspected bugs | User makes decisions D1–D4 |
| M13.1 (`archive/ios-m13.1`) | Reusable harness: fake station world, network guard, reset seams, Now Playing probe, runner | Smoke scenario green 20× on the dedicated simulator; replacement device sign-off accepted |
| M13.2 (`archive/ios-m13.2`) | CarPlay Now Playing scenario suite; known bugs as strict expected failures | User approves spec S1–S7 first |

If E1–E5 pass cleanly, merge M13.1 and M13.2 into one milestone. They are
separate so the harness is proven reliable before scenarios pile onto it.

The end goal is a suite that scripts a station (songs, tracklist, artwork,
timings) and asserts the title, artist, album, and artwork that iOS publishes
for CarPlay.

---

## Progress

Last updated 2026-10-04. E1 and E2 reports were committed at `7f78aba`; E3 to E7 are
in the commit that follows it.

| Experiment | Status | Report |
|---|---|---|
| E1 Read back output | **PASS**: 400/400 iterations over 20 launches | [2026-10-04_m13_e1](../experiments/2026-10-04_m13_e1.md) |
| E2 Real playback | **PASS**: 6/6 launches; median 5.22 s, p95 5.27 s | [2026-10-04_m13_e2](../experiments/2026-10-04_m13_e2.md) |
| E3 Network interception | **PASS**: fixtures, Kingfisher loopback and guard all work; real-playback inventory clean | [2026-10-04_m13_e3](../experiments/2026-10-04_m13_e3.md) |
| E4 Reset and isolation | **PASS**: 4 `#if DEBUG` seams; order-independent with them, contaminated without | [2026-10-04_m13_e4](../experiments/2026-10-04_m13_e4.md) |
| E5 Determinism and cost | **PASS**: 50/50, 0.2 s spread; host sleep breaks audio, so use `caffeinate` | [2026-10-04_m13_e5](../experiments/2026-10-04_m13_e5.md) |
| E6 Gherkin runner | minimal runner (156 lines) meets all 5 checks; no library tried | [2026-10-04_m13_e6](../experiments/2026-10-04_m13_e6.md) |
| E7 Baseline H1–H3 | **H1 and H2 reproduced; H3 not** | [2026-10-04_m13_e7](../experiments/2026-10-04_m13_e7.md) |

The stop-early gate did not trigger. All seven experiments are done. The next
step is the decision gate below. Bugs found: [bug 4](../bugs/bug_4.md) (H1) and
[bug 5](../bugs/bug_5.md) (H2, a start-up race, and a stale dedupe key).

### Evidence for the decisions

| Decision | Evidence | Suggested answer |
|---|---|---|
| D1 Input tier | E5: 50/50 real-stream runs, about 5.7 s per title change. E7's bugs depend on real playback timing. | Real ICY stream for every scenario. Keep an injection shortcut only for pure logic scenarios. |
| D2 Fake-world placement | E2 to E7: in-process `NWListener`, `URLProtocol` and loopback art server all worked. | In-process Swift. |
| D3 Gherkin runner | E6: minimal parser meets all five checks at 156 lines. The one stale library candidate was not tested. | Minimal in-bundle parser. |
| D4 Spec S1–S7 | E7: H1 and H2 are real; H3 passes. Needs the S1–S7 wording reviewed against this. | Your call. See M13.2. |

### Where the code is

- Worktree `pocket-radio-ios-carplay/`, branch `spike/carplay-harness`, based on
  `trunk` `0751918f8`. **Nothing is committed** in `pocket-radio-ios` (no approval
  yet), so the spike exists only as uncommitted files in that worktree:
  - `Makefile`: `test_carplay_spike`, `CARPLAY_SIM_UDID`, `CARPLAY_TESTS`.
  - `PocketCastsTests/Tests/CarPlayOutputSpike/`: `CarPlayOutputSpikeE1Tests` to `E5Tests`,
    `CarPlayArtworkFeatureTests` (E6/E7), `SpikeIcyServer` (in-process `NWListener` ICY
    server), `SpikeSupport` (art server, network guard), `SpikeScenarioCase` (shared
    scenario and reset code), `SpikeGherkin` (the minimal runner), probes, `SpikeLog`,
    `tone_128k.mp3`.
  - Draft spec `contracts/features/now_playing/carplay_artwork.feature` in the shell,
    uncommitted until D3.
- Four `#if DEBUG` reset seams in production files (E4): `PlaybackManager`,
  `NowPlayingHelper`, `TrackArtworkResolver`, `RadioTracklistService`. No other
  production change.
- Dedicated simulator: "PocketRadio CarPlay Tests", UDID
  `6565636E-BB8D-4C34-A9EB-56F2BB638400`, iOS 26.5, signed out. Never sign in on it.
- Run: `make test_carplay_spike` (both classes), or
  `make test_carplay_spike CARPLAY_TESTS=CarPlayOutputSpikeE2Tests`.
  `xcodebuild test-without-building` avoids a rebuild when only re-running.
- Raw logs go to `/tmp/m13_results/` on the host. That folder is not in any repo
  and may be cleared; the reports quote what matters.

### Findings from E3 to E7

- **The fake world needs no production seams for the network.** `URLProtocol` on
  `URLSession.shared` and on Kingfisher's `sessionConfiguration` covers the tracklist,
  iTunes and artwork. AVPlayer traffic is not covered, so scenarios must use loopback
  stream URLs only.
- **Four `#if DEBUG` seams are needed** (E4): `PlaybackManager.lastResolvedRadioKey`,
  `NowPlayingHelper.radioTrackStationId`, `TrackArtworkResolver` (cache and key) and
  `RadioTracklistService` (cache and toasts). Two are in upstream files and reset
  `private` state. They are in the spike worktree and are not committed.
- **The E2 cleanup is not a reset.** Without the seams, a second scenario that starts on
  the first one's last song loses its artwork.
- **The host must stay awake.** The Mac's maintenance sleep makes the simulator's audio
  fail (`CoreMediaErrorDomain -66681`); titles never arrive. Wrap runs in
  `caffeinate -dimsu`. This must be part of the M13.1 Make target.
- **Playback touches `UserDefaults.standard`** (`StatsListenedTo`, `lastPauseTime`,
  `lastPausedAt`). Harmless on the dedicated simulator, but the harness should document it.
- **Cost:** about 3.3 s to start and 5.7 s per title change. Scenarios in E7 took 17 to 29 s.
  A 15-scenario suite is roughly 3 to 5 minutes.
- **Still not covered:** the HLS path (KCRW's real stream), AAC, an offline (Wi-Fi off)
  run, and the full and mini players' own artwork resolution.

### Findings that changed earlier experiments

- **Latency.** A real ICY title change costs about 5 s of real time, mostly the
  gap between where the server writes the block and where the playhead is. This is
  an inference; the burst size was not varied. E5 should use it for the cost estimate.
- **AVPlayer opens two connections.** A `Range: bytes=0-1` probe with no
  `icy-metadata` header, then the real stream. The fake world must tolerate both.
- **E2 disabled the tracklist prefetch and widget republish** (`prefetchTracklist: false`,
  `republishWidgetState: false`), so no tracklist or artwork code ran. E3 and E7 must
  turn those paths on.
- **The E2 cleanup matters.** `endPlayback(saveCurrentEpisode: false)` plus registry
  removal keeps the next launch from restoring the radio shim. E4 should fold this
  into a proper reset.
- **Artwork colour comparison** needs a tolerance of at least 2/255 (observed max 1).
- **Template buttons** (`CPNowPlayingTemplate.shared`) are readable without a scene.
  Whether the favourite and mute buttons are in M13.2's scope is still the user's call (D4).

### Open items

- **Wi-Fi was on for every experiment run.** Offline operation was not validated. The user later rejected the Wi-Fi-off checkpoint and accepted two clean device runs instead; no Wi-Fi change remains required.
- **KCRW's real stream is HLS and AAC.** Everything so far used MP3 over ICY. The HLS path
  is untested in this harness. It matters most for the alignment work in M14.
- **Full and mini players** run their own artwork resolution and were not covered by E7.
- **Decisions D1–D4** are the user's, see "Evidence for the decisions" above.
- **Nothing is committed in `pocket-radio-ios`.** The spike is uncommitted files in the
  worktree, including four `#if DEBUG` seams in production files.

## Goal

Find out whether the existing `PocketCastsTests` host can run a hermetic,
in-process test of CarPlay output. The test plays a radio station from a fake
local world and reads what CarPlay would show. M13 gathers the evidence for
four design decisions before any harness code is kept.

## User checkpoint

The experiment checkpoint is complete: real localhost playback and Now Playing readback were proven, and the user accepted real ICY inputs, in-process Swift, the minimal runner and the proposed output policies. The original Wi-Fi-off requirement was rejected on 2026-10-07. Do not repeat it; the maintained harness and its accepted device sign-off are recorded in `archive/ios-m13.1:docs/ios/milestones/milestone_13.1.md`.

---

## Known facts (source reading, 2026-10-03)

- **What CarPlay shows.** CarPlay's Now Playing screen is drawn by iOS, not
  the app, from `MPNowPlayingInfoCenter.default().nowPlayingInfo`. The radio
  writers are in `NowPlayingHelper`:
  - `setRadioTrackInfo` writes title, artist, and album.
  - `setArtworkImage` writes the artwork.
  - `setRadioAlbumTitle` writes lyric lines into the album field, and is
    suppressed while CarPlay is connected.
  - `setAllNowPlayingInfo` is the full rebuild. It installs the station logo
    as artwork.
- **Readback already works for text.** `CarPlayConnectionStateTests` writes
  and reads `nowPlayingInfo` synchronously in the test host. Nothing has
  tested artwork image readback yet.
- **The tracklist is fetched in only two places.** `RadioPlaybackStarter`
  prefetches it once per playback start (`RadioPlaybackStarter.swift:55`).
  `StationDetailViewController` also fetches it. **A CarPlay session where
  the phone never opens station detail never refreshes the tracklist after
  the start.**
- **Artwork resolution only runs for curated stations.** The station's UUID
  must be in `CuratedStationsLoader.enhancementsByUUID` with a `tracklistUrl`
  (`PlaybackManager.swift:560`).
- **Tracklist parser selection uses the URL host.** The parser is chosen by
  whether the host contains `kcrw` or `kexp`. A `127.0.0.1` URL parses to an
  empty list.
- **Different services use different HTTP stacks:**
  - The tracklist (`RadioTracklistService.shared`) and the iTunes lookup
    (`TrackArtworkResolver.shared`) use `URLSession.shared`.
  - Artwork images use Kingfisher's own session.
  - Audio uses `AVPlayer`.

  Only `URLSession.shared` is reachable by `URLProtocol.registerClass`.
- **An existing test asserts the behaviour the review calls a bug.**
  `testBestResolveEntryPopulatedCacheICYMismatchFallsBackToTop` asserts the
  feed-top fallback that the review flags as a bug.
- **`make test_staging` doesn't pin a simulator.** It targets the last
  available iPhone simulator by name, not a pinned UDID. A dedicated
  `PocketRadio Tab Tests` simulator already exists.

## Hypotheses to test

These are predictions from reading the code. None has been observed.

- **H1, the expected CarPlay bug.** Suppose the phone never opens station
  detail during a CarPlay session. For every song after the first,
  `TrackArtworkResolver.bestResolveEntry` finds no tracklist match for the
  new ICY title, so it returns the stale top entry. That entry has the same
  key as before, so `lastResolvedRadioKey` suppresses any new resolution. The
  result: CarPlay shows the correct title and artist with the **first song's
  artwork**. Whether it happens depends on navigation history, because a
  station detail screen that is retained but hidden still fetches on ICY
  changes. That would explain intermittent reports. Sources:
  `PlaybackManager.swift:530–566`, `TrackArtworkResolver.swift:105–126`.
- **H2.** A full Now Playing rebuild, such as play/pause, replaces resolved
  artwork with the station logo. The dedupe key then prevents recovery
  (review §2).
- **H3.** A slow artwork download for song A can publish after song B has
  started (review §2).

---

## Experiments (the fan-out units)

Record each result in `docs/ios/experiments/2026-MM-DD_m13_<id>.md`,
mirroring `docs/menubar/experiments/`. Each report states the question, the
method, the raw results, pass or fail, and the decision it feeds.

### E1 — Read back CarPlay-visible output

- **Question:** Can a test read title, artist, album, `IsLiveStream`, media
  type, and the artwork **image** when the production code writes them from
  a main-queue hop?
- **Method:** Call `setRadioTrackInfo` and `setArtworkImage` with a
  solid-colour image. Read back the fields. Call `MPMediaItemArtwork.image(at:)`
  and sample the centre pixel. Also check whether `CPNowPlayingTemplate.shared`
  button state is readable in the test host.
- **Pass:** Every field and the pixel colour read back correctly in 20 of 20
  runs.
- **Feeds:** the probe design in M13.1. It also decides whether the favourite
  and mute buttons are in M13.2's scope.

### E2 — Real playback inside the test host

- **Question:** Inside the test host, does `RadioPlaybackStarter` →
  `PlaybackManager` → `AVPlayer` reach the playing state against a localhost
  ICY stream? Do ICY titles reach `radioStationNowPlayingDidChange`?
- **Method:**
  1. Build a minimal in-process ICY server on `NWListener`. It serves a
     generated tone fixture with `icy-metaint` set.
  2. Register a curated station UUID (KCRW) with a localhost `streamUrl`.
  3. Change the title three times.
  4. Record the latency from the ICY title being sent to the notification
     arriving.
- **Also check:** On a fresh, signed-out dedicated simulator, launching the
  test host does not restore or autoplay another episode.
- **Pass:** Playback reaches the playing state, and every title is observed.
  Record the median and p95 latency.
- **Fallback:** If the in-process server fails, for example because of pacing
  or main-thread contention, try an out-of-process Python server. It passes
  its port through a `TEST_RUNNER_`-prefixed environment variable. Record why
  the in-process server failed.
- **Feeds:** D1 and D2.

### E3 — Network interception and the network guard

- **Questions:**
  - Can tracklist and iTunes requests be redirected to the fake world by host
    rewrite, while keeping the real hostname so the parser selection still
    works?
  - Do Kingfisher downloads from `http://127.0.0.1` work?
  - What else touches the network during a scenario?
- **Method:**
  1. Register a `URLProtocol` on the shared session. It rewrites
     `tracklist-api.kcrw.com` and `itunes.apple.com` to the fake world.
  2. Point the fixture artwork URLs at loopback.
  3. Add a guard that logs every non-loopback request.
- **Pass:** The KCRW parser parses the fake tracklist. The iTunes fallback
  resolves art from the fake. The guard's inventory is empty, or every
  unexpected host is listed with the code that calls it.
- **Feeds:** the network design and the list of stubs in M13.1.

### E4 — Reset and isolation

- **Question:** Which process-wide state must be reset between scenarios? Can
  every reset be done with a `#if DEBUG` seam that leaves production
  behaviour unchanged?
- **Candidates:**
  - `PlaybackManager`: current episode, queue, and `lastResolvedRadioKey`.
  - `RadioStationRegistry`.
  - `RadioTracklistService`: the cache and the toast set.
  - `TrackArtworkResolver`: the `NSCache` and `currentKey`.
  - `NowPlayingHelper.radioTrackStationId`.
  - `radioAlbumArtCache`, both memory and disk.
  - `MPNowPlayingInfoCenter`.
  - `CarPlaySceneDelegate.isConnected`.
  - Any `UserDefaults` keys that playback touches.
- **Method:** In one process, run scenario X then Y, then Y then X, then X
  twice. Diff the outputs.
- **Pass:** Results don't depend on order. List each seam that was needed and
  the file it lives in.
- **Feeds:** the reset seams in M13.1. Check them against the test-host
  lessons in [bug_1](../bugs/bug_1.md) and [bug_2](../bugs/bug_2.md).

### E5 — Determinism and cost

- **Question:** Is an end-to-end scenario stable enough to gate a merge?
- **Method:** Run the combined E2 + E3 scenario 50 times, with fixed timeouts,
  on the dedicated simulator.
- **Pass:** No failures. Record the median time per scenario and estimate
  the run time of about 15 scenarios.
- **Feeds:** D1. If this fails, most scenarios inject metadata through a seam,
  and only two or three real-stream smoke scenarios remain.

### E6 — Gherkin runner for iOS

Gherkin is decided. iOS is the first platform, and the `.feature` files are
meant to be shared across platforms later. The specs live in the shell at
`contracts/features/`, and each platform implements its own step
definitions.

- **Question:** Which runner turns shared `.feature` files into XCTest
  results: a minimal in-bundle Gherkin parser, or a maintained Swift
  Cucumber library?
- **Method:**
  1. Write the H1 scenario as a draft at
     `contracts/features/now_playing/carplay_artwork.feature`. Use
     platform-neutral wording such as "the system now-playing display
     shows", with tags `@ios @carplay`.
  2. Load the file from the test bundle by `#filePath`, the way
     `RemoteCommandFixtureTests` loads `contracts/remote/`.
  3. Run it with each runner candidate.
- **Check, for each runner:**
  - whether each scenario appears as its own result in the `.xcresult`;
  - whether `-only-testing:` can select a single scenario;
  - whether a failure points to both the `.feature` line and the Swift step
    definition;
  - whether an undefined step fails loudly;
  - the cost in lines, or the dependency's maintenance status.
- **Pass:** None. This is a comparison.
- **Feeds:** D3. Also check whether the step wording reads naturally for a
  later Android Auto or menubar implementation.

### E7 — Baseline the hypotheses

- **Question:** Do H1, H2, and H3 reproduce in the spike harness on
  unmodified `trunk`?
- **Method:** Write one scenario per hypothesis. Apply no fixes.
- **Pass:** None. Record "reproduced" or "not reproduced" with the evidence.
  Each reproduced bug gets its own `docs/ios/bugs/bug_N.md`, with the
  scenario as its evidence.
- **Feeds:** D4, the expected-failure list in M13.2, and
  `fix/stream-presentation`.

**Order.** Run E1 → E2 → E3 → E4 → E5 → E7. Run E6 in parallel once E2
passes. **Stop early if E1 or E2 fails.** That means the in-process approach
isn't viable. The fallback is a UI-test target that drives the app, and its
cost and benefit should be re-evaluated before going further.

---

## Decisions (made 2026-10-04)

The user accepted the recommendations.

| Decision | Outcome |
|---|---|
| D1 Input tier | Real ICY stream for every scenario. A metadata-injection shortcut is allowed only for pure-logic scenarios. |
| D2 Fake-world placement | In-process Swift (`NWListener`, `URLProtocol`, loopback art server). |
| D3 Gherkin runner | Minimal in-bundle parser, promoted from the spike's `SpikeGherkin.swift`. |
| D4 Spec | S1–S7 approved as proposed in `archive/ios-m13.2:docs/ios/milestones/milestone_13.2.md`. Favourite and mute buttons (behavior 14) stay a stretch goal. |

M13.1 and M13.2 merge into one milestone on `feature/carplay-harness`, as this
plan said they would if E1–E5 passed. They stay as two files so the harness
and the scenarios are reviewed as separate steps.

## Decision gate (user) — original options

| Decision | Options | Evidence |
|---|---|---|
| D1 Input tier | Real ICY stream for every scenario / real-stream smoke tests plus a metadata-injection seam | E2, E5 |
| D2 Fake-world placement | In-process Swift (`NWListener`) / out-of-process Python | E2 |
| D3 Gherkin runner | Minimal in-bundle parser / maintained Swift Cucumber library | E6 |
| D4 Spec | Approve or change S1–S7 in `archive/ios-m13.2:docs/ios/milestones/milestone_13.2.md` | E7 |

## Scope (spike code, disposable)

- `PocketCastsTests/Tests/CarPlayOutputSpike/`: spike tests, ICY server,
  `URLProtocol`, and fixtures. This is a synchronized group, so it needs no
  `project.pbxproj` edit.
- `podcasts/…`: only the `#if DEBUG` reset seams that E4 identifies. Nothing
  from M13 merges to `trunk`.
- `pocket-radio-ios/Makefile`: `test_carplay_spike`, pinned to the dedicated
  simulator's UDID.
- `docs/ios/experiments/`: one report per experiment.

## Out of scope

- Fixing any bug found. Fixes go in `fix/stream-presentation`.
- Head-unit rendering, truncation, physical CarPlay, and Bluetooth.
- Implementing the shared `.feature` files on other platforms. Specs are
  worded platform-neutrally, but only iOS implements steps.
- CarPlay list templates, such as the Radio tab rows.
  `RadioCarPlayRowBuilderTests` and `RadioCarPlayAdapterTests` already cover
  them.
- Lyric timing.
- KEXP. Add it after the KCRW path is proven.

## Risks

- **Flaky playback.** Real `AVPlayer` in the test host may be slow or flaky.
  E5 measures this, and D1 provides the fallback.
- **Upstream merge conflicts.** `PlaybackManager` and `NowPlayingHelper` are
  upstream files. Reset seams added there increase the conflict cost of
  future merges. Put seams in fork-owned files under `podcasts/Radio/` and
  reset only state our extensions own. Keep any unavoidable seam in an
  upstream file to a single `#if DEBUG` extension.
- **Overlap with planned iOS stream work.** The review's
  `fix/stream-presentation` branch edits the same files the seams touch.
  Land the harness on `trunk` before that branch starts, so the fix branch
  starts from the harness instead of conflicting with it.
- **Wasted harness work.** If the
  [session-model refactor](../architecture/reviews/stream-monitoring-review-2026-09-16.md#3-proposed-event-model)
  lands, harness code that is coupled to legacy notifications would be wasted.
  The harness should feed inputs on the wire and assert on
  `MPNowPlayingInfoCenter`, so it survives the refactor.
