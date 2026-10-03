# M11-B — First attended Apply candidate smoke capture

**Status:** One listener-reported song transition. The user said the regular tracklist showed the next song early while the **scrolling menubar title changed exactly when they heard the song change**. This is useful attended evidence for Apply on the speaker route, **not** a station timing distribution, first-audible-sample measurement, synced-lyric validation, or rollout approval.

## Local provenance

- Signed Debug app `/tmp/pocketradio-m11b-apply-build/Build/Products/Debug/PocketRadio.app`; menubar M11-A base `186aa6d` with uncommitted M11-B changes. Mode `apply_candidate`, output route **`speaker` recorded in the sidecar**, session-only measured player item `https://streams.kcrw.com/e24_aac/playlist.m3u8`, frozen `+160s`, unmuted. The listener later confirmed all prior runs and this one used speakers; the previous third Observe sidecar still says `unrecorded` and remains immutable.
- Local owner-only `0600` trace basename `kcrw-cd849825-3861-475d-a95f-715bf559b5e7.jsonl`, SHA-256 `a2882bdf3926a735379cced0bf3b27a2eed939faaf8982285c061dec4199fa4d`; matching `.decisions.json` SHA-256 `38f977157101ce8faa6d9358daeb15efe7fd63bb4c9672052602866c19592226`. Neither raw file has been copied to the repo. 169 events / 162.445s, explicit `ended=user`, 159 playback samples, six successful feed responses, no feed failures, two human markers, no pause or lyric landmark.
- Raw `stream-lab replay` succeeded twice with byte-identical SHA-256 `dfe10a5a0ad9ef890d9a0b9ca8bc97a08013a064b805f2f9060e1709a09e339d`; wall/monotonic clocks agree with no gap >2s. M11-A `stream-lab select --offset 160` with a **temporary local feed-inferred No Others annotation**, excluded from aggregate metrics pending explicit listener song-title confirmation, succeeded twice with byte-identical SHA-256 `9e99de8104893944c8771a974285cabb7057a305f4727f9a6a90660902b44e31`. Its three selected occurrence transitions match the app sidecar's candidate and separately recorded `publishedTitle` transitions at sampled times. Replay contacts no live station.

## Timeline (seconds from fresh item)

| Elapsed | Evidence | Interpretation |
|---:|---|---|
| 5.987 | Candidate and published menubar title become “Bedroom Eyes” — Poolside. | Mid-song join; no listener song marker. |
| 10.050 | Candidate and published title become “The Letter Blue (Branchez Remix) - Heavy Duty” — Wet. | Another startup transition only 4.063s later; audible identity at this moment was not verified. |
| 12.820 | `speech_or_commercial` button. | The exact spoken start/end is unknown. Do not infer an ad-timing policy. |
| 45.050 | Separate legacy tracklist connection's title becomes “No Others” — Momoko Gill. | The early next-song entry the user noticed; not the published Apply title. |
| 60.446 | Experimental raw feed top first becomes “No Others.” | Feed availability, not audible onset. |
| **156.047** | Core candidate **and app `publishedTitle`** become “No Others.” | One same-item player-sample publication; exact media-clock sampled song estimate about 0.030s. |
| **159.653** | User marks `heard_song_change`. | User says scrolling title changed when the new music was heard. The sampled title leads the coarse button press by **3.606s**; listener perception and reaction time cannot be recovered from the press. |

Legacy title precedes the button by 114.603s; experimental feed top precedes it by 99.207s. Neither span is the exact duration of a wrong audible title. The title selected from history can differ from the feed-top row without losing feed chronology; lyric-line and Now Playing accuracy were **not** observed in this run. An early tracklist row is expected to be browseable; the visible selection marker and published title must still follow the same-item clock. The only audible title timing judgment is the listener's report for this one transition.

## Next checkpoint

Ask whether the heard new song was “No Others” — Momoko Gill; do not count its name as independently confirmed until then. Review applied title and Now Playing, selected history row, and any recognizable timed lyric landmarks on further **attended, speaker-route** sessions before a timing/lyric claim. Do not retune `+160s`, modify station URLs or saved lyric offsets, or commit/merge/roll out on this one smoke capture. Reconnect pause must be validated before buffered pause is considered.
