# KCRW/KEXP stream monitoring: review and proposed event model

**Recommendation:** develop and measure the timing model on macOS first, using the menubar app's Swift/AVPlayer stack. Make the playback session—not a screen—the owner of current-track state, timing, lyrics, and artwork. All displays should consume the same versioned snapshot. Add a bounded diagnostic trace before changing stream transport or trying to replace manual lyric correction with a fixed delay. Validate iOS publication and output-route behavior separately.

**Scope:** iOS working tree at `aeef76a7c`, reviewed 2026-09-16; follow-up source comparison with menubar `a995f06` and console `de2014d`. This is a proposal, not an approved milestone or an implementation. Source locations below are relative to `pocket-radio-ios/` unless another project is named. Existing unrelated working-tree changes were left untouched. The menubar and console checkouts currently lack the `AGENTS.md` files advertised by the root instructions; their current milestones were read, and no app source was changed.

**Evidence limits:** findings below come from source inspection and one read-only fetch of each station's public tracklist. No listening session, device reproduction, build, or test suite was run. The code explains several failure paths; it does not establish which caused a particular listening incident.

## 1. What runs today

There is no single extended-stream monitoring loop:

```text
AVPlayerItem timed metadata
  → RadioMetadataObserver → radioStationNowPlayingDidChange
      → PlaybackManager: system title/artist/album + artwork resolution
      → full/mini player: independent artwork resolution
      → station detail: labels + tracklist fetch after 2 seconds

RadioPlaybackStarter → optional one-time tracklist prefetch
StationDetailViewController → immediate fetch, then every 30 seconds
  → RadioTracklistService cache + radioTracklistDidRefresh
      → PlaybackManager: system artwork, NOT system title
      → full/mini player: artwork; full player also reads feed-top title
  → station detail: table, lyrics for feed-top song,
                    system title if its local top-song key changed

Station detail → LyricSyncController: wall-clock timer
Full-screen lyrics → separate wall-clock timer for a fixed entry
```

The regular feed polling stops when station detail disappears. Its ICY notification observer remains registered, however, and can start a new fetch while that controller is hidden but retained. Thus even hidden-screen behavior depends on navigation history.

Tracklist rows load each entry's artwork URL directly. Player artwork takes a separate selection, lookup, caching, and publication path. A correct image in the table does not prove that the player selected or published that entry.

Sources: `Radio/RadioPlaybackStarter.swift:55`, `Radio/StationDetailViewController.swift:199–225,362–380,453–476`, `Radio/TracklistCell.swift:97–118`, `PlaybackManager.swift:524–594`.

## 2. Findings

### High: the screens disagree on which song is current

- System metadata uses ICY title, but fills missing artist/album from the cached **top** feed entry without checking whether it is the same song. This can assemble fields from two songs (`PlaybackManager.swift:530–542`).
- Full-player labels use the cached feed top, even when the notification contains a newer ICY title (`NowPlayingPlayerItemViewController+Update.swift:279–297`).
- `TrackArtworkResolver.bestResolveEntry` chooses the feed top when ICY does not match any cached entry. A valid new title can therefore get the previous song's cover (`Radio/TrackArtworkResolver.swift:105–126`).
- A tracklist refresh updates system artwork but not system title through `PlaybackManager`. The feed-based title fallback lives in station detail instead (`PlaybackManager.swift:548–552`; `Radio/StationDetailViewController.swift:453–476`).

**Impact:** stale titles, mixed title/album/art, and different answers between the phone and car. There is no continuous feed fallback independent of screen lifecycle. Thirty-second polling adds detection delay while active; minutes-long errors require examining feed delay, missing polling/metadata, buffering, or stale state—not merely changing that interval.

### High: system artwork can be overwritten and then deduplicated out of recovery

A full Now Playing rebuild preserves song text but unconditionally installs baseline station artwork (`NowPlayingHelper.swift:57–74,105–132`). `PlaybackManager.lastResolvedRadioKey` then suppresses another resolve for the same station/artist/title (`PlaybackManager.swift:564–566`).

The key is recorded **before success**, excludes artwork URL/revision, and has no reset elsewhere in this file. Consequently:

