# M7: Unify curated enhancements across Favorites + Browse

**Status**: COMPLETED 2026-05-18 — shipped on `pocket-casts-ios` trunk in commit `1a7134c`.
**Builds on**: M6.1 (committed at `8d557f3`).

## Goal

Today's Streams page treats "curated" and "browsed" stations as two parallel populations. KCRW + KEXP + NPR appear in `curated_stations.json` with their own string ids (`"kcrw"`, `"kexp"`, `"npr_hourly"`), their own bundled logos and tracklist URLs, while the same stations also exist in radio-browser results with different UUIDs and zero enhancements. Same physical station, two different code paths, depending on how the user discovered it.

M7 restructures so curated entries become **decorations keyed by radio-browser UUID(s)**. Browse + Favorites + the detail screen all consult one inverted index: `radio-browser UUID → enhancement (logo, tracklistUrl, preferred display name)`. A user favoriting any KCRW variant from Browse gets the curated treatment automatically. A user favoriting a KCRW MP3 instead of the AAC variant also gets the curated treatment, because both UUIDs belong to the same enhancement group.

`playbackBehavior` (live vs onDemand for NPR-as-podcast) is **out of scope** for M7. That belongs to M8.

## Done when

- `podcasts/Radio/curated_stations.json` is restructured: each entry has `id` (logical group id), `name`, `logoAsset`, `tracklistUrl?`, `radioBrowserUUIDs: [String]` (one or more), and `defaultSeedUUID: String` (one entry from `radioBrowserUUIDs` chosen for the first-launch seeder).
- A build-time computed `[String: CuratedEnhancement]` inverted index — keyed by radio-browser UUID — is exposed by `CuratedStationsLoader` (lazy, computed once per app session).
- The `streamUrl`, `donateUrl`, `homepageUrl`, `city`, `bitrate` fields are **removed** from `curated_stations.json`. Those come from radio-browser. (Donate and homepage may resurface later if needed; for M7, drop.)
- `RadioStation` instances constructed from radio-browser results pick up `logoAsset` and `tracklistUrl` via the inverted index when their UUID matches a curated group. Non-matching stations get no enhancement.
- `StationDetailViewController` shows the curated logo + tracklist for any station whose UUID is in the inverted index, regardless of whether the user got there via Favorites or Browse. Visual identity is uniform.
- The Favorites tab displays the same enhanced logo for curated UUIDs.
- The seeder uses `defaultSeedUUID` from each curated entry to populate Favorites on first launch.
- When a curated enhancement references a tracklist URL that fails to load (HTTP error / parse error), the user sees a `Toast.show(...)` message ("Couldn't load tracklist") and the rest of the screen stays usable.
- Existing tests pass. New tests cover: the inverted-index build, enhancement resolution by UUID, and the Toast trigger path.

## Architecture

- **Curated JSON format change.** Existing string ids (`"kcrw"`, `"kexp"`, `"npr_hourly"`) become logical group ids. Each carries an array of radio-browser UUIDs and one `defaultSeedUUID`. No more `streamUrl` field — the playable URL comes from the radio-browser entry the user actually selected.
- **CuratedStation model** gains: `radioBrowserUUIDs: [String]`, `defaultSeedUUID: String`. Loses: `streamUrl`, `donateUrl`, `homepageUrl`, `city`, `bitrate`. Keeps: `id`, `name`, `description`, `logoAsset`, `tracklistUrl`, `seedAsFavorite`.
- **CuratedEnhancement** — new lightweight struct extracted from `CuratedStation`. Holds the display-time decoration fields: `name`, `logoAsset`, `tracklistUrl`, `description`. The `id` and seeding fields don't belong here.
- **CuratedStationsLoader** gains `enhancementsByUUID: [String: CuratedEnhancement]` — lazy, computed by walking the curated list and producing one entry per UUID in `radioBrowserUUIDs`.
- **RadioBrowserAPI** at the point where it builds `RadioStation` from a radio-browser response: look up the enhancement by UUID. If present, pass `tracklistUrl` and `logoAsset` through to the constructed `RadioStation`. If absent, both stay nil.
- **RadioStation model** gains `logoAsset: String?` — already implicit via curated path; M7 makes it explicit and consumable from Browse too.
- **StationDetailViewController** stops asking `curatedStation` for the logo. It reads `station.logoAsset` directly (which the radio-browser path now populates when enhancement applies). The "look up curated by stationId" fallback added in M6.1 is removed — no longer needed because the radio-browser entry already carries the logo asset name.
- **Tracklist refetch error path.** `refetchTracklist()` currently swallows errors silently. M7 changes the catch block to surface a single `Toast.show("Couldn't load tracklist for \(station.displayableTitle())")` — but only on the first failure per session for a given station, so the user doesn't get spammed if the feed is flapping. Track per-station "already toasted" state in the service.
- **Seeder migration.** M6 seeder seeds by curated `id` string (`"kcrw"`, etc.). M7 changes it to use `defaultSeedUUID` — meaning the favorited row in Supabase carries the radio-browser UUID, not the string id. **This is a breaking change for existing seeded favorites.** A migration is needed: on first-launch under M7, if `radioFavoritesSeeded` is already true (M6 ran the old seed), un-seed old string ids and re-seed with UUIDs. Or: bump the flag to `radioFavoritesSeededM7` and run a fresh seed of new UUIDs, leaving the old string-id favorites stranded in Supabase (user can clean up). Pick the second; simpler and the legacy rows are harmless dead data.

