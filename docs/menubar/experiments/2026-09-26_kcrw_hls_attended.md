# KCRW AAC/HLS attended sessions — 2026-09-26

**Status:** Observed in two audible macOS AVPlayer captures; candidate alignment policy, not a production calibration. This record supplements the [earlier unattended MP3 sessions](2026-09-25_kcrw_sessions.md) and [M10 execution handoff](../milestones/milestone_10_handoff.md). The listener identified the named transitions and reported one missed marker and one station-ID commercial. A human keypress is coarse evidence, not the first audible sample.

## Setup and retained evidence

- Menubar checkout: `feature/stream-monitoring-lab` at `a995f06`; `Tools/StreamLab/` untracked. `swift test` passed **51 tests** (29 StreamLab, 22 StreamDiagnostics) before capture. macOS 26.6.2 (25G83).
- Explicit stream: `https://streams.kcrw.com/e24_aac/playlist.m3u8`; unmuted AVPlayer. Explicit feed: `https://tracklist-api.kcrw.com/Music/all/1?page_size=5`; serial polling every 30s. The persisted trace strips the feed query. `caffeinate -is` prevented sleep; both replay clock sections show no >2s gap. Listener output route was **not recorded**; do not extrapolate to Bluetooth, iOS, another stream, or another device.
- s1: 1500.541s (25m), end reason `user`, 50 feed responses / 0 failures, 1447 playback observations, 0 timed-metadata events, 5 heard-change markers and one 11.000s pause/resume. Trace: [`traces/2026-09-26_kcrw_hls_attended_s1.jsonl`](traces/2026-09-26_kcrw_hls_attended_s1.jsonl), SHA-256 `8c72bd4b694e55892cb36b9cc96063e85dbc4e271f4c1c503e996b7688924057`.
- s2: 929.185s (15m), end reason `user`, 31 feed responses / 0 failures, 902 playback observations, 0 timed-metadata events, 5 `heard_song_change` markers **including one commercial**, and one 31.367s pause/resume. Trace: [`traces/2026-09-26_kcrw_hls_attended_s2.jsonl`](traces/2026-09-26_kcrw_hls_attended_s2.jsonl), SHA-256 `92d5a557fa0633cd1eb3561b0f92fdd3645153583173ce9ae773d8c482b3805c`.
- Replay offline with `.build/debug/stream-lab replay <trace-path>` from `pocket-radio-menubar/Tools/StreamLab`. Both traces are owner-only `0600`, contain public feed titles, artwork CDN URLs and media timing but no audio. Privacy scan found no account credentials, cookies, tokens, unredacted local paths, or signed HLS query parameters. The separate 25 MB browser HAR remains **only in `~/Downloads/www.kcrw.com.har`**; it includes browser request data and is **not** copied into the repo.

## Track-to-audio timing

Each row pairs the feed entry's `playedAt` with a listener's marker, then finds the nearest one-second AVPlayer sample's `programDate` (`AVPlayerItem.currentDate()`). Track names for s1's first three markers are inferred from the matching order and intervals; the listener explicitly identified “Things Take Time” and the missed “What Was I Made For?” transition. In s2 the listener explicitly distinguished the station ID from “Fools in Love.” Marker/one-second-sample uncertainty is a few seconds.

| Session | Audible transition | Marker elapsed | Wall marker − feed `playedAt` | Player `programDate` − feed `playedAt` | Feed first seen before marker |
|---|---|---:|---:|---:|---:|
| s1 | I Go Up, You Go Down | 70.169s | 165.751s | 160.004s | already present at start; first capture poll 70.090s earlier |
| s1 | Hardy (feat. Clairo) | 280.526s | 166.097s | 160.767s | 99.641s |
| s1 | I Feel Electric (Max Essa remix) | 512.842s | 165.412s | 159.252s | 120.679s |
| s1 | What Was I Made For? | **missed** | — | — | observed in feed; no audible marker |
| s1 | Things Take Time | 1250.627s | 168.194s | 162.669s | 133.896s |
| s1 | Wanderlust (after 11.000s pause) | 1454.514s | 178.081s | 160.789s | 156.765s |
| s2 | Barthelona | 88.860s | 168.739s | 163.171s | already present at start; first capture poll 88.714s earlier |
| s2 | Fools in Love (after station ID) | 304.635s | 165.513s | 160.458s | 123.909s |
| s2 | Friend of Mine | 584.657s | 164.578s | 159.057s | 102.622s |
| s2 | Colosse (after 31.367s pause) | 833.198s | 196.122s | 158.863s | 170.361s |

