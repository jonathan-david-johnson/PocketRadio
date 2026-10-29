# Initiatives

What is running across PocketRadio, what each one is waiting for, and what is parked. This is the one index. Each milestone doc stays the authority for its own details.

**Last verified: 2026-10-29.** Refresh the facts with `python3 tools/initiatives.py`. It reads the current milestone, branches, worktrees, uncommitted files and open bugs. It does not read judgment, so the "State", "Next" and "Needs you" columns below are written by hand. Update them when you open, close or park a milestone.

## How parallel work is organised

- A platform has one `current_milestone.md` symlink, so it can point at only one milestone. When two initiatives run in one platform, this page is the index. Each milestone's **Where the work happens** table names its repo, branch and worktree.
- One initiative, one branch, one worktree. A parallel branch in the same platform goes in a sibling worktree `pocket-radio-<platform>-<topic>/` (see `docs/REPO_STRUCTURE.md`).
- An initiative that spans platforms gets a **global milestone** as its parent. The parent holds the goal, the slice list, and the decisions. Each slice is a normal platform milestone.
- Cross-platform behavior lives in `contracts/`. Platforms port the same fixtures.

## Active initiatives

| # | Initiative | Parent milestone | Code | State | Next | Needs you |
|---|---|---|---|---|---|---|
| 1 | **iOS: KCRW alignment and routes** | [iOS M14](ios/milestones/milestone_14.md), step 14.4 | `pocket-radio-ios`, branch `experiment/unified-skew` (`56a7ecf21`), worktree `pocket-radio-ios-alignment/`. 16 commits are not on `trunk` | The stall cause is found and a Debug fix passed about 21 minutes on the phone's speaker. **Not resolved** (see below) | Run Bluetooth, wired CarPlay and locked/background checks on the fixed build | Wired phone for installs; the car; a decision on the production path for the fix |
| 2 | **Web player** | [Web M2](web/milestones/milestone_2.md), then M3a, M3 | `pocket-radio-web` `main` (`dbf7759`); M3a branch `feature/m3a-now-playing` in `pocket-radio-web-m3a/` | M2 merged 2026-10-29. Its missed-refocus observation and deleted-playlist hand check remain open. M3a has started. | Build the M3a resolver | Run the two M2 follow-ups only when you want to validate them live |
| 3 | **Now Playing normalization** | [Global M4](global/milestones/milestone_4.md) | Web: M3a in `pocket-radio-web-m3a/`. Menubar: M13 package branch `feature/now-playing-feed` in `pocket-radio-menubar-nowplaying/`. iOS: not opened | Research done (cycle 1). Contract on `main`. The isolated Swift package passes its tests and remains unintegrated. ADR 0008 accepts no server-side ICY peek for now. | Build the web resolver; decide later whether to merge the Swift package | No decision now |
| 4 | **CarPlay verification backlog** | iOS M14.4, and closed M13.x (bugs 4–8) | Same as 1 | The simulator suite passes (128 tests, nine expected failures). **No real-CarPlay run is recorded. Deferred by the user on 2026-10-29.** | Wait until the user schedules a session | A parked car, the wired cable, consent for device-harness runs |

## Parked or dormant

| Platform | Current milestone | State (as the doc says) | Note |
|---|---|---|---|
| Menubar | [M12](menubar/milestones/milestone_12.md) | ACCEPTED 2026-10-04, merged | Bugs 1, 2, 3 open. M12 and the M10–M11 milestone files are finished but not closed. iOS depends on the menubar `StreamSession` package by path |
| Global (remote control) | [M1.1](global/milestones/milestone_1.1.md) | M1 is IN PROGRESS, M1.1 PLANNED, M2 and M3 are stubs | Leave as is, per the user on 2026-10-29 |
| Console | [M5](console/milestones/milestone_5.md) | The file has no Status line; 4 commits name M5 | Three uncommitted Go files date from before 2026-06-08 |
| Roku | [M10](roku/milestones/milestone_10.md) | NOT STARTED | Two uncommitted icon files |
| Android | [M0](android/milestones/milestone_0.md) | Not scaffolded | No repo directory |

## Is the intermittent dropping resolved?

**No.** [Bug 15](ios/bugs/bug_15.md) is open. What is established:

