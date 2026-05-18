# M6.1: Tracklist enrichment for curated radio stations

**Status**: COMPLETED 2026-05-18 — shipped on `pocket-casts-ios` trunk in commit `8d557f3`.
**Builds on**: M6 (committed at `02d1a00`).

## Goal

Bring back the per-station tracklist feed for curated stations that have one (KCRW, KEXP), narrowly scoped so ICY metadata stays canonical for "what's playing right now" and the feed only enriches the display with album, album art, and play history. Restructure `StationDetailViewController` so the current track replaces the city/country line and the previous "Now Playing" single-line area becomes a scrollable tracklist with the layout from the user's reference (title bold, artist + album grey, square album art on the right).

The feed is fetched only when ICY signals an Artist/Track change — no fixed-interval polling.

## Done when

- `RadioStation` and `CuratedStation` regain a `tracklistUrl: String?` property. `curated_stations.json` re-adds `tracklistUrl` for KCRW (`https://tracklist-api.kcrw.com/Music/all/1?page_size=10`) and KEXP (`https://api.kexp.org/v2/plays/?limit=10`). NPR Hourly stays without one.
- `StationDetailViewController` layout matches the reference:
  - Station logo at top (unchanged from M6).
  - Station name (unchanged).
  - Bitrate label (moved to just under the name; replaces the old position).
  - **Current Track row**: replaces the city/country line. Renders the current `(title, artist, album, art)` in the row format from the user's image. Bold title, grey artist + album, square thumbnail.
  - **Tracklist** (replaces the old `nowPlayingSection` stack): a scrollable list of the most recent plays from the feed. Same row format. The current track sits at the top — visually unified with the rest of the list.
- For stations without a `tracklistUrl` (NPR, anything from radio-browser Browse): the tracklist area is hidden; the Current Track row still shows ICY title/artist (no album, no art); city/country reappears below the name as a fallback.
- The tracklist fetch is triggered by `radioStationNowPlayingDidChange` from `RadioMetadataObserver`. No fixed-interval polling. First fetch also runs on `viewWillAppear` so the list is populated immediately, even before any ICY frame.
- Album art is sourced only from the feed. No third-party music-API search fallback. If the feed doesn't include art for a track, that row shows a placeholder (small generic note icon — already used elsewhere) or the station logo. Decision in implementation; either is acceptable.
- City/country line is removed from the prominent slot. It is preserved for stations without a tracklist (fallback display) but can be omitted entirely if it complicates layout — verify in manual smoke.

## Architecture

- **Model change.** `tracklistUrl: String?` re-added to `CuratedStation` and `RadioStation`. `RadioBrowserAPI` still passes `nil`. Curated entries restore the field in JSON.
- **TracklistFeed.** New `RadioTracklistService` lives under `podcasts/Radio/`. Async function `fetch(stationId:url:) async throws -> [TracklistEntry]` that:
  - Dispatches per-station parsing based on `stationId` ("kcrw" vs "kexp").
  - Returns `[TracklistEntry]` — a model with `title`, `artist`, `album`, `albumArtURL: URL?`, `playedAt: Date?`.
- **Trigger.** `StationDetailViewController` observes `radioStationNowPlayingDidChange` (already does, from M6). On each notification matching the displayed station, kick off a `Task` to refetch the tracklist. Coalesce so only one in-flight request exists per station — drop duplicates within ~2 seconds (debounce).
- **UI structure.** Reuse a single tracklist UI for both "current track" (top entry, possibly visually highlighted) and the play history rows. Implementation: a `UITableView` (or `UICollectionView` with list layout). Each cell mirrors the user's image — title label, artist label, album label, square `UIImageView` for art on the trailing edge. The top row's `title` is the live value from ICY; the rest come from the feed.
  - On feed refresh: replace the data source with the feed's results. If ICY emitted a title that doesn't match the feed's top entry yet (race during feed update), keep the ICY title pinned in the top row until the next feed refresh resolves the discrepancy.
- **Bitrate position.** Moves from "between cityLabel and play button" to "below name, above current track row" — single line, small font, secondary color.
- **No third-party art lookup.** Explicit decision: M6.1 does not add an iTunes / MusicBrainz / etc. fallback. Stations without a feed get logo + ICY text only. Future milestone can add that if desired.

## Files

