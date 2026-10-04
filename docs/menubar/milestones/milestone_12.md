# Menubar M12 — KCRW alignment in normal playback

**Status:** ACCEPTED (2026-10-04) — the user ran the installed build in ordinary use and reported it works well. Merged to menubar `main` at `8838df5` (feature commit `fb1943d`) and pushed. Bugs 2 and 3 are accepted as open, non-blocking follow-ups.
**Depends on:** Accepted M11-A/M11-B, merged and pushed at menubar `e6fa855`.
**Execution plan:** [All-Sol subagent implementation plan](milestone_12_subagent_plan.md).
**Verification:** [Implementation and review handoff](milestone_12_handoff.md) — final commands, results, build paths, and remaining uncertainty.
**Open user-check issues:** [Bug 2 — alignment message on a nonplaying stream](../bugs/bug_2.md); [Bug 3 — footer Remote Debug button has no visible action](../bugs/bug_3.md). Filed on 2026-10-04; not fixed; non-blocking for acceptance.

## Where the work happens

| Area | Location |
|---|---|
| Plan | Shell `main`: this file, the menubar index, and any verification notes |
| Code | `pocket-radio-menubar`, branch `feature/kcrw-normal-use` from verified `main` successor `464ca70` |
| Worktree | `pocket-radio-menubar/`, provided no other menubar branch is active there |
| Shell changes | Additive documentation only; no shared contracts or backend changes |

**Goal:** Use the accepted KCRW alignment path during ordinary playback without requiring the Debug Apply picker. Keep experimental recording separate and explicitly opt-in. Do not turn experiment telemetry into normal-use monitoring.

**User checkpoint:** In normal app use, play an eligible KCRW Eclectic24 station without opening Debug controls. Titles and lyrics follow the player clock, pause/resume reconnects normally, and no recording starts. Other stations and podcasts retain their existing behavior.

## Approved implementation decision

The user approved promoting alignment to normal playback for the existing exact eligible KCRW variants, selecting the measured HLS endpoint and frozen `+160s` policy without rewriting saved station URLs. Debug **Off** disables the experiment, not ordinary alignment; Observe remains a comparison override and capture stays explicit. This does not authorize other streams, routes, platforms, or background telemetry. The user separately approved the macOS installation and replacement-app launch.

## Scope

- `StreamExperimentConfiguration.swift` and `PlayerViewModel.swift`: separate ordinary KCRW alignment eligibility/endpoint resolution from Debug experiment mode. The normal path must not need an experiment session or recorder to be explicitly armed.
- `RadioPlaybackSession.swift`: reuse the same-item clock, occurrence selection, generation guards, and independent feed polling. Preserve reconnect-only pause and explicit unavailable-alignment states.
- `LyricsService.swift` and applied lyric integration: keep one occurrence/resource/clock across the menubar and live detail. Preserve uncertainty about recording identity. Do not reuse wall-clock station offsets as the calibrated clock's lyric position; do not rewrite or delete saved offsets.
- `StreamExperimentView.swift` and `StreamExperimentRecorder.swift`: keep capture and human markers in the explicit Debug experiment. Ordinary playback must not create traces or sidecars.
- Focused app/core tests and documentation. Reuse the accepted qualitative evidence; additional long listening sessions and recorder telemetry are not prerequisites for this proposed scope.

## Behaviors to test (red -> green, one at a time)

1. **Eligible source only:** approved normal-use KCRW playback resolves to the exact measured HLS endpoint; saved source URLs remain unchanged. Unsupported KCRW paths, other stations, and podcasts retain existing resolution.
2. **No experiment required:** titles, selected history, Now Playing, and live lyrics use the same-item selection without opening Debug controls. Feed-only receipt cannot publish the next occurrence early.
3. **No recording by default:** normal playback and reconnect create no trace/sidecar files. Only an explicit Debug capture starts the recorder; no audio or telemetry upload is added.
4. **Lifecycle isolation:** pause tears down the old item; resume joins from a new valid clock. Late feed/lyric callbacks, history browsing, and station/podcast switches cannot publish into another generation.
5. **Lyric clock and correction:** menubar/live detail use the same line index. Missing timing disables highlights. Recording correction stays separate from `+160s` and legacy saved offsets; correction resets on a different occurrence/resource.
6. **Fallback and regression:** unsupported sources keep legacy behavior. Missing clocks/history produce a clear unavailable state, not a falsely aligned feed-top title. Existing podcast, remote-command, and other-station tests pass.

## Out of scope

- Additional experiment recorder fields, continuous timing monitoring, or measured ±5s/±2s claims.
- MP3/direct-AAC calibration, KEXP alignment, route-parity claims, or an iOS port.
- Saved favorite/curated/Supabase URL migration or legacy lyric-offset deletion.
- Buffered pause, new lyric catalogs, artwork refactors, automatic audio capture, or uploads.
