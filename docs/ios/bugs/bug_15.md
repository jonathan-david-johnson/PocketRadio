# Bug 15 — KCRW HLS audio stalls on Bluetooth and the iPhone speaker

**Status:** Open. Cause found and recorded in [ADR 0011](../adr/0011-kcrw-hls-pins-each-session-to-its-server.md): `streams.kcrw.com` rotates between two servers in DNS, each session lives on one, and AVPlayer's new connections can reach the other, which answers segments with `404`. A Debug-only fix that pins the session to its server is committed at iOS `56a7ecf21` and played about 21 minutes on the phone's speaker with no stall. The user selected this pin-and-backstop path for Release on 2026-10-29, after the remaining routes pass: Bluetooth, wired CarPlay and locked/background playback. The code remains Debug-only until that separate change is tested and approved.
**Environment:** Jonathan iPhone (iPhone 15), the previously tested build corresponding to iOS `eba2c9977`, `experiment/unified-skew`. Alignment On, Auto anchor Off, KCRW skew 155.6 s. Bluetooth output: IONIQ 5. Wired CarPlay has not been validated. The logs identify cellular streaming; they do not establish continuous media-server reachability.
**Related:** [ADR 0007: live-radio stall recovery without seeking](../adr/0007-live-radio-resumes-after-a-stall-without-seeking.md), [ADR 0004: KCRW playback clock](../adr/0004-kcrw-playback-clock-on-ios.md).

## Cause and current experiment — 2026-10-28

ADR 0011 has the measurements. In short: DNS for `streams.kcrw.com` returns one of two servers (30 s cache, changing between lookups). The session ID names its server. AVPlayer opens new connections every 25–100 s and on Wi-Fi/cellular changes; one made after DNS has changed reaches the other server, and AVPlayer logs `-12889` within milliseconds. KCRW's own iOS app plays a single direct stream; the web player keeps one connection busy.

**Phone run of the replacement backstop (15:30–15:36):** four replacements, each about 7 s of silence and about 7 s skipped, no replay. Each new session lost its loader again within 40–90 s, so replacement alone is not a fix. A later run (16:22–16:27, Wi-Fi then cellular) was captured on the wire and showed the reconnect-to-the-other-server sequence above.

**Fix (committed at `56a7ecf21` on `experiment/unified-skew`, Debug, KCRW HLS only):**

- `KCRWSessionPinning` serves the master playlist through a resource loader and rewrites its variant URL to `http://<owning server>/…`. It logs `[pin]` lines, never the address or session.
- `LiveLoaderWatchdog` and `KCRWLoaderRecovery` remain as a backstop: replace the item when the loaded end hasn't grown for 20 s while playing, at most once per 60 s and three times per play.
- `MediaStallDiagnostics` logs each new AVPlayer error event once, with its comment redacted.

Verification: 135 tests passed across `KCRWSessionPinningTests`, the backstop tests, `MediaStallDiagnosticsTests`, `StallRecoveryTests`, `RadioPlaybackSessionTests`, `AlignedNowPlayingTests` and `KCRWEndpointResolutionTests`. On the Mac, the app's loader file played 2.5 minutes with the variant pinned, the program date present and no errors. `make build_device` succeeded.

**Phone runs with pinning:** 2026-10-28 at 19:09 (Wi-Fi, 3 min) and 19:13 (cellular, 6 min, with a pause and resume), and 2026-10-29 at 05:51 (12 min, switching from Wi-Fi to cellular while playing). Each logged `[pin] variant pinned`. There were no AVPlayer errors, stalls or `[recovery]` lines, and the buffer stayed at 107–122 s. The user heard no drops.

**Next:** the route checks in M14 14.4 on this build, starting with Bluetooth.

## User observations

