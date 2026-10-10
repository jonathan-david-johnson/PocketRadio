# Shared feature specs

Plain-language [Gherkin](https://cucumber.io/docs/gherkin/) scenarios describe what a PocketRadio surface should show or do. Platforms implement their own steps. Today only iOS does.

The Now Playing suite contains 15 individually registered scenarios. Its [test boundary ADR](../../docs/ios/adr/0003-carplay-output-test-boundary.md) explains the real-playback boundary, two narrow testability hooks and evidence limits.

## Layout

`contracts/features/<area>/<name>.feature`

| File under `now_playing/` | What it specifies |
|---|---|
| `smoke.feature` | First song: title, artist, album, artwork and live/music markers |
| `carplay_artwork.feature` | Detail closed/open, stale feed, iTunes and no-art fallbacks |
| `carplay_lifecycle.feature` | Pause/resume, controlled cached start and stop/replay |
| `carplay_races.feature` | Delayed artwork across song, station and podcast identities |
| `carplay_policy.feature` | Ads, lyric suppression/disconnect restoration and live/music/audio markers |

## Vocabulary

Describe the listener, stream and display, not a platform API.

| Phrase family | Meaning |
|---|---|
| the system now-playing display | OS-level output. On iOS, CarPlay and the lock screen consume `MPNowPlayingInfoCenter`. |
| a station streams from the local test server | A fake station backed by the platform's local fake world |
| the station's tracklist lists a song with COLOUR artwork | Scripted recent-plays feed |
| the tracklist takes N seconds / fails with status N | Fault staging |
| the station detail screen is open | Retain the real platform detail controller |
| the station tracklist is ready before playback | Warm the real cache through the fake service |
| playback starts with artwork resolved before the initial display rebuild | Hold the real rebuild, prove actual artwork publication, then release it for the same identity |
| the listener starts/pauses/resumes/stops/replays a station | Normal playback controls |
| the stream announces a song with an album / with no album metadata | Explicit or absent ICY album through the live stream |
| a second station or podcast starts | Switch playback identity while older artwork is pending |
| CarPlay connects / disconnects | Model output-policy connectivity; use the shared real disconnect handler |
| a lyric line reaches the album publishing boundary | Real output policy, not lyric retrieval/sync timing |
| the stream sends an ad frame | Script and record socket delivery, not receiver acknowledgement |
| the system now-playing display is empty | Reset precondition |
| the display shows title/artist/album/COLOUR artwork | Assert identity and sampled artwork |
| the rebuilt display shows … | Assert after a lifecycle transition, distinct from setup |
| the display uses the station logo | Compare with the app's actual bundled logo |
| the display album is not X | Accept absent, empty or different album; reject borrowing X |
| the display keeps values/album for N seconds | Assert through a hold |
| the display never uses old red artwork | Poll through delayed completion/cache arrival and a post-completion hold |
| the display is marked as a live music stream | Live/music fields, not podcast presentation |
| every radio display write is marked live, music, and audio | Required fields at sampled metadata/artwork/transport checkpoints |

The features contain the literal executable phrases; this table groups their vocabulary.

## Tags and known defects

Each core scenario carries `@ios @carplay`. The current iOS parser does not propagate feature-level tags. `@smoke` selects a short check; `@ios-only` identifies platform-specific policy coverage.

Known bugs never appear as shared tags. Each platform keeps its own mappings. On iOS a strict `XCTExpectFailure` targets one exact output step and classified diagnostic. A passing marked check fails. Wrong identity, readiness, missing input evidence, unexpected network traffic, reset and teardown remain ordinary failures; later unrelated checks remain visible.

Keep desired output assertions when fixing a defect and remove its marker. Do not weaken the shared spec to match today's app.

## Changing a spec

Specs change additively. Rewording a step another platform implements is breaking: update every implementation together, or retain the old phrase until they migrate.

## iOS implementation

`PocketCastsTests/Tests/CarPlayOutput/Harness/Gherkin/NowPlayingSteps*.swift` implements the steps. Five classes in `HarnessTests/` register smoke, artwork, lifecycle, race and policy scenarios.

The runner locates contracts from the test file's path. The shell checkout must sit beside the iOS checkout and any iOS worktree so `../contracts/features/` resolves. Run `make test_carplay` in `pocket-radio-ios/` (or `make ios-test-carplay` from the shell); see its `Harness/README.md` for opt-in and destructive-state warnings.
