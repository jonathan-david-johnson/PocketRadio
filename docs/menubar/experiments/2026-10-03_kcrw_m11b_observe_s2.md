# M11-B — KCRW Observe-only session 2 (five identified songs; delayed buttons)

**Status:** Fresh 15m12s capture replays cleanly. The listener later confirmed all five new-song identities and explicitly confirmed **speakers for all Observe runs, including this one**, but **the route category was not recorded in this sidecar**. They deliberately waited a few seconds before each song button to rule out a commercial; the 5–8s candidate-to-button spans **cannot test the ±5s immediate-boundary target**. At the first wrong-title button they heard “calling all angles” while the menubar displayed “Get Better”; the feed and candidate spell the earlier title “Calling All Angels” — Jane Siberry. The earlier song's spelling/identity was not explicitly reconciled. Do not retune `+160s` or enable Apply candidate from these data.

## Local evidence

- Signed Debug Observe-only app with uncommitted M11-B code on M11-A base `186aa6d`; measured session-only `https://streams.kcrw.com/e24_aac/playlist.m3u8` item, frozen `+160s`, selected age `1200s`, feed silence `120s`. Existing title remained published. **Sidecar routeCategory=`unrecorded`**; the listener subsequently confirmed speakers for all Observe runs (and the current Apply test). Keep this post-hoc statement separate from immutable metadata; do not rewrite the sidecar or claim independently measured device latency or route continuity.
- Owner-only local trace basename `kcrw-0170b28a-dec0-4215-b466-4f8fb64c0f97.jsonl`, SHA-256 `e58ce9cd00609767bc4c5e850fce2a7c5cd9501b5cc433fe352bab7cc81c4f41`; matching `.decisions.json` SHA-256 `fca6e8ea9ee6ac27008105588ba8d440bf3696a43cb49cad3cbb90651454dea6`. Both `0600` in the app's local sandbox; neither copied into the repo. 956 events over 912.508s, ended explicitly by user; 912 player samples, 31 HTTP 200 feed responses and zero failures; five song-change buttons, five wrong-title buttons, one speech/commercial button; no pause or lyric landmark.
- `stream-lab replay` twice succeeded, byte-identical SHA-256 `35d210802dbfe4439d416af0ff17177aae33af76962649795a45ab1f225dc483`. Wall and monotonic time agree with no gap >2s; feed cache age up to 48s. M11-A `stream-lab select --offset 160` with **temporary local, listener-confirmed title annotations excluded from timing metrics due to deliberately late buttons** twice succeeded, byte-identical SHA-256 `fc4790b68f1f10a839d1d0f1255be3712562766fa55e54376d940656728762f5`. Six occurrence transitions match the app sidecar by ID and sampled time; aggregate timing metrics are intentionally `none`. The core reports only one startup missing clock pair, not a later invalidation. No audio was captured; neither replay contacted the live stream.

## Timeline and marker interpretation

The listener confirmed the five new song names after the capture. For each, they waited a few seconds after hearing music to be sure it was not a commercial. The reported time differences are to **delayed button presses**, not independently measured music onsets.

| Event | Elapsed (s) | Observation |
|---|---:|---|
| Initial candidate “Calling All Angels” | 3.341 | Feed artist Jane Siberry; mid-song join. Legacy menubar title already says “Get Better.” |
| **First wrong title** | **14.068** | User says the menubar showed **“Get Better”** while **“calling all angles”** played; candidate still showed “Calling All Angels.” Treat spelling/identity as an open confirmation, not a second title. |
| Candidate “Get Better” / song button | 54.365 / 59.522 | **−5.157s** sampled candidate-to-delayed-button difference; listener confirmed new song. |
| Legacy “Talk It Over” / wrong-title button | 113.378 / 133.947 | Candidate still “Get Better” at wrong-title button. |
| Candidate “Talk It Over” / song button | 260.380 / 265.434 | **−5.054s**; listener confirmed new song. |
| Legacy “Fossils” / wrong-title button | 294.436 / 313.535 | Candidate still “Talk It Over.” |
| Candidate “Fossils” / song button | 438.364 / 445.983 | **−7.619s**; listener confirmed new song. |
| Legacy “cherry spice” / wrong-title button | 536.364 / 539.958 | Candidate still “Fossils.” |
| Candidate “cherry spice” / song button | 682.376 / 689.320 | **−6.944s**; listener confirmed new song. |
| Legacy “Something Holy (Live at Funkhaus, 2019)” / wrong-title button | 777.360 / 790.494 | Candidate still “cherry spice.” |
| Speech/commercial button | 839.736 | Onset and end of speech not precisely marked; not a music start. |
| Candidate “Something Holy (Live at Funkhaus, 2019)” / song button | 890.377 / 898.477 | **−8.101s**; listener confirmed new song; speech may have preceded the music. |

Differences above are sampled candidate-change time minus listener button time, **not first-audible-sample errors**. Descriptively, the five absolute candidate-to-button spans have median **6.944s** and worst **8.101s**; both reflect intentional button delay of unmeasured length, so the five annotations are excluded from title-onset timing aggregates. Do **not** classify the >5s differences as a proven timing failure or infer that `+160s` needs retuning. The first wrong-title button confirms the legacy menubar title was wrong then; the candidate showed a similar, feed-spelled previous title, but the listener's “calling all angles” spelling was not separately confirmed. The listener confirmed speakers afterward, but the category was not recorded in this sidecar. Neither ad timing nor lyric accuracy follows from the trace. These five identified songs do not constitute a five-*precisely marked* session on a recorded route.

## Next checkpoint

For a future tighter onset test, set the in-app route category **before** capture and mark **immediately upon an audible change**, then confirm the song identity afterward; mark suspected speech separately. Do not retune the frozen offset from delayed button presses. Apply candidate was later separately approved for an opt-in test, not validated by this Observe trace; lyric, pause, commit, and rollout decisions remain separate.
