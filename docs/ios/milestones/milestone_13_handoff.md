# M13 closeout review

**Status:** Closure and extraction approved by the user on 2026-10-08. The intermittent setup failure is deferred, not fixed or suppressed; bug 8 remains open. This handoff is working state for archival, not a permanent destination.

## Completed actions

- Shell `154dc99`: removed the rejected Wi-Fi-off checkpoints from M13.1 and its execution plan; committed the plain-language decision rule in root `AGENTS.md` without staging pre-existing lifecycle changes.
- iOS `52dd7c1f7`, then `541f0ca0f`: preserved manual Xcode 26.5 Simulator setup/input recovery, always-install instructions, device-evidence limits and named harness coverage in the harness README. The app-path lookup was checked against actual build settings.
- `feature/carplay-harness` is merged by fast-forward into `trunk`; both are at `541f0ca0f`. The main checkout's unrelated working diff remained byte-for-byte unchanged. No executable code or shared scenario changed.
- Post-integration verification: first full run **128 tests, 1 ordinary initial-artwork failure**; isolated scenario **1 test, 0 failures**; second full run **128 tests, 0 failures**. The passes do not identify or erase the first failure. Draft bug 8 preserves it.

## Extraction table for approval

| Durable item | Destination | Status |
|---|---|---|
| Rejected Wi-Fi-off requirement and accepted original device sign-off | Harness README; acceptance rationale in ADR 0003 | README committed; ADR draft |
| Manual CarPlay GUI setup and dedicated-device input recovery | Harness README | Committed |
| Plain-language choices with recommendations | Root `AGENTS.md` | Committed |
| Real ICY / in-process Swift / minimal runner choices, untried alternatives, insufficient-reset negative result | `docs/ios/adr/0003-carplay-output-test-boundary.md` | Draft; archive citations resolve when tags are created |
| Maintained behaviors and verification limits | Existing tests/contracts and harness README coverage map | Present/committed |
| Manual lyric-policy counterexample and unclassified UI/timing/artwork observations | `docs/ios/bugs/bug_7.md` | Draft open issue; lyric sync stays deferred |
| Intermittent loopback artwork/setup failure and passing reruns | `docs/ios/bugs/bug_8.md` | Draft open harness issue; cause unresolved |
| Roadmap, surviving evidence citations and next-plan references | `docs/ios/README.md`, bugs 4–6, M14, `docs/test-architecture.html` | Draft; roadmap rows/pointer change only on approved closure |
| Progress, phase plans, experiment reports/screenshots and retired milestone roles | Archive tags below, then deletion | Not tagged or deleted |

No original app bugs were fixed. Leave bugs 4–8 in place. Preserve all unrelated/untracked work, including the old M13 role files owned by another session.

## Bundle proposed for archival and deletion

### M13.1 — `archive/ios-m13.1`

- `archive/ios-m13.1:docs/ios/milestones/milestone_13.1.md`
- `archive/ios-m13.1:docs/ios/milestones/milestone_13.1_subagent_plan.md`

### M13.2 — `archive/ios-m13.2`

- `archive/ios-m13.2:docs/ios/milestones/milestone_13.2.md`
- `archive/ios-m13.2:docs/ios/milestones/milestone_13.2_subagent_plan.md`
- `archive/ios-m13.2:docs/ios/experiments/2026-10-07_m13_2_baselines.md`
- `archive/ios-m13.2:docs/ios/experiments/2026-10-08_m13_2_verification.md`
- `archive/ios-m13.2:docs/ios/experiments/2026-10-08_m13_2_manual_carplay.md`
- `archive/ios-m13.2:docs/ios/experiments/traces/2026-10-08_m13_2_manual/01-anyone-else-but-you.png`
- `archive/ios-m13.2:docs/ios/experiments/traces/2026-10-08_m13_2_manual/02-carnival.png`
- `archive/ios-m13.2:docs/ios/experiments/traces/2026-10-08_m13_2_manual/03-a-good-day.png`
- `archive/ios-m13.2:docs/ios/experiments/traces/2026-10-08_m13_2_manual/04-a-good-day-lyric-offset.png`
- `archive/ios-m13.2:docs/ios/experiments/traces/2026-10-08_m13_2_manual/05-simetachin.png`
- `archive/ios-m13.2:.pi/agents/m13-2-sol.md`
- `archive/ios-m13.2:.pi/agents/m13-2-luna.md`
- `archive/ios-m13.2:.pi/agents/m13-2-review.md`

The screenshots are human evidence, not tool replay fixtures; retain them in the archive, not as live experiment files.

### M13 — `archive/ios-m13`

- `docs/ios/milestones/milestone_13.md`
- `docs/ios/milestones/milestone_13_handoff.md` (this review)
- `docs/ios/experiments/2026-10-04_m13_e1.md`
- `docs/ios/experiments/2026-10-04_m13_e2.md`
- `docs/ios/experiments/2026-10-04_m13_e3.md`
- `docs/ios/experiments/2026-10-04_m13_e4.md`
- `docs/ios/experiments/2026-10-04_m13_e5.md`
- `docs/ios/experiments/2026-10-04_m13_e6.md`
- `docs/ios/experiments/2026-10-04_m13_e7.md`

The disposable spike has no unique commits. The maintained implementation is the merged harness, not the original uncommitted spike. No other bundle-specific references were found in the platform checkout/worktree scan.

## Closure framework prerequisite

The lifecycle-framework owner committed their approved shell changes as `933256c`, including the root lifecycle bullets, `docs/REPO_STRUCTURE.md`, the live pre-commit hook/checker and milestone skills. The obsolete committed M13 link is removed, satisfying the framework prerequisite. Their platform instruction/skill moves are separately owned. Do not stage unrelated Makefile edits.

Their throwaway-clone deletion dry-run found seven remaining E1–E7 links in `docs/test-architecture.html`; those are now replaced with archive retrieval instructions. Roadmap tag rows and the active symlink are intentionally unchanged until closure approval. No other blocking references were reported.

Do not force-remove the CarPlay worktree after merge: it still contains another session's pre-existing Makefile edits. Keep it until that work is resolved or the user approves a safe preservation/cleanup plan. Archive tags are local; no push is authorized.

## User decision

The user approved closure and said to ignore the intermittent setup failure for now. Proceed with the accepted baseline, retaining the failed run and unresolved cause in bug 8. Do not add diagnostics, change timeouts or add an expected-failure marker as part of closure.

Manual discrepancies and app defects remain open. This does not authorize a production fix, device test, lyric-sync work or push.

Use `close-milestone` in order: M13.1, M13.2, then M13. Reconcile remaining references at each step, commit final bundle forms, tag the last containing commit, verify each archived file, then delete/commit explicit paths. Replace each roadmap row with its archive tag. Repoint the active milestone to proposed M14 without starting implementation. Do not delete before this review is approved.