- Initial speaker check: title, artwork and lyrics changed at the appropriate time or within a couple of seconds. This was a short qualitative check, not a sustained-playback pass.
- Bluetooth: “Moving to L.A.” by Art Brut appeared about 20 s after the audible song began. The next song, “Mama…”, appeared on time, but audio became silent for over a minute. Control Center showed Pause bars and IONIQ 5 as the output. The user subsequently stopped playback.
- Speaker control run: audio dropped around 18:21 and returned without user intervention. The user described about a minute of silence. Whether recovered audio repeated an earlier part of the song was not confirmed. The user stopped playback after recovery.
- Home Wi-Fi, speaker, 2026-10-28: user heard a dropout around 10:10 and confirmed audio returned on its own. Whether it replayed already-heard audio was not confirmed.

## Device-log evidence

Times below are the device log's local wall times on 2026-10-27. An AVPlayer status of `playing` is not proof that the listener heard audio.

| Session / time | Observation |
|---|---|
| Bluetooth `4B6FF567`, 17:59:26 | Session starts on the measured KCRW HLS endpoint with skew 155.6. Route changed to IONIQ 5 at 17:59:19. |
| 18:02:04 and 18:04:47 | Earlier stalls: buffer ahead 0.1 s, buffer empty, keep-up false. The handler logs recovery without seeking; subsequent samples jump backward and selected titles regress. |
| 18:04:26–27 | The app first observes the feed row for “Moving to L.A.” and publishes it at estimated song position 23.4 s. This is consistent with the reported late title, but does not distinguish provider availability from the 30 s polling phase. It is not a measurement of Bluetooth latency. |
| 18:07:26 | “Mama (Feat. Sudan Archives & Kamasi Washington)” by Dexter Story is selected at estimated song position 0.4 s. |
| 18:07:30 | Buffer drains to 0.1 s, then empty; AVPlayer enters `waiting`. The handler again logs recovery without seeking. |
| 18:08:14 | Playback fails with `CoreMediaErrorDomain -12889`; the session is torn down. No interruption or route-change event is logged around the dropout. All 18 feed polls succeeded. |
| Speaker `D9763199`, 18:15:38 | New session, same endpoint and skew. Output changes from IONIQ 5 to Speaker at 18:15:47. |
| 18:21:03 | Buffer drains to 0.1 s and AVPlayer enters `waiting`; the handler logs recovery without seeking. |
| 18:21:15 | Media position changes from 317.9 s to 252.0 s, and program date moves from 22:20:56.846Z to 22:19:50.971Z: about 66 s backward between samples. |
| 18:21:20 | AVPlayer reports `playing` and samples advance again. The user independently confirms audible recovery, but the precise audible recovery time is not known. Further clock discontinuities are logged before the clock settles. |
| 18:24:16 | User pause is logged. All 18 feed polls in the session succeeded; playing samples were at 1.00×. |
| 18:24:35 | `CoreMediaErrorDomain -12889` occurs after the manual pause and causes teardown. Do not count this as a second confirmed dropout during active speaker playback. |

A separate session `FE297914` started at 18:09:45, was paused at 18:09:47 without reaching playing, and failed at 18:12:39. It is not another completed active-playback control run.

The summary's `poll attempts ... below 58` verdict is an inherited fixed-run threshold, not evidence that feed requests failed in these short checks. Do not use that verdict to explain the audio stall.

### Diagnostic run on home Wi-Fi — 2026-10-28

The user installed the uncommitted diagnostic build over wired USB, started KCRW on the speaker, and confirmed home Wi-Fi. Session `DF65B4ED` started at 10:05:41; the network monitor reported `isExpensive: false`. At 10:10:12, the buffer reached 0.1 s and the player entered `waiting` for `minimizeStalls`. The last access-log event reported 44 media requests and 8,448,908 bytes; the logged error event was `CoreMediaErrorDomain -12889` at **10:09:00.712**, about 71 s before the stall. That timestamp does not prove the error caused the stall. Feed polls succeeded.

At 10:10:14 the media position jumped from 263.9 to 192.0 s and program date moved backward by about 72 s. At 10:10:18 the player reported `playing`; the user independently confirmed audible recovery but did not time it. No `[media-diag]` seek line was recorded during this session. The diagnostic covers `DefaultPlayer.seekTo` and its starting-position path, not every possible seek elsewhere or AVPlayer's internal operations.

