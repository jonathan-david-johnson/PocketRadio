# M11-B — Opt-in KCRW AAC/HLS menubar experiment

**Status:** M11-A committed at menubar `186aa6d`. Off / Observe / opt-in Apply candidate are implemented on menubar `feature/stream-session-model` at `94814f6`; three fresh Observe captures were replayed offline: one single-transition smoke, a second run with three listener-confirmed music markers and a corrected commercial button, and a third with five listener-confirmed song identities but deliberately delayed buttons, no recorded output-route category, and later speaker-route confirmation for all runs. These do not complete the attended immediate-boundary protocol; do not treat delayed buttons as a timing failure or retune. The user explicitly approved Apply candidate; the opt-in Debug implementation and signed synthetic tests were committed in the menubar feature repo at `94814f6`. The [first attended Apply smoke](../experiments/2026-10-03_kcrw_m11b_apply_s0.md) recorded `speaker` and one listener-reported perfectly timed scrolling-title change, while the legacy/feed next row appeared early. This is not a title distribution, Now Playing check, or lyric validation. A later [Apply pause capture](../experiments/2026-10-03_kcrw_m11b_apply_pause_teardown.md) was exported automatically at item teardown; it has five raw song buttons, one later corrected by the listener to station-ID-like speech, and no independently confirmed song identities or resumed item. The user does not want another long capture merely to resolve this marker; after Resume they reported a good title with aligned Now Playing and lyrics. This is attended qualitative feedback, not a second post-resume trace, independent recording match, lyric-landmark measurement, or completion of the formal multi-session targets. The user chose **reconnect-style pause only**; buffered pause is out of scope. The user approved a local Debug export-status UI fix; a new signed build and 18 app unit tests passed, and the user authorized switching to that build. The listener visually checked its banner after a short completed Apply capture and said it looks good. A focused review then fixed an Apply lyric-detail row-ID refresh issue in a separate signed, unit-tested build that has not been launched for listening. The user approved this scoped M11-B commit. No merge, push, default-endpoint change, or rollout approval. See [Apply staging](../experiments/2026-10-03_kcrw_m11b_apply_staging.md) and [M11-B handoff](milestone_11b_handoff.md), the [first smoke report](../experiments/2026-10-03_kcrw_m11b_observe_smoke.md), [second session report](../experiments/2026-10-03_kcrw_m11b_observe_s1.md), and [third delayed-marker report](../experiments/2026-10-03_kcrw_m11b_observe_s2.md).

**Goal:** Put the frozen M11-A occurrence-selection candidate behind explicit, reversible controls in the menubar app, observe it on the same AAC/HLS player item, and collect fresh title and lyric evidence without changing production defaults or saved user data.

**User checkpoint:** On a recorded macOS output route, enable observe-only mode, verify the exact AAC/HLS item and candidate clock, then explicitly apply the candidate. Hear at least five identified song changes in each of two fresh fixed-policy sessions, compare selected history/title and lyric highlights with the audio, exercise reconnect-style pause and fresh-item resume, export the app's trace, replay its decisions offline, and disable the experiment without changing station URLs or saved lyric offsets.

## Entry criteria from M11-A

M11-B may start only after the user reviews M11-A and explicitly approves all of the following as a frozen candidate configuration:

- exact endpoint;
- feed-to-program-date offset;
- occurrence identity/coverage policy;
- missing-clock and stale-history behavior;
- title-transition target and known uncertainty;
- annotation/report format for fresh sessions.

Do not tune these values during a validation session. A change starts a separately labeled run and forfeits that run as fixed-policy evidence.

## Experimental behavior

### Reversible modes

Provide debug-only modes:

- **Off:** existing production behavior and endpoint resolution.
- **Observe only:** use the exact measured AAC/HLS endpoint for this session and display legacy and candidate decisions without publishing the candidate as current.
- **Apply candidate:** publish the frozen candidate to experimental menubar title, selected history row, live lyrics, and existing system-title output.

Changing endpoint or mode creates a fresh player item/generation. Never write the override to favorites, Supabase, `curated_stations.json`, `Constants.swift`, or any station record.

### Session-owned candidate

A serialized experimental `RadioPlaybackSession` owns the active item identity, paired media/program clock, bounded feed history, selected occurrence, lyric resource, correction, transport state, and uncertainty reason. Browsing history for another station cannot replace its poller or publish into it. Reject callbacks from older sessions, items, occurrences, or resources at the final publication boundary. Disable parallel ACR title publication for the experimental session because a second stream connection is not its audio timeline.