- A later full rebuild can replace a valid cover with the logo, with no same-song restoration.
- A failed lookup/download suppresses same-song retries.
- Artwork arriving later for the same song can be ignored.
- Returning to the same station/song can reuse a stale deduplication decision.

The final image-download publication also lacks a current-session/current-episode check at the point it writes. Switching to a podcast during an outstanding download can allow old radio artwork to publish (`PlaybackManager.swift:578–593`).

**Impact:** a direct code-level explanation for correct table art but incorrect lock-screen/Bluetooth/CarPlay art. Actual head-unit receipt/rendering still requires physical testing.

### High: lyrics use broadcast wall time, not playback position

The effective calculation is:

```text
lyric position = Date.now − feed.playedAt + saved station offset
```

There is no audio-position anchor or response to stalls, pauses, reconnects, inserted ads, or route changes (`Radio/LyricSyncController.swift:89–95,144–150`). A station timestamp need not be the exact song boundary heard on this device. A saved station offset cannot represent every session, output route, or recording version.

`RadioMetadataObserver` receives timed groups but discards their time ranges and item identities when emitting artist/title/album (`Radio/RadioMetadataObserver.swift:41–51,116–139`). Even those timing observations are unavailable downstream.

**Impact:** making the timer faster cannot fix the underlying clock mismatch. Depending on the error source, lyrics can lead or lag the audio.

### High: full-screen lyrics introduce a second clock and an offset-reset bug

Station detail captures elapsed time when a row is tapped. Full-screen lyrics later reconstructs its start date as `Date.now − initialOffset`, after navigation/fetch delay. That delay becomes additional lyric lag (`Radio/StationDetailViewController.swift:586–590`; `Radio/LyricsViewController.swift:298–309,373–379`).

Meanwhile, pushing that screen calls station detail's `viewDidDisappear`, which stops and resets `LyricSyncController`, including setting its offset to zero. The full-screen view retains the previously copied offset, but its buttons call the reset controller. For example, a copied −42-second correction can become +1 after pressing `+`, rather than −41. A subsequent hidden-controller metadata fetch may change this state again.

Full-screen lyrics also retains a fixed entry and `isCurrentSong` flag; it does not follow a new track or a playback pause.

Sources: `Radio/StationDetailViewController.swift:205–214,602–604`; `Radio/LyricSyncController.swift:128–129,172–185`; `Radio/LyricsViewController.swift:11–14,270–278`.

### Important: breaks, repeat plays, and late corrections are lost

- Ad/break metadata returns `nil` rather than emitting a non-music transition. Feed parsing drops KCRW breaks and KEXP non-track plays. Empty feed results do not clear the shared cache. The previous song can remain current during speech or ads.
- Lyric identity is only artist/title. Loading the same key returns immediately, ignoring a corrected start timestamp or a distinct repeat play.
- Feed fetches can overlap between polling, metadata-triggered fetching, and prefetch. The cache has no request sequencing or source revision check to prevent a late older response from replacing a newer one.
- Lyric album-field writes have no active-station guard. Browsing another station can write its lyric into the current system item. CarPlay suppresses lyric writes, but ordinary Bluetooth does not.

Sources: `Radio/RadioMetadataObserver.swift:65–89`; `Radio/RadioTracklistService.swift:88–103,140–149,179–186`; `Radio/LyricSyncController.swift:54–57,132–134`; `Radio/StationDetailViewController.swift:619–620`; `NowPlayingHelper.swift:243–252`.

### Important: lookup success is not necessarily the correct recording

Lyrics lookup strips qualifiers including “live,” “remix,” and “edit,” then accepts the first search result with synced lyrics. It does not verify recording/version or duration, and its cache key excludes album/version (`Radio/LyricsService.swift:30–50,79–93,109–136,182–184`). Some apparent timing errors may be the wrong lyric timeline, which no constant offset can repair.

Artwork fallback similarly accepts the first iTunes result. The shared resolver has one global current request key, rather than independent/coalesced requests per resource. An unrelated lookup can suppress an active caller's completion (`Radio/TrackArtworkResolver.swift:30–34,72–93,150–176`).