After recovery, while media time advanced normally, program date jumped forward about 80 s at 10:10:42 and backward about 78 s at 10:10:48, with similar oscillation around 10:11:12–18. The clock rejected these discontinuities. The user stopped at 10:14:48; the copied log contains the pause summary, not a complete teardown. A buffered log tail may still be missing because no explicit flush was performed. This is evidence from one phone's player session, not an upstream HLS trace or proof of the exact audio replayed.

### Extended diagnostic Wi-Fi run — 2026-10-28

The user installed the extended diagnostic build over wired USB and played KCRW on the speaker at home. Session `86AA27C0` began at 10:48:36, reached playing at 10:48:42 and was paused at 11:07:26: about **18 minutes 44 seconds** of reported playing. The user heard no dropouts. The copied log contains no stall notification, logged error event or clock discontinuity for this session; at pause it reports 38 successful feed polls, zero poll failures and a 1.00× player rate. It does not contain a teardown/error-log snapshot, so it cannot establish that AVPlayer's error log was empty or that every segment succeeded. The pause summary's `poll attempts 38 below 58` is the unrelated fixed-run threshold noted above. No explicit flush was performed; the trailing buffered log may be incomplete.

This clean run confirms that failure is intermittent; it neither clears the earlier Wi-Fi reproduction nor proves or disproves phone-side HTTP 404s.

### Separate upstream playlist check — 2026-10-28

After the phone playback stopped, a separate Mac HTTP client fetched the KCRW master and followed its one advertised AAC variant. The master and three media-playlist requests returned HTTP 200. This is a **different connection**; it does not show what the phone received or prove the earlier stall's cause.

The first media response advertised 3 segments, media sequence 0, and program dates 14:16:07–14:16:19 UTC. Seven seconds later the next response advertised 20 segments, sequence 1, and program dates through **14:18:06.984 UTC**—about 108 s ahead of that response's wall time. The third response, seven seconds later, retained the rolling 20-segment window and dates through 14:18:12.997 UTC. These were playlist claims, not yet proof that each future-dated segment was playable. Segment URIs were not retained or logged.

**Follow-up segment probes, 14:18–14:21 UTC:** A new independent Mac client sampled 16 media playlists and requested the first, middle and last listed segments with `Range: bytes=0-0`. All 16 playlists returned HTTP 200. Of 48 segment requests, **35 returned 206 and 13 returned 404**. The initial response listed 3 segments; subsequent responses listed 20, including last segments stamped roughly 109–114 s ahead of the playlist request's wall time. The first 404 occurred at 14:19:25 for the last segment. From the next sampled playlist, all three selected positions returned 404 across four consecutive samples, even though each playlist itself returned 200. Only one byte was read from each successful segment; no audio was saved.

A second fresh connection sampled six playlists and requested the last listed segment both with a one-byte range and as an ordinary GET, reading at most one byte each time. The first four pairs returned 206/200; the last two returned **404/404**. The 404 is therefore not explained solely by the Range header. These checks establish inaccessible listed segments on separate Mac sessions, not which segment the phone requested or why the provider returned 404. Raw output from the first probe, with only hashed segment identifiers, is at `/tmp/pocketradio-hls-upstream.UcQSZx/results.log`; the second summary was captured in the session transcript.

**Staggered repeat:** Three new AAC HLS sessions started roughly 20 s apart. Each sampled 16 playlists and probed first, middle and last listed segments concurrently, reading at most one byte. In sessions 1 and 2, **15 of 48** probes returned 404; in session 3, **18 of 48** did. Each initially obtained 206 responses. Their first 404s appeared around 81, 61 and 42 s after their respective starts—approximately the same wall-clock interval despite the stagger. All three positions failed together across multiple samples; all sessions later got 206 again, with one additional failing sample in session 3. This is consistent with an intermittent interval shared by these Mac connections, not a fixed startup delay. It does not prove a global provider outage: they share a host/network path, and they did not capture the phone's requests. Evidence: `/tmp/pocketradio-hls-repeat.7fjG3Y/results.log`.

