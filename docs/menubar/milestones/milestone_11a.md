# M11-A — Offline KCRW media-clock selection proof

**Status:** COMPLETE — reviewed and accepted as the frozen candidate for M11-B. M11-A was committed at menubar `186aa6d`; the user later accepted the M11-B qualitative prototype and approved commit, merge, and push on 2026-10-04. Existing merge `e6fa855` includes both slices and is pushed to `origin/main`. No production default or iOS rollout approval. Work branch `feature/stream-session-model` began at M10 feature head `0d6653e`; M10 was merged at `a3787ff`.

**Execution tracking:** [M11-A handoff, results, and open decision](milestone_11a_handoff.md).

**Goal:** Test the fixed KCRW AAC/HLS occurrence-selection rule against the two retained attended traces. Derive every decision from events available at that point in replay, quantify its error against the annotated listener markers, and expose failure/uncertainty instead of silently falling back to feed-top or wall time.

**User checkpoint:** Review one deterministic report containing all nine identified song transitions, the missed marker, the commercial exclusion, both pauses, selection/coverage failures, and a predeclared offset-sensitivity comparison. Decide whether to reject or freeze a candidate for M11-B. No new listening session is required.

## Rule under test

For the measured endpoint and a valid player sample:

```text
estimatedStart(entry) = entry.playedAt + feedToProgramOffset   // fixed candidate: +160s
selected = latest unambiguous received occurrence
           with estimatedStart <= playerProgramDate
songSeconds = playerProgramDate − estimatedStart(selected)
```

The positive offset delays selection; it is not added to lyric elapsed time. A sample at `playedAt + 190s` must produce a 30s song position, not 190s or 350s.

The selector may use only feed occurrences received by that event sequence. It must not inspect a later response while reconstructing an earlier decision. Explicit feed breaks remain occurrences; an omitted commercial is not invented. When history does not cover the player clock, the result is unavailable rather than the closest future row or an indefinitely retained old occurrence.

For the report, the signed marker error is:

```text
first replay decision elapsed − listener marker elapsed
```

A negative value means the candidate changed before the marker. Player sampling and human reaction make this a coarse measurement. The source observations imply an unsampled `160s` threshold residual range of approximately `−3.171s...+1.137s`; the implementation must derive sampled decisions from the traces rather than hard-code that range or the annotated table.

## Evidence boundaries

- Inputs are the original retained s1 and s2 traces plus separate marker annotations. Never rewrite the trace files.
- The nine markers helped motivate `160s`; this is development-set replay, not an independent holdout.
- Three s1 identities were inferred from order and intervals. Preserve that provenance in the output.
- Exclude the missed “What Was I Made For?” marker and the station-ID commercial from song-start error aggregates, while keeping both visible in the sequence.
- Do not report lyric accuracy. These captures have no lyric landmarks.
- Cache age can affect when an entry becomes available. It does not alter `estimatedStart`.

## Scope

| Area | Files/modules and responsibility |
|---|---|
| Deterministic core | **New** `Packages/StreamSession/Package.swift`, `Sources/StreamSession/{OccurrenceHistory,OccurrenceSelector,MediaClock,SessionState}.swift`, and focused tests. Foundation-only inputs, policy, reducer, and snapshots; no AVPlayer, networking, preferences, account access, or UI. |
| Replay adapter | `Tools/StreamLab/Package.swift`; **new** `Sources/StreamLab/SelectionReplay.swift` and `Tests/StreamLabTests/SelectionReplayTests.swift`. Map schema-v1 raw observations into the core and render a separate candidate report without changing observation-only replay output. |
| Synthetic fixtures | **New** fixtures under `Packages/StreamSession/Tests/StreamSessionTests/Fixtures/`. Use relative times and invented titles for CI. Do not make package tests depend on the parent shell checkout. |
| Retained-trace annotations | Add bounded sidecars under `docs/menubar/experiments/` containing marker classification, matched occurrence, identity provenance, and exclusion reason. Keep public station metadata only; do not copy audio or private paths. |
| Results | **New** M11-A experiment report and, after implementation begins, `milestone_11a_handoff.md`. Record commands, hashes, selected occurrence IDs, residuals, exclusions, policy values, and evidence limits. |

