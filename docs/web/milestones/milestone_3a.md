# Web M3a — Now Playing resolver

**Status**: IN PROGRESS — worktree and branch created from web `main` at `dbf7759` on 2026-10-29. The pure TypeScript contract port and request builders are committed on the branch (`77c513f`, `e918742`); the authenticated resolver Function and cache are not built yet.
**Depends on**: Web M2 (session validation, `curated_stations`, the `/api/playback` pattern); web [ADR 0006](../adr/0006-direct-https-playback-without-an-audio-relay.md) and [ADR 0008](../adr/0008-now-playing-comes-from-a-server-side-resolver.md); shell contract `contracts/now_playing_feed/`
**Parent**: [Global M4](../../global/milestones/milestone_4.md)
**Required by**: Web M3 (the Now Playing card and Media Session read this record), Web M4 (lyrics need a verified timing label)

## Where the work happens

| | |
|---|---|
| Plan | Shell `main`: this file |
| Code | `pocket-radio-web`, branch `feature/m3a-now-playing` from `main` after M2 merges. Confirmed by the user, 2026-10-29 |
| Worktree | `pocket-radio-web-m3a/`, a sibling of the main checkout. Confirmed by the user, 2026-10-29 |
| Shell changes | Additive: `contracts/now_playing_feed/` (already on `main`); a `supabase/migrations/` file adding a nullable `metadata_source` column to `curated_stations` and a public-read table `station_metadata_sources` |

**Goal:** Give the web player one Now Playing record per station, built on the
server from allowlisted metadata endpoints. The first release covers KEXP, KCRW,
AzuraCast, laut.fm and Sveriges Radio. Every other station answers
`unsupported`. The record follows the shared contract, so iOS and the menubar can
adopt the same cases. This milestone builds no player UI.

**User checkpoint:** Signed in on the staging site, open
`/api/now-playing?stationId=<id>` for KEXP and KCRW. The title, artist, artwork
and start time match what the iPhone shows. Open it for a live AzuraCast station:
it shows a song, and after the song's end plus a minute it shows `between`, not
the old title. Open a SomaFM station: it shows `unsupported`. Open it signed out:
`401`.

## Scope

- **Shared code (`shared/now-playing/`).** The record types; one adapter per
  source (a request builder and a pure parser); the time converters; the junk
  filter; the status rules (`playing`, `between`, `stale`). No I/O inside parsers.
- **Contract runner (`tests/now-playing/`).** Loads every file in
  `../contracts/now_playing_feed/cases/` and `junk_filter.json`, serves each
  case's `raw` in place of the network, and checks the produced record equals
  `expected`. Also validates every expected record against `schema.json`.
- **Function (`functions/api/now-playing.ts`, `functions/_lib/nowplaying/`).**
  `GET` with one `stationId`; session and same-origin checks as `/api/playback`;
  station lookup; adapter choice; fixed upstream host list; no redirects; byte cap;
  8 s timeout; 8 s cache on success and 60 s on failure; `pollAfterSec`.
- **Adapter choice.** `curated_stations.metadata_source` first, then
  `station_metadata_sources` by radio-browser UUID, then URL-pattern rules. The
  URL-pattern step does no network I/O.
- **Migration (shell `supabase/migrations/`).** `curated_stations.metadata_source
  jsonb null`; `station_metadata_sources(station_uuid, adapter, params, enabled,
  terms_reviewed_on, notes)` with public read, no client write. `enabled` is the
  per-adapter kill switch. KEXP and KCRW get their `metadata_source` from their
  existing `tracklist_url` rows.
- **Seed.** The first rows of the head-sweep: the AzuraCast, laut.fm and
  Sveriges Radio stations in the top 300 web-playable stations, found from the
  sweep's CSV.

## Behaviors to test (red -> green, one at a time)

1. For each adapter in the first release, every contract case for it produces its
   `expected` record.
2. The junk filter returns the expected kind for every case in `junk_filter.json`.
3. Time rules: ended recently is `between`; ended long ago is `stale`; no
   duration and an old stamp is `stale`; a show is never `stale` for lack of a
   duration.
4. A record validates against `schema.json`.
5. Adapter choice follows the order above. A station with no match returns
   `unsupported`. A SomaFM station returns `unsupported`.
6. The Function rejects a signed-out request (`401`), a request from another
   origin (`403`), a missing or repeated `stationId` (`400`), and an unknown
   station (`404`).
7. For a station whose own host is the metadata host, a host that fails ADR 0006's
   checks (HTTP, an explicit port, an IP address, credentials) is refused before
   any request.
8. An upstream redirect is not followed. An oversized body and a slow upstream
   both end in `unavailable` and are cached for 60 s.
9. Two requests inside 8 s for the same station make one upstream request.
10. No test double records a request to a station's audio URL. A fake `fetch`
    fails the test if it is called with one.
11. The response never includes the upstream body or headers.
12. An adapter with `enabled = false` answers `unsupported` without a request.

## Out of scope

- The Now Playing card, Media Session, and polling in the page: web M3.
- Lyrics: web M4. This milestone only supplies the `timing` label.
- Triton, iHeart, Radio France, NPR Composer, Airtime Pro, RadioKing, Live365,
  ABC, NPO: held until a terms review is recorded. Each becomes a later slice.
- SomaFM: excluded by decision. Radio Paradise, NTS, TuneIn: not recorded yet.
- A server-side ICY peek, browser-side ICY, and hls.js. Server-side peeking is not chosen for now (ADR 0008); a new ADR amending ADR 0006 is required before reconsidering it.
- History and next-up lists.
- The Swift port of the contract. iOS and the menubar adopt it in their own
  milestones.

## Docs impact

- **Docs this changes or makes stale:** web ADR 0006 (add a pointer to ADR 0008
  where it says metadata feeds "may be investigated later"); `docs/web/README.md`
  roadmap; `docs/web/architecture/communication.md` (a new endpoint);
  `docs/web/CONTEXT.md` (terms: Now Playing record, Adapter, Between);
  `contracts/now_playing_feed/README.md` once a port has checked it.
- **Questions this must settle:** whether the resolver stays on a Cloudflare free
  plan once Cloudflare's current limits are checked; who reads the laut.fm API
  docs and records the terms entry; whether `station_metadata_sources` belongs
  in the shared database or the web's own.
