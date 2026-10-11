# Experiment: can ShazamKit anchor and self-heal KCRW's feed-to-audio offset?

**Status**: IN PROGRESS — 2026-10-10. The learner and the test knob are built and tested in simulation; the ShazamKit anchor spike (Phase 0) is next. Belongs to [M14](../milestones/milestone_14.md); found while closing 14.3 ([ADR 0008](../adr/0008-kcrw-lyrics-follow-the-media-clock-in-apply.md)). The outcome decides what 14.4 does about timing.
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
