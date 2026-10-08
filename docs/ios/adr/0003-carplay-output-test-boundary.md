# CarPlay output tests use real playback and narrowly scoped testability hooks

**Decision:** Accepted 2026-10-08. Use shared feature specs, real app playback and the system Now Playing record. Permit only the startup barrier and shared disconnect handler described below; neither fixes an app defect.

## Boundary

The harness scripts loopback MP3/ICY streams, KCRW-shaped tracklists, iTunes responses and artwork. The real app parses metadata, resolves/downloads images, runs AVPlayer and writes `MPNowPlayingInfoCenter`. The probe reads that record: title, artist, album, live/music/audio markers and sampled artwork color.

Do not mock playback or write desired snapshots to make a scenario pass. A fake station world owns one process-wide network guard, including when it owns a second station or local podcast fixture. Streams and media must stay loopback because AVPlayer bypasses URLProtocol interception.

The guard covers URLSession.shared and Kingfisher, not every session in the app. Controller-triggered auxiliary requests need precise fixtures. The suite does not prove complete network hermeticity, CarPlay rendering, physical-device behavior or HLS/AAC transport.

A renderer can omit a visible cover while using artwork for a background gradient, as observed in the manual simulator setup. Do not equate that omission with absent published artwork, or treat approximate background colors/phone tracklist covers as proof of the exact Now Playing artwork. Validate that object through the probe; validate physical presentation separately.

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

Release retained controllers, tasks, observers and pending barriers before resetting playback/caches. Local podcast fixtures remove their synthetic rows. Never directly mutate personal defaults from a test. Playback still affects the dedicated simulator's queue and listening stats.

The reset's main-queue fence does not prove that every background startup task has finished. Detect dirty state as an ordinary error rather than suppressing it.

Late-artwork tests prove request start, playback identity change, response completion and client-cache arrival, then pump callbacks and poll through an additional hold. Polling does not intercept every setter or prove absence at unsampled instants. Ad evidence proves server socket delivery, not receiver acknowledgement.

Keep the laptop lid open. Caffeinate prevents idle sleep, not clamshell sleep; host sleep invalidates simulator audio/timing evidence. Restart the dedicated simulator after interruption and check power logs before accepting reruns.

Device harness runs require separate approval: they replace the current episode, clear local Up Next and change listening stats. No app-bug fixes belong to the harness work.
