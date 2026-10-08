# M13.2 — final automated verification

**Status:** Original baseline verification passed; manual exercise performed with discrepancies. The user accepted the recorded limitations and approved baseline commits on 2026-10-08. The baseline is now merged. Fresh integration verification had one ordinary setup failure, followed by an isolated pass and a full pass; its cause remains unresolved. See [integration verification](#integration-verification) and [manual observations](2026-10-08_m13_2_manual_carplay.md).
**Date:** 2026-10-08 UTC.
**Code:** Tested as uncommitted changes on `2358aab83` in `pocket-radio-ios-carplay/`, `feature/carplay-harness`; subsequently committed as `12c3cfb60` after user approval. Executable source/feature behavior was unchanged during final reconciliation.
**Shell:** `main`, HEAD `8752ff8` at verification capture, with uncommitted feature specs and docs. That hash alone does not pin the tested contract changes.
**Decision record:** [CarPlay output test boundary](../adr/0003-carplay-output-test-boundary.md).

This supersedes the partial checkpoint in [the unmarked baseline report](2026-10-07_m13_2_baselines.md). No app defects were fixed and no expanded-suite device run occurred. Baseline commits were explicitly approved after the manual exercise. The user subsequently authorized integration and closure preparation; the user subsequently approved extraction/deletion and deferred the intermittent setup failure on 2026-10-08. No push, app fix or device test is authorized.

## Final checks

| Check | Result |
|---|---|
| `make format` | Passed. Removed formatter-only edits to previously clean, unrelated files. |
| Three consecutive final `make test_carplay` runs, fresh host per invocation | **128 tests, 0 failures** each; 440.688 s, 440.626 s and 440.500 s test execution |
| Actual shared scenarios | **15**, registered individually; 8 unmarked passing scenarios and 7 known-bug scenarios |
| Real strict markers | **9 designated output checks** across those 7 scenarios, linked to bugs 4, 5 and 6 |
| Sleep during final three runs | None in the power log |
| Ordinary run without harness environment | **27 selected destructive tests skipped**, 0 failures |
| Release simulator build, signing disabled | Passed; hook excluded by DEBUG guards, and no `RadioOutputTestHooks` symbols found in the Release app binary |
| Independent Sol review | One test-contract finding fixed; follow-up confirms it resolved, with no remaining verified defect in reviewed scope |
| Diff whitespace checks | Passed in shell and iOS worktree |

Before the final two comparison tests were added, three full runs also passed at 126 tests. The first integration run had one obsolete harness assertion requiring race tests to remain unmarked; it was corrected to validate their two evidenced bug-6 markers. Those earlier runs are not substituted for the final 128-test runs.

## Scenario results

| Scenario | Result |
|---|---|
| First song | Pass |
| Second song, detail closed | Expected bug 4: previous artwork retained |
| Second song, detail open | Pass |
| Tracklist one song behind | Expected bug 4: previous album and artwork retained; two checks |
| Track lacks art, iTunes hit | Pass |
| No art anywhere | Pass |
| Pause/resume | Expected bug 5 A: artwork lost |
| Cached tracklist at start | Expected bug 5 B: artwork lost after controlled initial rebuild, including subsequent hold; two checks |
| Stop/replay same song | Expected bug 5 C: artwork not restored |
| Slow previous-song art | Pass |
| Switch stations during art load | Expected bug 6: late old radio artwork publishes |
| Switch to local podcast during art load | Expected bug 6: late radio artwork publishes over podcast |
| Ad frame | Pass |
| CarPlay lyric suppression/disconnect restoration | Pass at modeled connection/publishing boundary; separate restoration check passes. Manual Carnival screenshot contains a lyric in CarPlay's third line; full scene connectivity is not certified. |
| Live/music/audio markers | Pass at the specified write-path checkpoints |

Expected failures are strict and narrow. Wrong titles, missing input evidence, readiness/network/reset errors and later unrelated failures remain ordinary failures. The existing synthetic runner tests prove that unexpected passes fail the run.

## Approved app-source changes

- Nine-line DEBUG hook in `PlaybackManager.playerDidFinishPreparing()`, plus fork-owned `podcasts/Main/RadioOutputTestHooks.swift`. Three independent unmarked runs proved actual red artwork before release, followed by its loss to the unchanged rebuild.
- Five-line extraction in `CarPlaySceneDelegate`: the real callback calls the shared internal `handleDisconnect()`; its body is unchanged. Formatter also normalized the connection flag's declaration modifier order, without changing behavior.
- No production artwork, album, dedupe or stale-callback fix.

## Independent review correction

The S2 negative-album check initially required a nonempty album. That would reject a legitimate future fix which leaves an absent album rather than borrowing the old one.

It now requires the announced station and exact display identity, permits absent/empty/different albums, and fails only for the forbidden album. New pure comparison tests cover all four outcomes and ordinary failures for missing/wrong display identity. The focused review-fix selection passed 39 tests; all three final full runs include this correction.

A separate final documentation review verified counts, hooks and evidence limits.
It found one invented runtime-target flag in the rewritten harness README. The
README now documents the actual `CARPLAY_HARNESS`/`CARPLAY_ON_DEVICE` flags and
explicitly states that no runtime-target validation gate exists. This was a docs-only
correction; no additional production safety mechanism was implemented.

## Limits and manual checkpoint

- The reset main-queue fence cannot prove all global startup work completed. One cold-start precondition failure appeared before the final hook/reset work; no reset/readiness failure occurred in the final three runs. This is observed stability, not proof of every scheduling order.
- Output checks use polling, not interception of every write or acknowledgement of every framework callback.
- ICY MP3 fixtures do not cover KCRW's real HLS transport.
- S7 covers the actual album-publishing boundary and shared disconnect handler, not system-created scene delivery or lyric retrieval/sync timing.
- Device and Wi-Fi-off checks were not run for this milestone.
- Physical rendering/truncation remains a user check.

1. Keep the lid open and the dedicated simulator signed out.
2. Build/launch the normal app without harness enablement. On this machine `make run_sim` built successfully but its `open -a Simulator` helper failed under Xcode 27. The actual run used the existing built app and Xcode 26.5's Simulator from `~/Downloads`; the [manual report](2026-10-08_m13_2_manual_carplay.md#simulator-setup-findings) records setup and input recovery.
3. In Simulator select **I/O → External Displays → CarPlay**.
4. Play KCRW through three song changes. Compare title/artist/album/artwork/live presentation against the scenario observations; known artwork defects remain intentionally unfixed.
5. Record the result before approving commits or closing the milestone.

Result recorded 2026-10-08: four songs / three transitions, with five preserved
screenshots. Visible cover omission is expected in this simulator setup. The
Carnival lyric line is a separate S7 counterexample; initial station-only identity,
control glyphs and uncertain fallback artwork also limit sign-off. No causes or
fixes were established. The user deferred lyric synchronization work. The manual
exercise is done; the user subsequently accepted the discrepancies as follow-up
work and approved the baseline commits. Integration/closure remains separate.

## Integration verification

The user authorized the external review's documentation corrections, integration and milestone closure preparation. iOS `trunk` was fast-forwarded to `feature/carplay-harness` at `52dd7c1f7`, including the durable manual simulator procedure. Byte-for-byte comparison of the main checkout's working diff before/after integration confirmed its unrelated local Xcode/instruction edits were preserved.

Verification used the existing dedicated CarPlay worktree at the same committed revision to avoid those unrelated main-checkout Xcode edits. Its pre-existing Makefile spike cleanup does not change the harness target or selection. Normal real-radio playback was terminated first; no physical-device test was run.

| Check | Result |
|---|---|
| First fresh full run | **128 tests, 1 ordinary failure**, 443.903 s; `CarPlayArtworkTests.scenario_L58_ios_carplay_a_song_without_artwork_anywhere_shows_the_logo` failed at the initial red-artwork precondition, before the no-art Song B transition |
| Isolated failing scenario | **1 test, 0 failures**, 17.464 s; initial red art and the subsequent logo transition both observed |
| Follow-up full run | **128 tests, 0 failures**, 440.734 s; no source, fixture, timeout or marker changes |

The failed request was `http://127.0.0.1:57621/art/red-large.png?song=…`, with URLSession error −1005 at 12:01:38.518 EDT. The last display snapshot retained the station logo. Scenario teardown began at 12:01:55.996, so normal teardown of that scenario does not explain the earlier connection loss. No host sleep was found during the run.

A focused read-only review could not establish the cause. The server's cancel-after-send pattern and a stale-world URL/late background work remain hypotheses, not findings. The request's current-world identity and server-event timeline were not captured in the failure. The isolated pass does not prove suite-order independence or erase the full-run failure. The user approved milestone closure with this failure deferred as an open follow-up. The subsequent full pass also does not identify the first failure's cause. No production code, fixture code, timeout or expected-failure marker was changed. The unresolved fixture/setup failure is retained in [bug 8](../bugs/bug_8.md).

Logs: `/tmp/m13-integration-test.log`, `/tmp/m13-integration-focused.log`, and `/tmp/m13-integration-test-2.log`. The built-app lookup in the new manual procedure was also checked: it resolves an existing StagingDebug `podcasts.app` with bundle ID `com.jdj.pocketradio`.

## Workstation-local logs

- `/tmp/m13-2-full-5.log`, `-6.log`, `-7.log`: final full runs
- `/tmp/m13-2-final-summary.log`: run summaries and power checks
- `/tmp/m13-2-ordinary-skip.log`: enablement protection
- `/tmp/m13-2-release-build.log`: Release build
- `/tmp/m13-2-approved-hooks.log`: controlled unmarked startup and S7 evidence
- `/tmp/m13-2-known-bug-mapping.log`: narrow mappings and expected-failure checks
- `/tmp/m13-2-review-fix-tests.log`: comparison correction
- `/tmp/m13-2-format-final.log`: formatting

The counts and findings above summarize the verified execution; local logs are disposable.
After those runs, only documentation and a source comment pointing to the durable ADR
changed. No executable code or feature scenario changed during final reconciliation.
The iOS commit includes only suite-related Makefile hunks; pre-existing removal of
unused spike variables/targets remains uncommitted. Default test selection is the
same as in the verified runs.