### NEW
- `podcasts/Radio/RadioTracklistService.swift` — async fetch + per-station parsing. KCRW + KEXP parsers move here (they used to live in `StationDetailViewController` pre-M6; mostly recreate from the M6 deletion plus the new `TracklistEntry` shape).
- `podcasts/Radio/TracklistEntry.swift` — `struct TracklistEntry { let title, artist, album, albumArtURL: URL?, playedAt: Date? }`.
- `podcasts/Radio/TracklistCell.swift` — `UITableViewCell` (or equivalent) rendering one row in the reference layout.

### EDIT
- `podcasts/Radio/CuratedStation.swift` — re-add `tracklistUrl: String?`.
- `podcasts/Radio/RadioStation.swift` — re-add `tracklistUrl: String?`. Init arg with default nil.
- `podcasts/Radio/RadioBrowserAPI.swift` — pass `tracklistUrl: nil` again when constructing `RadioStation` from radio-browser results.
- `podcasts/Radio/curated_stations.json` — re-add `"tracklistUrl"` keys for KCRW and KEXP. NPR stays without.
- `podcasts/Radio/StationDetailViewController.swift` — restructure layout. Add `UITableView` or list-style stack for the tracklist. Move bitrate label under the station name. Replace the city/country line with the Current Track row. Subscribe to `radioStationNowPlayingDidChange` (already does); on each match, debounce + refetch tracklist via `RadioTracklistService`.

### NO CHANGE
- `podcasts/Radio/RadioMetadataObserver.swift` — keeps its M6 behavior. Triggers feed fetches by being observable, not by knowing about feeds.
- `podcasts/DefaultPlayer.swift` — observer-hook stays as-is.
- `podcasts/Radio/StreamsHostViewController.swift` — Streams page structure (Favorites + Browse) unchanged.
- `podcasts/Radio/RadioFavoritesSeeder.swift` — seeder seeds the same three stations.

## Risks / Edge cases

