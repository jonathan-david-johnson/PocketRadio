# Bug 5 — Resolved artwork is lost on a Now Playing rebuild and is not restored

**Status:** Open — reproduced in the M13 test harness (2026-10-04); not yet observed on a device. Not fixed.

Found by M13 E4 and E7 (H2). Evidence: `archive/ios-m13:docs/ios/experiments/2026-10-04_m13_e4.md` and `archive/ios-m13:docs/ios/experiments/2026-10-04_m13_e7.md`; the original `@h2` draft in `contracts/features/now_playing/carplay_artwork.feature`. M13.2's named lifecycle scenarios and unmarked baseline report (`archive/ios-m13.2:docs/ios/experiments/2026-10-07_m13_2_baselines.md`) reproduce A and C, and expose nondeterministic startup ordering for B.

The symptoms share one cause, so they are lettered under one doc.

---

## Symptom A — Pause and resume replaces the song's artwork with the station logo

Song A is playing with its artwork. The listener pauses and resumes. The display keeps "Song A" but the artwork becomes the KCRW logo, and it stays that way until the next song.

Harness timeline: `+8.95 pause()`, `+10.51 play()`, `+10.66 artwork` changes from red to the logo (`rgb(7,9,7)`). The runner waited 8 s and saw no recovery.

## Symptom B — Artwork resolved before the first full rebuild can be lost at playback start

The tracklist response and the first `setAllNowPlayingInfo` rebuild race. If the artwork resolves first, the rebuild overwrites it with the logo. It is seen once in an undelayed run: red at +0.10 s, logo at +0.20 s, never restored, even after Song A's ICY title arrived. A cached tracklist (second start of the station in one app session) makes this order likely. In M13.2, warming the cache through a real fetch produced a passing run followed by a failing independent repeat (red at +0.43 s, logo at +0.92 s). A strict expected-failure marker would therefore be flaky. After simulator restart, two clean awake runs again showed red at about +0.43–0.44 s and the logo at +0.53 s. Sleep is not the cause of those failures, but the earlier passing outcome still makes a strict marker unsafe without further ordering control. The user subsequently approved a DEBUG-only startup barrier, which now establishes the required ordering for the strict regression checks. Ordinary production startup scheduling remains uncontrolled.

## Symptom C — Stopping and replaying the same song skips artwork resolution

`PlaybackManager.lastResolvedRadioKey` survives `endPlayback`. If the user stops KCRW and starts it again while the same song is playing, the key matches and artwork resolution is skipped. Harness: scenario 2 started on the song scenario 1 ended on and never requested its artwork (no iTunes or artwork request), and the display showed the logo instead of the expected green image.

## Root cause (from code, confirmed by the harness)

`NowPlayingHelper.setAllNowPlayingInfo` rebuilds the whole info dictionary and installs the station logo (`setRadioArtwork`). It does not tell `PlaybackManager`. `lastResolvedRadioKey` therefore keeps saying "this song's artwork was already resolved", and `resolveRadioArtworkForLockScreen` returns early on every later call for the same song. The key also is not cleared when playback ends (symptom C).

In short: the dedupe key outlives the artwork it vouches for.

## Not decided

How to fix it. The M13 plan keeps fixes in `fix/stream-presentation`. A fix should tie the key to what is actually displayed, for example by clearing it whenever the info is rebuilt or playback ends.

## Notes

- The review in `architecture/reviews/stream-monitoring-review-2026-09-16.md` §2 predicted symptom A.
- H3 (a slow download for an earlier song replacing the current artwork) was **not** reproduced on this path. The key guards in the same function work.

## Harness update — 2026-10-08 UTC

The user approved the startup barrier, and it is implemented. This resolves the
coverage block described under B, not the app defect. Three independent unmarked
runs prove actual red artwork publication while the real initial rebuild is held,
then release that unchanged rebuild and observe the station logo.

The accepted baseline verification (`archive/ios-m13.2:docs/ios/experiments/2026-10-08_m13_2_verification.md`) includes four
strict bug-5 output checks across three scenarios:

- A, pause/resume: `display.title-artwork.artwork`.
- B, controlled cached start: `display.title-artwork.artwork` and
  `display.sustained-artwork.artwork`.
- C, stop/replay: `display.title-artwork.artwork`.

Only the post-transition checks are marked. Initial red-artwork setup, callback
capture/release identity, fresh ICY input, wrong titles and cleanup remain ordinary
failures. All three final 128-test runs reproduce the designated failures. Normal
startup scheduling remains uncontrolled outside the explicitly armed DEBUG test.
The [test boundary ADR](../adr/0003-carplay-output-test-boundary.md) records the hook.