## Files

### NEW
- `podcasts/Radio/CuratedEnhancement.swift` — display-time decoration struct.

### EDIT
- `podcasts/Radio/CuratedStation.swift` — schema change: drop streamUrl/donateUrl/homepageUrl/city/bitrate; add radioBrowserUUIDs + defaultSeedUUID; expose conversion to `CuratedEnhancement`.
- `podcasts/Radio/CuratedStationsLoader` (inside `CuratedStation.swift`) — add `enhancementsByUUID` lazy property.
- `podcasts/Radio/curated_stations.json` — restructure to new schema. **Rule for `defaultSeedUUID`: always pick the highest-bitrate variant available in the group.** UUIDs to populate:
  - KCRW Eclectic 24: `["18e31f25-53c8-4213-a1ec-dccc0443a788", "25ff2df8-f8ea-4af8-b283-48ba3bdcaf69", "6238f5e8-a9ee-4c88-9713-2d1ab4112ac9"]`. `defaultSeedUUID = "6238f5e8-a9ee-4c88-9713-2d1ab4112ac9"` (AAC 256k — highest).
  - KEXP: `["445cbb3a-1c4e-49aa-a268-f5b6acfa8f2e", "399ca326-0f67-4015-a51b-d7ba2bd4ebbe", "a509502d-1ba7-4d51-9791-0be5a7d5ec34"]`. `defaultSeedUUID = "445cbb3a-1c4e-49aa-a268-f5b6acfa8f2e"` (AAC 162k — highest; the 65kbps AAC+ variants are excluded from the group entirely).
  - NPR Hourly Newscast: `["a5314180-7573-4b46-aafc-51ed2d5b9e71"]`. `defaultSeedUUID` = same (only variant).