The executable interface should accept explicit trace and annotation paths plus an offset parameter. The exact command spelling may follow existing `stream-lab` argument conventions, but normal `replay` must remain byte-compatible for the same schema-v1 input.

## Behaviors to test (red -> green, one at a time)

1. **Occurrence identity and bounded history.** Repeated polls preserve an occurrence; repeats at different source timestamps remain distinct; explicit breaks survive. Test same-occurrence field revision, unambiguous timestamp correction, ambiguous correction, failed request, successful empty response, out-of-order response, eviction, and expiry. No random UUID-per-poll identity.
2. **Threshold selection.** An early received occurrence stays pending until `playedAt + offset` is reached. Test equality, immediately before/after, multiple eligible entries, initial join mid-song, missing/non-finite dates, and uncovered history. Feed receipt age affects availability only.
3. **Paired media clock.** Establish song position from a valid program-date/media-time pair, then advance from media time rather than wall time. Freeze through pauses and stalls. Invalidate on missing dates, incompatible jumps, item replacement, or a new generation. Wall-clock corrections do not move song position.
4. **Causal deterministic replay.** Feed rows enter history only at their recorded response event. Replay twice and require byte-identical decisions. Preserve schema-v1 observation replay and reject incomplete/invalid traces as before.
5. **Annotated retained-trace report.** For each of the nine identified transitions, emit matched occurrence, first candidate-decision elapsed, marker elapsed, signed error, absolute error, identity provenance, and relevant sampling uncertainty. Report median absolute error and worst absolute error. Show, but exclude from those aggregates, the missed marker and commercial.
6. **Pause and commercial regressions.** Demonstrate that the 11s and 31.367s pauses do not advance selection/song position from wall time. Require “Fools in Love” to transition near its song marker, not at the earlier commercial marker. Do not invent a break absent from the feed.
7. **Predeclared sensitivity check.** Compare fixed offsets `158s` through `163s` in one-second steps, without choosing a winner solely from the lowest in-sample error. Also report leave-one-session-out median calibration: derive from s1 and report s2, then derive from s2 and report s1. Label both sessions as related development evidence, not independent validation.
8. **Failure reporting.** Missing annotations, an occurrence mismatch, unsupported schema, unavailable player clocks, insufficient history, or a non-finite offset must produce an explicit reason. No case may silently select feed row zero or use `Date.now`.

## Execution and approval gates

1. **Complete:** `feature/stream-session-model` was created from M10 `feature/stream-monitoring-lab` at `0d6653e`. M10 was subsequently merged by `a3787ff`; the M11-A branch intentionally remains rooted at the feature head.
2. Implement behaviors 1–4 with synthetic red/green tests.
3. Add annotation sidecars, then run behaviors 5–8 against copies or explicit paths to the retained traces. Never mutate the originals.
4. Run all Stream Lab and StreamSession tests. Record exact counts, commit/dirty state, trace hashes, commands, and report hash.
5. Review the report with the user. Decide whether `160s` is sufficiently stable to freeze for a fresh attended experiment, needs revision, or should be rejected.
6. Stop. M11-B app work, commits, and merges require their own explicit approvals.

## Proposed evaluation

M11-A passes mechanically when replay is causal and deterministic, all annotations are accounted for, pause/commercial exclusions are correct, failures are explicit, and the complete report is reproducible. The proposed quality signal is that fixed `160s` selects the intended occurrence for all nine identified markers and keeps sampled transition error within ±5s.

Passing that signal only justifies considering M11-B. It does not validate a new route, lyrics, a production default, or a universal KCRW constant.

## Out of scope

- Menubar app, Xcode project, endpoint override, UI, system Now Playing, app-side recorder, or live playback changes.
- Selecting or tuning a lyric recording, applying legacy station offsets, or claiming lyric-line accuracy.
- New live KCRW or KEXP listening sessions.
- Default endpoint, favorite, Supabase, or curated-station changes.
- Commit, merge, rollout, or iOS work without separate approval.
