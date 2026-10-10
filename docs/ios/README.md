# PocketRadio iOS

The iOS app is a fork of Pocket Casts with radio playback and CarPlay integration. Code lives in `pocket-radio-ios/`; platform decisions, architecture and open issues live here.

## CarPlay regression boundary

The maintained harness uses real AVPlayer playback, loopback external inputs and the in-process system Now Playing record. It tests PocketRadio's output extensions, not upstream-only podcast behavior or head-unit rendering.

- [Harness operation and manual simulator setup](../../pocket-radio-ios/PocketCastsTests/Tests/CarPlayOutput/Harness/README.md)
- [Shared Now Playing contracts](../../contracts/features/README.md)
- [ADR 0003: test boundary and rejected alternatives](adr/0003-carplay-output-test-boundary.md)
- Open defects: [stale metadata/artwork](bugs/bug_4.md), [artwork lost on rebuild](bugs/bug_5.md), [late artwork crossing playback identities](bugs/bug_6.md), and [manual CarPlay policy discrepancies](bugs/bug_7.md)

A separate [harness reliability issue](bugs/bug_8.md) retains the intermittent initial-artwork setup failure and its passing reruns; its cause is unresolved.

Passing flag-controlled policy tests does not certify real CarPlay scene connectivity. Lyric retrieval/synchronization remains deferred. Device harness runs require separate consent because they replace playback and clear local Up Next.

## KCRW alignment

KCRW Eclectic24 alignment uses the player's program-date clock on the measured HLS endpoint and the shared `StreamSession` core. It is Debug only: Settings > Developer > **KCRW alignment**, mode Off / Observe / Apply. In Apply, the lock screen, players, widget and station detail follow the audible song. See [ADR 0004](adr/0004-kcrw-playback-clock-on-ios.md) (clock and session) and [ADR 0005](adr/0005-kcrw-aligned-now-playing-single-writer.md) (single writer). Open: [mini player and widget artwork](bugs/bug_9.md).

## Roadmap

| Milestone | Delivers | User checkpoint | State |
|---|---|---|---|
| M13 (`archive/ios-m13`) | CarPlay output feasibility experiments | Accept real ICY inputs, in-process Swift and the minimal feature runner | Closed |
| M13.1 (`archive/ios-m13.1`) | Reusable output harness | Repeated smoke runs and fault reporting; accepted with two clean device runs, not Wi-Fi-off | Closed |
| M13.2 (`archive/ios-m13.2`) | Fifteen individually selectable output scenarios | Strict known failures and manual real-radio CarPlay exercise with discrepancies retained | Closed; bugs 7–8 deferred |
| [M14](milestones/milestone_14.md) | KCRW playback alignment port | Prove the iPhone playback clock before changing publication | In progress |
| M14.1 (`archive/ios-m14.1`) | KCRW playback clock feasibility | Observe-only readout; clock valid, 30 minutes locked, native speed on the iPhone | Closed |
| M14.2 (`archive/ios-m14.2`) | KCRW aligned titles and Now Playing | Lock screen and players follow the audible song with Apply on; pause and resume recover | Closed; bug 9 open |
| [M14.3](milestones/milestone_14.3.md) | KCRW lyrics on the media clock *(planned)* | Highlighted line follows audio across a transition, a pause, and navigation into full-screen lyrics | Planned |

Close milestones through the shell's `close-milestone` skill. Replace each closed roadmap link with its `archive/ios-m<id>` tag after extracting durable knowledge and obtaining deletion approval.