### Additional diagnostic checks

- Confirm metadata attachment on every load path: `DefaultPlayer.swift:128` tests `episode as? RadioStation`, whereas registry-based radio detection elsewhere explicitly supports database `Episode` shims. This is a coverage risk, not a measured failure here.
- Record actual resolved stream URL and transport. Historical notes describe KCRW HLS delay, but current curated configuration stores radio-browser UUIDs, not a fixed transport. Do not hardcode an old −42-second observation.
- Preserve the existing radio-neutral playback effects and tap bypass. The recent [radio speed investigation](../../bugs/bug_3.md) and shelved stream-loader experiment are reasons not to change audio plumbing before measuring it.

## 3. Proposed event model

### One playback-session owner

Introduce a `RadioPlaybackSession` coordinator, serialized on one actor/executor. Start it with the actual player item and stop it on item teardown. Reconnection creates a new generation even for the same station.

Screens subscribe to state; opening a tracklist or lyrics view must not start, stop, or redefine the playback monitor. Browsing another station may fetch its history, but cannot publish into active Now Playing.

Suggested identity and state:

| Field | Meaning |
|---|---|
| Session ID + item generation | Reject work from a previous connection/player item |
| Station ID + resolved endpoint | Distinguish stream variants and transport behavior |
| Track occurrence ID | One airing, not just artist/title; use provider play ID/start evidence where available |
| Revision | Increases for every accepted state change |
| Content state | Unknown, music, speech/break, advertisement |
| Transport state | Connecting, playing, waiting/stalled, paused, stopped |
| Track fields + provenance | Identity, album, art, and which observation supplied each field |
| Timing anchor + confidence | Song-relative position tied to player media time; known, estimated, or unavailable |
| Artwork/lyrics state | Pending, ready, unavailable, failed; resource identity and retry eligibility |

Do not conflate content and transport: music can be paused; an ad can be playing.

### Events in, snapshots out

| Event | Required behavior |
|---|---|
| Session/item started | New generation; station fallback; attach metadata; immediate feed fetch |
| Timed metadata observed | Preserve identifier, raw payload, group media time, receipt time; classify music/break/ad/unknown |
| Feed response observed | Preserve request ID, receipt time, provider timestamps/IDs, and freshness; update history independently of current-track selection |
| Current occurrence changed | Publish new title/artist with station-logo fallback immediately; start matching art/lyrics work |
| Artwork/lyrics resolved | Accept only for matching session, occurrence, and resource revision; publish a new snapshot |
| Player position/state changed | Advance from media position, not timer invocation count; stop advancing when media stops |
| Discontinuity/reconnect/route changed | Invalidate or re-estimate timing as appropriate; never silently reuse a known-invalid anchor |
| Metadata timeout/network failure | Mark uncertainty/staleness; bounded retry/backoff; do not silently call old data fresh |
| Screen attached/system rebuild | Render the latest complete snapshot; do not restart lookups or reset valid art |
| Session stopped | Cancel work and reject late events at the final publication boundary |

The coordinator is the only authority for selecting the current occurrence. A separate Now Playing adapter is the only radio writer to `MPNowPlayingInfoCenter`. Full player, mini player, live lyrics, and that adapter consume the same snapshot. History rows remain historical records; highlight the selected occurrence rather than assuming row zero is audible.

Artwork resolution happens once per resource, with shared results and bounded retry. A song change clears old cover art immediately; a same-song refresh keeps valid art until a replacement is ready. A system rebuild republishes the selected image, not the logo.

### Reconcile evidence instead of “last writer wins”

1. Player-timed metadata is useful identity evidence, but its alignment and semantics must be measured for each stream. A periodic ICY frame is **not automatically an exact song-start marker**.
2. Match feed enrichment to the selected occurrence. Never borrow album/art from an unrelated feed-top song.
3. A feed-top change can create a candidate or low-confidence fallback. Do not immediately replace reliable player-aligned evidence with broadcaster live-edge data that may be ahead of buffered audio.
4. Preserve break/ad events. A feed airbreak is still broadcast-side evidence; it must not clear a song early if this listener is behind the live edge.
5. Track request ordering, freshness, and provider corrections. An identical artist/title with a new occurrence or corrected timestamp is not a duplicate event.
6. If evidence conflicts, expose that conflict in the trace and mark confidence honestly. Define station-specific fallback/expiry policy from captures, not a universal “newest timestamp wins.”

