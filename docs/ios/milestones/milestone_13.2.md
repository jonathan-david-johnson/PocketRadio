# iOS M13.2 — CarPlay Now Playing output suite

**Status**: MERGED — iOS baseline `12c3cfb60` is in `trunk` (2026-10-08). The user accepted the recorded manual discrepancies and authorized integration/closure preparation. Original automated verification passed; fresh integration runs had one ordinary artwork-setup failure, then isolated/full passes without changes. Its cause remains unresolved ([bug 8](../bugs/bug_8.md)). The user approved extraction/deletion and deferred investigation of bug 8 on 2026-10-08. Both approved hooks are implemented. No app-bug fixes or expanded-suite device runs. S1–S7 remain approved as proposed on 2026-10-04.
**Depends on**: M13.1
**Required by**: `fix/stream-presentation`. That branch removes the
expected-failure markers when it fixes each bug.
**Model**: Original assignment: **Opus** writes the spec and scenario wording;
**Sonnet** implements the step bodies. The [subagent execution plan](milestone_13.2_subagent_plan.md)
proposes provider-local **Sol 6.1 / Luna** assignments for the active
`openai-codex` OAuth session. Budgeting is omitted at the user's request.

---

## Where the work happens

| | |
|---|---|
| Plan | Shell `main`: this file, plus bug docs in `docs/ios/bugs/` |
| Code | `pocket-radio-ios-carplay/`, branch `feature/carplay-harness`, baseline commit `12c3cfb60` on `2358aab83`; merged to `trunk` |
| Worktree | `PocketRadio/pocket-radio-ios-carplay/` |
| Shell changes | Additive, committed straight to `main`: new `.feature` files under `contracts/features/now_playing/` |

The durable [CarPlay output test boundary](../adr/0003-carplay-output-test-boundary.md) records the real-playback design, approved hooks and limitations.

## Execution checkpoint

See [final automated verification](../experiments/2026-10-08_m13_2_verification.md)
for scenario outcomes, logs and remaining limits. The [unmarked baseline report](../experiments/2026-10-07_m13_2_baselines.md)
retains the earlier ordering/sleep failures; it is not the final sign-off.

- All **15 scenarios** are registered individually across five classes. Default selection includes 17 harness self-test classes.
- **9 strict output-check markers across 7 scenarios** cover bugs 4, 5 and [6](../bugs/bug_6.md). Eight scenarios pass unmarked. Setup, wrong identity, network, reset and teardown failures remain ordinary.
- The approved DEBUG startup barrier proves actual artwork before releasing the unchanged initial rebuild. Three independent unmarked baselines reproduced bug 5 B; no flaky timing marker was accepted.
- The approved shared disconnect handler retains the existing body. S7 passes at the modeled connection/publishing boundary; a separate real-playback test proves restoration from a real pre-connect lyric. Manual Carnival output contains a lyric in CarPlay's third line: the full scene/connection path is not signed off.
- Independent review found an overstrong S2 album assertion. It now accepts absent/empty/different albums and rejects only the borrowed album, with two additional self-tests. Follow-up review accepted the correction.
- Formatting passed. Three final full runs each passed **128 tests, 0 failures**, with no host sleep. Ordinary invocation skipped 27 selected destructive tests. Release simulator build passed and excludes the startup hook.
- Reset now waits for cache completion and drains queued main callbacks. No final-run reset failures occurred, but this cannot prove all unobservable global startup work finished.
- The user observed four real KCRW songs / three transitions. [Manual evidence](../experiments/2026-10-08_m13_2_manual_carplay.md) records expected simulator cover omission, changing background colors, roughly 10-second tracklist lag, a lyric-policy counterexample and control-state discrepancies. Lyric synchronization stays deferred.
- **Approval:** the user explicitly approved committing this test/docs baseline with the discrepancies deferred. iOS commit: `12c3cfb60`. Existing Makefile spike-cleanup edits were excluded and preserved uncommitted.
- **Integration update:** the user authorized review corrections, integration and closure preparation. `trunk` was fast-forwarded to the harness branch; unrelated local changes were preserved byte-for-byte. The first fresh 128-test run had one ordinary initial-artwork failure with a loopback connection error. The isolated scenario and a second full 128-test run then passed without changes; those reruns do not erase the failed full run or establish its cause. See the final verification report's integration section.
- **Closure approval:** the user approved the extraction table and deletion, deferring the intermittent setup failure as open bug 8. Proceed through child-before-parent archival; no push, app fix or device test is authorized.

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

## Spec decisions (approved 2026-10-04)

The user approved S1–S7 as written. E7 results against them:

| Rule | Original E7 evidence |
|---|---|
| S1, S2 | Broken: [bug 4](../bugs/bug_4.md) |
| S3 | Broken: [bug 5](../bugs/bug_5.md), symptoms A and B |
| S4 | Holds (H3 not reproduced). Keep as a passing regression guard. |
| S5, S6, S7 | Not yet tested |

Additions from E7: add a scenario "A cached tracklist at playback start keeps the
artwork" (bug 5, symptom B) and one for stop-and-replay on the same song (symptom C).
Behavior 14 (favourite and mute buttons) stays a stretch goal.


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
- No production code changes except the two approved narrow testability exceptions above.

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

Only designated, evidenced output checks run inside strict `XCTExpectFailure`,
with the bug ID in the message. The iOS table matches exact scenario name,
output-step text and classified diagnostic. A passing marked check fails the run;
later unrelated checks remain visible. No marker lives in shared feature tags.

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
cd pocket-radio-ios-carplay
make format
make test_carplay
```

Automated result: three consecutive **128-test** passes after review correction;
Release build and ordinary-run skip checks passed. See the final report above.

Manual result: **performed with discrepancies**, not a clean all-policy pass.
The user supplied five screenshots across four songs / three transitions on
2026-10-08. See [manual observations](../experiments/2026-10-08_m13_2_manual_carplay.md).
This simulator omits visible covers and uses background gradients; that alone is
not missing artwork. Carnival visibly contains a lyric in the CarPlay third line,
contrary to S7. Connection-state/scene behavior remains unresolved; lyric timing
is explicitly deferred. The user accepted this baseline and explicitly approved
commits on 2026-10-08. The user subsequently approved integration and closure with the discrepancies and intermittent setup failure retained as open follow-ups. Do not claim them fixed.

## Docs impact

| Document | Update |
|---|---|
| `docs/ios/adr/0003-carplay-output-test-boundary.md` | Durable real-playback boundary, hooks, alternatives and evidence limits |
| `contracts/features/README.md` | Current five-file suite, vocabulary and strict marker policy |
| Worktree `CarPlayOutput/Harness/README.md` | Enablement, destructive reset, selection, implementation and limitations |
| Bugs 4, 5 and 6 | Reproduction evidence and narrow iOS output-check mappings; all remain open |
| Final experiment report, manual report/screenshots and subagent plan | Automated results, manual discrepancies and explicit baseline commit approval |
