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

## Roadmap

| Milestone | Delivers | User checkpoint | State |
|---|---|---|---|
| M13 (`archive/ios-m13`) | CarPlay output feasibility experiments | Accept real ICY inputs, in-process Swift and the minimal feature runner | Closed |
| M13.1 (`archive/ios-m13.1`) | Reusable output harness | Repeated smoke runs and fault reporting; accepted with two clean device runs, not Wi-Fi-off | Closed |
| M13.2 (`archive/ios-m13.2`) | Fifteen individually selectable output scenarios | Strict known failures and manual real-radio CarPlay exercise with discrepancies retained | Closed; bugs 7–8 deferred |
| [M14](milestones/milestone_14.md) | KCRW playback alignment port | Prove the iPhone playback clock before changing publication | In progress |
| [M14.1](milestones/milestone_14.1.md) | KCRW playback clock feasibility | Observe-only readout; clock valid, 30 minutes locked, native speed on the iPhone | Planned; decisions D6–D8 approved |

Close milestones through the shell's `close-milestone` skill. Replace each closed roadmap link with its `archive/ios-m<id>` tag after extracting durable knowledge and obtaining deletion approval.
