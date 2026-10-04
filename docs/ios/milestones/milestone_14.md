# iOS M14 — KCRW playback alignment (port from menubar)

**Status**: PROPOSED — plan only, written 2026-10-04. Nothing is approved or started. `current_milestone.md` still points at M13; do not repoint it until the user starts this.
**Depends on**: Menubar M11-A/M11-B/M12, accepted. Core and adapter at menubar `main` `8838df5`. iOS base is `trunk` `0751918f8`.
**Required by**: The later stream-presentation work in the [stream-monitoring review](../architecture/reviews/stream-monitoring-review-2026-09-16.md) §6 steps 2 and 5.
**Related**: [M13](milestone_13.md) (CarPlay output harness). M14 can start without it. M13.2 gives M14 its strongest output test, so see decision D2.

## Where the work happens

| | |
|---|---|
| Plan and reports | Shell `main`: this file, `docs/ios/experiments/`, `docs/ios/bugs/` |
| Code | `pocket-radio-ios`, branch `feature/kcrw-alignment` from `trunk` |
| Worktree | `pocket-radio-ios-alignment/`, sibling of `pocket-radio-ios/`, so `../contracts` and `../.githooks` resolve. The M13 spike worktree `pocket-radio-ios-carplay/` stays untouched. |
| Shell changes | Docs only, unless D1 moves the shared core into the shell |

**Goal:** On iPhone, an eligible KCRW Eclectic24 station shows the song that is audible, not the feed's newest row. Lock screen, Bluetooth, CarPlay, the full and mini players, station detail, and live lyrics all follow the player's own clock. The port reuses the menubar's selection core unchanged and adds iOS adapters. Other stations and podcasts keep today's behavior.

**User checkpoint:** Play KCRW on the phone with the screen locked. The title and artwork on the lock screen change when you hear the song change. Open live lyrics mid-song and across a transition. The highlighted line follows the audio, and a pause and resume keeps it right. Repeat on Bluetooth and CarPlay.

## What carries over, and what does not

The menubar work separates cleanly into a core and its adapters.

| Piece | iOS status |
|---|---|
| `Packages/StreamSession` (`SessionState`, `MediaClock`, `OccurrenceHistory`, `OccurrenceSelector`) | Reuse as is. It is Foundation-only, has 23 tests, and already declares `.iOS(.v16)`. |
| Frozen policy: exact endpoint `https://streams.kcrw.com/e24_aac/playlist.m3u8`, `+160s` feed-to-program offset, history/clock limits | Reuse as the starting hypothesis. Verify on iOS. See "What iOS must prove". |
| Eligibility predicate (`StreamExperimentConfiguration.ineligibilityReason`) | Port. It is plain logic over name, host, and path. |
| `RadioPlaybackSession` (item generation, paired samples, 30 s feed poller, stale-callback guards) | Port, then adapt to iOS. It binds to one `AVPlayerItem` and stays free of UI. |
| Lyric clock, shared line index, correction isolated from saved offsets | Port the rules. iOS implementation differs because `LyricSyncController` is separate code. |
| `StreamDiagnostics` recorder and replay (`Tools/StreamLab`) | Do not port in full. Add only an on-device log of decisions. D4 decides whether to do more. |
| Menubar `PlayerViewModel` wiring | Do not port. iOS has different owners. |

The iOS owners that the port touches:

- **Item creation:** `PlaybackItem.createPlayerItem` calls `EpisodeManager.urlForEpisode`. Radio stations reach it through a shim whose `downloadUrl` is the stream URL. This is the endpoint-override seam, and it leaves the saved station URL alone. Radio HLS is not the podcast `hasHLSStream` path, so `isStreamingHLS` stays false and the podcast buffer settings do not apply. Confirm that, because [bug 3](../bugs/bug_3.md) says radio must stay at native speed.
- **Player and metadata:** `DefaultPlayer` creates the `AVPlayer` and attaches `RadioMetadataObserver` for radio. The session attaches here too.
- **System Now Playing:** `PlaybackManager` and `NowPlayingHelper` write title, artist, album, and artwork from several paths. These are the "last writer wins" problem in the review.
- **Titles and lyrics today:** `StationDetailViewController` polls the feed only while visible. `LyricSyncController` uses wall time. Full-screen `LyricsViewController` has its own clock.
- **ACR:** `ACRFingerprinter` opens a second stream connection. It cannot publish titles for an aligned station.

