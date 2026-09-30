# KEXP AAC attended session — 2026-09-27

**Status:** First audible KEXP Stream Lab capture; useful metadata/feed counterexample, not enough identified song changes for a station timing policy. Complements the [KCRW AAC/HLS sessions](2026-09-26_kcrw_hls_attended.md) and [M10 handoff](../milestones/milestone_10_handoff.md).

## Setup and retained evidence

- Explicit stream: `https://kexp.streamguys1.com/kexp160.aac` (AAC/Icecast endpoint, **not** KCRW's HLS path). Explicit feed: `https://api.kexp.org/v2/plays/?limit=10`, polled every 30s. Stream Lab's persisted trace redacts the feed query. Unmuted macOS AVPlayer under `caffeinate -is`; output route not recorded. Menubar checkout remains `feature/stream-monitoring-lab` at `a995f06`, with `Tools/StreamLab/` untracked. Most recent package test result before capture: 51 passed on 2026-09-26.
- User reported initial pre-roll, a pause during “Sea Of Heartbreak,” and stopping at an airbreak. The user described the pause as ~30s; recorded commands at 549.481s and 588.511s are **39.030s apart**. Four `heard_song_change` markers were recorded: three named songs and the final airbreak, which is **not** a fourth song change.
- 737.777s (12m18s), ended `user`; 25 feed responses / 0 failures, 724 playback observations, **11 timed-metadata events**, one `playback_stalled` notice at 190.580s, and zero samples with `AVPlayerItem.currentDate()`. Replay clock spans agree, with no >2s gap. These are observations on this player item, not independent proof of speaker output timing.
- Retained trace: [`traces/2026-09-27_kexp_aac_attended_s1.jsonl`](traces/2026-09-27_kexp_aac_attended_s1.jsonl), owner-only `0600`, SHA-256 `2379d0d7a86226f8fe761a1d4cf317963448f9debe485295cb707be5006d3bd8`. Replay offline with `.build/debug/stream-lab replay <trace-path>`. Privacy review found public station/feed URLs, provider IDs, titles, artwork CDN links and timing, but no credentials, cookies, tokens, signed URLs, or local paths. No audio was recorded.

## Listener, metadata, and feed on one elapsed axis

| User-identified event | Human marker | First related player metadata | Feed-top first seen | Interpretation |
|---|---:|---:|---:|---|
| Initial pre-roll | No marker | 4.647s: ICY `insertionType=preroll`; first song title at 19.388s | Initial feed at 0.240s already listed “Pulling Up Roots” | A live feed entry can exist during listener-specific pre-roll. No first-song audible marker was taken. |
| The Deslondes — Good to Go | 159.054s | 143.082s (16.0s before marker); repeated at 161.448s (2.4s after) | 181.281s (22.2s after marker) | First title metadata was early; repeated title was later. One ICY callback is not necessarily an audible boundary. |
| Daniel Norgren — The Day That's Just Begun | 364.776s | 363.277s (1.5s before marker); repeated at 398.780s | 392.549s (27.8s after marker) | Metadata was close in this one transition; feed top lagged this listener. |
| Don Gibson — Sea Of Heartbreak | 542.044s | 540.421s (1.6s before marker); repeated at 608.912s | 573.735s (31.7s after marker, while paused) | Feed arrival is not a playback signal; repeat ICY title is not a second song start. |
| Airbreak / user stopped | 729.625s (`heard_song_change` key used for audible break) | 715.051s: `Kevin Sur - The Roadhouse` show title; no asserted first-break sample | 694.536s: provider `airbreak` row (35.1s before marker) | Preserve airbreak as a distinct content type, not a track. User ended at 737.777s. |

**Pause:** AVPlayer was paused at 549.481s and resumed at 588.511s. Its sampled media time remained approximately 538.2s throughout. The stream has no observed `currentDate()` media-to-UTC mapping, so the KCRW HLS `playedAt + ~160s` rule cannot be transferred to KEXP. One stall at 190.580s adds another reason not to estimate position from wall time alone.

**Replay regression (fixed 2026-09-30):** the KEXP parser had retained the provider `airbreak` row at 694.536s, but replay previously omitted it from `feed transitions` because it has no title. A synthetic track → untitled airbreak → track test now requires the break exactly once, and replaying this unchanged trace reports **five feed-top transitions**, including `"airbreak" (kind=airbreak)` at 694.536s. These are feed transitions, **not** five heard song changes; the listener marked only three songs and one break.

## Boundaries and next test

- The KEXP stream supplied useful `StreamTitle` values, unlike the measured KCRW streams. Their delivery is variable: a first title was ~16s early in one case and ~1.5s early in two others. Do not use the first ICY receipt alone as an exact audible boundary; do not treat the newest feed entry as audible either.
- Three identified song transitions plus one airbreak are insufficient for a five-song timing distribution. Another attended KEXP session should mark at least five **named songs**, note pre-roll and speech separately, record the output route, and exercise an intentional pause. Test occurrence selection against both early/repeated ICY and late feed entries without conflating this AAC/Icecast connection with KCRW AAC/HLS.
- No production playback code or station configuration was changed by this capture.
