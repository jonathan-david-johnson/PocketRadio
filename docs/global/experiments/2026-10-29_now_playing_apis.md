# Experiment: how do Now Playing sources behave, and how do we normalize them?

**Status**: Part 1 (investigation) is DONE — 2026-10-29. Parts 2 and 3 are PROPOSED. Nothing in them is decided. Follows the [free audio landscape experiment](2026-10-29_free_audio_landscape.md). Evidence: [`traces/2026-10-29_now_playing/`](traces/2026-10-29_now_playing/).
**Update (2026-10-29, later):** the plan was approved except SomaFM, which stays skipped. Cycle 1 changed the ranking: Triton is on hold. See [cycle 1](2026-10-29_now_playing_cycle1.md).
**Scope**: Cross-platform. Part 3 targets the web player, under [web ADR 0006](../../web/adr/0006-direct-https-playback-without-an-audio-relay.md).

## Result in brief

1. **There is no single Now Playing API.** There are about ten source types (archetypes). I verified a live, working example of 21 distinct adapters across them. They all give a title, and most give an artist. They disagree on everything else: timestamps, duration, artwork, history, time zones, and whether they publish junk (ads, jingles, file names).
2. **Normalizing is feasible.** A prototype normalizer produced a consistent record for 33 of 38 live targets as a song (2 as shows; 3 as placeholder, unknown or nothing). It needs three things beyond field mapping: a **staleness rule**, a **junk filter**, and a **timing label** that says whether the start time came from the source or from us.
3. **Sources publish late.** Across 119 song changes, the median delay between a song's own start stamp and its appearing in the API was 16 s; the 90th percentile was 73 s. Automated playout is fast (2–15 s). Human-logged feeds are slow (KEXP 65 s, KCRW 111 s, NPO 64 s, SR 51 s). The UI must not show a song that has already ended.
4. **For the web, a server-side resolver beats browser-direct.** Direct calls from a real browser worked for 20 of 24 APIs. But one resolver gives one schema, one place for the junk filter, a shared cache that protects small hosts, and answers for the non-CORS sources. Proposal in [Part 3](#part-3-proposal-a-now-playing-resolver-for-the-web-player).
5. **Platform APIs cover only part of listening.** Verified platform adapters cover 25% of clicks on web-playable stations. Broadcaster networks and unclassified hosts hold the other 75%. The head is flat: the top 1,000 web-playable stations are only 48% of clicks.
6. **Corrections to my earlier report.** The earlier report recommended adding SomaFM first. ADR 0006 records that SomaFM's published terms restrict third-party clients, and that direct playback is not an established exception. Treat SomaFM as blocked until permission is checked. The earlier report also said iHeart and RadioKing now-playing were "not verified". They now are (see 1.1).

Decisions needed are at the [end](#decisions).

---

# Part 1. What the Now Playing APIs are

## Method and limits

- **Observed** means a request from this Mac on 2026-10-29, recorded in `traces/`. **Documented** means my recollection of vendor docs, not re-checked. I did not read any terms of service.
- 38 live targets (17 named sources, 21 from the landscape sample) plus 3 Zeno stations were monitored for 21 minutes. Each API was polled every 8 s while the station's in-band ICY stream was held open. 119 song changes carried a start stamp.
- The ICY arrival time is when the title came over the socket on **my** connection. It is not what a listener hears. A listener's audio runs behind the server by the player's buffer. Nothing here measures that offset.
- Poll interval 8 s means every lag number is ±8 s. Lag is shown as medians.
- One vantage point (US), one 21-minute window, 2–15 song changes per target.
- Prototype code is in [`scripts/`](traces/2026-10-29_now_playing/scripts/). It is a research prototype, not production code.

## 1.1 The archetypes

"Verified" means I called a live endpoint and parsed the answer.

| # | Archetype | Verified examples | Stations it covers | Browser-direct |
|---|---|---|---|---|
| A1 | **Station's own tracklist API** | KEXP, KCRW, SomaFM, Radio Paradise, NTS | One station each | Yes, except Radio Paradise |
| A2 | **Broadcaster-network API** | Radio France (`livemeta/pull/<id>`), Sveriges Radio, ABC (`music.abcradio.net.au`), NPO Radio 2, NPR Composer (public radio), WNYC (show only) | Many stations per network | Yes, except WNYC |
| A3 | **Hosting-platform API** (multi-tenant) | AzuraCast, laut.fm, Radio.co, RadioKing, RadioJar, Live365, Airtime Pro, Triton/StreamTheWorld, iHeart/Revma, Zeno (SSE) | Thousands per platform | Yes |
| A4 | **Server status page** | Icecast `status-json.xsl`, SHOUTcast `7.html` and `stats?json=1` | Any self-hosted server | Icecast mostly; SHOUTcast almost never |
| A5 | **In-band ICY** | 96.7% of progressive streams | Nearly all | Only 22% (see 1.6) |
| A6 | **In-band HLS timed metadata** | SomaFM, iHeart (ID3 `TIT2`/`TPE1`), Mediastream (`DATERANGE` ads) | About 23% of HLS | Not exposed natively (see 1.6) |
| A7 | **Directory-published** | TuneIn `Describe.ashx` | Whatever the station pushes | No CORS |
| A8 | **Programme or schedule only** | NTS, WNYC, Composer `onNow`, Airtime `shows` | Show title, no song | Varies |
| A9 | **Fingerprint** | ShazamKit on iOS (existing) | Any audio | Not on the web without an audio path |
| A10 | **Nothing** | 31% of ICY streams send an empty first title | — | — |

Seven things that surprised me:

- **iHeart's Now Playing works** (`us.api.iheart.com/api/v3/live-meta/stream/<stationId>/currentTrackMeta`). The id is the iHeart station id, not the number in the stream URL. It returns title, artist, album, artwork, start and end times, and a `lyricsId`. It returned an empty body for a station with no track.
- **RadioKing's working URL** is `api.radioking.io/widgets/api/v1/radio/<numeric id>/track/current`. The older `www.radioking.com` path redirects without CORS headers and fails in a browser.
- **Airtime Pro** exposes `<name>.airtime.pro/api/live-info-v2`, with CORS `*`.
- **Live365's** `current-track` includes `start`, `duration` and a `sync_offset`. This is the only source that publishes an offset field.
- **AzuraCast's all-stations endpoint can exceed 400 KB.** Use the per-station endpoint `/api/nowplaying/<shortcode>`.
- **ICY and the platform API agreed on the title** in the 147 matched changes, with ICY usually first (see 1.3). The platform APIs add artwork, start time, duration and history.
- **Empty ICY is not rescued by status pages.** Of 162 stations whose ICY title was empty, the Icecast or SHOUTcast status page gave a title for 1. The data is missing at the source. Only a broadcaster API or fingerprinting can fill it.

## 1.2 What each source gives you

`✓` = field present. Observed from live responses.

| Adapter | Title | Artist | Album | Artwork | Start stamp | Duration | History | Next | Show | Notes |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|---|
| KEXP | ✓ | ✓ | ✓ | ✓ | ✓ | | ✓ | | ✓ | Also airbreaks (`play_type`), comment text, MusicBrainz ids |
| KCRW | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ (iTunes ms) | ✓ | | ✓ | Spotify and iTunes ids |
| SomaFM | ✓ | ✓ | ✓ | (blank) | ✓ | | ✓ | | | Terms restrict third-party clients |
| Radio Paradise | ✓ | ✓ | ✓ | ✓ | | | | | | `get_block` API carries scheduled times; not parsed |
| NTS | | | | | ✓ | ✓ | | ✓ | ✓ | Show level only |
| AzuraCast | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | | Plus `elapsed`, live DJ, listeners |
| laut.fm | ✓ | ✓ | ✓ | | ✓ | ✓ | ✓ | ✓ | | Separate `last_songs`, `next_artists` |
| Radio.co | ✓* | | | ✓ | ✓ | | ✓ | | | *One `Artist - Title` string |
| Triton | ✓ | ✓ | | | ✓ (ms) | ✓ (ms) | ✓ | | | XML. May hold template text |
| RadioJar | ✓ | ✓ | ✓ | ✓ | | ✓ | | | | |
| Live365 | ✓ | ✓ | | ✓ | ✓ | ✓ | | | | `sync_offset` |
| iHeart | ✓ | ✓ | ✓ | ✓ | ✓ (ms) | ✓ | | | | `lyricsId` |
| RadioKing | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | | ✓ | | |
| Airtime Pro | ✓ | ✓ | ✓ | | ✓ | ✓ | ✓ | ✓ | ✓ | **Station-local time, not UTC** |
| NPR Composer | ✓ | ✓ | ✓ | | ✓ | ✓ (ms) | | ✓ | ✓ | Mixed date formats |
| Sveriges Radio | ✓ | ✓ | ✓ | | ✓ | ✓ | ✓ | ✓ | | `/Date(ms)/` format |
| ABC | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | | | Multiple artwork sizes; service ids |
| Radio France | ✓ | ✓ | ✓ | ✓ | ✓ (s) | ✓ (end) | ✓ | | ✓ | A tree of "steps"; choose the song step that spans now |
| NPO Radio 2 | ✓ | ✓ | | ✓ | ✓ | ✓ | ✓ | | | Naive local time, no zone |
| Icecast status | ✓ | rarely | | | | | | | | Per-mount; some servers hide it |
| SHOUTcast | ✓* | | | | | | | | | *`Artist - Title`, no stamp |
| Zeno (SSE) | ✓* | | | | | | | | | *`streamTitle` plus `streamUrl` with artist and album |
| ICY | ✓* | | | | | | | | | *One string, no stamp |
| TuneIn `Describe` | ✓ | ✓ | ✓ | ✓ | | | | | | Null unless the station pushes it (KCRW: null) |

## 1.3 Timing

For each API I recorded when a new song first appeared, and compared it with the song's own start stamp (**publication lag**) and with the same title arriving in ICY (**ICY − API**; negative means ICY came first). Full table: [`monitor_summary.txt`](traces/2026-10-29_now_playing/monitor_summary.txt).

| Source | Publication lag, median (s) | Notes |
|---|---:|---|
| Radio France (FIP) | 5 | Automated |
| laut.fm | 2–9 | Three stations |
| AzuraCast | 5–13 | Three stations |
| RadioKing | 12 | |
| Airtime Pro | 12 | |
| iHeart | 13–15 | |
| Triton | 15 | One live station |
| ABC (triple j) | 16 | |
| SomaFM | 16 | |
| Radio.co | 12–20 | Three stations |
| Live365 | 26 | |
| NPR Composer (KUTX) | 36 | Playlist logged by hand or by automation with delay |
| Sveriges Radio (P3) | 51 | |
| NPO Radio 2 | 64 | |
| KEXP | 65 | Lower than the 100–150 s seen on the phone on 2026-10-14; the method and window differ |
| KCRW | 111 | |
| **All sources, n=119** | **16 (p90: 73)** | |

- **Overall, ICY arrived before the API:** median −6 s over 147 matches; ICY was later in 21 of 147. Individual medians run from −53 s (NPO) to about 0 (Live365, Radio Paradise). They are bounded by my 8 s polling.
- **Consequence for the UI.** When a feed lags, the previous song's title stays on screen after the song ended. A normalized record must say when a song should be treated as over: `startedAt + duration + grace`. Where a feed has no duration (KEXP, Radio.co, Icecast), the record carries `endsAt: null`, and the client falls back to "stale after 15 minutes".
- **Consequence for lyrics.** Feed stamps are the station's clock, not the listener's audio position. Synced lyrics (web M4) need the alignment work done on iOS. Feed publication time is not usable as the audio clock.

## 1.4 What the junk looks like

Junk seen on 38 live targets and in the 525-stream ICY sample:

| Kind | Example (observed) |
|---|---|
| Jingle or station ID as a track | Radio.co: `Shine 879 DAB - The World's Leading Dance Music Station`; `Unknown Artist - XYZ_ID6` |
| Advert as a track | Radio.co history: `Envirovan Van Hire - Envirovan Van Hire Essex` |
| File name | Airtime: ` - 26_Q4_Good_English_Billboard_Style_Meloxicam.mp3`; Triton: `069_dis` / `eng-bodhinatha-veylanswami-kauai-h` |
| Unfilled template | Triton: `program_id = {cartNumber}` |
| Placeholder | AzuraCast: `Problème technique - Nous revenons rapidement`; KUTX ICY: `THIS STATION WILL CONTINUE AFT…` |
| Station name as title | RadioJar: `ISWARA JAKARTA`; VRT ICY: `VRT Radio 1`; BBC WS ICY: `BBC World Service Online` |
| Bare status word | SHOUTcast: `Live`, `Searching` |
| Automation format | Icecast: `Song*I'M NOT IN LOVE*10 CC*1975*41…` |
| Automation fields in the title | ICY: `song_spot="T" spotInstanceId="-1" length="03:00:00" …`; `text="Spot Block End"` |
| Stale feed | Triton `ABC NOTICIAS 1310`: newest item 5 hours old |
| Empty-ish | Zeno: ` - ` |
| HTML entities | NTS: `W/ FLO &amp; Operelly` |
| Encoding loss | Zeno: `Hit Super Hits??90's??` |

The prototype's filter (`classify()` in `np_adapters.py`) catches ads, placeholders, file names, and templates by pattern. It has not been tested for false positives. A song called "Live" would be filtered. The filter belongs in a shared contract with test fixtures, not in each client.

## 1.5 Time formats

Eight formats appear across the 21 adapters, and four of them break a naive parser (naive local time, `/Date(ms)/`, `+0100` without a colon, and `Date.toString()`).

| Format | Used by |
|---|---|
| Epoch seconds (integer or string) | AzuraCast, SomaFM, Radio France |
| Epoch milliseconds | Triton, iHeart |
| ISO with offset and colon (`-07:00`) | KEXP, Radio.co, Live365 (with fractional seconds) |
| ISO with offset, no colon (`+0100`, `+0000`) | laut.fm, RadioKing |
| **Naive local time, zone in another field** | Airtime v2 (`station.timezone`), NPO (Europe/Amsterdam, by assumption), NPR Composer `_start_time` (`MM-DD-YYYY`, station zone) |
| `/Date(1793270805000)/` | Sveriges Radio |
| JavaScript `Date.toString()` form | NPR Composer `nextUp` entries |
| Both ISO and a human form in one response | NPR Composer |

## 1.6 What a browser can do

Tested in Chrome 155 on this Mac, from an `https` page, with no relay ([`browser_tests.md`](traces/2026-10-29_now_playing/browser_tests.md)).

| Test | Result |
|---|---|
| Direct `fetch` of 24 Now Playing APIs | **20 work.** Failures: Radio Paradise API, TuneIn OPML, WNYC (no CORS), SHOUTcast (`http` page-origin mixed content) |
| ICY via `fetch` with `Icy-MetaData` header, 46 `https` streams | 15 allow the request; `icy-metaint` is readable on **10 (22%)**. KEXP and KCRW are blocked |
| Same streams, no custom header | 42 allow the request; `icy-metaint` readable on **0** |
| HLS in a native `<audio>` element | Plays (Radio France, SomaFM). **No ID3 cues appear** in `textTracks` |
| Codec support (`canPlayType`) | MP3, AAC, AAC-in-MP4, Opus, Vorbis, FLAC: `probably`. HLS: `maybe` |
| `navigator.mediaSession` | Present |

So browser-side ICY is a bonus for about a fifth of streams, not a baseline. Native HLS plays, but in-band HLS titles need a library such as hls.js, which changes the playback path. That is outside ADR 0006.

## 1.7 Reach: which archetypes matter

Clicks are radio-browser's 24-hour click counts (213,856 total). They reflect radio-browser's own users, not ours. Use them as a rough guide.

**Platform adapters on web-playable stations** (https, default port, DNS host; 53% of stations, 57% of clicks):

| Platform | % of web-playable stations | % of web-playable clicks |
|---|---:|---:|
| Zeno | 7.4 | 8.1 |
| Triton | 5.3 | 5.7 |
| AzuraCast | 4.9 | 4.0 |
| iHeart/Revma | 2.3 | 2.2 |
| laut.fm | 2.2 | 1.4 |
| Live365 | 1.5 | 1.2 |
| Radio.co | 1.7 | 1.0 |
| RadioJar, RadioKing, Airtime | 1.8 | 1.5 |
| **All platform adapters** | **27.0** | **25.1** |
| Everything else | 73.0 | 74.9 |

**Head versus tail** (web-playable): top 25 stations hold 10.4% of clicks, top 100 hold 19.5%, top 500 hold 37.3%, top 1,000 hold 48%. The top 100 are spread over 64 different domains.

**Biggest unclassified groups** (share of all clicks): Infomaniak 1.9; Radio France plus France Info 1.7; ARD family (`rndfnk`, `wdr`, `dlf`, `swr`) 2.6; Akamai-hosted 1.4; Russian hosting 1.3; NRJ 1.0; BBC 0.5; RAI 0.5; NPO 0.45; SRG 0.4.

Two readings:

- A platform adapter fixes a lot of stations at once but only a quarter of listening.
- The stations with **no usable in-band metadata at all** (HLS-only, Radio France, ABC, BBC) are the ones where a broadcaster API matters most.

Also: managed platforms already have healthy ICY (Zeno, laut.fm, Radio.co: 0% empty in the sample). Their API adds artwork, timing and history, not basic titles. Empty ICY is concentrated in self-hosted Icecast (36%), SHOUTcast (37%), Triton (50%) and unclassified hosts (33%).

## 1.8 What I could not verify

- Terms of use for every API above. Several are the endpoints a station's own website calls, with no published contract (iHeart, RadioKing, ABC, NPO, Radio France `livemeta`, Live365, KCRW). **Documented** as official, from memory and unverified: AzuraCast, laut.fm, Triton, Sveriges Radio, KEXP, Airtime.
- Geo-blocking: BBC `rms.api.bbc.co.uk` returned 403 from here; no other BBC check was made.
- How NPR Composer ids map to stations. The one id I tried worked (KUTX). The NPR Station Finder output did not show it.
- Zeno's SSE behavior over hours; it re-sent the current title on each reconnect.
- How the Now Playing record should line up with listener audio. Nothing in Part 1 measures that offset.
- Whether hls.js exposes ID3 cues for these streams (assumed yes; untested).

---

# Part 2. Proposal: how to prioritize further investigation

## Principles

- **Breadth means every archetype gets surveyed. Depth means one archetype is taken all the way to shipping.** Treat them as two independent scales, and track them on a board: archetypes down, maturity across.
- **Do not go deep on a source before the whole field is mapped to survey level**, except for one pathfinder that proves the pipeline end to end.
- **Stop an archetype when the next step costs more than it returns.** Define that in numbers up front.

## The maturity scale

| Level | Name | Evidence required | Who signs off |
|---|---|---|---|
| L0 | Named | One live example seen | — |
| L1 | Surveyed | Archetype card complete; at least 10 instances probed with the standard battery | Me |
| L2 | Spiked | Adapter prototype; raw→normalized fixtures for 3+ instances; timing measured; browser reachability tested | Me |
| L3 | Contracted | Fixtures in the shared contract; schema frozen; terms reviewed and recorded; ADR drafted | **You** (terms) |
| L4 | Integrated | Shipped on one surface behind a flag; 7-day canary at 99% success | **You** (UX) |
| L5 | Sustained | All surfaces; weekly re-probe in place; drift alerts | — |

Where things stand today:

| Archetype | Level now |
|---|---|
| A1 KEXP, KCRW | L4 on iOS and macOS; L0 on web |
| A1 others (Radio Paradise, NTS) | L2 |
| A3 platforms with a verified adapter | L2 (prototype exists; 10 platforms) |
| A2 Radio France, SR, ABC, NPO, Composer | L2 (one instance each) |
| A4 status pages | L2 |
| A5 ICY | L4 (existing apps) |
| A6 HLS timed metadata | L1 (observed; no adapter) |
| A7 TuneIn | L1 |
| A8 schedule-only | L1 |
| A9 fingerprint | L4 on iOS only |

## The standard battery (breadth work)

Extend `tools/source-survey.py` so one run produces an **archetype card**. Fields for each archetype card:

1. Instance count probed and success rate.
2. Endpoint shape and an example response.
3. Field coverage (the 1.2 table row).
4. Timing: publication lag, 20+ song changes over 30+ minutes.
5. Junk catalogue with examples.
6. Time format and zone.
7. Browser reachability (real Chrome run, as in 1.6).
8. Auth and key requirements.
9. Terms status: official, undocumented, or restricted, with a link.
10. Stability: change in behavior over a second probe 7 days later.
11. Reach: share of web-playable clicks and share of stations.

A battery run takes one session per archetype. It needs no integration work.

## How to rank archetypes for depth

Rank on four numbers, each written down, not guessed:

- **Reach** — share of web-playable clicks the archetype covers (section 1.7).
- **Gap** — share of that archetype with no usable in-band title today (empty or junk ICY, no ICY). Measured from the sample.
- **Cost** — adapter size: number of formats, auth, id mapping, parsing hazards. Rated S, M, L.
- **Risk** — terms and stability. Rated from the card: official API (low), undocumented but stable (medium), restricted or blocked (high).

Priority is Reach × Gap, then break ties by Cost, and **veto any High risk until you decide**.

Initial ranking from today's data:

| Rank | Archetype | Reach (web clicks) | Gap | Cost | Risk | Why |
|---:|---|---|---|---|---|---|
| 1 | **Triton/StreamTheWorld** | 5.7% | 50% empty ICY | S (XML, one endpoint) | Low (documented, CORS `*`) | Largest gap among platforms. 22 of 40 mounts returned live data; 18 returned an empty list, and one live item was 5 hours old, so the filter and stale rule matter |
| 2 | **AzuraCast** | 4.0% | 10% | S | Low (official, built for this) | Richest schema (duration, elapsed, art, history). **Best pathfinder:** proves the pipeline cheaply |
| 3 | **iHeart/Revma** | 2.2% (plus many of the top stations) | 7 of 12 sampled streams are HLS with no ICY | M (station-id lookup) | Medium (undocumented) | Strong data incl. artwork and timing; no in-band title on HLS |
| 4 | **Radio France (`livemeta`)** | 1.7% of all clicks | No ICY on the 3 streams tested | M (steps tree) | Medium (unofficial) | One adapter covers FIP, France Inter, France Info and others |
| 5 | **NPR Composer** | not measurable | KUTX ICY is a placeholder | M (id mapping unknown) | Medium | Covers many public stations |
| 6 | **ABC** | small | No ICY on the stream tested | S | Medium | |
| 7 | laut.fm, Radio.co, Live365 | 3.6% together | 0% | S | Low–medium | Gain is artwork and timing only, not titles |
| 8 | **Zeno** | 8.1% | 0% | S–M (SSE) | Medium | Biggest reach, but ICY already works; low gain |
| — | **SomaFM** | 0.7% of all clicks | 0% | S | **High (terms)** | Vetoed pending your decision |
| — | **BBC** | 0.5% | HLS, no ID3 | ? | High (403 from here) | Blocked until geo and terms are understood |

Before Cycle 1, re-run the Reach column on the web-playable subset for the A2 networks (it is only measured across all clicks above).

## Cadence

Work in cycles of about one week. Each cycle is one **breadth sweep** plus one **depth step**. Keep at most **two** archetypes between L2 and L4 at once.

| Cycle | Breadth (to L1/L2) | Depth (one archetype) |
|---|---|---|
| 0 (done) | Landscape and this report | — |
| 1 | A6 HLS ID3 (hls.js test); A7 TuneIn terms; head sweep of top 100 web-playable stations | **Pathfinder: AzuraCast to L4 on web** |
| 2 | A2 networks: ARD, BBC, RAI, SRG, RTÉ, CBC, NPR station ids | Triton to L4 |
| 3 | A8 schedule-only (cover show-level display) | iHeart or Radio France, whichever the head sweep favors |
| 4 | Re-probe all L1 archetypes after 3 weeks to measure drift | Next archetype by rank |

The **head sweep** is the key breadth tool for the 75% that is not on a platform. For the top 100 web-playable stations, find each one's Now Playing source by hand (about 15 minutes each, so about 25 hours total). Record it as one row in a `station_metadata_sources` table. That turns "other" into named archetypes, and shows which new archetypes deserve a card.

## Definition of done for an archetype (depth)

An archetype reaches L4 only when all of these hold:

1. The shared contract has raw→normalized fixtures covering: a song, between songs, past end, an ad or jingle, a placeholder, an outage, and the archetype's own odd cases.
2. The adapter passes the fixtures on the web and on one other platform (Swift).
3. The terms review is recorded in an ADR, with the link and date.
4. A 7-day canary polls five instances every 5 minutes, with 99% success and no schema drift.
5. The UI renders each state (song, show, between, stale, unsupported) per Part 3.
6. The metric "share of playing time with a valid title" is measured for the archetype on the web, so it can be re-ranked.

## Feedback loop

After the web player ships Part 3, log locally, per station and without account data: playing seconds with a valid title, and playing seconds without. Aggregate by archetype. That replaces radio-browser clicks with our own usage for ranking. This is a privacy decision (below).

---

# Part 3. Proposal: a Now Playing resolver for the web player

## Constraints (from ADR 0006 and Part 1)

- Audio goes straight from the station to a native `<audio>` element. No audio relay. The server must not GET, HEAD or probe the station's audio URL.
- The web player plays only `https` on the default port: 53% of stations and 57% of clicks.
- Browsers can read ICY on about 22% of streams. Native HLS gives no ID3 cues.
- 20 of 24 Now Playing APIs are reachable directly from a browser. SHOUTcast is not; neither is Radio Paradise's.
- Web M4 (lyrics) waits on per-station metadata and a trustworthy timing label.

ADR 0006 allows "a fixed, bounded metadata lookup" on the server and says station metadata feeds "may be investigated later". A Now Playing resolver is that. It needs its own ADR, because it contacts hosts other than radio-browser.

## The normalized record

```json
{
  "stationId": "<radio-browser uuid or curated id>",
  "status": "playing | between | stale | unsupported | unavailable",
  "item": {
    "kind": "song | show | ad | station_id",
    "title": "…", "artist": "…", "album": "…",
    "artworkUrl": "https://…",
    "startedAt": "2026-10-29T10:45:00Z",
    "durationSec": 297,
    "endsAt": "2026-10-29T10:49:57Z"
  },
  "show": { "title": "Eclectic 24" },
  "history": [ { "title": "…", "artist": "…", "startedAt": "…" } ],
  "provenance": {
    "adapter": "azuracast",
    "channel": "api",
    "observedAt": "2026-10-29T10:47:12Z",
    "timing": "stamped | observed | none"
  },
  "pollAfterSec": 10
}
```

Rules:

- **`kind` is computed after the junk filter.** Ads, jingles, file names, templates and placeholders never reach the UI as songs. They become `status: "between"` (or `station_id` when the source labels it).
- **`startedAt` is in UTC.** Every adapter converts its own format and zone (1.5).
- **`timing` is the honesty flag.** `stamped` means the source gave a start time. `observed` means we saw the change at `observedAt`. `none` means neither. M4 lyrics may use only `stamped`, and only after alignment. ADR 0006 already says "feed observation time is not the listener's audio position".
- **`stale` and `between`** follow from `endsAt` and the default 15-minute fallback (1.3).
- **`unsupported`** means no adapter matched. The UI shows the station name and nothing else.

## Architecture

```
Browser ──GET /api/now-playing?stationId=…──▶ Pages Function
                                              1. validate session + same-origin (like /api/playback)
                                              2. look up station (radio-browser by uuid, or curated row)
                                              3. choose adapter from `metadata_source` or from URL pattern (string match; no fetch)
                                              4. check short-lived cache for (adapter, params)
                                              5. call the adapter's fixed upstream host(s)
                                              6. normalize + junk filter + stale rule
                                              7. return record + pollAfterSec
Browser ──── plays audio directly from the station, as today ────▶ <audio>
```

Details:

- **Adapters are pure TypeScript.** Each is `request(params) → URL` and `parse(response) → NowPlaying`. No I/O inside `parse`. They sit in `shared/` so tests, the Function, and a future browser-direct path run the same code.
- **Adapter selection order:** (1) curated `metadata_source` JSON on the station row (replaces `tracklist_url`); (2) a row in `station_metadata_sources` keyed by radio-browser uuid; (3) a URL-pattern rule (for example `*.stream.laut.fm` → laut.fm). Nothing in step 3 contacts the station.
- **Upstream allowlist.** The Function calls only hosts named in the adapter table (`api.laut.fm`, `np.tritondigital.com`, `public.radio.co`, …). For AzuraCast, Airtime and similar self-hosted installs, the host is the station's own domain, derived from its stream URL. These must pass the same validation as ADR 0006 (public DNS name, `https`, port 443, no credentials) plus a manual-redirect rule and a response-size cap (65 KB for the common case, a larger cap only for known-large endpoints).
- **Cache.** Cache the normalized upstream result for 8 s (shorter if `endsAt` is sooner), keyed by adapter and params, in the Cloudflare Cache API. Failed calls are cached for 60 s. With a cache, 1,000 listeners on one station cost one upstream request per 8 s per Cloudflare location, not 1,000. Small hosts are protected.
- **Client polling.** Poll at `pollAfterSec` (default 10 s). Slow to 30 s when the tab is hidden. Stop when playback stops.
- **Media Session.** Set `navigator.mediaSession.metadata` from the record, so lock screens, headsets and the OS media panel match iOS.
- **UI states.** `playing`: artwork, title, artist. `show`: show title with the station logo. `between`: station name, no stale title. `stale`, `unsupported`, `unavailable`: station name only. This one table is the web side of the shared UX contract.

## Why server-side, not browser-direct

| | Server resolver (proposed) | Browser-direct |
|---|---|---|
| Reaches non-CORS sources (Radio Paradise, TuneIn, WNYC) | Yes | No |
| One junk filter and one schema | Yes | Per client, but shared code can fix this |
| Protects small hosts from N listeners | Yes, via cache | No: every listener polls |
| Hides the listener's IP from the metadata host | Yes | No |
| Works for SHOUTcast | Only if the host allows our fetch; port rules still apply | No (mixed content, no CORS) |
| Cost | A Function call per poll (about 360 per listener-hour, minus cache) | None |
| Offline or CORS-change risk | One place to fix | Every client breaks together |
| SSRF risk | Real; needs allowlist and caps | None |

The resolver costs a request per poll. At Cloudflare's free-tier limit of 100,000 requests per day, that is roughly 277 listener-hours a day before caching helps. **I did not check current Cloudflare pricing or limits.** The paid plan is the likely answer if usage grows.

**Optional later optimization:** try the adapter directly in the browser first for adapters flagged CORS-open, and fall back to the resolver. Two paths double the testing. Don't do it until request cost is a measured problem.

## What I would leave out of the first version

- **Server-side ICY peek.** A Function could connect to the stream, read the first title block, and disconnect. That would cover stations with no API, but it GETs the audio URL, which ADR 0006 forbids. It would need an ADR change. Defer.
- **Browser-side ICY.** Works on about a fifth of streams. ADR 0006 rules out a second audio connection.
- **hls.js for in-band HLS titles.** It changes the playback path.
- **SHOUTcast and Icecast status pages.** They only apply to `https`, port-443 hosts, and gave a title in just 1 of 162 empty-ICY cases. Add after the platform adapters, if the head sweep shows a need.
- **SomaFM.** Blocked on terms.

## Contract and tests

- Add `contracts/now_playing_feed/`, following the `contracts/nav_layout/` pattern: raw upstream bodies and the expected normalized record, per adapter and per odd case. The web port runs them first. iOS and macOS adopt them later, so the platforms can't drift.
- Record fixtures from the traces already collected (for example `triton_nowplaying.txt`, `radio.co_status.txt`).
- Unit-test the junk filter on a list of real titles including false positives ("Live", "Unknown" as a song name).

## Slicing into web milestones

| Slice | Content | Gate |
|---|---|---|
| W1 | Normalized record, contract fixtures, resolver Function, **KEXP and KCRW** through it (replaces their direct use), stale/junk rules, Now Playing card | You see the same card for KEXP and KCRW as today, now fed by the resolver |
| W2 | **AzuraCast** adapter (pathfinder), Media Session | A live AzuraCast station shows title, artwork, then goes to `between` correctly |
| W3 | Triton, laut.fm, Radio.co | Fixtures pass; 7-day canary |
| W4 | iHeart, Radio France, NPR Composer | Per Part 2 ranking |
| W5 | Feed M4 lyrics with `timing: "stamped"` only | After alignment work |

## Risks

- **Terms.** Most adapters call endpoints without a published contract. A server-side resolver makes our servers the visible caller. Each adapter needs a terms entry before L3, and a kill switch.
- **Cache staleness vs lag.** An 8 s cache adds up to 8 s to publication lag. Acceptable against a median of 16 s; revisit if a source's `endsAt` is short.
- **Station id mapping.** iHeart and NPR Composer need ids that are not in the stream URL. That mapping must come from the head sweep.
- **Drift.** Undocumented endpoints change without notice. The weekly re-probe in Part 2 is the only defense.
- **ADR conflict.** The resolver contacts station-owned domains (AzuraCast, Airtime). ADR 0006 bans touching the audio URL, not other station hosts, but a new ADR should say so explicitly.

---

# Decisions

Each is stated in plain words with a recommendation.

1. **Approve the maturity scale and cycle plan (Part 2)?** This means breadth to L1 for every archetype before going deeper than one pathfinder. **Recommendation: yes.** Changing it later costs little.
2. **Which archetype is the pathfinder?** AzuraCast (cheap, documented, richest schema, official API) versus Triton (bigger gap, more messy data). **Recommendation: AzuraCast first**, then Triton. Triton's junk and staleness rules are better tested on a pipeline that already works.
3. **Approve a server-side Now Playing resolver on Cloudflare (Part 3)?** It needs a new ADR that extends ADR 0006 to metadata hosts. **Recommendation: yes.** Browser-direct would be simpler but cannot reach three sources, can't protect small hosts, and splits the filter.
4. **How to treat undocumented APIs (iHeart, RadioKing, ABC, NPO, Radio France, KCRW, Live365).** Options: (a) use them with a kill switch and a terms note; (b) use only officially documented ones (AzuraCast, laut.fm, Triton, SR, KEXP, Airtime); (c) ask each owner. **Recommendation: (b) for the first release, (a) once each has a recorded terms review.** This delays iHeart and Radio France. Which APIs count as "officially documented" is from memory and must be confirmed first (follow-up 4).
5. **SomaFM.** Stay blocked, or contact SomaFM for permission. **Recommendation: contact them.** They are the best-behaved source in the sample.
6. **Local usage metric for ranking.** Log playing seconds with and without a valid title, per station, aggregated, no account data. **Recommendation: yes, but keep it local and aggregate-only.** If you say no, ranking falls back to radio-browser clicks.
7. **Spend the head-sweep hours.** About 25 hours to name the Now Playing source for the top 100 web-playable stations. **Recommendation: yes, after W1.** It is the only way to shrink the unclassified 75%.

## Follow-ups worth running

1. Hold the same 38-target monitor for 24 hours to catch overnight behavior (automation, live shows, outages).
2. Test hls.js against SomaFM and iHeart HLS to confirm ID3 cues arrive and match the API.
3. Find the NPR Composer id for 10 public stations.
4. Read the terms or API pages for each adapter and record them as a table.
5. Measure the browser audio offset from the server's live edge for 10 stations. Without it, no alignment claim for web lyrics is safe.