### Lyrics need an audio anchor

Preferred calculation, once a valid anchor exists:

```text
song position = song position at anchor
              + (current player media time − player media time at anchor)
```

A UI timer merely samples that position. Pauses/stalls no longer advance lyrics. A media-time discontinuity requires a new mapping. Keep wall time for comparing provider timestamps; use monotonic time for elapsed diagnostics so wall-clock corrections do not move lyrics.

Potential anchors, strongest available first:

- Verified stream timing metadata/program-date mapping that actually identifies song position.
- Recognition/alignment of the **same audio timeline the player is consuming**, if a supported, reliable capture path is available.
- An explicitly estimated feed-time mapping with measured delay and uncertainty.

Joining mid-song cannot be solved by starting the song clock at the first ICY callback. Output-route latency is another calibration boundary: measure its relationship to player time and avoid applying latency compensation twice.

The existing `ACRFingerprinter` does not solve this. It opens another stream connection, returns identity/confidence only, and adds a history row dated at recognition completion. A second connection can hear another buffer position or another ad (`Radio/ACRFingerprinter.swift:64–86,150–165`; `Radio/StationDetailViewController.swift:431–450`). Provider position fields and same-session audio capture would need investigation before implementing alignment.

**Limit:** neither a late/manual playlist timestamp nor a title-only ICY frame guarantees lyric precision. Keep manual correction as a diagnostic/fallback until automatic anchors are validated. Prefer unsynced lyrics to confidently highlighting the wrong line. Separate session/route delay from recording-specific lyric correction; do not persist them as one universal station offset.

## 4. Validation plan

### A. Add an opt-in stream diagnostic mode first

Use structured, bounded JSONL events plus an on-screen summary/export action. Existing `Lyrics` logs report fetches and offsets, but metadata selection, feed timing, artwork decisions, and final publications currently lack a correlated trace. Simply turning up existing logging is insufficient.

Every event should carry sequence number, monotonic elapsed time, UTC time, session/item generation, station, occurrence, revision, event type, and reason. Record:

- Build identifier, stream endpoint/transport, actual playback rate, output route and available latency estimates. Redact signed URL parameters and device identifiers.
- Metadata attach/detach; item identifiers, raw/sanitized frames, group time ranges, arrival media position; accepted/rejected decisions, including duplicates and breaks.
- Feed request/response timing, status/cache headers, provider timestamps/IDs, candidates, selected match, and freshness. Retain bounded response fixtures in capture mode.
- Player media position sampled about once per second; state changes, waiting reason, buffer ranges, stalls, interruptions, route changes, and reconnects.
- Lyric lookup match/version/duration, anchor source/confidence, calculated song position, line index, and offset changes. Do not log full lyric text by default.
- Artwork candidate, request/result, resource hash, retry/deduplication decisions, and discarded stale completions.
- Every radio UI render and every system Now Playing write, including full rebuilds: revision, track ID, art hash, and writer. Instrument competing legacy writes while diagnosing them.

Add **Heard song change**, **Lyrics match here**, and **Wrong artwork now** markers. These are coarse human observations, not subsecond ground truth. Keep debug work off the audio render thread, rate-limit events, rotate files, and make export explicit. Do not log credentials, auth headers, or unrelated account data.

**First device sessions:** use a known build, play each station through at least five transitions on the speaker, then repeat on Bluetooth and CarPlay. Include leaving detail, opening live lyrics across a transition, a 15-second pause, mute, an interruption, network loss/recovery, and a station/podcast switch during an art fetch. Observe ad/break transitions when they occur.

### B. Deterministic event replay

Inject clock, metadata/feed source, artwork and lyrics loaders, and publication sinks. Replay captured events without real services, account state, or `UserDefaults.standard`. Assert the snapshot sequence, not just individual parser outputs.

