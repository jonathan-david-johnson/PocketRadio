# iOS M13 — CarPlay output harness: experiments

**Status**: PLANNED
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
| [M13.1](milestone_13.1.md) | Reusable harness: fake station world, network guard, reset seams, Now Playing probe, runner | Smoke scenario green 20× offline |
| [M13.2](milestone_13.2.md) | CarPlay Now Playing scenario suite; known bugs as strict expected failures | User approves spec S1–S7 first |

If E1–E5 pass cleanly, merge M13.1 and M13.2 into one milestone. They are
separate so the harness is proven reliable before scenarios pile onto it.

The end goal is a suite that scripts a station (songs, tracklist, artwork,
timings) and asserts the title, artist, album, and artwork that iOS publishes
for CarPlay.

---

## Goal

Find out whether the existing `PocketCastsTests` host can run a hermetic,
in-process test of CarPlay output. The test plays a radio station from a fake
local world and reads what CarPlay would show. M13 gathers the evidence for
four design decisions before any harness code is kept.

## User checkpoint

You run one Make target against a dedicated simulator with Wi-Fi off. A spike
test plays a fake KCRW station from localhost and changes song twice. After
each change it prints the title, artist, and album from `nowPlayingInfo`, plus
the sampled colour of the artwork. You then read the experiment reports and
make decisions D1–D4.

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

## Decision gate (user)

| Decision | Options | Evidence |
|---|---|---|
| D1 Input tier | Real ICY stream for every scenario / real-stream smoke tests plus a metadata-injection seam | E2, E5 |
| D2 Fake-world placement | In-process Swift (`NWListener`) / out-of-process Python | E2 |
| D3 Gherkin runner | Minimal in-bundle parser / maintained Swift Cucumber library | E6 |
| D4 Spec | Approve or change S1–S7 in [M13.2](milestone_13.2.md#spec-decisions-user-approves-before-any-scenario-is-written) | E7 |

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
