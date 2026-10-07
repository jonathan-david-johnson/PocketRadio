# iOS M13.1 — CarPlay output harness

**Status**: PLANNED. M13 decisions D1–D3 made 2026-10-04 (see below). Not started.
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
- **Not yet covered:** HLS/AAC streams, and an offline (Wi-Fi off) run.

## Goal

Build a reusable, hermetic harness in `PocketCastsTests` with three parts:

- a fake station world that a scenario scripts;
- a guard that blocks any other network traffic;
- a probe that reads what CarPlay would show.

M13.1 ships the harness and one smoke scenario. M13.2 adds the scenarios.

## User checkpoint

Turn Wi-Fi off and run `make test_carplay` on the pinned simulator. The smoke
scenario passes 20 runs in a row. Then make the fake tracklist return a 500:
the scenario fails with a message naming the endpoint and showing the last
Now Playing snapshot.

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