**Alternate MP3 HLS:** `https://streams.kcrw.com/e24_mp3/playlist.m3u8` returned a master playlist with one variant, but its variant playlist returned 404 in all 12 requests over about 70 s. No MP3 HLS segment was available to test. This does not test the separately served direct MP3 stream, and does not establish a permanent endpoint failure. Evidence: `/tmp/pocketradio-hls-mp3.BqaFEu/results.log`.

### Direct MP3 and recovery investigation — 2026-10-28

A separate Mac connection read and discarded the direct `https://streams.kcrw.com/e24_mp3` stream for **100.1 s**. It returned HTTP 200, `audio/mpeg`, 192 kb/s and `icy-metaint: 16000`; 3,120,000 audio bytes and 195 metadata blocks arrived, with maximum measured audio read wait 0.97 s. One metadata block was nonempty, but its content was not classified. A separate 35 s run of `tools/stream-probe.py kcrw --icy-only` reported empty ICY titles and warned after 50 consecutive empty blocks. No audio was stored. Evidence: `/tmp/pocketradio-kcrw-direct-mp3.PEK3Ih/result.log`; probe output was reported in the session. These are parallel HTTP connections, not AVPlayer playback, a complete reliability test, or a measured listener timeline.

Direct MP3 is distinct from the tested MP3 HLS variant, whose media playlist returned 404. The current aligned KCRW profile explicitly overrides either saved KCRW source with AAC HLS and uses `AVPlayerItem.currentDate()` plus a saved stream skew. Direct MP3 does not carry the HLS program-date clock assumed by that profile. The existing `.mediaTime` profile machinery for KEXP anchors player media time to when playback first advances, but switching KCRW to it requires separate calibration and on-device validation; the saved HLS skew of 155.6 s cannot be reused as proven correct. Turning alignment Off instead preserves ordinary direct-stream behavior but loses aligned presentation and falls back to legacy metadata/lyrics. Do not silently switch transport while claiming unchanged alignment.

**Recovery path inspected:** For transient stalls, `DefaultPlayer` already re-applies the rate without seeking (ADR 0007). On terminal item failure, `playFailedObserver` clears its play intent and calls `PlaybackManager.playbackDidFail`; the manager pauses and cleans up. `retryUrlLoad` is for podcast URL refresh and depends on a parent podcast, so it is not a suitable KCRW reconnect mechanism. `RadioPlaybackStarter.reload` can register and load a fresh item, but it is not an automatic retry guard; calling it after an asynchronous failure without preserving and rechecking user intent could restart after the user stops or changes stations. A fresh item tears down the old alignment session and starts a new generation.

**Earlier reconnect design, replaced 2026-10-28:** A Debug-only `KCRWReconnectPolicy`, `KCRWReconnectCoordinator`, `KCRWRecoveryActivationGate`, `KCRWRecoveryIntent` and `PlaybackManager` hooks triggered a reload after 20 s of `waiting` or a terminal failure, one per play intent. They were never wired to playback. They were removed because the trigger missed the recovered stalls (waits of 6 and 17 s) and the reload path needed asynchronous activation guards. Their files were deleted; the temporary backup was lost in a reboot.

## What is known, and what is not

- Buffer starvation and a recovery-time clock rewind reproduce outside Bluetooth. A car-specific route delay is not a sufficient explanation.
- Feed HTTP success does not prove that HLS playlist or segment requests were healthy.
- The existing no-seek branch is being selected. `DefaultPlayer` calls `performSetPlaybackRate`, not `play()`/`jumpToStartingPosition`, from that branch. This does not rule out another seek caller or AVPlayer's own recovery behavior.
- Radio still has `preferredForwardBufferDuration == 0`, meaning AVPlayer chooses the buffer. It already holds the whole advertised window (113–119 s) before each failure, so raising the preference cannot help (ADR 0011).
- On macOS, AVPlayer's comment for `-12889` is "No response for media file in 5.99s": a segment not delivered within about one target duration. The phone's own comment and HTTP status codes have not been captured yet.
- No notification interruption is logged during either reported dropout. That is absence of logged evidence, not proof about every system event.

