# iOS M13.1 — CarPlay output harness

**Status**: MERGED (2026-10-08). Baseline `2358aab83` from `feature/carplay-harness` is now in iOS `trunk`, together with M13.2. Not pushed. Sign-off was two clean device runs instead of the rejected Wi-Fi-off check. The user approved extraction/deletion on 2026-10-08. See [Progress](#progress).
**Depends on**: M13 (complete). D1 real ICY stream, D2 in-process Swift, D3 minimal parser.
**Required by**: M13.2
**Model**: **Sonnet** for the servers, fixtures, and probe. **Opus** reviews
the reset seams in upstream files.

---

## Where the work happens

| | |
|---|---|
| Plan | Shell `main`: this file |
| Code | `pocket-radio-ios`, branch `feature/carplay-harness` from `trunk` |
| Worktree | `PocketRadio/pocket-radio-ios-carplay/`, reused from M13 (`git switch -c feature/carplay-harness trunk`) |
| Shell changes | Additive, committed straight to `main`: `contracts/features/README.md`, the first `.feature` file, and a delegating `ios-test-carplay` target in the top-level `Makefile` |

If M13 E1–E5 pass cleanly, this milestone and M13.2 merge into one on the same branch.

The [test boundary](milestone_13.md#test-boundary) from M13 applies: test
our extensions, not upstream behavior.

## Progress

Built by the [subagent plan](milestone_13.1_subagent_plan.md) on 2026-10-07. All numbers below are from runs on the dedicated simulator with the Mac kept awake.

| Check | Result |
|---|---|
| `make test_carplay` (harness self-tests + smoke + fault check) | 43 tests, 0 failures, 90.8 s |
| Smoke scenario, 20 separate launches in a row | 20 of 20 passed, each 9.15 to 9.19 s (run on the build before the review fixes). After the fixes: 3 more launches passed, and the full 43-test run passed. |
| Tracklist fault (HTTP 500) | Fails at the `.feature` line, names `tracklist-api.kcrw.com` and `HTTP 500`, shows the last Now Playing snapshot and the diff |
| Harness skips itself outside `make test_carplay` | Confirmed: a plain run reports the harness tests as skipped |
| **On the physical device** ("Jonathan iPhone", signed in, 2026-10-07, `make test_carplay_device`) | 43 tests, 0 failures, 92 s, after two fixes (below). The first device run had 15 failures. |
| Single scenario selection | `-only-testing:…/NowPlayingSmokeTests/scenario_L12_…` runs exactly that scenario |

### Device run (2026-10-07)

You chose a device run instead of the Wi-Fi-off check. What it showed:

- **The harness works on a real device**: real iOS audio session, loopback servers in the app process, the same scenarios and the same 20 s per scenario. The tone and the `.feature` files had to be bundled into the test target, because the Mac's source paths do not exist on the phone. `make test_carplay_device` copies the contracts in first.
- **A signed-in install is chatty.** The guard blocked 7 to 16 requests per scenario, only to two endpoints: `supabase.co /rest/v1/radio_favorites` (radio favorites sync) and `api.pocketcasts.com /up_next/sync`. They are now tolerated on device runs (still blocked, never sent), and listed nowhere else. This also means the Up Next wipe the run causes was **not** sent to the server by `URLSession.shared` (the sync was blocked). The phone's local Up Next is still gone, and I have not checked whether the app restores it on its next sync.
- **Real episode on the phone.** One probe test read a real "Syntax" podcast title, because the app already had an episode loaded. The probe tests now reset the app first.
- **A timing race showed up on the device**: the Y scenario lost its artwork once, the known [bug 5](../bugs/bug_5.md) symptom B (the tracklist beat the first Now Playing rebuild). The reset test now delays the tracklist by 2 s, like the smoke scenario.
- **Side effects on the phone**: Up Next cleared locally, current episode replaced then ended, listening stats (`StatsListenedTo`, `lastPauseTime`, `lastPausedAt`) changed, a quiet tone played.

Not done, by design or by your checkpoint:

- **Wi-Fi-off run.** Skipped by choice. The device run covered the real-network-present case: the guard saw and blocked everything unexpected.
- **Phone UI state helper** (`StationDetailViewController`). Deferred to M13.2.
- **HLS/AAC fake station.** Still ICY over MP3 only.
The baseline was subsequently committed as `2358aab83` and merged to `trunk`. The maintained tree has no `CarPlayOutputSpike/` folder. Unrelated Makefile spike-cleanup edits remain uncommitted and are not part of this closure.

Review findings fixed before this checkpoint: stale delayed responses no longer cross scenarios, the harness refuses to run outside `make test_carplay`, teardown order, a fixture class that could break a whole-target run, and a few weak tests. Known remaining notes are in the plan's outcome section.

### User checkpoint

The user rejected the Wi-Fi-off check on 2026-10-07 and accepted two clean physical-device runs instead. That sign-off is complete; do not ask the user to disable Wi-Fi or repeat destructive device tests.

For later simulator verification, run `make test_carplay` from `pocket-radio-ios-carplay/`. The M13.1 checkpoint had 43 tests; M13.2 expands the selection. The tracklist fault fixture is `HarnessTests/Fixtures/smoke_tracklist_500.feature`.

## Carried over from the M13 spike

The spike in `spike/carplay-harness` already proves most parts. M13.1 turns it into
kept code. Things the spike learned that this milestone must build in:

- **Hold the Mac awake.** `make test_carplay` wraps `xcodebuild` in `caffeinate -dimsu`.
  Host sleep makes the simulator's audio fail ([E5](../experiments/2026-10-04_m13_e5.md)).
- **Loopback stream URLs only.** AVPlayer traffic bypasses the guard, so the station
  factory rejects a non-loopback `streamUrl`.
- **Kingfisher ignores `URLProtocol.registerClass`.** Add the guard to its
  `sessionConfiguration.protocolClasses` as well, and set `downloadTimeout` above any
  scripted slow-download delay.
- **Four `#if DEBUG` reset seams** ([E4](../experiments/2026-10-04_m13_e4.md)):
  `PlaybackManager`, `NowPlayingHelper`, `TrackArtworkResolver`, `RadioTracklistService`.
  Opus reviews the two in upstream files.
- **Playback writes `StatsListenedTo`, `lastPauseTime`, `lastPausedAt`** to
  `UserDefaults.standard`. Document it in the harness README.
- **Tracklist arrival order matters.** The control API needs `setLatency` on the
  tracklist, because artwork survival at start depends on whether it beats the first
  Now Playing rebuild ([E7](../experiments/2026-10-04_m13_e7.md)).
- **Runner.** Promote `SpikeGherkin.swift` (156 lines). Its dynamic scenario
  registration is the part most exposed to XCTest changes.
- **Not yet covered:** HLS/AAC streams. Offline operation was not validated; a Wi-Fi-off run is not an acceptance requirement.

## Goal

Build a reusable, hermetic harness in `PocketCastsTests` with three parts:

- a fake station world that a scenario scripts;
- a guard that blocks any other network traffic;
- a probe that reads what CarPlay would show.

M13.1 ships the harness and one smoke scenario. M13.2 adds the scenarios.

## User checkpoint

Run `make test_carplay` on the dedicated signed-out simulator, with Wi-Fi unchanged. The smoke scenario passes 20 runs in a row. Then make the fake tracklist return a 500: the scenario fails with a message naming the endpoint and showing the last Now Playing snapshot. These simulator checks and the replacement device sign-off are complete; see [Progress](#progress).

---

## Scope

### Fake station world

Placement follows D2. Default: in-process Swift.

- **ICY stream.** Honours `Icy-MetaData: 1` and interleaves metadata blocks
  every `icy-metaint` bytes. Paces the audio at its real bitrate.
- **KCRW-shaped tracklist.** Entries and their timing are scriptable,
  including a lag behind the stream.
- **iTunes Search responses.** Each is a hit with an artwork URL, or an empty
  result.
- **Artwork images.** Solid-colour PNGs on loopback. Each fake album has a
  distinct colour, so assertions compare colours instead of image bytes.
- **Control API:**
  - `play(song)`: title, artist, album, and art colour.
  - `setTracklist(entries)`.
  - `setLatency(endpoint, seconds)`.
  - `fail(endpoint, status)`.
  - `dropStream()`.
  - `sendAdFrame()`.
- **Audio fixture.** A short generated tone. Commit the script that
  generates it (`afconvert` or similar) next to the fixture.

### Network guard

- A `URLProtocol` registered on `URLSession.shared`. It rewrites
  `tracklist-api.kcrw.com` and `itunes.apple.com` to the fake world, keeping
  the real hostname as far as the app can see.
- It fails any other non-loopback request and names the host and the caller.
- Artwork reaches Kingfisher through loopback URLs, so Kingfisher needs no
  interception.

### Reset seams

These are the `#if DEBUG` seams that E4 identified. Put them in fork-owned
files where possible. Each reset runs before every scenario, and clearing
`radioAlbumArtCache` covers both memory and disk.

### Now Playing probe

- `snapshot()` returns title, artist, album, `IsLiveStream`, media type, and
  the sampled artwork colour (or `nil`).
- `waitUntil(_ predicate:, timeout:)` fails with the last snapshot seen and a
  diff against the expected one.
- `holds(_ predicate:, for:)` supports "still shows X" assertions. It polls
  rather than sleeping.

### Phone UI state

> **Deferred to M13.2 (2026-10-07).** M13.1 did not build this helper. H1 and H2 reproduce without a station detail screen, so the harness needs it only for the scenario that models "station detail is open" (M13.2 behavior 3).

- An optional helper that creates and retains a `StationDetailViewController`.
  This models "the phone has station detail open", which changes when the
  tracklist is fetched. See H1 in M13.

### Gherkin runner and step definitions

- **Runner.** Follows D3: a minimal in-bundle parser or a maintained Swift
  Cucumber library. Each scenario reports as its own test result. An
  undefined step fails the scenario.
- **Specs.** Live in the shell at `contracts/features/<area>/*.feature`.
  They are worded platform-neutrally and tagged by platform, for example
  `@ios @carplay`. The test bundle loads them by `#filePath` from
  `../contracts/features/`.
- **Step definitions.** iOS-only Swift in the harness directory. They map
  neutral phrases such as "the system now-playing display" to
  `MPNowPlayingInfoCenter`.
- **`contracts/features/README.md`.** Explains the shared vocabulary, the tag
  scheme, and that specs change additively. Rewording a step that another
  platform already implements is a breaking change.

### Make targets and documentation

- `make test_carplay` in `pocket-radio-ios/Makefile`, pinned by UDID to a
  dedicated, signed-out simulator named `PocketRadio CarPlay Tests`. Add a
  `make carplay_sim` target that creates the simulator if it's missing.
- A top-level `ios-test-carplay` target that only delegates.
- A short `README.md` in the harness directory covering the architecture, how
  to add a scenario, and what the suite can't prove.

## Behaviors to test (red → green, one at a time)

1. **ICY framing.** The fake server's output, parsed back, has metadata
   blocks at exact `icy-metaint` offsets. A title change appears in the next
   block.
2. **Contract between the fake tracklist and the real parser.** The fake
   KCRW tracklist, run through `RadioTracklistService.parseKCRW`, yields the
   scripted entries. This includes a null `albumImageLarge`.
3. **Network guard: rewrite.** A request to `tracklist-api.kcrw.com` from
   `URLSession.shared` reaches the fake world.
4. **Network guard: block.** A request to any other external host fails the
   test, and the failure names that host.
5. **Reset.** Running scenarios X then Y gives the same snapshots as running
   Y then X.
6. **Probe colour.** Artwork set to a red image samples as red. No artwork
   samples as `nil`.
7. **Probe timeout.** A timed-out `waitUntil` reports the last snapshot and a
   diff.
8. **Smoke scenario.** The fake KCRW plays, and song 1's title, artist,
   album, and artwork appear. The scenario comes from a `.feature` file in
   `contracts/features/now_playing/`.
9. **Undefined step.** A `.feature` step with no Swift definition fails with
   the step text and its file and line.

## Out of scope

- The scenario suite (M13.2).
- CI. The suite runs locally on a Mac.
- KEXP's fake feed (M13.2 stretch).
- Bluetooth, physical CarPlay, and head-unit rendering.

## Verification

```bash
cd pocket-radio-ios
make format
make build_staging
make test_carplay          # harness self-tests + smoke, pinned sim
for i in $(seq 20); do make test_carplay || break; done
```
