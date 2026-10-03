# iOS M13.2 — CarPlay Now Playing output suite

**Status**: PLANNED, provisional. Revise after M13 E7 and the M13.1 smoke.
**Depends on**: M13.1, and the user's approval of S1–S7 below
**Required by**: `fix/stream-presentation`. That branch removes the
expected-failure markers when it fixes each bug.
**Model**: **Opus** writes the spec and the scenario wording. **Sonnet**
implements the step bodies.

---

## Where the work happens

| | |
|---|---|
| Plan | Shell `main`: this file, plus bug docs in `docs/ios/bugs/` |
| Code | `pocket-radio-ios`. If merged with M13.1, continue on `feature/carplay-harness`. Otherwise use `feature/carplay-suite` from `trunk` after M13.1 lands. |
| Worktree | `PocketRadio/pocket-radio-ios-carplay/` |
| Shell changes | Additive, committed straight to `main`: new `.feature` files under `contracts/features/now_playing/` |

The [test boundary](milestone_13.md#test-boundary) from M13 applies.

## Goal

Pin down what CarPlay's Now Playing screen shows across song changes:
artwork, title, artist, album, and the live markers. Scenarios that pass
today guard against regressions. Scenarios for known bugs ship as **strict**
expected failures, each linked to a bug doc, so the fix milestone has a
ready-made red → green target.

## User checkpoint

Run `make test_carplay`. The report lists every scenario. Known-bug
scenarios show as expected failures with their bug IDs. If you apply a fix
locally, its scenario reports as **unexpectedly passing** and fails the run,
so a fix can't land without its marker being removed.

---

## Spec decisions (user approves before any scenario is written)

The suite asserts a policy. Today's code and the stream-monitoring review
disagree in places, and one existing unit test,
`testBestResolveEntryPopulatedCacheICYMismatchFallsBackToTop`, encodes
today's behavior. The defaults below are drawn from
[review §3](../architecture/reviews/stream-monitoring-review-2026-09-16.md#3-proposed-event-model).

| ID | Proposed rule |
|---|---|
| S1 | On a new song, title and artist come from ICY immediately. Artwork is the matching tracklist or iTunes art, or else the station logo. It is **never** the previous song's art. |
| S2 | Album and artwork are never borrowed from a tracklist entry that doesn't match the current song. |
| S3 | A rebuild for the same song, such as play/pause, keeps the resolved artwork. |
| S4 | A result that arrives after the song, station, or episode has changed is dropped. |
| S5 | An ad or break frame leaves the current display unchanged. A content-state model is deferred to the session-model work. |
| S6 | If no artwork is found anywhere, the station logo is shown. |
| S7 | While CarPlay is connected, lyric lines are never written to the album field. Disconnecting restores the real album. |

Existing unit tests that contradict an approved rule get updated in
`fix/stream-presentation`, not here.

## Scope

- `contracts/features/now_playing/*.feature`, in the shell: one scenario per
  behavior below. Use platform-neutral wording ("the system now-playing
  display shows") and tag each scenario `@ios @carplay`. Tag a scenario that
  only makes sense on iOS `@ios-only`.
- `PocketCastsTests/Tests/CarPlayOutput/`: the iOS step definitions for any
  new phrases.
- `docs/ios/bugs/bug_N.md`: one per reproduced bug, if E7 didn't already
  create it.
- No production code changes.

## Behaviors to test (one scenario each)

Phone UI state is noted where it changes the code path.

1. **First song.** Title, artist, album, and artwork come from ICY plus the
   tracklist.
2. **Second song, station detail never opened.** Artwork is song 2's art or
   the logo (H1).
3. **Second song, station detail open.** Same expectation as 2, but on the
   path where the tracklist refreshes on ICY changes.
4. **Tracklist one song behind the stream.** No song-2 title shown with
   song-1 art or album (S2).
5. **Tracklist has no art for a song.** The iTunes fallback art is shown.
6. **No art anywhere.** The station logo is shown, not the previous song's
   art (S1, S6).
7. **Play/pause during a song.** The resolved artwork survives the rebuild
   (H2, S3).
8. **Slow art for song A, then song B starts.** Song A's art never appears
   during song B (H3, S4).
9. **Station switch while art is loading.** The old station's art never
   publishes (S4).
10. **Switch to a podcast while art is loading.** Radio art never publishes
    over the podcast (S4).
11. **Ad frame mid-song.** Title, artist, and artwork are unchanged (S5).
12. **CarPlay connected.** Lyric lines don't reach the album field.
    Disconnecting restores the album (S7).
13. **Live markers.** `IsLiveStream` is true and the media type is music
    after every write path, including a rebuild.
14. **Favourite and mute buttons** (only if M13 E1 showed
    `CPNowPlayingTemplate` state is readable). The radio button set appears
    while a station plays.

Behaviors that E7 reproduced as bugs run as
`XCTExpectFailure(strict: true)`, with the bug ID in the message. The
marker lives in an iOS-side known-bugs table that maps scenario name to bug
ID, not in a tag on the shared `.feature` file. A bug on iOS says nothing
about another platform, so it doesn't belong in the shared spec.

## Out of scope

- Fixing anything. Fixes belong to `fix/stream-presentation`, guided by the
  review's session-model plan.
- KEXP, as a stretch goal. If it fits, add one smoke scenario for KEXP's
  `results` feed shape.
- Head-unit layout and truncation. These remain a manual check: in the
  Simulator, choose **I/O → External Displays → CarPlay**, play KCRW through
  three song changes, and compare the screen against the suite's snapshots.
- Physical CarPlay and Bluetooth. Use the pinned device per `AGENTS.md`.

## Verification

```bash
cd pocket-radio-ios
make format
make test_carplay
```

Manual: run the CarPlay-simulator check above once, and record the result in
this file.
