# CarPlay output tests use real playback and narrowly scoped testability hooks

**Decision:** Accepted 2026-10-08, retaining the harness design choices accepted on 2026-10-04. Use shared feature specs, real app playback and the system Now Playing record. Retain the four DEBUG reset seams; the only additional testability exceptions are the startup barrier and shared disconnect handler described below. None fixes an app defect.

## Boundary

The harness scripts loopback MP3/ICY streams, KCRW-shaped tracklists, iTunes responses and artwork. The real app parses metadata, resolves/downloads images, runs AVPlayer and writes `MPNowPlayingInfoCenter`. The probe reads that record: title, artist, album, live/music/audio markers and sampled artwork color.

Do not mock playback or write desired snapshots to make a scenario pass. A fake station world owns one process-wide network guard, including when it owns a second station or local podcast fixture. Streams and media must stay loopback because AVPlayer bypasses URLProtocol interception.

The guard covers URLSession.shared and Kingfisher, not every session in the app. Controller-triggered auxiliary requests need precise fixtures. The suite does not prove complete network hermeticity, CarPlay rendering, physical-device behavior or HLS/AAC transport.

A renderer can omit a visible cover while using artwork for a background gradient, as observed in the manual simulator setup. Do not equate that omission with absent published artwork, or treat approximate background colors/phone tracklist covers as proof of the exact Now Playing artwork. Validate that object through the probe; validate physical presentation separately.

## Design choices and rejected alternatives

| Choice | Reason and evidence | Alternative not selected |
|---|---|---|
| Real ICY playback for each output scenario | Real-stream repetition was stable on an awake host, and startup/rebuild defects depend on actual playback ordering. Evidence: `archive/ios-m13:docs/ios/experiments/2026-10-04_m13_e2.md` and `archive/ios-m13:docs/ios/experiments/2026-10-04_m13_e5.md`. | Metadata injection exercises a different path and cannot establish these lifecycle sequences. It is permitted only for pure-logic self-tests, not as a replacement for scenario playback. |
| In-process Swift fake world | Loopback listeners, network fixtures and real artwork downloads worked inside the app test host. Evidence: `archive/ios-m13:docs/ios/experiments/2026-10-04_m13_e2.md` and `archive/ios-m13:docs/ios/experiments/2026-10-04_m13_e3.md`. | An out-of-process Python server was a fallback if the in-process approach failed. It was not needed or tried; do not describe it as an experimentally rejected design. |
| Minimal in-bundle feature runner | The spike proved independent XCTest results, single-scenario selection, source-located failures and undefined-step reporting without adding a dependency. Evidence: `archive/ios-m13:docs/ios/experiments/2026-10-04_m13_e6.md`. | Third-party runners were inspected through repository metadata, not built or run. There was no experimental comparison establishing that they could not work. Revisit if the shared specs need unsupported Gherkin constructs. |

These tests target PocketRadio's radio extensions, not upstream-only podcast behavior. Upstream playback code stays real because it lies on the radio output path. Shared scenarios preserve the accepted title, artwork, lifecycle, race and lyric-publication policies; favourite/mute suite expansion remains deferred.

## Shared specifications and platform-local defects

Platform-neutral scenarios live in `contracts/features/now_playing/`. Each has explicit platform tags. Each iOS scenario appears as its own XCTest result and can be selected individually.

Known failures belong in iOS code, never in shared feature tags. A marker identifies a stable unique scenario name, one exact output step, a bug identifier and an exact classified diagnostic. Use strict expected failures: a passing marked check fails the run until its marker is deliberately removed.

Readiness, undefined/ambiguous steps, feature loading, wrong identity, unexpected network traffic, reset and teardown errors remain ordinary failures. A marked output check must not hide later assertions. Reject stale mappings and ambiguous scenario identities.

## Startup barrier

Artwork resolved before the initial full rebuild can be replaced by the station logo. Network/image-cache timing alone does not impose this order reliably.

A DEBUG-only hook in `PlaybackManager.playerDidFinishPreparing()` may capture its actual display-rebuild continuation for an explicitly armed radio identity. Fork-owned `RadioOutputTestHooks` stores the continuation and a generation-bound ticket.