Advance candidate eligibility from player media/program samples, not feed-poll callbacks or `Date.now`. Freeze through pause/stall. A missing program date, timing discontinuity, item change, or incompatible media jump invalidates the anchor. If alignment is unavailable, display that state, keep history browsable, and remove timed lyric highlighting instead of silently reverting to feed-top/wall-clock behavior while claiming alignment.

### Lyrics and correction

Use the candidate occurrence's lyric resource and current media position. Bar and live detail consume the same line index. Keep a recording-specific experimental correction separate from the frozen feed-to-program offset:

```text
lyricSeconds = candidateSongSeconds + recordingCorrection
```

Start correction at zero, hold it in memory, and reset it for a different occurrence/recording. Do not read, apply, or save the existing per-station lyric offset. A fuzzy lookup or mismatched recording remains uncertain; do not retune the station mapping to hide it.

### Pause behavior — reconnect only

The user explicitly wants **Reconnect on resume**, which matches the existing radio behavior: Pause tears down the item and ends its capture, invalidating the old generation. Resume joins from a new item and valid current clock; a new capture is a **separate** trace. Validate the fresh-generation title and lyric anchor after resume and reject late callbacks from the old item. Make the automatic export and its path conspicuous in the Debug UI so Pause does not appear to lose a capture. **Preserve buffer is not requested and is out of scope.** Do not change radio pause behavior outside the experiment.

## Scope

| Area | Files/modules and responsibility |
|---|---|
| Shared core | Consume the frozen `Packages/StreamSession` library from M11-A. Policy changes require a new labeled validation, not hidden app-only logic. |
| Configuration | **New** `PocketRadio/Services/StreamExperimentConfiguration.swift`. Off/observe/apply mode, exact endpoint, frozen policy, reconnect-only pause behavior, and in-memory correction; injectable store with no production persistence writes. |
| Player/session adapter | **New** `PocketRadio/Services/RadioPlaybackSession.swift`; focused changes to `PocketRadio/View Models/PlayerViewModel.swift`. Item generation, paired samples, lifecycle, endpoint override, candidate publication, and stale-callback rejection. Keep policy out of the large view model. |
| Feed adapter | **New** `PocketRadio/Services/RadioFeedClient.swift`; narrow changes to `APIService.swift` only where the experimental adapter needs stable occurrence/break/failure evidence. Serial active-session polling, distinct empty/failure/stale state, and feed publication before optional artwork enrichment. Legacy callers remain unchanged when off. |
| Lyrics | Narrow `LyricsService.swift` integration that exposes resource identity and lookup provenance. Reuse one resource/clock across experimental surfaces and keep correction isolated from saved offsets. No general catalog rewrite. |
| UI/output | **New** `PocketRadio/StreamExperimentView.swift`; focused `ContentView.swift` and existing Now Playing writer changes. Show mode, endpoint, paired clocks, feed top, candidate, uncertainty, selected occurrence, correction, and marker actions. No unrelated redesign or new artwork pipeline. |
| Recorder/replay | **New** `PocketRadio/Services/StreamExperimentRecorder.swift`. Reuse bounded/redacted trace primitives and add versioned decisions/annotations for the same player session. Replay through the M11-A core. Record no audio, full lyrics, credentials, signed query parameters, or device identifiers. |
| Tests/docs | Focused unit/integration/presentation/recorder tests, Xcode local-package wiring, `milestone_11b_handoff.md`, and a fresh attended experiment report. |

## Behaviors to test (red -> green, one at a time)

