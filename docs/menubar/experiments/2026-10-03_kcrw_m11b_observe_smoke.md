# M11-B — First KCRW Observe-only same-player smoke capture

**Status:** Provisional; one attended song marker. The listener clarified that the earlier wrong-title button referred to the normal menubar title, not the Observe-only candidate. The previous audible song's identity remains unconfirmed. No Apply candidate or lyric validation. The app trace and decision sidecar remain local; this report contains only public station metadata and hashes.

## Capture and provenance

- Menubar: `feature/stream-session-model` at M11-A commit `186aa6d`, with uncommitted M11-B changes. Signed Debug build from `/tmp/pocketradio-m11b-aac-source` (build location is not a retained artifact).
- Source favorite: KCRW Eclectic 24 (AAC), with source path `/e24_aac`. Session-only player item: exactly `https://streams.kcrw.com/e24_aac/playlist.m3u8`. No saved stream URL changed.
- Mode: Observe only; `+160s` frozen candidate, `maxSelectedAge=1200s`, `maxFeedSilence=120s`. Existing title stayed published. Output-route **category recorded by the user as speaker**, not independently verified; rendition/codec were not inspected.
- Local trace basename: `kcrw-2976607b-63e3-4efc-8582-44f901ccff16.jsonl`; SHA-256 `23033b16be7b2b1f86e9f978230ed62cc93ddaf3fb3fb2c68ac5b2e7b8ccb0f6`. Decision sidecar: matching `.decisions.json`; SHA-256 `c466e2579ef9e9cb83b710d0d31a0d95b5fe7dece792cf01384acd73fa674e2c`. Both owner-only `0600`, stored under the app's local sandbox Application Support; neither was copied to this repository.
- Complete trace: 228 events, 216.332s, explicit `ended=user`, 216 paired playback observations, eight HTTP 200 feed responses with zero failures, two human markers, no player metadata. Replay found no monotonic/wall-clock gap >2s. Cache age reached 36s. No pause or route change is evidenced.
- Offline observation `stream-lab replay` ran twice with byte-identical output (SHA-256 `f577f1eb6887a879c77cd1c13b6e83191fa6fcd8bfe90b4de909cc9fafa1da48`). M11-A `stream-lab select` with a **temporary, non-retained Bow Down annotation** ran twice at `--offset 160` with byte-identical output (SHA-256 `2b2abb5317231f0543452d0807a073390fc54f504bb7e479dcd1ce64880e80b2`). The generic `select` header calls all input “development evidence”; this fresh capture is an M11-B smoke check, not one of the M11-A retained development traces. The annotation excludes this single marker from aggregate metrics.

## Timeline (elapsed from this item, seconds)

| Event | Elapsed | Evidence |
|---|---:|---|
| Initial candidate “The Only One” — Logic1000 | 3.120 | Paired player sample and available feed occurrence; mid-song join, song estimate 56.000s. |
| Existing published title becomes “Bow Down” — Geese | 54.189 | App decision sidecar; legacy tracklist connection, not a player-audio boundary. |
| Experimental feed first receives “Bow Down” as top row | 60.401 | Raw trace response; not a player-audio boundary. |
| User marks `wrong_title_or_line` | 178.583 | Legacy menubar title and feed top are “Bow Down”; candidate remains “The Only One” (song estimate about 231s). The listener confirmed the **normal menubar title “Bow Down” was wrong** at this moment. The previous audible song was not named. |
| Candidate selects “Bow Down” | 194.182 | Player-triggered M11-A core replay and app sidecar agree on occurrence ID and sampled transition; candidate song estimate 0.033s. |
| User marks heard transition to “Bow Down” | 198.573 | Coarse listener marker reported in follow-up; both legacy and candidate display “Bow Down” here. |

**Candidate signed sampled error:** `194.182 − 198.573 = −4.391s` (candidate changed before the button press). The legacy published title changed `144.384s` before that marker; the feed top changed `138.172s` before it. Those are display/feed-to-marker spans, **not** proof of the first audible sample. Human reaction, player sampling, and the unidentified previous audible song limit the timing claim. The listener confirmed that the legacy menubar title “Bow Down” was wrong at the earlier marker; the candidate did not yet show “Bow Down” then. This is one marker, excluded from median/worst aggregates; it cannot establish an offset distribution, lyric-line accuracy, or route/rendition generality.

## Next decision

The wrong-title marker is now attributed to the **legacy menubar title “Bow Down.”** It was known wrong at 178.583s and the listener reported Bow Down became audible near the 198.573s button press; do not infer an exact audible onset or the earlier song's identity from those two coarse markers. Recommend a fresh fixed-policy Observe-only session with at least five identified changes before deciding whether to enable Apply candidate at its separate explicit checkpoint. Record route and lyric evidence separately.