- **Two sources of truth for title.** ICY frames vs. tracklist API. Resolution: ICY is canonical. The Current Track row's `title` always reflects the latest ICY emission. The feed contributes `album` + `albumArtURL` + history rows. If the feed's top entry's `title` doesn't match ICY's current title (clock skew, feed lag), trust ICY for the top row's title but still use the feed's top entry for album + art (best-effort match by approximate string compare; fall back to "—" for album, station logo for art).
- **Feed lag.** KCRW + KEXP feeds update on the station's automation cadence — usually within seconds of a track change, sometimes minutes late. The user will sometimes see ICY title change a few seconds before the feed-derived album/art row catches up. Acceptable.
- **Feed downtime.** Feed HTTP errors must not blank the screen. On error, keep the previously-fetched tracklist visible and log; show ICY title alone in the current track row until the next successful fetch.
- **Debounce window.** Multiple ICY frames within a short window (e.g. ad insertion → real track) should not trigger N fetches. 2-second debounce on the trigger.
- **Memory in tracklist.** Cap the visible history at 10 entries (matches the feed's natural `page_size`). No infinite scroll in this milestone.
- **Album art loading.** Use the existing image-loading infrastructure in the app if there is one (search for cached `UIImage(named:)` usage or a shared loader). If none obviously fits, plain `URLSession` + `UIImage(data:)` is fine for M6.1 — premature optimization to introduce a new caching layer.
- **Non-curated stations.** Browse-found stations have `tracklistUrl == nil`. UI must gracefully hide the tracklist area, hide the album/art slot on the current track row, and fall back to ICY title + artist + station favicon.
- **Bitrate position change.** Moving the bitrate label means callers that test for its position in the stack (none currently, but future tests) should not depend on the old slot.

## Reference sweep

```bash
grep -rn "tracklistUrl\|parseKCRW\|parseKEXP\|RadioTracklistService\|TracklistEntry" \
  podcasts/ PocketCastsTests/
```

After M6.1 lands, expect `tracklistUrl` references in `CuratedStation.swift`, `RadioStation.swift`, `curated_stations.json`, `RadioBrowserAPI.swift`, `StationDetailViewController.swift`, and the new service file. Should NOT appear in any test file other than service tests.

## Automated tests

NEW `PocketCastsTests/Tests/Radio/RadioTracklistServiceTests.swift`
- KCRW parser: decodes a fixture JSON response into `[TracklistEntry]` with correct field mapping.
- KEXP parser: decodes a fixture JSON response, filters out non-`trackplay` entries (commercials, station IDs), returns only real plays.
- Unknown stationId: returns empty array, no throw.
- Malformed JSON: throws, doesn't crash.
- Album art URL: extracted when present, nil when absent.

NEW `PocketCastsTests/Tests/Radio/TracklistEntryTests.swift`
- `TracklistEntry` `Equatable` / `Hashable` round-trip (if conformances are added).

Existing tests must continue to pass:
- `RadioMetadataObserverTests` — unchanged.
- `RadioFavoritesSeederTests` — unchanged.
- `StreamsHostViewControllerTests` — unchanged.

`StationDetailViewControllerTests` is **not** added in this milestone. The detail-VC integration relies on URLSession + ICY notifications; testing it well needs a stubbed service + injected dependency. Defer to a follow-up if test coverage demand grows.

## Manual smoke

1. `make run_sim`.
2. Tap KCRW from Favorites → detail screen.
3. Confirm layout: logo at top, name `KCRW`, bitrate `192 kbps` below name, Current Track row, Tracklist list below.
4. Tap Play → wait past preroll → Current Track row populates from ICY (title + artist). Within ~2 seconds the album and art appear, sourced from the feed.
5. Scroll the tracklist → previous plays visible with title, artist, album, art.
6. Tap KEXP → same behavior; feed source is the KEXP API.
7. Wait for a track change on KCRW or KEXP → ICY change triggers a refetch. Current Track row updates, tracklist top row matches, older rows shift down.
8. Tap NPR Hourly → tracklist area is hidden. Current Track row shows ICY title + artist if any, or stays blank. No errors.
9. Browse → pick a radio-browser station with ICY metadata (e.g. KEXP via browse, or any KCRW-like indie station) → confirm tracklist area is hidden but current track populates from ICY alone.
10. Network log: confirm tracklist fetches happen only on `radioStationNowPlayingDidChange` (debounced), not on a fixed timer.
11. Lose network mid-play → existing tracklist stays visible; next ICY change attempts a fetch and fails gracefully (no crash, no UI wipe).

## Agentic plan

Sequential phases. Each agent reads this file as ground truth.

### Phase 1 — Restore `tracklistUrl` + introduce service + entry types
- Agent: `general-purpose`, model: Sonnet 4.6.
- Files allowed:
  - `podcasts/Radio/CuratedStation.swift`
  - `podcasts/Radio/RadioStation.swift`
  - `podcasts/Radio/RadioBrowserAPI.swift`
  - `podcasts/Radio/curated_stations.json`
  - NEW `podcasts/Radio/TracklistEntry.swift`
  - NEW `podcasts/Radio/RadioTracklistService.swift`
  - NEW `PocketCastsTests/Tests/Radio/RadioTracklistServiceTests.swift`
- Re-add `tracklistUrl: String?` to model + JSON. Define `TracklistEntry`. Implement `RadioTracklistService` with KCRW + KEXP parsers (port the M6-deleted parsers, plus the album / art / playedAt fields the M6 versions ignored).
- Verify: `make test_staging ONLY_TESTING=PocketCastsTests/RadioTracklistServiceTests` then `make build_staging`.

### Phase 2 — Detail VC restructure + tracklist UI
- Agent: `general-purpose`, model: Sonnet 4.6.
- Files allowed:
  - `podcasts/Radio/StationDetailViewController.swift`
  - NEW `podcasts/Radio/TracklistCell.swift`
- Restructure layout per the goal. Subscribe to `radioStationNowPlayingDidChange`, debounce, fetch on change, render. Reference image layout for cell. Move bitrate label.
- Verify: `make build_staging`.

### Phase 3 — Review
- Agent: `caveman:cavecrew-reviewer`, model: Sonnet 4.6.
- Focus: ICY vs. feed precedence for `title` (ICY wins); debounce correctness; feed-error handling (don't blank visible data); memory of the in-flight `Task` (cancel on VC dealloc); tracklist UI for stations without a `tracklistUrl` (hidden cleanly); reference-sweep cleanliness.

### Phase 4 — Manual smoke
- Human runs Manual smoke list. Sign off before commit.

## Notes

- Album art lookup via third-party search (iTunes / MusicBrainz) is explicitly **out of scope** for M6.1. Future milestone if desired.
- The Streams host (M6) and ICY observer (M6) are reused as-is. No regressions expected in those areas.
- Tracklist row visuals follow the user's reference image: title bold, artist + album in secondary text color, square album-art thumbnail trailing.
