# M11 — KCRW playback-aligned tracklist and lyrics experiment

**Status:** Approved for offline validation, 2026-09-30. Planning and replay tests may start; no production endpoint change, app rollout, merge, or default behavior change is approved by this document.

**Goal:** Test whether KCRW's AAC/HLS program-date clock can select the track the listener has reached and drive its lyrics. Prove the selection rule offline first, then run it behind an explicit experimental control in the menubar app. Keep feed history, selected occurrence, and lyric position separate, and expose uncertainty rather than presenting feed-top as audible.

**User checkpoint:** Enable the KCRW AAC experiment on a recorded macOS output route. Hear at least five song changes per session, see the corresponding history row become selected, and compare the title and lyric highlights with the audio. Exercise both reconnect-on-resume and buffered pause. Browse another station and open/close lyrics without disturbing active monitoring. Export the app's own trace and replay the decisions offline. Disable the experiment without changing saved station URLs or lyric offsets.

## Evidence and constraints

- The [two attended sessions](../experiments/2026-09-26_kcrw_hls_attended.md) matched nine song changes at `programDate − playedAt = 158.863–163.171s`, including after 11s and 31s pauses. Start with **160s as an experimental parameter**, not a universal station constant or a proven lyric correction.
- The measured endpoint is `https://streams.kcrw.com/e24_aac/playlist.m3u8`. Neither MP3 nor another AAC variant inherits this calibration. The output route was not recorded; validate the intended route again.
- Cached feed entries arrived ahead of the corresponding audio. Feed receipt time and cache age describe availability, not when to switch titles.
- The s2 marker at 246.879s was a station ID, not the start of “Fools in Love”; the song marker was at 304.635s. The feed omitted the break. Ad recognition is not required and must not become a hidden acceptance condition.
- There are no measured lyric landmarks in these captures. A stable song-start relationship does not prove that the fetched lyrics represent the same recording or align line by line.
- [M10's handoff](milestone_10_handoff.md) remains authoritative for capture status and merge gates. This is a separate implementation slice, not an expansion of M10's observation-only scope.

### Verified menubar starting point

Source inspected at menubar `a995f06`; paths below are relative to `pocket-radio-menubar/`.

| Area | Current behavior | Required experimental change |
|---|---|---|
| `PocketRadio/View Models/PlayerViewModel.swift` | `startTracklist` owns one poller; selecting another stream pill replaces it even without switching playback | Keep active-session polling separate from browse/history requests |
| Same file | `refreshNowPlayingFromTracklist` immediately selects `tracklist.first` | Publish the media-clock-selected occurrence instead |
| Same file | Lyrics use `Date.now − playedAt + lyricOffset`; correction is saved per station to Supabase | Use a media anchor and an isolated, non-persisted experimental correction |
| Same file | Live-radio pause destroys the player item | Validate that existing reconnect path first; add an explicitly selected buffered-pause experiment |
| `PocketRadio/Services/APIService.swift` | `TracklistEntry.id` is a new UUID on parsing; breaks are discarded; failures become empty arrays; artwork lookups delay the feed result | Preserve stable occurrence evidence, break rows, and distinct failure/empty results; publish feed data before artwork enrichment |
| `PocketRadio/ContentView.swift` | Lyrics identifies the current song from row zero and artist/title; detail fetches lyrics separately | Select by occurrence; live detail shares the active lyric resource and clock; history stays historical |
| `curated_stations.json` in the shell repo, and `PocketRadio/Utils/Constants.swift` | KCRW defaults name `e24_mp3`; actual radio playback reads the station URL | Override only the explicitly enabled experimental session; do not rewrite defaults or favorites |

The nested menubar checkout currently has no `AGENTS.md` or Makefile. Follow the shell instructions and current milestone; do not assume those advertised files exist. Repository housekeeping is not a prerequisite for writing this plan.

## Proposed behavior

### One session owns the experiment

Create a serialized `RadioPlaybackSession` for the active experimental player item. Its identity includes station, selected endpoint, session ID, and item generation. A reconnect creates a new generation even for the same station. Its snapshot contains:

- feed history and freshness, independently of the selected occurrence;
- occurrence ID and revision, track fields, and associated artwork/lyric resource identity;
- transport state, sampled media time and program date;
- calibration version/value, timing validity, song position, and an uncertainty reason;
- lyric status and line index from the same resource used by live detail.

All experimental title, selected-row, live-lyric, and system Now Playing updates consume that snapshot. Browsing cannot replace its poller or publish into it. Reject late feed, artwork, and lyric results at the final publication boundary using session, generation, occurrence, and resource revision. Disable parallel ACR title writers for the experimental session; a second connection is not its audio clock.

### Select an occurrence, not a receipt

For a valid paired AVPlayer sample and this endpoint's experimental calibration:

```text
estimatedStart(entry) = entry.playedAt + feedToProgramOffset   // initially +160s
selected = latest unambiguous occurrence with estimatedStart <= playerProgramDate
songSecondsAtAnchor = playerProgramDate − estimatedStart(selected)
songSeconds = songSecondsAtAnchor + (currentMediaSeconds − mediaSecondsAtAnchor)
lyricSeconds = songSeconds + recordingCorrection              // initially 0s
```

The positive 160s value shifts the estimated start later. It is not added to lyric elapsed time. Increasing `recordingCorrection` advances lyric highlighting without changing track selection.

- Re-evaluate eligibility as the player clock advances, not just every 30s feed poll. A timer samples player position; it never accumulates elapsed seconds or substitutes `Date.now`.
- Keep every received occurrence within a bounded history, including explicit breaks. Do not assume the feed's five current rows cover a long buffered pause. If coverage is insufficient, show unavailable alignment rather than choosing the closest future row or retaining an old song forever.
- Prefer provider play IDs. Where KCRW supplies none, derive a deterministic key from station, source timestamp, kind, and original track identity. A repeat at another timestamp is another occurrence. A corrected timestamp is not automatically a new airing: reconcile only an unambiguous overlapping-history match; otherwise invalidate the selection and record the ambiguity. Album/art changes revise the resource without restarting the song.
- Retain the last good history on a failed request, but expose stale status. A successful empty response is distinct. Make history limits, source-freshness limits, and maximum unsupported occurrence age explicit policy inputs with boundary tests before live use; do not derive them from the 160s calibration. This prevents both wall-clock-driven song changes and indefinite stale selection.
- Freeze song/lyric position when media stops. Feed polling may continue during buffered pause, but new feed rows do not move the player clock. Evidence corrections may revise state with an explicit reason; polling is not a transition signal.
- A missing/non-finite program date or media time, a timing discontinuity, or a new item invalidates the anchor. Re-establish it only from valid paired samples and covered history. Detect jumps by comparing program-date progression with media-time progression, not wall time. An output-route change marks calibration unvalidated and requires a new attended check.
- When alignment is unavailable, show the station name or an explicitly stale last candidate, keep history browsable, and remove timed lyric highlighting. Never silently revert to feed-top or wall-clock lyrics while claiming experimental alignment.
- Preserve reported breaks but do not invent missing ones. During the unreported commercial the candidate may remain the preceding song; the experiment must not claim to have identified the ad. Lyric duration/last-line exhaustion may suppress highlights, but does not prove that speech or an ad is playing.

### Keep transport and correction changes reversible

Provide debug-only **Off**, **Observe only**, and **Apply candidate** modes. Both enabled modes explicitly select the measured AAC/HLS URL and display it before playback. Changing endpoint or mode starts a fresh item; it does not reuse a calibration from MP3. **Observe only** compares the legacy feed-top/wall-clock result and the candidate against the same player item. **Apply candidate** publishes the candidate snapshot.

Do not save the URL override to favorites, Supabase, `curated_stations.json`, or `Constants.swift`. Log the requested endpoint and any observable rendition/redirect details with URL redaction. Verify codec/bitrate information where available; the preference for high-quality AAC does not establish that every rendition is the highest available quality. Selecting a different endpoint requires a new measurement.

Keep **Reconnect on resume** as the initial pause behavior. Offer **Preserve buffer** only as a separately selected experimental pause mode after reconnect tests pass. In that mode, pause the existing item; if HLS window eviction or AVPlayer recovery jumps to live, invalidate and reanchor rather than pretending continuity. Provide a **Go live / reconnect** action. M11 does not change the default pause behavior for other stations or for experiment-off playback.

Leave existing saved station lyric offsets untouched and unused by the experimental calculation. Start `recordingCorrection` at zero, keep it in memory for the current occurrence/lyric resource, and reset it on a different occurrence or recording. Do not call the existing Supabase save path from experimental controls. Keep calibration adjustment separate and diagnostic-only. Record both values in the trace so a good-looking lyric result cannot conceal double compensation.

## Scope

Proposed new files are marked **new**. No code is created by this plan.

| Area | Files/modules and responsibility |
|---|---|
| Deterministic core | **New** `Packages/StreamSession/Package.swift`, `Sources/StreamSession/{SessionState,OccurrenceHistory,OccurrenceSelector,MediaClock}.swift`, and `Tests/StreamSessionTests/`. Foundation-only inputs/reducer/snapshots; no AVPlayer, networking, preferences, or account access. Inject all policy parameters. |
| Replay adapter | `Tools/StreamLab/Package.swift`; **new** `Sources/StreamLab/SelectionReplay.swift` and `Tests/StreamLabTests/SelectionReplayTests.swift`. Map existing raw events into the core and emit a separate candidate report. Preserve observation-only `replay` output and schema-v1 compatibility. |
| Fixtures | **New** `Packages/StreamSession/Tests/StreamSessionTests/Fixtures/` for synthetic relative-time scenarios. Use the retained attended traces as explicit-path offline validation inputs, not a test dependency on the parent shell checkout. Store marker classifications/provenance alongside validation expectations; never rewrite the original traces. |
| Feed adapter | `PocketRadio/Services/APIService.swift`; **new** `PocketRadio/Services/RadioFeedClient.swift`. Experimental serial 30s polling, five-entry KCRW response as captured, failure/empty/freshness evidence, history accumulation, and nonblocking enrichment. Legacy API callers retain existing behavior when the experiment is off. |
| Player adapter | **New** `PocketRadio/Services/RadioPlaybackSession.swift` and `StreamExperimentConfiguration.swift`; `PocketRadio/View Models/PlayerViewModel.swift`. Own lifecycle, paired samples, transport events, endpoint override, browse isolation, and snapshot publication. Keep policy out of the large view model. |
| Lyrics | `PocketRadio/Services/LyricsService.swift` plus session integration. Expose matched recording/resource identity and lookup provenance; distinguish exact and sanitized/search matches. Keep an experimental cache key that includes album/version. Use the same loaded resource for bar and live detail. Do not treat fuzzy-match success as verified recording alignment. |
| UI and system output | `PocketRadio/ContentView.swift`; **new** `PocketRadio/StreamExperimentView.swift`; existing Now Playing writer in `PlayerViewModel.swift`. Selected-row indicator by occurrence, explicit live-versus-history lyric modes, diagnostic controls, candidate/legacy comparison, and marker buttons. No unrelated redesign or new system artwork pipeline. |
| App capture | **New** `PocketRadio/Services/StreamExperimentRecorder.swift`. Reuse the `StreamDiagnostics` library's bounded/redacted raw trace facilities, not the capture executable or its separate player. Add a versioned decision sidecar keyed to raw session/event sequence for configuration, route, snapshots, and marker annotations. |
| Integration/tests | `PocketRadio.xcodeproj/project.pbxproj`; **new** `PocketRadioTests/StreamSessionIntegrationTests.swift`, `StreamExperimentPresentationTests.swift`, and recorder tests. Link local library products only. Inject feed/resource loaders, player samples, publication sinks, and settings stores. |
| Documentation | `Tools/StreamLab/README.md`, this milestone's future `milestone_11_handoff.md`, and a new attended report under `docs/menubar/experiments/`. Record commands, selected endpoint, policy values, decisions, and evidence limits as implementation lands. |

## Behaviors to test (red -> green, one at a time)

Each numbered behavior is a work unit. Paths refer to the scope table; use synthetic data and fake services unless explicitly running an attended validation.

1. **History identity and coverage — `OccurrenceHistory` + core tests.** Repeated polls preserve IDs; repeats remain distinct; explicit breaks survive; same-occurrence artwork revisions do not restart timing. Test unambiguous timestamp correction, ambiguous correction, empty response, failed request, out-of-order response, history eviction, and expiry. No random UUID-per-poll identity. Define and test bounded policy values here before the app adapter uses them.
2. **Media-clock selection — `OccurrenceSelector` + core tests; depends on 1.** An entry arriving 1–3 minutes early remains pending until `playedAt + 160s` is reached. Test equality at the boundary, just-before/after, multiple eligible entries, missing dates, initial join mid-song, and uncovered history. A sample at `playedAt + 190s` yields 30s song position, not 190s or 350s. Feed age affects availability, not the start calculation.
3. **Clock lifecycle — `MediaClock` + core tests; depends on 2.** Freeze through 11s/31.367s pauses and stalls. Wall-clock changes do not affect song position. Missing dates, backward/forward media jumps, item replacement, route invalidation, and HLS window loss remove the anchor. A valid reconnect joins at the current song position, not zero or the previous item's position.
4. **Deterministic evidence replay — `SelectionReplay` + its tests; depends on 1–3.** Feed events enter only when they were received; no future observations leak into earlier state. Replay twice and compare byte-identical decisions. For each of the nine annotated song changes, report the predicted selection transition and signed error against the marker. Do not require the new song at the exact marker sample: some observed media-date offsets are just below 160s. Preserve the annotations' uncertainty, including the three order-inferred s1 identities. Exclude the missed marker and commercial from song-start accuracy counts. Keep the commercial in the sequence and test that it is not labeled the Fools start. Use synthetic fixtures for CI; run both retained real traces separately.
5. **Session and endpoint isolation — configuration/session adapters + integration tests; depends on 1–3.** Opt-in KCRW uses the exact AAC endpoint. Off, other stations, and podcasts retain their current paths. Browsing another station does not cancel active polling. Station switches, reconnects, and stop reject old callbacks; mismatched endpoints cannot use the calibration. ACR cannot overwrite experimental selection.
6. **Nonblocking feed lifecycle — `RadioFeedClient` + integration tests; depends on 1 and 5.** One in-flight request per active session, immediate startup fetch, then 30s polling without cache-busting. Slow art lookup does not delay selection. Failure/empty/stale states remain distinct, and a cancelled or older response cannot roll history back. Popover visibility does not own polling.
7. **Two pause paths — session/`PlayerViewModel` integration tests; depends on 3 and 5.** Default experimental pause tears down and resume gets a new generation. Explicit buffered pause preserves the item and clock; feed polls cannot advance lyrics. Test mute separately: media and lyrics continue. Forced go-live, failed item, and window eviction reanchor; no default behavior changes outside the experiment.
8. **Lyric resource and correction isolation — `LyricsService`/session + integration tests; depends on 2–3 and 5.** Fetch completion uses the current media position, not request time. A late response cannot populate another occurrence. Bar and live detail use identical lines and indices. Experimental correction begins at zero, changes lyrics only, and never reads/applies/saves the legacy station offset. Repeat plays reset position even when a lyric resource is reused. Flag recording mismatch/uncertainty rather than automatically retuning the 160s parameter.
9. **One selected occurrence across displays — `ContentView`, `StreamExperimentView`, publication adapter + presentation tests; depends on 5–8.** History keeps its feed order, with selected occurrence identified even when it is not row zero. Menubar title and system title agree with that snapshot. Live lyrics follows transitions; opening historical lyrics neither moves the active anchor nor gains live highlights. Opening/closing views does not reset correction. Missing timing removes timed highlighting without suppressing history access.
10. **Same-player diagnostic export — recorder + recorder/replay tests; depends on 4–9.** Capture paired clocks, transport, feed evidence, selection/reason, calibration, correction, lyric resource/line timestamp, and publication revision. Marker actions identify heard change, lyric landmark, and wrong title/line; later annotation can distinguish speech or a missed marker. Raw trace plus sidecar replay offline. Old raw traces still replay. Limits/write failures produce explicit incomplete exports; files are owner-only and never overwritten. No audio, credentials, full lyrics, signed URL parameters, or device identifiers are recorded.
11. **Reversibility/regression — integration tests; depends on 5–10.** Turning the experiment off cancels its tasks and pending saves, tears down its item, and restores original URL resolution on fresh playback. Use spies to prove no writes to station URLs or existing lyric-offset storage. Run existing podcast/remote-command tests and check KEXP/unsupported-station legacy behavior without claiming their timing is calibrated.

Items 1–4 precede app integration. Work on independent fake adapters/tests may run in parallel after the core contract is fixed; only one implementation owner should edit `PlayerViewModel.swift` at a time. Give a sub-agent the Goal, relevant Scope rows, assigned behavior, and its dependency results—not an unbounded cross-platform refactor.

## Execution and approval gates

1. **Finish M10's commit/push checkpoint.** Attended KEXP capture/replay is complete and commit/push approval was received on 2026-09-30. Do not move `current_milestone.md` yet, and do not merge without separate approval.
2. **Establish the M11 work branch when implementation starts.** Use menubar `feature/stream-session-model` from updated `main` after approved Stream Lab integration. Keep shell plan/report changes in the shell repo and app/package changes in the nested repo. Repoint the milestone symlink only when M11 becomes active; never write through it.
3. **Run offline behavior tests and retained-trace validation.** Complete 1–4. Record the selected IDs and all nine marker residuals, the missed marker, the commercial interval, and both pauses. Fit/check alternatives offline without treating the same training captures as independent proof. Freeze the candidate configuration before the next attended session.
4. **Build the opt-in app path.** Complete 5–11. Use the existing `make menubar-test` and `make menubar-build` entry points; add the new package test command to the runbook. If adding build targets, put new implementation logic in a menubar Makefile and delegate from the shell rather than expanding its legacy inline recipes. Do not launch a live stream as part of automated tests.
5. **Run the attended protocol below.** Start with observe-only on the actual AAC item. Move to apply-candidate after checking endpoint, clocks, and plausible selections. Do not change policy values mid-session; log and start a separately labeled run if tuning is needed.
6. **Review evidence with the user.** Report title alignment and lyric alignment separately. Decide whether to revise the model, collect more evidence, or approve a later default-endpoint/rollout change. M11's success does not itself authorize a production default switch, commit, merge, or iOS port.

## Attended menubar validation

Prerequisites: offline tests pass; the user approves audible playback; capture is enabled; build/dirty state, exact endpoint, output route category, pause mode, and all policy values are recorded. Keep `caffeinate -is` active and inspect the exported clock-gap report. Do not run a separate probe or browser player as if it represented this audio timeline.

1. **Observe the same player's two predictions.** Show feed top, candidate, legacy title/lyric position, paired clocks, and alignment status in the diagnostic panel. Confirm the AAC override actually feeds the active item. Record observable codec/rendition details without assuming quality from the URL alone.
2. **Mark at least five identifiable song transitions per session in two fresh sessions on the intended route.** Use one session for reconnect-on-resume and one for buffered pauses of about 11s and 31s. Do not count a missed transition or commercial as a song start. Keep policy fixed across these holdout sessions.
3. **Mark lyric landmarks separately.** For at least three songs with a plausible matched lyric recording, annotate recognizable lines and their lyric timestamps. Record baseline error with zero recording correction before nudging it. If suitable lyrics are unavailable, leave lyric validation incomplete rather than inferring success from title timing.
4. **Exercise lifecycle changes.** Close/reopen the popover, browse another station without playing it, enter/leave live lyrics, open historical lyrics, mute, reconnect, and switch station/podcast during a pending resource lookup. Brief network interruption and a long/window-expiring pause test fallback and recovery, not just the happy path. Repeat route changes as a separately labeled validation, not a transfer of the original calibration.
5. **Replay the exported app session offline.** Compare candidate decisions with the recorded snapshots. Report signed marker error, median absolute error, and worst absolute error for title transitions; report lyric-landmark error separately. Also report unknown/stale periods, lookup delays, discarded late results, and all excluded markers. Human reactions and sampling limit precision.

**Proposed evaluation targets:** zero mixed-occurrence or stale cross-session publications; zero song/lyric advancement caused solely by a paused wall clock; deterministic replay; and no saved-setting changes. For continuous calibrated playback, aim for every identified title transition within ±5s of its coarse human marker in these holdout sessions. This is a prototype gate, not sample-accurate ground truth. Aim for lyric landmarks within ±2s on a matched recording, but only claim that result when marker precision supports it. If title timing passes and lyrics fail, investigate recording identity/correction separately; do not tune the station mapping to conceal a lyric mismatch.

A default rollout needs a separate user decision on endpoint, pause semantics, calibration/fallback limits, and migration (if any) of legacy offsets. Record results in a new experiment report and execution status in `milestone_11_handoff.md`.

## Out of scope

- Changing default station endpoints, shared curated configuration, favorite rows, or saved Supabase lyric offsets during M11.
- Automatic ad recognition, audio capture/upload, ACR alignment, stream proxies, custom decoders, or guaranteed lyric precision from station timestamps.
- KEXP calibration, MP3 calibration, iOS/background/Bluetooth/CarPlay parity claims, or a console port. M10 still owns KEXP observation; other routes/platforms need their own later measurements.
- A general lyric-catalog matching rewrite. Preserve recording evidence and expose mismatch in this experiment; improve search/ranking separately if it blocks validation.
- A new system-artwork pipeline, unrelated podcast/UI refactors, broad repository cleanup, or automatic branch/commit/merge actions.
