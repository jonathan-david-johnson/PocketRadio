# Now Playing comes from a server-side resolver over allowlisted metadata endpoints

Status: accepted (2026-10-29). The user approved the plan after a Now Playing
investigation; its evidence is in `docs/global/experiments/2026-10-29_now_playing_apis.md`
and `2026-10-29_now_playing_cycle1.md`, which are working state and will move to
an archive tag. Extends [ADR 0006](0006-direct-https-playback-without-an-audio-relay.md).
It does not change how audio plays.

## Decision

The web player gets Now Playing data from one Pages Function,
`GET /api/now-playing?stationId=…`. It returns the record defined by the shared
contract [`contracts/now_playing_feed/`](../../../contracts/now_playing_feed/README.md).
The page does not call station or platform metadata APIs itself.

- **Metadata only.** The Function calls only endpoints named in an adapter's
  definition. It never GETs, HEADs, probes or follows a station's **audio** URL.
  That includes reading ICY titles from the stream.
- **Adapters are pure.** Each adapter is a request builder and a parser with no I/O
  inside the parser. Code lives in `shared/` so tests, the Function, and any later
  port run the same logic. The shared contract is the test.
- **Adapter choice** is, in order: a `metadata_source` on the curated station row;
  a row in a `station_metadata_sources` table keyed by radio-browser UUID; a
  URL-pattern rule on the station's stream URL. Matching a URL pattern is string
  work. It contacts nothing.
- **Host rules.** Upstream hosts are fixed per adapter. Where the host is the
  station's own (for example a self-hosted AzuraCast), it comes from the station's
  stream URL and must pass ADR 0006's checks: `https`, port 443, a public DNS name,
  no credentials. Redirects are not followed. Each response has a byte cap and an
  8 s timeout.
- **Caching.** A normalized result is cached for 8 s (less when the item ends
  sooner), keyed by adapter and parameters. A failure is cached for 60 s. One
  upstream request serves every listener of that station in that location.
- **First release adapters:** KEXP, KCRW, AzuraCast, laut.fm, Sveriges Radio. These
  are sources that publish an API for this use, or that every PocketRadio app
  already calls. Any other adapter needs a recorded terms review before it ships.
  The review is a table row with a link and a date.
- **SomaFM is excluded.** Its published terms restrict third-party clients, and
  ADR 0006 records that direct playback is not an established exception. No adapter
  until the user decides otherwise.
- **Timing is labelled.** `provenance.timing` is `stamped` only when the source
  gave a start time. A stamp is the station's clock, not the listener's audio
  position. Lyrics (web M4) may use a title only after alignment is proven.
- **Junk is filtered once.** Ads, slates, file names and templates become
  `between`, using the shared rules. Clients do not re-filter.

## Consequences

- The server now contacts hosts other than radio-browser. This is a security
  surface (SSRF, response size, redirect chains). The checks above and tests for
  each are required. The response must not be returned to the page raw.
- Each Now Playing poll is a Function request. At 10 s per poll that is about 360
  requests per listener-hour before caching. Current Cloudflare limits and prices
  were not checked; check them before launch.
- Stations with no adapter show the station name and no track. By the
  head-sweep of the top 100 web-playable stations, that is most of them: platform
  and broadcaster APIs reach about a fifth of the clicks there, while 58% of those
  clicks come from stations whose ICY already carries a title, which the web
  cannot read.
- Several adapters call endpoints that a station's own site uses without a
  published contract. They are held until reviewed. The adapter table must carry a
  switch to turn each one off without a deploy of code.
- The record has no history list yet. Add it when a surface needs it.

## Considered options

- **Server-side resolver (chosen):** one schema, one junk filter, one cache that
  protects small hosts from many listeners, and reach to sources the browser cannot
  call (no CORS). Costs a Function request per poll.
- **Browser calls adapters directly:** free of server cost. In a real Chrome run,
  20 of 24 APIs worked; Radio Paradise, TuneIn, WNYC and SHOUTcast did not. Every
  listener would poll the station's host. The junk filter would run in every
  client. Keep as a later optimisation for adapters whose hosts allow it.
- **Server-side ICY peek:** would cover the 58% of top-100 clicks whose ICY has a
  title. It means the server connects to station audio URLs, which ADR 0006
  forbids. Each peek may look like a listener to the station. **Left open.** It
  needs a new ADR that amends 0006, and the user's decision.
- **Browser reads ICY:** works for about a fifth of streams (a station must allow
  the `Icy-MetaData` header) and needs a second connection per listener. Ruled out
  as a baseline by ADR 0006.
- **hls.js for in-band HLS titles:** exposes ID3 titles, which the native element
  does not. It changes the playback path. Not part of this decision.

## Verification

Web M3a builds the Function and runs every case in `contracts/now_playing_feed/`.
The first-release adapters are listed above; the milestone names its tests.