1. **Mode and endpoint isolation.** Off, unsupported stations, and podcasts retain existing URL resolution. Observe/apply use only the frozen KCRW endpoint for a fresh item. Spies prove there are no writes to station URLs, favorites, curated configuration, Supabase, or legacy lyric offsets.
2. **Session lifecycle.** Session/item generations reject late player, feed, artwork, and lyric callbacks. Station/podcast switches cancel work. Browsing another station does not replace active polling. ACR cannot overwrite the experimental candidate.
3. **Observe-only comparison.** Show legacy feed-top/wall-clock output and the frozen candidate against the same player item without publishing the candidate. Missing clocks/history show explicit reasons.
4. **Apply-candidate publication.** Menubar title, selected feed occurrence, live lyric resource, and existing system title consume one snapshot/revision. History stays in feed order and may select a row other than row zero. No broad artwork rewrite.
5. **Nonblocking feed lifecycle.** One in-flight request per active session; immediate startup fetch then bounded polling. Slow resource enrichment cannot delay occurrence selection. Failure, empty, stale, cancelled, and out-of-order results remain distinct.
6. **Reconnect pause path.** Pause teardown invalidates the item; resume creates a new generation and joins at the occurrence supported by its new clock. It never resumes the prior anchor or starts the current song at zero.
7. **Pause export visibility.** Tear-down finalizes the trace and sidecar with `item_teardown` before the old capture controls disappear. Prominently retain a completed-export status and path; do not leave the user thinking data were lost. A fresh resume capture must have a distinct item/generation. Mute remains separate and continues media progression.
8. **Lyric resource/correction isolation.** Late lookup results cannot populate another occurrence. Bar and live detail use identical lines/indices. Correction starts at zero, affects lyrics only, never touches selection/calibration, and never reads or saves legacy offsets. Repeat plays reset position even when reusing a resource.
9. **View lifecycle and historical lyrics.** Opening/closing the popover or live lyrics does not reset the session. Historical lyrics do not move the active anchor or gain live highlighting. Missing timing removes timed highlights without suppressing history.
10. **Same-player export and replay.** Capture configuration, sanitized endpoint, output-route category, paired clocks, transport, feed evidence, selection reason, correction, lyric-resource identity/timestamps, publication revision, and human markers. Raw observations and decisions replay deterministically. Limits and write failures produce an explicit incomplete export; files are owner-only and never overwritten.
11. **Reversibility/regression.** Turning off cancels experimental work, tears down its item, and restores existing URL resolution on fresh playback. Existing podcast, remote-command, KEXP, and unsupported-station tests pass without calibrated claims or default behavior changes.

## Execution and approval gates

1. Begin M11-B implementation after M11-A review. The frozen `+160s` values are staged only in Off / Observe mode; no Apply candidate or production policy is authorized.
2. Implement Off and Observe only first. Run unit/integration tests and inspect a **fresh same-player live trace** before enabling Apply candidate. A local synthetic recorder test does not satisfy the live evidence checkpoint.
3. Review observe-only evidence with the user. Enabling Apply candidate requires an explicit checkpoint, not merely a passing build.
4. Validate reconnect-on-resume and the automatic teardown export. Buffered pause is out of scope by user choice.
5. Freeze policy values and run the attended protocol below. Do not launch a live stream from automated tests.
6. Review title and lyric evidence separately. A successful experiment still requires separate commit, merge, default-endpoint, pause-semantics, and rollout decisions.

## Attended validation

Prerequisites: tests pass; capture is enabled; exact build/dirty state, endpoint, observable codec/rendition details, output-route category, mode, pause mode, and policy values are recorded; `caffeinate -is` is active; and no parallel probe/browser player is treated as the same audio timeline.

1. Start in Observe only. Verify that the AAC/HLS override is the active player item and that paired clocks and candidate decisions are plausible.
2. Run two fresh fixed-policy sessions with at least five identified song transitions each on the intended route. Exercise reconnect-on-resume in one and keep the other uninterrupted; a paused item and resumed item produce separate traces. Do not count missed markers, speech, or commercials as song starts.
3. Move to Apply candidate only after the explicit checkpoint. Mark every identified transition and any wrong-title interval.
4. For at least three songs with plausible matched synced lyrics, mark recognizable lyric landmarks and their lyric timestamps. Measure the zero-correction baseline before any adjustment. If suitable lyrics are unavailable, leave lyric validation incomplete.
5. Exercise close/reopen, browsing another station without playing it, live/historical lyrics, mute, reconnect, and station/podcast switching during a pending lookup. Treat network interruption, long pause, and route change as separately labeled recovery tests.
6. Replay the app export offline. Report title signed error, median absolute error, worst absolute error, unknown/stale intervals, excluded markers, discarded late results, and lyric-landmark error separately.

**Prototype targets:** zero mixed-occurrence or stale cross-session publications; zero selection/lyric advancement caused only by paused wall time; deterministic replay; no saved-setting changes; and every identified continuous-playback title transition within ±5s of its coarse marker. The lyric aim is ±2s only when recording identity and marker precision support that claim.

## Out of scope

- Default endpoint changes or persistence to favorite, curated, constants, or Supabase data.
- Production rollout, merge, or iOS port without later approval.
- Buffered/preserve-buffer pause; KEXP/MP3 calibration, ad recognition, audio capture/upload, or ACR alignment.
- Broad artwork, lyrics-catalog, podcast, UI, or repository refactors.
- Claims about unrecorded output routes or external displays.
