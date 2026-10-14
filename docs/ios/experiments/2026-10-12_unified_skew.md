# Experiment: can one per-station skew replace the +160 constant, the Debug skew, and the lyric nudge?

**Status**: IN PROGRESS — 2026-10-12. Phases 0 and 1 are built and pass in simulation and unit tests. Phase 2 (device) is next. Nothing is committed yet: the iOS rule is to test on the phone first. Follows the [ShazamKit offset experiment](2026-10-10_shazamkit_offset_anchor.md), which showed the offset is steady within a session (stdev about 0.3 s) and that ShazamKit can measure it. Belongs to [M14](../milestones/milestone_14.md). Work happens on a branch, `experiment/unified-skew`, in the existing `pocket-radio-ios-alignment/` worktree. It includes the heal button and the ACR removal ([ADR 0009](../adr/0009-acr-identify-button-removed-for-timing-recalibration.md)), which were never committed separately. It merges to `trunk` only if the pass criteria below hold.
**Question**: Timing today comes from three places: a frozen `+160 s` in code, a Debug feed skew, and a per-song lyric nudge that moves only the lyrics. Can one number per station, the **skew**, drive title, artwork, song position, lyrics, lock screen and widget, be measured by one heal, be fine-tuned by hand, and still work for a station the app has never seen?

## Definitions

- **Skew**: the difference between the stream's timeline and the tracklist's timeline, in seconds. A song that the feed stamps at time `T` starts in the stream at `T + skew`. It is the same quantity the core calls `feedToProgramOffset`.
- **Seed**: a known starting skew for a station. KCRW's seed is 160. A station with no seed starts at 0.
- **Heal**: the button that measures the skew with the microphone and ShazamKit, and replaces it.
- **Fine-tune**: the `+` and `−` on the lyrics page. Each tap adds or subtracts 0.5 s from the skew.
- **Alignment**: one switch, Off or On. Off is the old behavior. On is what Apply is today.

## The model

1. A stream starts with its seed, or 0.
2. The listener hears that title and artwork do not change with the song. They tap heal. The skew becomes the measured value, usually within a couple of seconds of right.
3. The listener checks the lyrics and fine-tunes in 0.5 s steps.
4. The skew is saved per station on this device. The next session starts from it.
5. A heal always **replaces** the skew. It does not keep an earlier fine-tune. Rationale: one number, one meaning. See Question 1.

Skew is the only timing input. Everything the aligned session shows reads it, so a change moves track start, track end, title, artwork and lyrics together.

## How the heal can start from any skew

Today's heal assumes the right song is already selected, and measures how far the position is off. That cannot fix a skew that is 160 s wrong, and the learner clamps at ±10 s. Unified skew needs a heal that does not depend on the starting value.