## What iOS must prove first

The menubar numbers came from macOS AVPlayer. Treat each as a hypothesis until a device run confirms it.

1. **`AVPlayerItem.currentDate()` is non-nil on iOS for this HLS endpoint.** The whole core depends on a program-date clock. This is cheap to check and is the stop-early gate.
2. **The `+160s` offset transfers.** It relates feed time to stream program time, so it should not depend on the player. Buffer depth, output route, and iOS stall behavior might still change what the listener hears. Check by ear with the same Observe/Apply comparison used in M11-B.
3. **Polling survives lock, background, and route changes.** The poller is a `Task` with a sleep. It must keep running while audio plays with the screen locked, and it must stop at item teardown.
4. **HLS gives no ICY titles.** On the aligned endpoint the feed is the only title source. Every ICY or feed-top title path must be off for an eligible station, or it will overwrite the aligned title.
5. **Route latency is separate.** Bluetooth and CarPlay add output delay on top of player time. Measure it separately. Do not fold it into `+160s`.

## Scope

All new iOS code goes in `podcasts/Radio/` as new files. Edits to `DefaultPlayer`, `PlaybackManager`, `NowPlayingHelper`, and `EpisodeManager` stay small. This is a fork of Automattic's repo, and small diffs keep upstream merges cheap.

- **Shared core wiring.** Add `StreamSession` as a local SwiftPM dependency of the app target. Location per D1.
- **Eligibility and endpoint.** New `KCRWAlignmentConfiguration` (name to be set at implementation). It holds the predicate and frozen policy. `EpisodeManager.urlForEpisode` returns the measured endpoint for an eligible radio shim. Saved stations, favorites, Supabase rows, and `curated_stations.json` stay unchanged.
- **Playback session.** New `RadioPlaybackSession` for iOS. `DefaultPlayer` creates it with the item for an eligible station and stops it at item teardown. Pause tears the item down and resume joins a fresh clock, as on the menubar. Sample from a periodic time observer, not from a UI timer.
- **Feed client.** Reuse `RadioTracklistService` parsing. Add the provider play ID and break rows the review says the parser drops. The poller is one in-flight request, owned by the session, and independent of any screen.
- **Single publication point.** One adapter owns the radio writes to `MPNowPlayingInfoCenter`. For an eligible station it writes from the selected occurrence only. It never borrows album or artwork from the feed-top row. This also fixes the artwork rebuild bug for this station. The adapter works for every station later, but this milestone enables it for KCRW only.
- **UI consumers.** Full player, mini player, and station detail read the session snapshot. History rows stay in feed order and highlight the selected occurrence, not row zero.
- **Lyrics.** Position is song seconds from the session clock. Full-screen lyrics reads the same clock and index. This removes the second timer and the offset-reset bug. Correction stays in memory, separate from `+160s` and from saved station offsets.
- **Debug mode.** A Debug-only Off / Observe / Apply control, as in M11-B. Observe shows legacy and aligned decisions side by side. It also writes decision lines to `FileLog`. No audio capture, no upload, and no Release behavior change beyond ordinary alignment.

## Sequence

| Step | Delivers | Gate |
|---|---|---|
| **14.1 Feasibility** | Core wired in. Eligibility, endpoint override, session, and an Observe-only readout on device. Nothing is published. | `currentDate()` is non-nil on a physical device. Poller survives a locked screen for 30 minutes. Radio speed stays native. Stop here if either fails. |
| **14.2 Apply: titles and Now Playing** | Single publication adapter. Full player, mini player, detail, and lock screen follow the selected occurrence. ICY, ACR, and feed-top title paths are off for the station. | Listener confirms title changes match audio on the speaker and the lock screen. Pause and resume work. |
| **14.3 Lyrics on the media clock** | Shared lyric index. Full-screen lyrics uses the session clock. Offset-reset bug fixed. | Highlighted line follows audio across a transition, a pause, and navigation in and out of full-screen lyrics. |
| **14.4 Routes and background** | Validation on Bluetooth and CarPlay, with the screen locked and the app backgrounded. | Listener confirms titles and lyrics on each route. Route delay is recorded as its own number. |

Each step ends at a user checkpoint. Per `pocket-radio-ios/AGENTS.md`, nothing is committed until the user has tested it and approved. Acceptance is qualitative, as in M11-B and M12. Formal ±5 s title and ±2 s lyric targets stay unverified unless the user asks for them.