The cached-start scenario must prove all of these before asserting preservation:

1. The real service/parser warmed the tracklist before playback.
2. The real startup callback reached the armed hook and its rebuild is pending.
3. The actual resolver/download path published the scripted artwork.
4. The test released the unchanged rebuild for the same playback identity.
5. Real playback settled and fresh ICY metadata arrived.

The unarmed DEBUG path follows the original rebuild. Release excludes the hook. Reset cancels pending continuations, never releases them. A stale ticket, changed identity or missing prerequisite is an ordinary harness failure. Do not manufacture display data or substitute pause/resume for startup.

## Disconnect handler

Apple supplies the typed scene/controller inputs to its disconnect callback. Tests cannot construct those through supported initializers.

The callback delegates to an internal `CarPlaySceneDelegate.handleDisconnect()` method containing the existing cleanup and album-restoration body unchanged. Tests call the same method; they do not copy restoration logic or invoke the callback with invalid framework objects.

The existing connection-state seam models connectivity at the output-policy boundary. A separate restoration check must first publish a real lyric value, then prove that disconnect restores the cached album while preserving title, artist and artwork. Merely observing an already-correct album is insufficient.

This covers our publication/cleanup logic, not Apple's delivery of actual scene connection/disconnection events or lyric retrieval/timing. A visible system CarPlay screen is not proof that the app's connection flag agrees with system state. Passing flag-controlled policy tests must not be presented as certification of that full lifecycle.

## Isolation and evidence

Use the dedicated signed-out simulator, one writer/simulator user at a time, and explicit harness enablement. Ordinary test runs skip destructive scenario tests before reset.

Stopping playback and clearing the display alone left singleton keys/caches contaminated: a second scenario could skip artwork resolution because it inherited the first scenario's deduplication key. The four DEBUG seams reset fork-owned radio state in `PlaybackManager`, `NowPlayingHelper`, `TrackArtworkResolver` and `RadioTracklistService`. The first two are in upstream files because their private state cannot be reset from a separate extension without widening visibility. Keep those edits narrow. Evidence: `archive/ios-m13:docs/ios/experiments/2026-10-04_m13_e4.md`; regression coverage: `ResetTests`.

Release retained controllers, tasks, observers and pending barriers before resetting playback/caches. Local podcast fixtures remove their synthetic rows. Never directly mutate personal defaults from a test. Playback still affects the dedicated simulator's queue and listening stats.

The reset's main-queue fence does not prove that every background startup task has finished. Detect dirty state as an ordinary error rather than suppressing it.

Late-artwork tests prove request start, playback identity change, response completion and client-cache arrival, then pump callbacks and poll through an additional hold. Polling does not intercept every setter or prove absence at unsampled instants. Ad evidence proves server socket delivery, not receiver acknowledgement.

Keep the laptop lid open. Caffeinate prevents idle sleep, not clamshell sleep; host sleep invalidates simulator audio/timing evidence. Restart the dedicated simulator after interruption and check power logs before accepting reruns.

Device harness runs require separate approval: they replace the current episode, clear local Up Next and change listening stats. The user rejected the Wi-Fi-off checkpoint on 2026-10-07 and accepted two clean device runs of the original 43-test harness instead. This is not evidence of offline operation or device validation of the expanded suite. Leave host Wi-Fi unchanged; do not restore that rejected acceptance requirement. Evidence: `archive/ios-m13.1:docs/ios/milestones/milestone_13.1.md`.

The simulator-only expanded suite passed three consecutive final runs of 128 tests with no failures. Its strict markers cover nine output checks across seven scenarios; eight scenarios pass unmarked. Ordinary invocation skipped 27 selected destructive tests, and the Release simulator executable contained no `RadioOutputTestHooks` symbols. Evidence: `archive/ios-m13.2:docs/ios/experiments/2026-10-08_m13_2_verification.md`.

Manual real-radio observation covered four songs and three transitions, but Carnival displayed a lyric while CarPlay was visible. The user accepted the baseline with that discrepancy deferred, not as full scene-policy verification. Keep the unresolved observations in [the manual CarPlay follow-up issue](../bugs/bug_7.md). Lyric timing stays deferred. No app-bug fixes belong to the harness work.