## Next investigation

The uncommitted Debug patch observes the current aligned KCRW item's access/error-log events and player status; snapshots on stalls, item failure and teardown; and records `DefaultPlayer` seek calls, tied to the alignment generation. It logs a bounded underlying error-domain/code chain and aggregate access data, not error descriptions, raw URLs, server addresses or account data. Unknown error domains are redacted, so this is intentionally not a complete raw error dump. It does not instrument seeks outside `DefaultPlayer` or prove which component initiated an AVPlayer-internal jump. Playback behavior, skew, buffer policy and restart behavior are unchanged.

After the Mac segment probes, the uncommitted patch was extended to extract an HTTP status only when the AVPlayer error comment explicitly labels it as HTTP, and to classify the error-event URI by path extension as `playlist`, `media`, `other` or `unknown`. It logged neither the URI nor the comment. Since 2026-10-28 it logs the comment with identifiers redacted, and every new error event rather than only the last. `httpFromComment=unknown` means AVPlayer did not provide a recognizable status; it is not evidence of a successful request. An error event's own domain/code remains separately labeled. AVPlayer may omit the failed resource URI or HTTP status, and this does not observe every segment request.

Verification on 2026-10-28: the original diagnostic, stall recovery, session and publisher selections passed **97 tests**, and `make build_device` succeeded. The earlier Wi-Fi stall demonstrates delivery of the original diagnostic for one session. After adding privacy-safe status extraction and resource classification, the selection passed **99 tests** and `make build_device` succeeded; results: `/tmp/pocketradio-media-http.UVdoug/`. The extended build was installed and ran on the phone during the clean session above; because no failure was observed, its new error fields remain unverified against a real failure. The patch remains uncommitted.

The earlier recovery design is replaced; see **Cause and current experiment** above. Also identify whether the phone's own segment requests encounter the same HTTP failures; the Mac probes now prove that listed segments can return 404, but the phone diagnostics have not attributed a 404 to AVPlayer. During a future phone stall, compare the extended build's timestamped, privacy-safe HTTP status/resource classifications with the symptom. An unavailable or unrecognized status remains inconclusive. Compare a fresh upstream session and an alternate endpoint only as separate connections. Do not change buffering, recovery or stream policy on the assumption that the Mac and phone saw identical failures. If a device comparison is needed, obtain approval before any further install or launch and confirm wired USB. Keep wired CarPlay, background acceptance and any device-harness run separate; the device harness still requires its own explicit consent. Flush the debug log before copying it when practical.

## Local evidence

Raw logs were copied over wired USB without installing or launching the app. They contain unrelated personal app activity and are not committed:

- Bluetooth capture: `/tmp/pocketradio-m14-4-bluetooth.YhOcQo/debug_log/`
- Speaker capture during recovery: `/tmp/pocketradio-m14-4-speaker.dYY4K5/debug_log/`
- Speaker capture after user stop: `/tmp/pocketradio-m14-4-speaker-final.y5FfGw/debug_log/`
- Phone logs and capture analysis from 2026-10-28 afternoon: `/tmp/pocketradio-recovery-device/`, `/tmp/pocketradio-kcrw-client/`
- Wi-Fi diagnostic during recovery: `/tmp/pocketradio-wifi-diag.S0K9d3/debug_log/`
- Wi-Fi diagnostic after user stop: `/tmp/pocketradio-wifi-diag-final.Fnx9eO/debug_log/`
- Extended diagnostic clean Wi-Fi session: `/tmp/pocketradio-wifi-http.ck3iRE/debug_log/`

These are temporary local locations, not a permanent raw-log archive. A reboot on 2026-10-28 deleted the earlier ones listed here, including the Mac probe outputs cited in older sections. The observations and relevant values above retain the evidence if those files are removed.