## Behaviors to test (red -> green, one at a time)

Tests use the `PocketCastsTests` host. Inject the clock, feed, lyrics, and publication boundaries. Never write real `UserDefaults.standard` keys. The test host is the app.

1. **Eligible source only.** An eligible KCRW radio shim resolves to the measured endpoint. The saved URL is unchanged. Other stations, unsupported KCRW paths, and podcasts resolve as before.
2. **No early publication.** A feed response alone cannot change the published title. Only a player sample can.
3. **Same-item guards.** Late feed, artwork, or lyric callbacks from an old item, station, or occurrence are rejected at the publication boundary.
4. **Lifecycle.** Pause tears the session down. Resume creates a new generation and a new clock. Station and podcast switches cancel the poller. A hidden or never-opened detail screen makes no difference.
5. **One writer.** For an eligible station, `nowPlayingInfo` title, artist, album, and artwork come from one occurrence. A full rebuild keeps the selected artwork instead of the logo. ICY titles and ACR results do not reach the system info.
6. **Missing clock or history.** Show an explicit unavailable state and no timed highlights. Do not fall back to a feed-top title while claiming alignment. This is where menubar [bug 2](../../menubar/bugs/bug_2.md) applies: show the message only while this station is the active, playing item.
7. **Lyric clock.** Same line index in every consumer. Equal timestamps pick one line. Correction resets for a new occurrence and never touches saved offsets.
8. **Regression.** Existing radio, CarPlay, tracklist, artwork, and lyrics tests pass. Some current tests require feed-top fallback on ICY mismatch. Change those only for the eligible station.

## Out of scope

- Other stations, KEXP, MP3 and direct-AAC calibration, and any station-specific constants beyond KCRW.
- Rewriting saved station URLs, favorites, curated data, or Supabase rows. Deleting legacy lyric offsets.
- Removing the `+ / −` lyric controls. Hide them only after multi-route validation, per the review.
- Buffered pause, continuous timing telemetry, audio capture, and uploads.
- Replacing the whole artwork pipeline. Only the single-writer rule for the eligible station.
- watchOS, tvOS, App Clip. Guard new code with `#if !os(watchOS) && !APPCLIP && !os(tvOS)`, as `DefaultPlayer` already does for the radio observer.

## Decisions needed from the user

| # | Decision | Options | Recommendation |
|---|---|---|---|
| D1 | Where the shared core lives | (a) Path dependency on `../pocket-radio-menubar/Packages/StreamSession`. (b) Move it to a shared location in the shell. (c) Copy it into iOS. | **(a)** for 14.1 to 14.2. It needs no move, and a fix lands in one place. Revisit before merging to `trunk`. A path outside the iOS repo is awkward for a fork, and a move to a shared location is easy then. Avoid (c): the copies will drift. |
| D2 | Order relative to M13 | (a) Start M14.1 now, in parallel. (b) Finish M13.1 and M13.2 first. | **(a).** 14.1 and 14.2 need only device checks. Use M13.2 for 14.2 and 14.4 only if it is ready. Do not block on it. |
| D3 | Does the iOS player stay on the feed-driven design for non-KCRW stations? | Leave as is, or apply the single-writer adapter to all stations later. | Leave as is now. Treat the adapter as ready for reuse. |
| D4 | Trace and replay on iOS | (a) `FileLog` lines only. (b) Port the bounded JSONL recorder and replay. | **(a).** M11-B and M12 were accepted on listener reports, and the offset is a feed-to-stream property. Do (b) only if 14.1 shows the iOS offset differs. |
| D5 | Carry the menubar bugs 2 and 3 into the port | Fix on menubar first, or design the iOS behavior around them. | Design iOS around bug 2 (behavior 6). Bug 3 is menubar UI and does not apply. Fix both on menubar separately. |

## First actions once approved

1. Create the sibling worktree `pocket-radio-ios-alignment/` on `feature/kcrw-alignment` from `trunk`. Confirm `../contracts` and `../.githooks` resolve.
2. Repoint `current_milestone.md` to this file, or to a 14.1 sub-file if the steps are split.
3. Build 14.1 with a red test for eligibility and endpoint resolution. Then run the `currentDate()` gate on the pinned device ("Jonathan iPhone") before anything else.