Minimum regression scenarios:

1. ICY says B while feed still says A; no B-title/A-cover combination.
2. Feed says B before buffered audio reaches B; preserve the audible occurrence.
3. Correct cover → full system rebuild; cover survives.
4. Cover missing/fails, then arrives for the same song; recover.
5. Delayed A result after B, a podcast switch, or same-station reconnect; reject it.
6. Older feed request completes last; cannot roll state back.
7. Pause/stall; song position and lyric line stop advancing. Reconnect reanchors.
8. Open/close full-screen lyrics; no timing jump and no offset reset. Live mode follows the next occurrence; explicitly selected historical lyrics remain historical.
9. Break/ad, empty feed, missing metadata, same song repeated, corrected start time.
10. Wrong recording/version; refuse high-confidence synced display.
11. Detail never opened, detail closed, and background playback; monitoring behavior is equivalent.
12. Another station's history/art lookup cannot change active playback.

Existing tests cover metadata/feed parsing, artwork fallback selection, and lyric lookup helpers. No tests were found for the coordinator behavior above, `LyricSyncController`, or the two lyric-screen clocks. Some current tests explicitly require feed-top fallback on ICY mismatch; those expectations must change with the new policy.

### C. Record/replay audio where it adds evidence

Use two distinct approaches:

- **Local transport fixture:** audio plus ICY/ID3 events, media offsets, original feed responses, and their response timing. Serve through a local HTTP fixture with controllable delay/stalls. Preserve ICY interleaving for Icecast, or playlists/segments/timed metadata for HLS. A plain MP3 loses this evidence. Run synthetic/rights-cleared fixtures in automated tests; retain short real captures locally, not in git.
- **Audible-output reference:** a timestamped capture of what the tested output actually played, with a shared sync marker and a video/trace of the UI. This validates speaker/Bluetooth/CarPlay delay. A parallel upstream download does not prove what the iPhone heard; screen recording alone may not capture routed audio faithfully.

Start with passive tracing, not a new production stream loader. A development proxy can later capture what the app consumes, but may itself change buffering; compare against an unproxied session. Keep real audio capture bounded, opt-in, local, and compliant with applicable permissions/terms. Do not upload it for recognition without an explicit design decision.

### D. Report separate error measurements

Measure separately:

- Audible boundary → selected song change.
- Selected occurrence → image readiness → per-surface publication.
- Publication → actual external-display change, where observable.
- Audible lyric landmark → highlighted lyric timestamp.
- Feed publication/receipt lag and player/route delay, rather than one combined “offset.”

Proposed initial targets, subject to baseline measurement:

- Zero mixed-occurrence snapshots or stale cross-session writes in replay.
- All app surfaces consume the same revision within one render cycle; system metadata is written promptly from that revision. This is not an acknowledgement from a car display.
- With a verified timing source, target song changes within 2 seconds and lyric landmarks within 1–2 seconds of audible output. Report distribution and worst case, not only averages.
- With weak/missing timing evidence, report confidence and unsynced fallback instead of claiming that accuracy.

## 5. Where to build the test bench

**Use the menubar stack as the primary timing lab; borrow the console's testable engine structure. Do not revive the whole TUI just for this investigation.** A small Swift command-line runner is also viable: terminal presentation does not require changing from AVPlayer to mpv.

| Choice | Verified starting point | Trade-off |
|---|---|---|
| Menubar / small macOS Swift runner | Swift + AVPlayer; existing lyrics, tracklist, and system Now Playing code | Closest path back to iOS; easier long captures and local fixtures. AVPlayer remains an opaque audio pipeline, and macOS timing is not identical to iOS timing. |
| Existing console engine | Go `Engine`, `NowPlaying` snapshot subscriptions, injected player/tracklister/clock, fake player, mpv IPC metadata events and integration tests | Good headless experiment framework, but mpv has different buffering and metadata behavior. No lyrics implementation was found; console M5 explicitly leaves lyrics/ACR to M6. |
| iOS | Actual target output routes and UI lifecycle | Required for final validation, but not the fastest place to iterate on recorder/replay tooling. |

The menubar app is **not already a timing reference**:

