# Experiment: Now Playing, cycle 1 — results and plan changes

**Status**: DONE — 2026-10-29. Follows [the Now Playing investigation](2026-10-29_now_playing_apis.md), whose plan the user approved the same day ("ok to plan … go"). Evidence: [`traces/2026-10-29_now_playing/`](traces/2026-10-29_now_playing/).

## Decisions taken

The user approved the plan in the Now Playing investigation. I read that as accepting my recommendation on each decision, with one explicit change:

| # | Decision | Outcome |
|---|---|---|
| 1 | Maturity scale and cycle plan | Accepted |
| 2 | Pathfinder | AzuraCast, then (see below) laut.fm. Triton moves back |
| 3 | Server-side resolver | Accepted. Recorded in [web ADR 0008](../../web/adr/0008-now-playing-comes-from-a-server-side-resolver.md) |
| 4 | Undocumented APIs | Documented sources only in the first release |
| 5 | SomaFM | **Skip for now. Do not contact them.** No SomaFM adapter |
| 6 | Local usage metric | Accepted in principle; not built in this cycle |
| 7 | Head sweep | Started (item 3 below) |

If I misread any of these, say so and I will reverse the matching doc.

## What cycle 1 produced

1. **The contract.** [`contracts/now_playing_feed/`](../../../contracts/now_playing_feed/README.md): a schema, 41 golden cases, and 28 junk-filter cases. 19 adapters plus ICY are covered. Each case holds a trimmed raw response, a fixed clock, and the expected record.
2. **A terms review of the adapters** (below). It changes the plan.
3. **A head sweep of the top 100 web-playable stations** (below). It exposes a decision.
4. **An HLS check with hls.js** (below).
5. **ADR 0008 and Web M3a** (the milestone that builds the resolver).

## 1. Terms review

I read the pages that I could fetch and searched them for rules on automated access, scraping, and APIs. Most sites had no relevant clause. A web page with no clause is **not** permission. Every row below is "what I found", not a legal conclusion.

| Source | What I found | First release? |
|---|---|---|
| AzuraCast | Official docs describe the Now Playing API: `/api/nowplaying` for all public stations and `/api/nowplaying/<station>`, no key. The docs note that elapsed time is cached for a few seconds | **Yes** |
| laut.fm | An API documentation site exists (`docs.api.laut.fm`, Swagger UI). I did not read its contents. I found no terms page | **Yes, after someone reads the API docs** |
| Sveriges Radio | Official open API docs read. **They say the API "is no longer maintained but can be used for now."** Terms: the material must not be used so as to harm SR's independence or credibility | **Yes, with a maintenance risk** |
| KEXP | `api.kexp.org` lists `v1` and `v2` endpoints publicly. I found no clause restricting use. Already used by every app | **Yes** (existing) |
| KCRW | Terms page returned HTTP 429; not read. Already used by every app | **Yes** (existing) |
| radio-browser | Docs say the API "is completely free and open source". Already used | **Yes** (existing) |
| Triton | Terms prohibit scraping Triton "IP & Data" for AI or blockchain use and reverse engineering. I did **not** find the public Now Playing API documentation at any URL I tried | **Hold** |
| iHeart | Terms prohibit obtaining information "through any means not intentionally made available" and scraping "for use in connection with AI Technology". The now-playing endpoint is the one their own site uses; no public docs found | **Hold** |
| Airtime Pro | Terms read; no clause on the API. LibreTime docs URL returned 404, so I could not confirm `live-info-v2` is documented | **Hold** |
| RadioKing | Terms read (a customer contract); no clause on the widget API | **Hold** |
| Live365 | The terms page is a JavaScript app; I could not read it | **Hold** |
| NTS | Terms read; no clause on the API | **Hold** |
| Radio France | An official Open API site exists (`developers.radiofrance.fr`). `livemeta` is not that API | **Hold**; apply for a key |
| NPR | NPR's API needs a registered key (terms read). The Composer product site exists; its terms were not read. The Station Finder does **not** reveal Composer ids | **Hold** |
| ABC, NPO, TuneIn, Radio Paradise | No terms or API pages found at the URLs I tried | **Hold** |

**Plan change.** Triton was ranked first. I could not find proof that its Now Playing API is public and documented, so it moves to "hold until someone finds the docs". The first release becomes: KEXP, KCRW, AzuraCast, laut.fm, Sveriges Radio. The pathfinder stays AzuraCast.

**Not checked:** whether any provider forbids a server-side proxy specifically, whether AzuraCast operators can turn the public API off (the docs speak of "public stations"), and any contract an owner has with a station.

## 2. HLS timed metadata with hls.js

Chrome 155, hls.js 1.x loaded from a CDN, 20 seconds per stream, audio muted.

| Stream | ID3 events | Text frames |
|---|---:|---|
| Amperwave (KMMS) | 4 | `TIT2`, `TPE1`, and a private frame `amperwave.metadata` holding JSON |
| SomaFM Groove Salad | 5 | `TIT2`, `TPE1`, `TALB` (the album frame held a leaked HTML error page) |
| Leanstream (two stations) | 4 and 6 | Apple timestamp frame only, in this window |

Reading: hls.js does expose in-band HLS titles, so A6 works **if the player uses hls.js**. The native `<audio>` element in the same browser exposed none. Using hls.js changes the playback path and is outside ADR 0006. A6 stays at L1.