- `podcasts/Radio/RadioStation.swift` — add `logoAsset: String?` as init arg + property. Init defaults to nil.
- `podcasts/Radio/RadioBrowserAPI.swift` — look up `CuratedStationsLoader.shared.enhancementsByUUID[uuid]` after building a station; pass `tracklistUrl` and `logoAsset` from the enhancement into the `RadioStation` initializer.
- `podcasts/Radio/StationDetailViewController.swift` — read `station.logoAsset` directly. Drop the M6.1 curated-by-stationId fallback. On `refetchTracklist()` failure, surface a one-shot toast per station per session. **Remove the donate button from the layout entirely** (curated `donateUrl` is dropped from the schema; radio-browser doesn't carry one). Future milestone can revive donate via `CuratedEnhancement.donateUrl?`.
- `podcasts/Radio/RadioTracklistService.swift` — track "already toasted" state per stationId so the same failure doesn't fire repeated toasts.
- `podcasts/Radio/RadioFavoritesSeeder.swift` — seed using `defaultSeedUUID` from curated entries. Switch the gating flag to `radioFavoritesSeededM7`. Leave old `radioFavoritesSeededM6` flag in place (do not unset it) so the old code path's logic remains coherent if reverted.
- `podcasts/Constants.swift` — add `radioFavoritesSeededM7` UserDefaults key.

### NO CHANGE
- `podcasts/Radio/RadioMetadataObserver.swift` — observes by stationId (the radio-browser UUID is what flows through). Already works for any station, curated or not.
- `podcasts/Radio/StreamsHostViewController.swift` — Favorites + Browse layout unchanged.
- `podcasts/Radio/FavoritesViewController.swift`, `BrowseViewController.swift` — list rendering already pulls from RadioStation properties; once those carry `logoAsset`, the cells will use them.
- `podcasts/DefaultPlayer.swift` — observer hook unchanged.

## Risks / Edge cases

- **Schema migration in curated_stations.json.** Existing fields removed. Any other code that read those fields needs updating. Reference sweep below.
- **Seeder behavior change.** New flag `radioFavoritesSeededM7`. Old `radioFavoritesSeededM6` favorites (string ids) remain in Supabase as orphans. Document; do not try to clean them up automatically — the rows are harmless and the user can prune from another client if desired.
- **radio-browser UUID drift.** A station's UUID is theoretically stable but radio-browser has occasionally cleaned up duplicates. If a listed UUID no longer resolves, that variant simply won't pick up enhancements. Acceptable; the user re-discovers via Browse and we add the new UUID to the JSON.
- **Multiple curated entries claiming the same UUID.** Inverted-index build should detect this and `assertionFailure(...)` in debug; in release, pick the first and log. Configuration error in the JSON.
- **Toast spam.** Without the per-station dedupe, the 2s-debounced tracklist refetch could fire ~30 toasts in a minute on a flapping feed. Per-station per-session dedupe is mandatory.
- **logoAsset for radio-browser-only stations.** Most Browse results have a `favicon` URL but no bundled asset. M7 still respects `favicon` when present (Browse already does this — verify). The new `logoAsset` field on `RadioStation` is populated only for curated UUIDs; everything else stays on the favicon path.
- **Bitrate display.** M6.1 had bitrate from curated JSON (overridden 192→256 for KCRW AAC) and from radio-browser response for Browse. With the curated `bitrate` field gone, bitrate ALWAYS comes from radio-browser. KCRW AAC reports `256` to radio-browser, so the display value is unchanged. Verify in smoke.
- **Detail screen for non-enhanced stations.** Station-without-enhancement should keep working: no logoAsset → falls back to favicon, no tracklistUrl → tracklist table hidden. Both branches already exist; the M7 changes simplify how `station.logoAsset` and `station.tracklistUrl` get populated, not how they're consumed.

## Reference sweep

```bash
grep -rn "streamUrl\|donateUrl\|homepageUrl\|\.city\|curatedStation\." \
  podcasts/Radio podcasts/Constants.swift PocketCastsTests/Tests/Radio
```

Confirm the schema-change deletions don't break unexpected callers. `streamUrl` is still consumed by playback (resolved from radio-browser entries) — verify that PlaybackManager / DefaultPlayer get the URL from `station.streamUrl` (the radio-browser-supplied URL on the RadioStation), not from any curated source.

## Automated tests

NEW `PocketCastsTests/Tests/Radio/CuratedEnhancementsIndexTests.swift`
- Inverted index has correct UUID → enhancement mapping for the three groups (KCRW, KEXP, NPR).
- Duplicate UUIDs across entries → `assertionFailure` (or controlled error) in debug.
- Looking up a UUID that's not in any entry returns nil.

NEW `PocketCastsTests/Tests/Radio/RadioBrowserEnhancementTests.swift`
- When `RadioBrowserAPI` constructs a `RadioStation` whose UUID is in the inverted index, the resulting `RadioStation` carries `logoAsset` and `tracklistUrl` from the enhancement.
- A `RadioStation` with a non-matching UUID has both fields nil.

EDIT `PocketCastsTests/Tests/Radio/RadioFavoritesSeederTests.swift`
- Update tests to assert seed uses UUIDs (not string ids).
- Update `radioFavoritesSeeded` references to `radioFavoritesSeededM7`.

EDIT `PocketCastsTests/Tests/Radio/RadioTracklistServiceTests.swift`
- Add a test that the "already toasted" tracker prevents repeat triggers within a session.

Existing tests:
- `RadioMetadataObserverTests` — unchanged.
- `RadioTracklistServiceTests` — unchanged except for the toast-dedupe test above.
- `StreamsHostViewControllerTests` — unchanged.

## Manual smoke

1. `make run_sim`.
2. Fresh install, signed in: confirm KCRW Eclectic 24 (AAC), KEXP (AAC 160k), NPR Newscast appear in Favorites with curated logos.
3. Tap KCRW from Favorites → detail screen shows KCRW logo + bitrate + tracklist.
4. Open Browse, search "kcrw" → results list. Tap a different KCRW variant (e.g. the MP3 192k). Detail screen should also show the KCRW logo and tracklist — proving the enhancement applies regardless of which variant was tapped.
5. Search Browse for a random radio-browser station (e.g. "BBC World") → tap it → detail screen shows the station's favicon (or generic icon) and NO tracklist — proving non-curated stations don't trigger the enhancement path.
6. Disconnect network mid-play on KCRW → wait for the 2s-debounced refetch to fire → confirm a single Toast appears. Stays absent for subsequent failures within the same session.
7. Reconnect → next ICY change triggers a refetch → no toast (success path resets the toast dedupe per station).
8. Verify no HTTP requests to `tracklist-api.kcrw.com` happen for non-KCRW stations.

## Agentic plan

Sequential phases. Each agent reads this file as ground truth.

### Phase 1 — Schema + inverted index
- Agent: `general-purpose`, model: Sonnet 4.6.
- Files allowed:
  - `podcasts/Radio/CuratedStation.swift`
  - NEW `podcasts/Radio/CuratedEnhancement.swift`
  - `podcasts/Radio/curated_stations.json`
  - `podcasts/Radio/RadioStation.swift` (add `logoAsset`)
  - `podcasts/Radio/RadioBrowserAPI.swift` (apply enhancement at construction)
  - NEW `PocketCastsTests/Tests/Radio/CuratedEnhancementsIndexTests.swift`
  - NEW `PocketCastsTests/Tests/Radio/RadioBrowserEnhancementTests.swift`
- Restructure JSON, build inverted index, wire enhancement into Browse path. Drop dead fields from CuratedStation. Old curated `streamUrl` / `donateUrl` / `homepageUrl` / `city` / `bitrate` callers may need cleanup — surface them.
- Verify: `make test_staging ONLY_TESTING=PocketCastsTests/CuratedEnhancementsIndexTests` then `make test_staging ONLY_TESTING=PocketCastsTests/RadioBrowserEnhancementTests` then `make build_staging`.

### Phase 2 — Detail VC simplification + toast on failure
- Agent: `general-purpose`, model: Sonnet 4.6.
- Files allowed:
  - `podcasts/Radio/StationDetailViewController.swift`
  - `podcasts/Radio/RadioTracklistService.swift`
  - `PocketCastsTests/Tests/Radio/RadioTracklistServiceTests.swift`
- Read `station.logoAsset` directly. Drop M6.1 curated-by-stationId fallback. Toast on tracklist failure with per-station dedupe in the service.
- Verify: `make test_staging ONLY_TESTING=PocketCastsTests/RadioTracklistServiceTests` then `make build_staging`.

### Phase 3 — Seeder + migration
- Agent: `general-purpose`, model: Sonnet 4.6.
- Files allowed:
  - `podcasts/Radio/RadioFavoritesSeeder.swift`
  - `podcasts/Constants.swift`
  - `PocketCastsTests/Tests/Radio/RadioFavoritesSeederTests.swift`
- Seeder uses `defaultSeedUUID`. New flag `radioFavoritesSeededM7`. Old M6 flag left untouched (idempotent, harmless).
- Verify: `make test_staging ONLY_TESTING=PocketCastsTests/RadioFavoritesSeederTests` then `make build_staging`.

### Phase 4 — Review
- Agent: `caveman:cavecrew-reviewer`, model: Sonnet 4.6.
- Focus: inverted-index correctness; logo resolution paths (Favorites vs Browse vs detail); toast dedupe lifetime (per session vs per VC instance); seeder migration semantics; reference-sweep cleanliness (no dead `streamUrl`/`donateUrl`/etc. callers).

### Phase 5 — Manual smoke
- Human runs Manual smoke list. Sign off before commit.

## Notes

- KCRW Eclectic 24 UUIDs were resolved via `https://de1.api.radio-browser.info/json/stations/byname/KCRW`. Three entries returned; AAC 256k chosen as `defaultSeedUUID` (was the M6.1 default after the AAC switch).
- KEXP: many variants exist. AAC 160k picked as default. The 65kbps AAC+ entries are deliberately excluded from the curated group — too low quality for the seeded default.
- NPR: a single `NPR Newscast` entry exists with bitrate `0`. Bitrate display will be hidden for it.
- "Donate to ..." button: dropping `donateUrl` from curated means the button needs a different source (radio-browser entries don't carry one). For M7 simplicity, hide the donate button entirely. If a user wants to donate to KCRW, the link is one tap away in Safari. Future milestone can revive the donate field as part of `CuratedEnhancement`.
- onDemand playback for NPR Newscast (skip-fwd/back, scrubber) is M8 work.