- `PocketRadio/View Models/PlayerViewModel.swift:502–547` polls the feed every 30 seconds and selects its top song.
- `:561–618` uses the same `Date.now − playedAt + offset` lyric model. No timed-metadata observer was found in the menubar source sweep.
- `:456–467` starts a new tracklist poller when a different stream pill is selected, replacing the existing single poller even before playback changes. A new monitor must separate browsing from playback there too.
- `PocketRadio/Services/TrackFingerprinter.swift:113–141` opens a separate stream connection, just like iOS. Moving to macOS does not make that a same-audio timing anchor.
- `PlayerViewModel.swift:1617–1650` publishes system text/rate but no track artwork, so it cannot reproduce the complete iOS artwork path unchanged.

The console is closer to the proposed *structure*, not the desired *correctness*. `internal/library/engine.go:592–603,789–793` lets both feed and ICY overwrite the title without reconciliation. `internal/player/mpv.go:242–248` can silently drop events when its channel is full. Diagnostic capture must preserve critical raw events or explicitly count losses rather than treating that channel as a lossless recorder.

### Suggested macOS deliverable: Stream Lab

Keep the first version independent of account/favorites sync and normal UI navigation:

1. Choose an explicit station endpoint and feed endpoint. Match the iOS stream variant rather than assuming station names imply identical audio.
2. Run an AVPlayer adapter that emits metadata, media-time, and transport events into a small UI-independent Swift state engine.
3. Show a diagnostic panel or terminal view: audible-track candidate, feed-top candidate, confidence, lyric position, artwork identity, buffer state, and trace markers.
4. Export a bounded session bundle containing trace, feed responses, resource metadata, and optional explicitly enabled audio reference.
5. Replay it with a virtual clock and controllable service responses. Reproduce late/out-of-order data without waiting for another real song change.

Put the selection/timing rules in a Foundation-only Swift module with injected clocks/services, rather than adding another subsystem to the large `PlayerViewModel`. If the experiment succeeds, package that core for menubar and iOS; keep AVPlayer/UI/system-publication adapters platform-specific. A language-neutral trace schema also lets a later Go/mpv comparison consume the same scenarios without requiring a shared Go runtime on iOS.

Use the console/mpv path as an **optional independent comparison** when asking whether an observed delay is specific to AVPlayer. Identical upstream fixtures are useful for that comparison; two simultaneous live connections may get different ads and are not automatically equivalent. Do not port an mpv-measured constant into AVPlayer.

## 6. Recommended sequence

1. Build the small macOS tracing/replay lab on the menubar AVPlayer stack. Establish a baseline for each explicit stream variant; do not change transport while measuring it.
2. In parallel or next, add minimal iOS tracing and failing regression tests for the artwork rebuild and lyric-navigation defects. Fix those locally without waiting for automatic audio alignment.
3. Prove the session-owned snapshot model in the lab, with continuous, single-flight feed monitoring, event-driven refresh, bounded reconciliation retries, and periodic fallback while playback is active. Screen visibility must not control this service.
4. Use paired trace/audio evidence to choose per-transport timing anchors and improve recording matching. Replay race/failure scenarios deterministically.
5. Bring the tested core/adapters to iOS and validate background behavior, Bluetooth, and CarPlay on the pinned physical device. macOS results do not establish external-display delivery or iOS audio-session behavior.
6. Hide routine `+ / −` controls only after multi-session, multi-route validation meets the timing target. Retain a diagnostic correction path.

## Appendix: public feed spot check

At approximately `2026-09-16T23:24:02Z`, the configured endpoints returned:

- KCRW: a flat array with `datetime`, nullable artwork fields, and `Cache-Control: max-age=15, public, must-revalidate`.
- KEXP: a `results` array with stable play IDs, `airdate`, track plays, and an intervening `airbreak`. The current parser drops the IDs and airbreaks.

This confirms useful evidence is available to retain. It does **not** measure either feed's lag against audio: the age of a top row may simply be the time the current song has already played. Temporary response/header files are in `/tmp/pocketradio-stream-review.mkT7IM`; they are not durable fixtures.