ShazamKit tells us **which song** is playing and **where in it** (`predictedCurrentMatchOffset`, which already includes the speaker's output delay). The tracklist tells us when each song was stamped. So:

1. Match the heard song to a tracklist entry by title and artist, among the entries the feed returned.
2. Read the stream's program date `P` at the instant of the match, and ShazamKit's position `s`.
3. The song started in the stream at `P − s`. The feed stamped it `T`. So `skew = P − s − T`.

Then:

- Take three such anchors. Reject any that differ from the median by more than 2 s, with the existing learner's outlier rule. Accept the median when at least three agree within 1 s.
- If the same song appears twice in the feed's window, choose the entry that gives the skew closest to the current one.
- The clamp becomes a sanity limit. This experiment uses ±600 s. A result outside it is rejected.
- If the heard song is not in the feed, report "That song isn't in the tracklist yet" and try again. The feed can lag.

The mic works only where it hears the audio: the phone's speaker, or a car cabin. Headphones and Bluetooth cannot be healed.

## What is removed

- The frozen `+160 s` constant. It becomes a seed table entry.
- Observe mode, the Self-heal picker (Off, Measure, Apply), the automatic 3-minute loop, the Debug feed-skew picker, and the poll-driver setting. One Alignment switch, Off or On, is left.
- The per-song, lyric-only nudge, including its saved per-station lyric offsets (`LyricOffsetStore`, `RadioFavoritesManager.upsertLyricOffset`). In Off the `+` and `−` are hidden. The `lyricOffsets` table in Supabase is untouched. I did not check what else reads it.

`+` and `−` stay where they are on the lyrics page, 0.5 s per tap. **`+` still moves the song position forward**, as it did, so it lowers the skew by 0.5 s (a larger skew means the song started later in the stream, so an earlier position). The label under them now reads `Skew 157.5 s`. Tests pin the direction.

## Phases

| Phase | What | Pass if |
|---|---|---|
| 0. Simulate | A pure `SkewSolver`: tracklist entries plus anchors (song, position, program date) in, skew out. Extend `SimulatedWorld` with a tracklist, a true skew, repeated songs, wrong-section matches and a missing song | From a starting skew of 0, ±60 s and the 160 s seed, three anchors converge to within 1 s of the true skew. A wrong-section anchor does not move the result by more than 1 s. A missing song gives a message and no change |
| 1. Unify | Replace the three inputs with one skew in the session. Add the Alignment switch. Remove what is listed above. Persist per station | Existing tests are updated and pass. Off behaves like the old Off apart from the missing nudge. A skew injected in a test moves title selection, lyrics and lock screen by the same amount |
| 2. Device heal | KCRW with the seed off, from skew 0. Tap heal on the speaker | The title, artwork and lyrics match the audio to within about 2 s after the heal. A follow-up anchor measures a residual of 1.5 s or less. Repeat from skew 0 in three sessions |
| 3. Fine-tune and persistence | `+` and `−` in 0.5 s steps. Kill and relaunch. Switch station and back. Heal after a fine-tune | The fine-tune survives relaunch and a station switch. The heal replaces it. Every post-heal fine-tune is logged with its size and sign |
| 4. Second station | One more station with a tracklist and a program-date clock | Heal reaches the same pass as KCRW, or the experiment records that no such station exists in the curated list. **No station is chosen yet** |

## Questions the experiment answers

1. **Does the heal have a constant bias?** Phase 3 logs each post-heal nudge. If you nudge about the same size and direction after most heals, the heal has a systematic error and a stored correction for it is warranted. If the nudges are random, one number is right. Decide after at least five sessions.
2. **Does skew survive across sessions?** The earlier data had true offsets of 158.2, 162.0, about 157, 159.2 and 157.9 s. A persisted skew should start within about 5 s of right.
3. **Does a route change the skew?** AirPlay can add about 2 s that the mic never hears. One skew per station cannot capture that. This stays unanswered and goes to 14.4.
4. **Is "stream-agnostic" real?** Only Phase 4 answers it. KCRW's HLS stream carries program dates. A plain Icecast stream may not, and would need the arrival time minus the buffer.

## Assumptions not checked

- Tracklist start times mark when the song began on air. KCRW's looked consistent (within 0.3 s inside a session). Another station may not be.
- Where skew is saved. This plan says local `UserDefaults` per station id, because the value depends on the device and its speaker. A cross-device store is not wanted. Not decided with the user.
- Station-id keys survive a station being renamed or its stream URL changing. Not checked.

## Consequences to decide before merging

- **Other stations lose the lyric nudge.** Alignment is eligible only for KCRW today (`KCRWEligibility`). After this change, a station that has lyrics but is not aligned has no way to adjust them. The branch merges only if that is acceptable, or if Phase 4 brings a second station in.
- **Alignment On is Debug-only today.** Making it the default is a separate decision, not part of this experiment.
- If it succeeds, an ADR replaces the frozen-offset parts of [ADR 0004](../adr/0004-kcrw-playback-clock-on-ios.md) and [ADR 0008](../adr/0008-kcrw-lyrics-follow-the-media-clock-in-apply.md). The shared KCRW ADR waits for M14 to close.

## Built

- `AlignmentSkewStore`: one skew per station in `UserDefaults`, a seed (KCRW 160, anything else 0) when nothing is saved, ±600 s limit, values rounded to 0.1 s, a notification on change. A saved 0 counts as saved, so a heal from skew 0 does not fall back to the seed.
- `RadioPlaybackSession` reads the skew each sample and selects with it. A change takes an immediate sample, so the title and lyric line move at once. The poll-driver setting, the Observe mode and the session's mode are gone; `startsPoller` is a test seam, not a setting.
- `SkewSolver` (pure), `ShazamAnchorProbe` (listen once, return a measurement), `SkewHealer` (three anchors within 1 s of their median, then save). Out-of-range results change nothing.
- One Alignment switch, Off or On. The Debug screen shows the skew, buttons to set 0, ±60 and the seed (to start a heal from a wrong value), and "Heal now". Self-heal modes, the 3-minute loop and the feed-skew picker are removed.
- The old lyric nudge, its Supabase save and `LyricOffsetStore` are removed. In Off the `+` and `−` are hidden.

## Phase 0 results (simulation, 40 seeded runs per row unless noted)

The simulated station stamps songs 150 to 400 s long, plays them `trueSkew` seconds later, and returns ShazamKit positions with Gaussian noise. The microphone listens 7 s per anchor. Error is `|saved skew − true skew|`.

| Case | Within 1 s | p95 | Worst | Anchors used | Gave up |
|---|---:|---:|---:|---:|---:|
| Start 0, true 158.2, noise 0.4 s | 100 % | 0.4 s | 0.6 s | 3.0 | 0 |
| Start 160 (seed) | 100 % | 0.4 s | 0.6 s | | 0 |
| Start 100, 220, −60 | 100 % | 0.4 s | 0.6 s | | 0 |
| True skew 0, 25, 90, 320 | 100 % | | 0.6 s | | 0 |
| 20 % wrong-section anchors (60 runs) | 98.3 % | 0.5 s | 0.6 s | 3.6 | 1 |
| Noise 0.8 s | 97.5 % | 1.0 s | 1.5 s | 3.5 | 0 |
| Song repeats every 3 rows, start 160 or 0 | 100 % | | 0.6 s | | 0 |
| Song repeats, start 600 (far side) | 25 % | | 0.3 s | | 30 of 40 |

- **Pass for Phase 0.** From any starting skew the heal ends within 1 s, and a wrong-section anchor never moved a result. A song missing from the feed gives a message and no change, after 8 tries.
- **The far-start repeat case fails closed.** The nearest-row rule picks the wrong play, the result lands outside the agreement or the limit, and the heal gives up with a message. It never saved a wrong skew in these runs. A start that far from the truth is not a case the app produces.
- **What the simulation does not tell us.** It assumes ShazamKit's noise is Gaussian and unbiased, and that the feed's stamps are exact. The device runs decide that.

## Next

A follow-up stub asks whether the heal can read the stream's audio directly instead of the microphone: [direct stream heal](2026-10-14_direct_stream_heal.md). It is not ready to run.

Phase 2, on the device: `make build_device`, install with the user's choice of USB or network, launch with `-PocketRadio.alignment.mode on`. Set the skew to 0 from the Debug screen, play KCRW on the speaker, tap the heal button, and compare by ear. Log: `[anchor]`, `[heal]` and `[align] skew` lines.

## Phase 2 interim results (device, 2026-10-14, speaker, KCRW)

Heal results and the user's fine-tune. Interim: more runs are in progress.

- **First runs found two bugs, both fixed.** ShazamKit refuses a session opened straight after another closes, so the heal waits 5 s between listens. A feed title with a version word ("remix", "radio edit") against a plain ShazamKit title gave anchors off by 99 s (remix) and 8 s (radio edit). Anchors from the same edit agree with each other, so the three-agree rule can't catch it. Those anchors are now skipped.
- **Anchors in one song are precise.** Three anchors on one song agreed within 0.1 s. Anchors spanning a song change can be 4 to 5 s off for the first one, and the three-agree rule rejected it.

| Heal | Song | Started from | Heal result | Final | Note |
|---|---|---:|---:|---:|---|
| A | Congratulations To Me | 0 | 158.7 | 157.2 | user nudged −1.5 |
| B | Runner, then Hold On | 157.2 | 158.0 | 157.5 | user nudged −0.5; ran across a song change |
| C | Hold On, We're Going Home | 157.5 | 158.4 | 158.4? | no nudge in the log |
| D | Budapest | 158.4 | 158.6 | 158.6? | no nudge in the log |

- The heal's results span 0.7 s over four songs. The user's finals for A and B are 0.3 s apart, below the heal's own spread.
- **Open:** whether C and D were left as healed. If so, a constant of −1.0 would be wrong. If they were moved to about 157.5, the constant fits. Decide after more runs, as planned in Questions above.
