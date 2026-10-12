# Experiment: can ShazamKit anchor and self-heal KCRW's feed-to-audio offset?

**Status**: IN PROGRESS — 2026-10-12. Phases 0 to 2 done on the device: ShazamKit anchors work, the offset is steady within a session, and the self-healing learner corrected it, including after a ±10 s injected error. Phase 3 (reliability) and a decision on shipping it remain. Belongs to [M14](../milestones/milestone_14.md); found while closing 14.3 ([ADR 0008](../adr/0008-kcrw-lyrics-follow-the-media-clock-in-apply.md)). The outcome decides what 14.4 does about timing.
**Question**: On the phone, the aligned title and the lyric line run about 3 s behind the audio (user, 2026-10-10: `+3` in full-screen lyrics brings them into sync). The core uses a frozen `+160 s` feed-to-program offset, measured on the Mac. Is the phone's real offset a stable stream property, and can ShazamKit measure it well enough that the app corrects itself?

## Hypothesis

The error is a **constant** latency between the stream and the tracklist feed, not song-to-song jitter (user's expectation: it is one continuous stream). If so, the correction `δ` is the same for every song on a given route, and a running estimate converges after a few anchors.

Definitions, so the numbers mean one thing:

- `songSeconds` — what the app computes now: player program time minus (feed `playedAt` + 160 s).
- `shazamOffset` — `SHMatchedMediaItem.predictedCurrentMatchOffset`: the timecode in Apple's reference recording that matches what the mic hears now. The mic hears the speaker, so it includes output delay.
- `δ = shazamOffset − songSeconds`. Positive δ means the audio is ahead of the app. The user's `+3` nudge predicts δ ≈ +3. The corrected policy offset would be `160 − δ` (about 157 s).

## What ShazamKit gives (checked in the iOS 27 SDK headers, not the web)

- `SHManagedSession` (iOS 17, Swift): `result() async -> SHSession.Result`, `results` as an async stream. It records from the mic itself. The app's deployment target is iOS 17.
- `SHMatchedMediaItem`: `matchOffset` (reference timecode of the query's start), `predictedCurrentMatchOffset` (reference timecode now), `frequencySkew`, and `confidence` (iOS 18.4 and later).
- Unverified until tried: the accuracy of the offset; whether KCRW's eclectic catalog matches; whether a match disturbs playback (the session may reconfigure audio); and whether the ShazamKit App Service must be enabled for `com.jdj.pocketradio` in the developer portal.

## Limits to keep in mind

- Works only where the mic hears the audio: the phone's own speaker, or a car cabin. Not headphones or a direct Bluetooth sink. So it can calibrate the speaker route, not Bluetooth.
- The reference recording may differ from the broadcast (radio edits, fades). The offset then drifts within a song, which shows up as a larger spread.
- Needs the mic permission. The current usage string is about Google Cast and must change.

## Phases

| Phase | What | Output | Go on if |
|---|---|---|---|
| 0. Spike | Debug button "Anchor now" runs one `SHManagedSession` match while KCRW plays in Apply on the speaker. Logs one `[anchor]` line: wall time, aligned title and artist, aligned `songSeconds`, Shazam title, artist, offsets, confidence, δ, and whether the identities agree | A handful of δ values, and answers to the unverified items above | Matches arrive, identities agree, playback is not disturbed |
| 1. Data | Auto-anchor every few minutes for one to two hours, over at least two sessions | δ series: spread, drift, whether it persists across songs and restarts | Spread (stdev) under 0.7 s and no trend across songs |
| 2. Learner | A pure `OffsetLearner`: median of the last N identity-verified anchors, outliers rejected by MAD, clamped to ±10 s, keyed by route. Debug picker Off / Measure / Apply. Apply adds δ to the lyric position and shifts the title selection to `160 − δ` | Learned δ, applied by the app | Converges in three or fewer anchors |
| 3. Reliability | Leave-one-out against later anchors, a route switch, an app restart, a 1 hour run | Worst residual error and flip-flop count | Residual under 1 s, no oscillation, and Off restores today's behavior exactly |

If Phase 1 shows a spread above 1.5 s or a drift, the hypothesis is wrong. Then a per-song anchor is the only automatic fix, and this experiment stops there with a report.

## Built so far

### The learner, tested in simulation (`OffsetLearner`)

A pure type: anchors in, one correction out. It keeps the last 7 anchors and reports their median, clamped to ±10 s. An anchor more than 2 s from the median is held back as an outlier. Three held-back anchors in a row that agree within 1 s replace the window, which is how it follows a real change in the feed's latency. It reports nothing until three anchors have arrived, then never goes back to nil: the last value is held through a long gap. One learner per output route.

`SimulatedWorld` runs it against scripted worlds with a seeded random generator, so every run is the same. The sweep (`OFFSET_SWEEP=1`, `testParameterSweep`) tried window 3, 5, 7 and 9, outlier threshold 1, 1.5, 2 and 3 s, and step run 2, 3 and 4, over four hours of anchors every 2 minutes. p95 absolute error after the first 12 minutes, with the defaults chosen (window 7, threshold 2.0, run 3):

| World | p95 error | worst | Visible lurches |
|---|---:|---:|---:|
| Constant offset, noise 0.5 s | 0.42 s | 0.75 s | 0 |
| Step from 3 s to 8 s at one hour | 0.63 s | 4.93 s | 0 |
| 20 % wrong-song anchors (8 to 20 s off) | 0.28 s | 0.48 s | 0 |
| Noisy anchors, noise 1.0 s | 0.88 s | 1.27 s | 0 |
| Drift of 0.3 s per 10 minutes | 0.68 s | 0.94 s | 0 |

- **The step's worst case is the lag.** It takes three agreeing anchors, about 6 minutes at one anchor per 2 minutes, to follow a real step. During that time the error is the size of the step. Two anchors would follow faster but flip on noise (2 lurches at threshold 1 s).
- **Window size.** A window of 3 is noisy. A window of 9 is smoother but slows a drift slightly. 7 is the middle.
- **What this does not tell us.** The simulation assumes anchor noise of 0.4 to 1.0 s, wrong matches that are far off, and an offset that is constant per route. Real ShazamKit noise and wrong-match behavior are the open questions for Phase 0 and Phase 1.

### The test knob: feed skew

A Debug-only stepper, "Feed skew", in the alignment screen, from −15 to +15 s in 0.5 s steps. It adds to the `+160 s` offset on the running session at its next sample, so titles and lyrics shift with it. It also reads `-PocketRadio.alignment.feedSkew 5` at launch. A line `[align] policy offset=165.0 s (feed skew +5.0 s)` is logged at the first sample and on every change. Release ignores it.

To make the shared selector accept a new offset mid-session, `SessionState` in the menubar's `StreamSession` package gained `updateSelectionPolicy(_:)`, an additive change with a test.

The knob also works as a manual calibration: the user's 3 s lag would be corrected by a skew of −3 s.

How it tests the learner on the real stream: with ShazamKit anchors running, set the skew to +8. The learner should report a correction near `+8` more than before and settle there, and it should follow when the skew changes mid-stream.

## Phase 0 and 1 results (2026-10-11, iPhone speaker, Apply)

ShazamKit works for KCRW. The mic and the match request worked once the ShazamKit App Service was enabled for the App ID (the first anchors returned HTTP 401, "Missing entitlements"). Playback was not disturbed. Every anchor of 20 returned the right song (confidence 1.00). Anchors take 15 to 30 s each.

`trueOffset` is the feed-to-program offset that would have made the app match the audio. It is independent of the Debug skew.

| Session | Anchors | Skew | trueOffset | Notes |
|---|---:|---|---|---|
| `F662BE3E` (18:07) | 1 | −3 | 158.2 | The Governor's Waltz |
| `A65113A5` (18:14 to 18:39) | 9 | −3 | 161.4 to 162.3, median 162.0 | 7 songs; spread 0.26 s; one 53 s outlier held back by the learner |
| `1553837A` (18:44 to 19:02) | 9 | 0, +2, −3 | 156.3 to 157.0 | Skew changed three times in one session |

- **Constant within a session.** The standard deviation within a session is about 0.3 s, against the 0.7 s pass line. That supports the user's hypothesis: a stream-to-tracklist latency, steady while a session runs.
- **It differs between sessions.** 162.0 in `A65113A5`, about 157 in `1553837A`, 158.2 in `F662BE3E`. `A65113A5` and `1553837A` were four minutes apart, with a stop and restart between them. The spread is about 5 s. The frozen 160 s sits in the middle of it.
- **The skew arithmetic holds.** In `1553837A` the offset that would have fixed it came out 156.3 to 157.0 at skew 0 (delta +3.7), at +2 (delta +5.0 to +5.7) and at −3 (delta +0.1). Delta moved with the skew and `trueOffset` did not.
- **Titles at skew 0.** The user judged the title changes "perfect" at 160 s, where the anchors say the audio was 3.7 s ahead of the app. A title flipping a few seconds late at a crossfade is hard to hear. A lyric line is not, which is why the lag showed first in the lyrics (3 s late at 160 s, fixed by −3 s). Skews of +2 and −3 both visibly moved the title.
- **The one bad anchor** (a 53 s miss near the end of a song) is a ShazamKit match to an earlier section of the same song. The learner holds it back as an outlier. Replaying the real anchors through the learner: after three anchors it reports −2.2 s in `A65113A5` and about −3.1 s in `1553837A`, relative to the frozen offset.
- **Not yet known.** Why the offset differs between sessions (join-time differences in the HLS stream's program dates, or the feed). Whether a fixed per-device value would do (the sessions span about 6 s, so no). Whether Bluetooth or CarPlay differ: the mic can't measure them.

Conclusion so far: the learner is worth building. Within a session the error is steady and a few anchors find it, and it differs between sessions by more than a fixed constant can cover.

## Phase 2 results: self-healing on the device (2026-10-12, iPhone speaker)

Self-heal in Apply mode: the learner restarts at each session start, takes about three anchors 5 to 10 s apart, then re-anchors every 3 minutes and moves the session's offset by the learned correction.

| Event | What happened |
|---|---|
| Session `653B0969`, skew 0 | True offset 159.1 to 159.3 (delta +0.7 to +0.9). Under the 1 s dead band, so nothing was applied. |
| Skew moved to +10 | Delta +10.9, true offset 159.1. The learner reset and calibrated again, as designed. |
| Station restart, new session `56B2678F` | True offset **157.9**, 1.3 s from the previous session. The session started from zero correction. |
| Skew +10, correction applied | The learner asked for +12.1 s (the 2 s the stream needs plus the 10 s injected). The clamp is ±10 s, so it applied +10.0 and left 2.5 to 2.7 s of residual. |
| Skew moved to −9 mid-session | The held +10 s correction made the offset 141 s: delta −16.3 on the first anchors. After three anchors, **28 s** later, it applied −6.3 s and the offset landed on **157.3 s**, exactly the true offset the anchors measured. |

- **Accuracy.** After recovery the applied offset equals the measured true offset (157.3 s) to the tenth of a second.
- **Speed.** About 30 s from a bad state to a corrected offset, because calibration anchors run back to back.
- **Outliers.** Two of 29 anchors across all runs were ShazamKit matches to a repeated earlier section of the song, 53 s off (`Mockingbird`, `Talk It Over`). The learner held them back. The 05:21 one came first in a calibration, and the median of three outvoted it.
- **Session to session.** True offsets across the sessions measured so far: 158.2, 162.0, about 157, 159.2, 157.9. The range is about 5 s, and the frozen 160 s is not at its center. The within-session drift was about 0.6 s over 10 minutes (157.9 to 157.3).
- **Two faults found and fixed.**
  1. The ±10 s clamp is on the total correction against the skewed model, so a +10 s skew (which needs 12 s) hit the clamp. The Debug controller now allows ±20 s. A real offset needs about 2 to 5 s, so the real clamp stays ±10 s.
  2. An anchor that finished after the station had restarted set a correction for the old session. It is now discarded, and the new session starts clean.
- **Open.**
  - A skew change keeps the old correction until three new anchors arrive, so a big swing costs about 30 s of larger error. A real feed step would behave the same.
  - The mic hears only the phone's speaker or a car cabin. Headphones and Bluetooth can't be calibrated by this.
  - Cost and consent: the mic is open for 15 to 30 s per anchor, about every 3 minutes, and ShazamKit sends an audio signature to Apple.

## Guardrails

- Debug only, behind its own picker. Off is today's behavior. Release is always Off.
- Learned δ is clamped to ±10 s, per route, and discarded on a station change.
- No audio is stored or uploaded by the app. ShazamKit sends a signature to Apple; say so in the permission text.
- Identity must agree (fuzzy title and artist) or the anchor is dropped, so a wrong-song match cannot move the offset.

## Hand-performed steps (to fill in with the user)

- [ ] Grant the mic permission. Enable ShazamKit for the App ID if a match fails with an authorization error.
- [ ] Phase 0: three manual anchors on the speaker over three different songs.
- [ ] Phase 1: an hour of KCRW on the speaker with auto-anchor on, then a second session later.
- [ ] Phase 3: switch to headphones and back; restart the app.

## Docs impact

- **Docs this changes or makes stale:** [ADR 0004](../adr/0004-kcrw-playback-clock-on-ios.md) and the future shared KCRW ADR (the `+160 s` policy and its calibration); the "KCRW alignment" section of `docs/ios/README.md`; ADR 0005 if the title selection shifts.
- **Questions this must settle:** is the offset constant per route; does ShazamKit measure it reliably enough to apply automatically; is a per-route value stored or re-learned each session; does the menubar's Mac measurement of `+160 s` still hold.
