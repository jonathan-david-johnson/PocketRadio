# M11-B — KCRW control versus Apply listener feedback

**Result:** The listener reported an early track-title change without Apply candidate, “perfect” menubar title timing with Apply candidate, subsequently “perfectly aligned” lyrics, and Off working “as expected.” These are positive qualitative reports, not measured title/lyric error or completion of the formal M11-B validation.

## Build and checks

- Date: 2026-10-04.
- Menubar branch/head: `feature/stream-session-model` at `8dcbb70`, including M11-B implementation `94814f6`.
- No tracked source changes during this verification; the pre-existing untracked `Tools/StreamLab/.pi/` directory was left alone.
- Tests passed: 23 StreamSession, 63 Stream Lab, 18 app unit, and 3 UI tests. The current UI launch test uses the current appearance rather than repeating across appearances; the older four-test count is historical.
- The Debug app at `/tmp/pocketradio-m11b-current-check/Build/Products/Debug/PocketRadio.app` passed `codesign --verify --deep --strict`.
- With the user's approval, the assistant launched that app. The assistant did not start playback. A subsequent process check confirmed that build remained running when the feedback was recorded.
- Frozen policy remains `+160s`; no calibration, endpoint default, saved station data, or lyric offset was changed.

## Listener report

The listener described two conditions, in this order:

| Condition | Reported result |
|---|---|
| Control: KCRW without Apply candidate | “It changed track title early.” |
| Experiment: Apply candidate enabled | “track title change in menubar timing is perfect.” |

These statements come from the listener, not an independently observed audio boundary.

After the assistant requested a zero-correction lyric check with Apply still enabled, the listener reported “lyrics are perfectly aligned.” The listener did not separately confirm the correction value, song/recording identity, or whether the menubar and lyric detail showed the same line. Record this as qualitative lyric-alignment feedback, not a timed landmark measurement.

After the assistant requested switching the experiment to Off and checking normal KCRW playback/no active experimental session, the listener reported “off works as expected.” This is qualitative confirmation of the Off check; the listener did not supply an item-generation trace, endpoint inspection, or saved-data comparison.

## Evidence limits

- The control's exact mode (Off versus Observe only), station source URL, and active player endpoint were not supplied. Do not assume both conditions used the same endpoint or player item.
- No output-route category was supplied for this check. Prior speaker-route reports do not establish this run's route.
- Song identities, transition count, marker times, and duration were not supplied.
- No trace/export was identified or replayed for this check. Capture status is unknown.
- “Perfect” describes the listener's perception. It does not establish zero error, subsecond precision, or the formal ±5s target.
- No lyric landmarks or timestamped line errors were supplied. Lyric feedback does not establish the formal ±2s aim or agreement between the menubar and lyric detail.
- Off was listener-confirmed, but fresh-item teardown, restored endpoint resolution, and saved-data isolation were not independently inspected in this check.
- This report does not validate selected history, system Now Playing, or reconnect behavior.

## Decision boundary

The user explicitly accepted the qualitative result and authorized commit, merge, and push: “Accept qualitative result, commit, merge, push, next.” M11-B is complete as an opt-in prototype on that basis. Existing menubar merge `e6fa855`, which includes tested feature head `8dcbb70`, is pushed to `origin/main`.

Keep the frozen candidate unchanged. Formal multi-session title timing and lyric-landmark targets remain unverified. Additional experiment-only lyric-resource telemetry and publication-revision export are deferred, not blockers to this acceptance. The user does not require more long listening sessions for prototype closeout. Default-endpoint changes, automatic recording, production rollout, and iOS work are not authorized by this acceptance.
