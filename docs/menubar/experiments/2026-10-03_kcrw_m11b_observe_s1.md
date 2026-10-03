# M11-B — KCRW Observe-only session 1 (three identified songs)

**Status:** 9m36s same-player capture with three listener-confirmed music-start markers and one button press corrected as a commercial. The listener confirmed the titles in follow-up; artist, kind, and provider timestamps come from public feed rows. This is not a five-identified-transition validation, nor Apply candidate or lyric evidence. The trace and sidecar remain owner-only local files, not repository fixtures.

## Provenance and health

- Menubar signed Debug build: M11-A base `186aa6d` plus uncommitted M11-B Observe-only implementation. Same measured session-only KCRW AAC/HLS item: `https://streams.kcrw.com/e24_aac/playlist.m3u8`. Frozen `+160s`, max selected age `1200s`, feed silence `120s`. Existing menubar title remained published; output route **category recorded as speaker**, not independently verified. No confirmed codec/rendition.
- Trace `kcrw-3813f218-1420-4a74-98e2-7c4629225b0f.jsonl`, SHA-256 `b14d66821c02a82b4b531112c7c64dd26d3bfd309555a69d84bdc9b7cce7bae5`; matching `.decisions.json` SHA-256 `3e92b920bb2d6845f36787602f75c4b7dfd7df86634e037bd00f8d309375c486`. Both are `0600` in local app Application Support; neither has been copied to the repo. 606 events over 576.430s, clean `ended=user`, 575 playback samples, 20 feed HTTP 200 responses, zero feed failures, no player metadata, four raw `heard_song_change`, one `speech_or_commercial`, four `wrong_title_or_line` buttons. No pause, lyric landmark, or confirmed route change.
- `stream-lab replay` passed twice, byte-identical SHA-256 `6105772eeea601bcfac35420231d8e2478f0b935ab4b89a6b3c78dbf8be5191c`; no wall/monotonic gap >2s. Feed cache age reached 44s. M11-A `stream-lab select` with a **temporary local annotation updated after listener confirmation** and frozen `--offset 160` passed twice, byte-identical SHA-256 `5ec9f0f11ecf7769aa3b72eda5afdcdb0a1c2da10c808fc36294389c1ed259f7`. Its four selected transitions match the app sidecar by occurrence and sampled time. Three confirmed song-start buttons are included in its metrics; the corrected commercial is not annotated as a song. The generic CLI footer about development-set traces does not reclassify this newly recorded smoke session as M11-A development input.

## Listener notes and timeline

The listener reported an approximately five-second **spoken KCRW commercial near the first song transition** but missed its speech button. Later, they pressed **Song change** at 440.837s, realized it was a commercial, pressed **Speech/commercial** at 451.316s, and pressed **Song change** at 501.000s when music returned. Treat the 440.837s press as a corrected speech/commercial marker, **not a song start**. The 451.316s speech button is not the precise beginning of the spoken segment. The earlier unmarked short commercial is a separate event. The listener confirmed **it ended before the 107.998s song-change button**, but its exact start/end are not recorded; the candidate's 106.442s change could have occurred during the ad. The listener also confirmed that the three marked new songs were “You've Made It,” “Twizzler,” and “How Long.” The feed contains no corresponding ad occurrence.

| Elapsed | Raw event or decision | Interpretation |
|---:|---|---|
| 3.391 | Candidate selects “What Am I Gonna Do?” — Aldous Harding | Mid-song join, not a marked start. Legacy title already displays “You've Made It.” |
| 47.203 | Wrong title button | Legacy “You've Made It”; candidate still “What Am I Gonna Do?”. Previous listener clarification says this button refers to the menubar title. |
| 106.442 / 107.998 | Candidate “You've Made It” — Gilligan Moss / song button | Signed sampled difference **−1.556s**; the short unmarked ad finished before the song button, but may overlap the candidate switch. |
| 144.445 / 153.193 | Legacy title “Twizzler” / wrong title button | Candidate still “You've Made It.” |
| 267.425 / 269.451 | Candidate “Twizzler” — Cigarettes After Sex / song button | Signed sampled difference **−2.025s**. |
| 385.442 / 388.753 | Legacy title “How Long” / wrong title button | Candidate still “Twizzler.” |
| 440.837 / 451.316 | Song button corrected as commercial / speech button | **Exclude 440.837s** from song-start metrics. Candidate remains “Twizzler”; it does not model ads. |
| 498.442 / 501.000 | Candidate “How Long” — Cousin Kula / listener says music returns | Signed sampled difference **−2.558s**; distinct from the corrected commercial marker. |
| 566.437 / 571.865 | Legacy “Wanderlust” / wrong title button | Candidate still “How Long”; no later heard-song-change button before stop. **Do not score “Wanderlust.”** |

**Three identified song starts:** candidate-to-button signed errors −1.556s, −2.025s, and −2.558s; median absolute error **2.025s**, worst **2.558s**. All three are within the proposed ±5s coarse-marker target, but n=3 is below the required five in one session. Buttons have human-reaction and approximately 1s player-sampling uncertainty, and the first ad's end was not timed; these are not first-audible-sample errors or ad-alignment proof. Legacy early-publication spans relative to the respective music buttons are 107.918s (“You've Made It,” from capture start), 125.006s (“Twizzler”), and 115.558s (“How Long”); these are display-to-button spans, not exact durations of audible title error. At 571.865s the wrong-title button has no subsequent music-change marker in this trace. No policy or offset was retuned.

## Next checkpoint

The listener confirmed the first short ad had ended before the 107.998s song button and named all three new songs. Do not promote the corrected 440.837s commercial button, the unmarked short ad, or the unconfirmed “Wanderlust” to song starts. This session has **three** identified music starts, fewer than five; a future full fresh fixed-policy session is required for the five-change target. Apply candidate remains a separate user-approval checkpoint, followed by lyric and pause validation.