- **Cause (measured):** `streams.kcrw.com` rotates between two servers in DNS. A listening session lives on one. When AVPlayer opens a new connection after DNS has changed, it reaches the other server, which answers segments with `404`. AVPlayer then logs `-12889`, the buffer runs dry, and audio stops for 6–17 s or fails. [ADR 0011](ios/adr/0011-kcrw-hls-pins-each-session-to-its-server.md) has the evidence.
- **Fix (works in the tested cases):** pin each session to its own server (commit `56a7ecf21`). About 21 minutes across three phone sessions on the speaker: Wi-Fi, cellular, a pause and resume, and a Wi-Fi to cellular switch. No errors, stalls or replacements. A Mac run forced a new connection on every request for 15 minutes: 0 errors pinned, 54 unpinned.
- **What is not resolved:**
  1. **It is Debug only.** A release or TestFlight build has no fix. The stall would still happen there.
  2. **Bluetooth, wired CarPlay, and locked/background playback have not been run on the fixed build.** The original failures happened on Bluetooth and the speaker.
  3. **The fix rests on an undocumented format.** It decodes the server from KCRW's session ID and sends plain `http://` to that server's address. If KCRW changes the format, the fix quietly stops working and the 20 s item-replacement backstop takes over, at about 7 s of silence each time.
  4. **It lives on an experiment branch** with 15 other commits (alignment, ShazamKit healing). None is on `trunk`.
  5. **Twenty-one minutes is a small sample.** The stalls were intermittent (a clean 18 minute run happened before the fix).
- **Options for a production path** (not decided; they are yours):
  - **A.** Ship the pin in Release, with the backstop, after the route checks pass. Fastest. Keeps the undocumented dependency.
  - **B.** Play KCRW's direct MP3 stream, which held for 100 s with no stall in a Mac test. It has no program-date clock, so alignment would need new calibration (ADR 0011 and bug 15 explain why the saved skew cannot be reused).
  - **C.** Ask KCRW to fix the session handling on their servers. Free, outside our control.
  - My recommendation is A for now (it is built and tested), with C attempted in parallel.

## CarPlay backlog

| Item | Where recorded | State | Consent needed |
|---|---|---|---|
| Real CarPlay, wired IONIQ 5: three transitions, locked and backgrounded, disconnect and reconnect | iOS M14.4 manual matrix | **Not run** | Parked car, cable, your presence |
| Bluetooth: three transitions, route switch | M14.4 | Failed before the pinning fix; **not rerun** | Phone wired for install |
| Locked and background playback | M14.4 | **Not run** | Phone wired for install |
| Device harness `make test_carplay_device` | M14 prerequisites; harness README | No run recorded in M14. It replaces playback and clears local Up Next | **Separate explicit approval each time** |
| Nine known-failure scenarios in `make test_carplay` | M14.4 results | Reproduce under strict expected-failure markers | None |
| [Bug 4](ios/bugs/bug_4.md) stale tracklist keeps the previous artwork | iOS bugs | Open, found in the harness; not seen on a device | None |
| [Bug 5](ios/bugs/bug_5.md) artwork lost on a Now Playing rebuild | iOS bugs | Open, harness | None |
| [Bug 6](ios/bugs/bug_6.md) late artwork overwrites after an episode switch | iOS bugs | Open, harness | None |
| [Bug 7](ios/bugs/bug_7.md) live lyric text can appear in CarPlay Now Playing | iOS bugs | Open, seen on the simulator | None |
| [Bug 8](ios/bugs/bug_8.md) intermittent initial-artwork setup failure in the CarPlay suite | iOS bugs | Open; investigation deferred when M13 closed | None |
| Lyrics on the head unit | iOS README | Deferred; phone lyrics only | — |

The simulator suite does not certify real head-unit behavior (ADR 0003). The real-car checks are the gap.

## Housekeeping debt

- **32 milestones that look finished are still on disk** (iOS 1–12 and M14, menubar 10–12), and `tools/docs_check.py` flags them. The convention is to close each with `close-milestone`. The check matches words such as "merged" and "accepted" in the Status line, so iOS M14 (IN PROGRESS, but its status says 14.3 "merged to `trunk`") is a false positive.
- **Five milestones have no Status line:** Android M0 and M1, Console M4, M5 and M6. Console M4 and M5 also have commits that name them.
- **Uncommitted work outside the shell:** iOS `trunk` checkout (3 build-config files), console (3 Go files), Roku (2 images), menubar (one untracked folder).
- **Open iOS bugs:** 12 of 14 (the others are a suggestion and an unlabeled file). Bugs 10–14 are UI issues found during M14.
- **`docs/todo.md`** has open items from earlier milestones (WordPress OAuth, stranded favorites, tab icon weight, upstream merge cadence).

## Decisions waiting for you

1. Production path for the KCRW stall fix (A, B or C above).
2. Whether to run the two remaining Web M2 hand checks (a missed refocus refresh and a deleted playlist).
3. Whether to merge the Swift package into menubar `main` after it remains isolated long enough for review.
4. Whether to schedule the real-car CarPlay session, and whether the device harness is wanted.
5. Whether to spend a session closing the finished milestones.
