# Experiment: what free audio sources exist, and how do they behave?

**Status**: DONE — 2026-10-29. One snapshot, one network vantage point (this Mac, US). Evidence is in [`traces/2026-10-29_landscape/`](traces/2026-10-29_landscape/). The survey tool is [`tools/source-survey.py`](../../../tools/source-survey.py).
**Scope**: Cross-platform. Informs which sources the apps add after KEXP, KCRW and radio-browser search.

## Result in brief

1. **Radio-browser is the right backbone.** It lists 69,425 stations. Its "working" flag was accurate: 96.5% of 600 sampled "working" stations answered with audio or a playlist.
2. **The field is uniform.** Of reachable stations, 94% serve progressive HTTP, almost all MP3 (69%) or AAC (23%), almost all with ICY metadata. HLS is 6%.
3. **Three problems recur:**
   - **In-band titles are often useless.** 31% of ICY streams send an empty first title. About 16% more echo the station name or send other non-song text.
   - **One in three streams is plain `http://`.** A page served over `https` cannot play it. 54% of the sampled `http` streams also worked over `https` with a valid certificate.
   - **A browser cannot read most stream headers.** Only 37% of progressive streams allow the `Icy-MetaData` request header in a CORS preflight.
4. **Hosting platforms have fixed now-playing APIs.** Some are open, some need keys, and several are open with CORS. One adapter per platform covers many stations. See [E4](#e4-metadata-side-channels-by-hosting-platform).
5. **Two sources are cleaner than anything in the sample:** SomaFM (JSON API, HLS with ID3 titles, CORS `*`) and Radio Paradise (lossless FLAC, JSON now-playing with cover art).
6. **Free non-radio audio exists but is a different player model.** Internet Archive, Audius and Wikimedia Commons serve files with Range support, not live streams.

Recommendations and the decisions they need are at the [end](#decision-gate).

## Question

Beyond the two custom integrations (KEXP, KCRW) and radio-browser search, what ways exist to get free, legally streamable audio? For each, what are its transport, codec, metadata, access rules and failure modes?

## Method and limits

- **Observed** means a request made on 2026-10-29 from this Mac, with a record in `traces/`. **Documented** means vendor behavior not re-checked here. Each claim below carries one of those labels or says so.
- The survey tool opens one connection per URL and reads up to 96 KB. It sends `Icy-MetaData: 1`, a fake `Origin` header (`https://app.pocketradio.example`), and a descriptive `User-Agent`. It stores no audio. It does not log in, solve challenges or get around geo-blocks.
- **Limits that affect the numbers:**
  - The tool speaks HTTP/1.0 and Python's system TLS. It cannot report TLS 1.3 support.
  - Some 401 and 403 failures may come from the user agent or the US vantage point. They are not proof the stream is dead.
  - Only the first ICY metadata block is meaningful. Later blocks are empty when the title is unchanged.
  - For HLS, only the first variant and the last segment were read.
  - A probe shows what a server sends. It does not show what AVPlayer or a browser plays.
- **Sample error:** with n≈600, a percentage is within about ±4 points. Stratum samples of 12 per platform are illustrations, not estimates.

## E1. Source taxonomy

Families, with at least one verified live example each unless marked. "Open" means no key or login was needed.

| Family | Examples | Access | What it gives |
|---|---|---|---|
| Community directory | radio-browser | Open, CORS `*` | 69,425 stations, stream URLs, codec, bitrate, HLS flag, check status, geo, tags |
| Commercial directory | TuneIn OPML, iHeart API | Open, no CORS (TuneIn); open with CORS `*` (iHeart) | Search, direct stream URLs, now-playing (TuneIn); 3,751 live stations (iHeart) |
| Legacy directory | Icecast YP (`dir.xiph.org`) | Open, CORS `*` | 30,255 entries, 10,144 with a listen URL |
| Keyed directory | SHOUTcast directory, Podcast Index, Jamendo | Free key | Observed: the request fails without a key |
| Partner-only directory | Airable (vTuner successor) | Documented: partner licence | Not verified: the TLS check failed from this Mac |
| Blocked or bot-protected | Radio Garden | Undocumented API | Search worked once, then a Cloudflare challenge blocked later requests. Not retried or bypassed |
| Site-only | radio.net, Streema | HTML only | No public API seen |
| Broadcaster-operated | BBC, NPR member stations, Radio France, ARD/Deutschlandfunk, NPO, VRT, RNZ, SRG, CBC, ABC, NHK | Open streams, no registration | The station's own URL |
| Curated indie | SomaFM, Radio Paradise, NTS, WFMU, dublab, Rainwave | Open streams, public APIs | Best metadata in the sample |
| Hosting platform | Icecast, SHOUTcast, AzuraCast, Zeno, laut.fm, Radio.co, RadioJar, RadioKing, Live365, Airtime Pro, Triton/StreamTheWorld, iHeart/Revma, StreamGuys | Stream open, API varies | Streams plus a platform-specific now-playing endpoint |
| Open-licence music | Audius, Wikimedia Commons, ccMixter | Open | Files with licence data; no live timeline |
| Archive | Internet Archive (14.2M audio items) | Open, CORS `*` | Files with Range support, per-item metadata |
| Spoken-word archive | LibriVox | Open | JSON catalogue; audio is zips and RSS, files live on archive.org |
| Podcast index | Apple iTunes Search | Open, CORS `*` | Podcast feed discovery |
| Preview-only | Deezer search | Open, no CORS | Documented: 30-second previews, not full audio |
| Not free-use | Spotify, SoundCloud | OAuth required (observed 401) | Out of scope |
| Retired | Free Music Archive API | Observed 404 | Dead |
| Not verified | Openverse audio API | Timed out at 30 s and 60 s | Retry later |

## E2. Directory corpus profile

Radio-browser dump of 2026-10-29 (`de1.api.radio-browser.info`): **69,425 stations; 62,375 flagged working (`lastcheckok=1`)**. Tables below describe the working set. Full tables: [`e2_corpus_tables.txt`](traces/2026-10-29_landscape/e2_corpus_tables.txt).

| Dimension | Result |
|---|---|
| Codec | MP3 67.9%, AAC+ 14.3%, AAC 13.4%, unknown 3.1%, Ogg 1.0%, FLAC 4 stations |
| HLS flag | 6.6% (4,118) |
| Scheme of resolved URL | `https` 64.5%, `http` 35.5% |
| Reported bitrate | 128 kbps 41.6%; **missing (0) 15.3%**; 64 kbps 13.1%; 192 kbps 11.9%; 320 kbps 8.5% |
| Distinct hosts / domains | 14,595 / 7,328 |
| Top countries | US 12.2%, DE 10.1%, FR 5.8%, RU 4.9%, MX 4.6%, GB 3.7% |
| Language field empty | 34.1% |
| Has favicon / homepage / geo point | 62% / 95% / 22% |
| URL differs from the submitted URL (playlist or redirect pre-resolved) | 4,624 (7.4%) |
| Same resolved URL listed more than once | 10,849 entries (17.4%) |
| Resolved URL carries a token or signature (`rj-tok`, `zt`, `token`, `sig`…) | 711 (1.1%), plus 487 with a `uuid` or session parameter |
| Extended info (`has_extended_info`) | 1.3% |

**Platform share by URL pattern** (heuristic, working set; [`e2_platform_share.txt`](traces/2026-10-29_landscape/e2_platform_share.txt)). About 34% of stations sit on a platform I could name:

| Platform | Share | | Platform | Share |
|---|---:|---|---|---:|
| Zeno | 4.9% | | Qingting/Qtfm (CN) | 2.1% |
| Triton/StreamTheWorld | 4.5% | | Infomaniak | 1.6% |
| Radiocast-family hosts | 4.5% | | iHeart/Revma | 1.4% |
| AzuraCast | 3.6% | | NRJ, SecureNet, Radio.co, StreamGuys, Live365 | 1.0–1.3% each |
| laut.fm | 2.4% | | Self-hosted on an explicit port | 26.0% |

40.2% matched no rule. These are unnamed hosts, not necessarily self-hosted.

Radio-browser's own check is fresh: 69,400 of 69,425 rows were last checked in October 2026.

## E3. Live probe of a station sample

1,194 URLs: 600 uniform from working stations, 100 from broken ones, 150 HLS-flagged, 22 platform strata × 12, 80 original playlist URLs. Seeded sample (`20261029`), so the list is reproducible: [`e3_sample_list.jsonl`](traces/2026-10-29_landscape/e3_sample_list.jsonl). Results: [`e3_probe_results.jsonl`](traces/2026-10-29_landscape/e3_probe_results.jsonl), tables in [`e3_tables.txt`](traces/2026-10-29_landscape/e3_tables.txt).

### Reachability

| Group | n | Reachable |
|---|---:|---:|
| Flagged working | 600 | 96.5% |
| Flagged broken | 100 | 6.0% |
| HLS-flagged working | 150 | 94.7% |
| Original URL was a playlist (PLS 50%, M3U 12.5%, plain 37.5%) | 80 | 98.8% |

- Failures of working-flagged stations: HTTP 403 (6), 404 (5), 401 (3), connect timeout (2), and one each of connect error, 503, DNS, 500, TLS.
- Failures of broken-flagged stations: 404 (25), connect error (14), DNS (14), connect timeout (11), 403 (7), 502 (6).
- 30% of reachable URLs needed at least one redirect or playlist hop.
- 95.5% of first bytes arrived within 2 seconds.

### Transport and codec (600 working-flagged, 579 reachable)

| | |
|---|---|
| Progressive HTTP | 93.8% |
| HLS | 6.2% |
| MP3 / AAC (ADTS) / Ogg (FLAC, Opus, Vorbis) | 68.9% / 23.1% / 1.6% (of reachable) |
| MP3 bitrate | 128 kbps 52%, 192 kbps 17%, 320 kbps 9%, 64 kbps 8% |
| `https` / `http` after redirects | 65.8% / 34.2% |
| ICY-style status line (`ICY 200 OK`) | 0.5% |
| Radio-browser codec matches observed codec | 529 of 532 stations labelled MP3 or AAC; reported bitrate matches exactly in 341 of 399 MP3 streams (85%) |

Content types seen: `audio/mpeg`, `audio/aacp`, `audio/aac`, `application/vnd.apple.mpegurl`, `application/ogg`. `audio/aacp` is HE-AAC by convention (documented), not by this probe.

### In-band metadata (progressive streams)

- 96.7% send `icy-metaint`. Intervals: 16000 (69%), 8192 (14%), 32768 (7%), 16384 (6%), 1024 (2%).
- 94.3% send `icy-name`.
- First `StreamTitle`, of the 525 streams with ICY:

| First title is… | Share | Example |
|---|---:|---|
| `Artist - Title` | 52.4% | `Collin Raye - The Gift` |
| Empty | 30.9% | KCRW, KEXP, NTS, NPR |
| Other text | 8.8% | `RENK FM TAMER KERIMOGLU 0532 691 16 72` |
| Echo of the station name | 7.6% | `The WOLF - Hannover` |
| Ad or spot marker | 0.4% | `text="Spot Block End" amgTrackId=…` |

- Two stations leak structured automation fields into the title (`song_spot=`, `spotInstanceId=`, `amgArtworkURL=`). Parsers must handle them.
- 18 of 543 progressive streams (3.3%) send no ICY at all, including Radio Paradise's FLAC, Rainwave and some Cloudflare-fronted stations.
- Ogg streams carry Vorbis comments instead of ICY. This probe's 24 KB read found none, so Ogg metadata is **not verified**.

### CORS and browser access (progressive)

- `Access-Control-Allow-Origin` on the stream: `*` 58.2%, echoes any origin 33.5%, absent 7.2%, a fixed other origin 1.1%. Plain `<audio>` playback needs none of this.
- Reading ICY from a browser needs `fetch` with the `Icy-MetaData` header, which triggers a preflight. The preflight response allowed that header in **37.3%** (listed 29.7%, wildcard 7.6%). 45.1% returned no allow-headers list and 17.7% returned a list without it.
- **KEXP's** preflight allows only `Range`. **KCRW's** allows `ETag, If-None-Match, X-AIS-SessionID`. Neither lets a browser request ICY.

### TLS and mixed content

- 34.2% of reachable streams end on `http://`. An `https` page cannot load them (documented browser rule). For native apps, whether App Transport Security blocks them is **not tested here**.
- [Upgrade test](traces/2026-10-29_landscape/e3_http_upgrade_results.jsonl): the same URL with `https://` worked for 118 of 198 `http` streams. A valid certificate was behind 106 of those (54% of the 198).
  - No explicit port in the URL: 103 of 105 worked.
  - Explicit port (for example `:8000`): 15 of 93 worked.
- Three streams in the main sample had certificate errors.

### HLS (142 reachable of the 150 HLS-flagged)

| | |
|---|---|
| Master playlist | 69% |
| Audio codec in master | AAC-LC (`mp4a.40.2`) 54%, HE-AAC (`.5`, `.29`) ~18%, `mp4a.40.34` (MP3) 3%, not stated 15% |
| Variants with video (`avc1`) | 5 stations |
| Segment type | MPEG-TS 47%, raw ADTS `.aac` 37%, MP3 4%, fMP4/CMAF 3.5% |
| Target duration | 10–11 s 44%, 6 s 17%, ≤4 s 19% |
| `EXT-X-PROGRAM-DATE-TIME` | 35% |
| `EXT-X-DATERANGE` | 3% (the ones inspected were ad markers: `X-AD-ID`, `X-AD-DURATION-MS`) |
| Encrypted | 0% (one playlist said `METHOD=NONE`) |
| Low-latency tags | 4% |
| Ended (VOD) playlists | 1.4% |
| ID3 tags in the last segment | 37% |
| Of those, with text frames (`TIT2`, `TPE1`, …) | about 32 stations, 23% of reachable HLS |
| Of those, only the Apple timestamp `PRIV` | about 22 stations |
| CORS `*` / origin echo / none | 73% / 24% / 3% |

Verified by reading the tags: SomaFM's HLS carries `TRSN`, `TRSO`, `TIT2` ("Hermetic Laws"), `TPE1` ("Jens Buchert") and `TALB`. iHeart's carries `TIT2`, `TPE1` and a `WXXX` frame with `song_spot="M" … length="00:03:06"`. So title metadata exists inside HLS audio segments for some stations, and `PROGRAM-DATE-TIME` is present on 35% (BBC, Radio France, ABC, NHK have it; CBC does not).

## E4. Metadata side channels by hosting platform

One request per station against its own origin, using real hosts from the E3 sample. "Useful" means the body held a now-playing field. Raw: [`e4_platform_sidechannels.jsonl`](traces/2026-10-29_landscape/e4_platform_sidechannels.jsonl).

| Platform | Endpoint | Tried | Useful | CORS on useful | Notes |
|---|---|---:|---:|---:|---|
| Icecast | `/status-json.xsl` | 70 | 37 (53%) | 33 | Per-mount `title`, `listeners`, `audio_info`. Some servers hide it |
| SHOUTcast | `/7.html` | 60 | 43 (72%) | **2** | `listeners,…,bitrate,Artist - Title` in an HTML wrapper |
| SHOUTcast | `/stats?sid=1&json=1` | 60 | 45 (75%) | **3** | Adds `songtitle`, `servertitle`, history on some |
| AzuraCast | `/api/nowplaying` | 44 | 35 (80%) | 35 | Rich: artwork, history, next song, listeners. 9 more returned `[]` or an error |
| laut.fm | `api.laut.fm/station/<name>/current_song` | 32 | 32 (100%) | 32 | Title, artist, album, start and end time |
| Radio.co | `public.radio.co/stations/<id>/status` | 14 | 14 (100%) | 14 | `current_track`, live-DJ info |
| Triton/StreamTheWorld | `np.tritondigital.com/public/nowplaying?mountName=…` | 40 | 22 (55%) | 22 | XML. The rest returned an empty list |
| RadioJar | `/api/stations/<id>/now_playing/` | 18 | 8 (44%) | 8 | The rest answered with an empty title |
| Live365 | `api.live365.com/station/<mount>` | 14 | 14 returned 200 | 14 | Station record; current-track field not extracted |
| Zeno | `api.zeno.fm/mounts/metadata/subscribe/<mount>` | 2 | 2 | `*` | Server-sent events: `streamTitle`, `streamUrl` with artist and album |
| RadioKing | `api.radioking.io/widget/radio/<id>/track/current` | 16 | 0 | | **Not verified.** The URL numeric id is not the API id |
| iHeart/Revma | `us.api.iheart.com/api/v3/live-meta/stream/<id>/currentTrackMeta` | 30 | 0 | | **Not verified.** The id taken from the stream URL is wrong |

Reading across the rows:

- **SHOUTcast has no CORS.** A web app needs a server-side proxy to use it. Icecast and the newer platforms mostly allow browsers.
- **No platform returns an audio timestamp.** Titles tell you what is playing, not where in the stream a song began. Media-time alignment (as used for KEXP and KCRW) still needs a clock source.
- The iHeart open search endpoint works, and so does `liveStations` (3,751 stations). The now-playing endpoint needs its own station id, which this experiment did not obtain.

## E5. Named-source profiles

Streams were probed with the survey tool. URLs came from the hand-picked list ([`e5_named_streams.jsonl`](traces/2026-10-29_landscape/e5_named_streams.jsonl)) and from radio-browser lookups by name ([`e5_radiobrowser_lookup.jsonl`](traces/2026-10-29_landscape/e5_radiobrowser_lookup.jsonl)). APIs were probed in [`e4_api_probes.jsonl`](traces/2026-10-29_landscape/e4_api_probes.jsonl). The two custom sources are first, as the baseline.

Radio-browser name lookup found a reachable stream for all 28 intended sources. Two of the entries it returned were dead (one dublab, one Worldwide FM), and the query "nts 1" matched an unrelated station (Northants 1).

| Source | Transport and codec | In-band title | Side channel | CORS (stream / API) | Notes |
|---|---|---|---|---|---|
| **KEXP** (baseline) | AAC 162 kbps ADTS, `https`; also MP3 128 at `live-mp3-128.kexp.org` | Empty in this run. The September menubar capture saw an ad pre-roll (not re-observed here) | `api.kexp.org/v2/plays/` JSON | `*` / `*` | Preflight allows only `Range` |
| **KCRW** (baseline) | MP3 192 or AAC 256, `https` | Empty (matches earlier finding) | `tracklist-api.kcrw.com` JSON | echoes origin / `*` | One of the guessed alternative URLs returned 404 |
| SomaFM | MP3 128/256, AAC 128/64/32, HLS AAC 320 | `Artist - Title` | `channels.json` (51 channels; `lastPlaying`, `listeners`, `preroll`, PLS per quality); `songs/<id>.json` | `*` / `*` | HLS has ID3 `TIT2`/`TPE1`/`TALB` and `PROGRAM-DATE-TIME` |
| Radio Paradise | MP3 128, AAC 320, **FLAC 1,441 kbps** (no ICY) | `Artist - Title` on MP3/AAC | `api.radioparadise.com/api/now_playing` (cover, year); `get_block` API with event timing | echoes origin / none | Lossless, free. API sends no CORS header |
| NTS | MP3 256 (`stream-relay-geo.ntslive.net`; radio-browser lists `*.radiomast.io`) | Empty | `nts.live/api/v2/live` (show title, times) | echoes origin / `*` | Show-level metadata, not track-level |
| WFMU | MP3 128 | Two formats seen: `Artist - Title` and `"Title" by Artist` | None found | one fixed origin | Title format varies by show |
| dublab | MP3 192 (Airtime Pro) | `Artist - Title` on the main stream; show title on dublab DE | Airtime Pro API (not probed) | echoes origin | `dublab.out.airtime.pro` |
| Worldwide FM | MP3 (RadioCult host) | `Live` | Not probed | n/a | My first guessed hostname did not resolve |
| WNYC | AAC | Show or segment title | Not probed | echoes origin | Titles are programme text, not songs |
| NPR 24-hour | MP3 96 | Empty | Station Finder API open (`api.npr.org/stationfinder/v3`); Listening API needs auth (401) | echoes origin / echoes origin | `KEXP` query returned no stations |
| BBC World Service | MP3 56 at `stream.live.vc.bbcmedia.co.uk` | Station-name echo | None | `*` / not probed | |
| BBC UK networks | HLS via `as-hls-ww-live.akamaized.net`, `PROGRAM-DATE-TIME`, no ID3 | none | `rms.api.bbc.co.uk` returned 403 | `*` / 403 | The old `bbc_6music` URL on `bbcmedia.co.uk` returned HTML, then HTTP 400. Radio-browser holds the new HLS URLs. Geo limits were not tested |
| Radio France | MP3/AAC on `icecast.radiofrance.fr`; HLS with `PROGRAM-DATE-TIME` | None | Live API returned 503 | echoes origin / none | |
| Deutschlandfunk, NDR (ARD `rndfnk.com`) | MP3 128 | `Artist - Title` or show | Not probed | echoes origin | |
| NPO, VRT, RTÉ, RNZ | MP3 192/128/160/64 | `Artist - Title` (NPO), station name (VRT), none or empty (RTÉ, RNZ) | Not probed | mixed | |
| SRG (SRF 3, Swiss Jazz) | MP3 128, redirects to `http` nodes | `Artist - Title` | Not probed | echoes origin | `http` after redirect |
| CBC | HLS AAC ADTS segments, 11 s target | none | Not probed | `*` | `PRIV` ID3 only; no `PROGRAM-DATE-TIME` |
| ABC (Triple J) | HLS and AAC via `abc.streamguys1.com`, `abc-cdn.net.au` | none | Not probed | | The `mediahubaustralia.com` URL returned 403 here |
| NHK | HLS with `PROGRAM-DATE-TIME` | none | Not probed | | My guessed URL did not resolve; radio-browser's did |
| Jazz24 | AAC 64 | `Artist with …` | Not probed | | |
| KUTX | AAC and MP3 192 on `streams.kut.org` | Fixed text: "THIS STATION WILL CONTINUE AFT…" | Not probed | | Title is a placeholder in this run |
| AzuraCast demo | MP3 128 | `Artist - Title` | `/api/nowplaying` | echoes origin / `*` | Reference implementation |
| iHeart | HLS AAC with ID3 `TIT2`/`TPE1`/`WXXX` | none | Open search and `liveStations` | `*` / `*` | Tokenised URLs (`rj-tok`) |
| TuneIn (OPML) | n/a (directory) | n/a | `Search.ashx`, `Tune.ashx` (direct stream URLs with reliability and bitrate), `Describe.ashx` (fields for current song, artist, album art) | none | Anonymous JSON. Documented: unofficial, terms unclear |
| Xiph directory | n/a | n/a | `yp.xml`, 8.3 MB, 30,255 entries | `*` | 33% have a listen URL, 27% a current song |
| Internet Archive | MP3, Ogg, FLAC files; `Range` supported; redirect to a data node | n/a | `advancedsearch.php`, `/metadata/<id>` (length, format, size) | `*` / `*` | 14.2M audio items. One download call returned 503 once |
| Audius | Stream via signed 302 to a creator node | n/a | `discoveryprovider.audius.co/v1/tracks/trending` and related | `*` / `*` | No key; `app_name` parameter. Signature timestamp in the redirect |
| Wikimedia Commons | Ogg, also Opus/FLAC/WAV (documented) | n/a | `commons.wikimedia.org/w/api.php` | none / none | Licence data in `extmetadata` |
| ccMixter | MP3 | n/a | `ccmixter.org/api/query` | none / none | Licence per upload |
| LibriVox | MP3 zips and RSS; files on archive.org | n/a | `librivox.org/api/feed/audiobooks` | none | No streaming URL in the API |

## Hypotheses

| # | Prediction | Result |
|---|---|---|
| 1 | Most stations are progressive MP3/AAC with ICY; HLS a minority | **Supported.** 93.8% progressive, 96.7% of those send ICY, HLS 6.2% |
| 2 | Dead entries exceed radio-browser's own count | **Not supported.** 96.5% of working-flagged stations answered; 6% of broken-flagged ones did too. Caveat: some failures may be client or region specific |
| 3 | Many stations lack CORS | **Partly supported.** Only 7% omit `Access-Control-Allow-Origin`, but 63% reject `Icy-MetaData` in a preflight |
| 4 | `http` streams are common enough to matter | **Supported.** 34–36% |
| 5 | Some ICY metadata is unusable | **Supported.** 31% empty, 16% echo or non-song text, 0.4% ad markers |
| 6 | Platforms share fixed metadata side channels | **Supported for 8 platforms** (Icecast, SHOUTcast, AzuraCast, laut.fm, Radio.co, Triton, RadioJar, Zeno). Two (RadioKing, iHeart) not verified |
| 7 | Non-radio sources have clean metadata and stable URLs but no live timeline | **Supported**, with one exception: Audius stream URLs are signed redirects with a timestamp |

## Other findings

- **Short-lived URLs.** Zeno (`zt=`), RadioJar and Revma (`rj-tok=`, `rj-ttl=5`) put tokens in their stream URLs. Radio-browser stores some of them. Those stored URLs may not outlive a day. The experiment did not test expiry.
- **URL churn.** BBC 6 Music's old `bbcmedia.co.uk` URL no longer serves audio to this client. Radio-browser lists different hosts (HLS on `akamaized.net`). NTS has two working hosts: `stream-relay-geo.ntslive.net` and `*.radiomast.io`. KUTX sends a placeholder title.
- **A real bot wall.** Radio Garden served one search and then a Cloudflare challenge (`cf-mitigated: challenge`). Not retried and not bypassed.
- **Other codecs are rare.** Ogg is 1.6% of the sample and 1.0% of the corpus. FLAC is 4 stations (plus Radio Paradise's own). WMA/ASX is 0.1%. RTMP and MMS: none seen. DASH: none seen.

## Not tested

- Whether AVPlayer, the web audio element, ExoPlayer or Roku play each codec. Documented, not verified: AVPlayer does not play Ogg Vorbis or Opus-in-Ogg.
- Geo-blocking. All requests came from the US.
- Stability over time. This is one snapshot.
- Whether an ICY title is accurate against the audio. E3 checks presence, not correctness.
- Terms of use for redistribution or caching of any source.
- Now-playing for iHeart and RadioKing; Openverse; the Airtime Pro API; Ogg comment metadata.

## Decision gate

The user decides. Each option is stated in plain words, with a recommendation.

1. **Which sources to add next.**
   - **A. Add SomaFM and Radio Paradise as curated stations.** They have documented APIs, clean titles, and CORS where needed. Radio Paradise adds lossless audio. Cost: low. Both are listed in radio-browser already, so a stub could work today.
   - **B. Add NTS.** Show-level metadata only. Cost: low.
   - **C. Add a new directory (TuneIn OPML).** It adds station coverage, but terms are unclear and the API has no CORS. Cost: medium. Risk: terms.
   - **D. Add on-demand sources (Internet Archive, Audius).** They are files, not live radio. They need a seek-capable player. Cost: high; a different product.
   - **Recommendation:** A, then B. Defer C until someone checks TuneIn's terms. Treat D as a separate milestone.
2. **Whether to build per-platform now-playing adapters.** An adapter would match a stream host to a platform and call its now-playing API. It would cover roughly 34% of the corpus by host pattern, and fix the 31% of streams with empty ICY titles only where a platform API exists. **Recommendation:** yes, starting with AzuraCast, laut.fm, Radio.co and Zeno (all with CORS, all verified). Add Triton, Icecast and SHOUTcast next. Those need a server-side proxy on the web. Verify iHeart and RadioKing first.
3. **Whether the web app needs a proxy for stream headers.** Only 37% of streams let a browser read ICY. A proxy would read ICY server-side, but ADR 0006 chose direct playback without an audio relay. A metadata-only proxy is not the same as an audio relay. **Recommendation:** decide in a web ADR; do not reverse ADR 0006 for audio.
4. **Whether search should hide or demote some stations.** Candidates: dead stations, `http`-only stations on the web, duplicate URLs (17.4% of entries), stations with tokenised URLs. **Recommendation:** on the web, try `https` first and hide only streams where it fails. Collapse duplicate URLs everywhere. Keep the broken flag as the filter, since it matched the probe.

## Follow-ups worth running

1. A codec compatibility test: AVPlayer on iOS and macOS, the web audio element, and Roku for AAC, HE-AAC, MP3, FLAC, Ogg and fMP4 HLS.
2. The same probe from a second region, to measure geo-blocking.
3. A repeat probe in 30 days of the same sample list, to measure URL rot and token expiry.
4. Verify iHeart and RadioKing now-playing; retry Openverse.
5. Compare ICY or side-channel titles against ShazamKit on 20 stations. The existing alignment work covers two.