New junk case found: an HTML error page inside a tag field. It is now in the junk filter list.

## 3. Head sweep: the top 100 web-playable stations

Web-playable means `https`, port 443, DNS host (ADR 0006). The top 100 hold 19.5% of web-playable clicks (23,675 clicks, 24-hour, radio-browser). Each station was probed once with `tools/source-survey.py`. Table: [`head100_table.csv`](traces/2026-10-29_now_playing/head100_table.csv).

| What the station gives a native app | Stations | Share of the top-100 clicks |
|---|---:|---:|
| ICY with a title | 60 | 58% |
| ICY with an empty title | 21 | 19% |
| HLS, in-band text titles | 1 | 7% |
| HLS, no in-band text | 16 | 14% |
| No ICY | 1 | 1% |
| Failed | 1 | 0% |

Platform-hosted stations (Zeno, Triton, laut.fm, iHeart, RadioJar, others with verified adapters) are **19% of the top-100 clicks**. The biggest single groups:

| Group | Stations | Clicks | States |
|---|---:|---:|---|
| ARD (`rndfnk.com`) | 8 | 1,966 | 6 ICY title, 2 empty |
| Zeno | 12 | 1,819 | 12 ICY title |
| NRJ | 4 | 1,320 | 3 title, 1 empty |
| Akamai-hosted HLS | 6 | 1,172 | 6 HLS with no text |
| Triton | 5 | 970 | 3 title, 1 empty, 1 HLS |
| Qingting (CN) | 5 | 832 | 5 ICY empty |
| Global (`musicradio.com`) | 3 | 778 | 3 title |

**What this means.** For these listeners, the best Now Playing source is the one native apps already use: ICY. On the web, the player cannot read it for 78% of streams (the earlier browser test). A resolver that uses only platform and broadcaster APIs reaches about a fifth of the top-100 clicks.

### New decision: should the resolver read ICY on the server?

ADR 0006 forbids the server to touch the station's audio URL. A server-side **ICY peek** would connect, read the first title block (a few KB), and disconnect. By the head-sweep figures it would add title coverage for **58% of the top-100 clicks**. Options:

| Option | What changes | Coverage on the top 100 | Risk |
|---|---|---|---|
| **A. No peek (ADR 0008 as written)** | Resolver uses documented APIs only | About 19% (platforms), plus whatever the head sweep names | Low. Web Now Playing is empty for most stations |
| **B. Browser reads ICY where allowed** | The page's `fetch` asks for ICY; works when the station allows the header | About 22% of streams in the browser test | Low cost. A second connection per listener; ADR 0006 rules this out as a baseline |
| **C. Server peek** | Amend ADR 0006. A Worker opens the stream briefly, every 15 s, cached per station | Up to 58% | Medium to high. Each peek looks like a listener to the station. That may inflate its listener counts and reports. I have not checked any station's reporting rules |

**Recommendation: A for the first release, B as an opt-in later, and C only if you decide the coverage is worth asking a few stations first.** It is your call; ADR 0008 leaves it open on purpose.

## 4. NPR Composer ids

The Composer id for KUTX is `50ef24ebe1c8a1369593d032`. The NPR Station Finder reports KUTX as org `1280`, service `s1280`, and stream ids that start `4fcf713f…`. None of them is the Composer id. So the mapping can only come from each station's own website, one station at a time. It belongs in the head sweep, not in code.

## 5. Other findings

- **iHeart's ICY title carries structured fields:** `Tame Impala / Jennie - text="Dracula" song_spot="M" … amgArtworkURL="…" length="00:03:23"`. `song_spot="T"` marks a station promo (Z100). The contract parses these fields. This gives iHeart streams artwork and duration **without any API**.
- **AzuraCast's own slate is common.** The station I first picked for a fixture had been showing "Problème technique" since 2026-10-21, and its API kept reporting that as the current song. This is the staleness rule's reason to exist.
- **Triton mounts:** `mountName=SRGSTR07AAC` works; `…_SC` returned an empty list. The mount name in a stream URL is not always the API's mount name.
- **Junk filter cost.** Of the first draft's rules, three caused false positives (a real song called "Jingle Bells", the band Live, and any title with no artist). They were fixed and are now pinned in `junk_filter.json`.
- **Known gaps in the filter.** A long station-ID string with no marker (Radio.co: `Shine 879 DAB - The World's Leading Dance Music Station`) passes as a song. A file-id title without an extension (Triton: `069_dis`) passes.

## Plan for cycle 2

| | Work |
|---|---|
| Breadth | Read the laut.fm and Triton API docs. Ask Radio France for an Open API key. Re-run the head sweep on ranks 101–300. Find out why 9 of 44 sampled AzuraCast hosts returned nothing useful (a hidden public API, a removed API, or an outage) |
| Depth | Web M3a: resolver, contract runner, KEXP, KCRW, AzuraCast, laut.fm, Sveriges Radio |
| User decisions | ICY peek (A, B or C). Branch and worktree for M3a. Whether to start the Swift port of the contract |

## Follow-ups worth running

1. Check one station operator's rules on listener counting, to price option C.
2. Read `docs.api.laut.fm` in full; confirm which endpoints are public.
3. Run the 38-target monitor for 24 hours.
4. Test the contract's time rules with a second implementation (the TypeScript port).