**Observed:** all nine identified song markers put AVPlayer's media/program date **158.863–163.171s** after that song's claimed feed timestamp, including both post-pause markers. This is an empirical ~160s relationship **for this exact HLS variant and this macOS listening path**, not proof of the feed timestamp's semantic meaning or a sample-accurate song boundary. The pre-pause wall-clock offsets are ~165–169s; after pausing, wall-clock offsets rise by approximately the pause duration while the media-date offsets remain near 160s. In s1, `programDate − wallTime` moved from roughly −5.8s before pause to −16.8s after it. In s2 it likewise moved by roughly 31s. The feed is sufficiently far ahead of this listener that even a cached result was visible well before the identified song became audible in these captures.

**Pause coincidence:** s1's `pause_requested` marker was at 1297.411s, and the next scheduled feed request returned “Wanderlust” at 1297.749s. AVPlayer was paused on “Things Take Time”; its media time stopped. The feed request was already due on the independent 30s poll cycle. Pausing did not cause the feed change. The later heard-Wanderlust marker retained the ~160s *media-date* difference.

**Station ID:** in s2 the listener heard a short KCRW commercial/station ID start at 246.879s, then “Fools in Love” at 304.635s (57.756s later). The feed first showed “Fools in Love” at 180.726s, remained on it through the commercial, and returned no `[BREAK]` in the captured five-entry responses. Thus the feed top is not an audible-track assertion; a title-only time shift cannot identify an unreported ad. The user does **not** require ad identification for this slice. The 246.879s marker must not be counted as a Fools song start.

**Cache:** s1 observed up to 60s of response age; s2 up to 43s. This confirms the earlier stale-cache finding for feed *arrival*, but revises its product implication for this HLS listener: a feed entry often arrives 1–3 minutes **before** that listener reaches the corresponding song. Cache refresh need not be the limiting factor for a playback-aligned title **if an established media-to-feed mapping is valid**. Do not mistake first receipt for publication time or use a stale preceding response to claim a positive publish-lag lower bound.

## Website comparison and product direction

A separate browser HAR of `https://www.kcrw.com/playlists?channel=Music` (2026-09-26 11:51–11:53 UTC) shows AAC HLS media requests for `e24_aac/playlist.m3u8` and segments. The bundled page code polls `/Music/all/1?page_size=5` every 30s and labels the first live row “Now Playing”; the global live player independently fetches `/Music` at start and every 60s for its title/art. Its day-long progress counter uses wall time against the schedule, not the audio element's media position. In the HAR, the player fetched “Let Me Go” at 11:52:39 UTC and the playlist first fetched it at 11:53:09 UTC: the two displays were 30s apart. This is **not** evidence that the website precisely follows the audible boundary. HAR audio and Stream Lab audio were on different connections and must not be put on one timeline.

**User preference:** use the AAC HLS variant for a proposed KCRW playback improvement; the user wants the highest-quality AAC route and is not prioritizing ad recognition. This is a product direction, not evidence that every AAC rendition or output route shares this calibration. The menubar app currently reads its actual radio URL from the station (`PlayerViewModel.swift`); the curated KCRW entry still names `e24_mp3`. Changing that production endpoint requires a separate explicit implementation and validation.

**Candidate, not shipped:** for this AAC/HLS variant, keep the full feed history but select the latest occurrence whose `playedAt + estimated ~160s` has been reached by `AVPlayerItem.currentDate()`, rather than assigning feed row zero immediately. Drive lyric position from that same media clock; freeze on pause/stall, reset/recalibrate on a new item or timing discontinuity, and keep station/endpoint calibration separate from the user's recording-specific lyric correction. The current menubar `PlayerViewModel.swift` selects `tracklist.first` on each 30s poll and drives lyrics with `Date.now − playedAt + lyricOffset`; its live-radio pause tears down the item, unlike Stream Lab's deliberate AVPlayer pause. Do not transfer this pause behavior or the 160s number blindly. Handle missing `currentDate()`, stale/missing entries, feed corrections, repeats, and unreported speech conservatively. No production code, station configuration, or persisted lyric offset was changed here.

Next: prototype the media-clock occurrence rule against these two replay fixtures, test early-feed/pause/commercial cases, then run an audible menubar build on the **actual selected AAC endpoint** and output route before adopting or tuning a production offset. KEXP and iOS/Bluetooth/CarPlay remain separately unmeasured.
