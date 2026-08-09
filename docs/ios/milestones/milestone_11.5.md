# iOS M11.5 — `RadioCarPlayRowBuilder` (pure structs)

**Status**: COMPLETED — `b9ea839`
**Depends on**: M11.4
**Required by**: M11.6

---

## Goal

A pure function: cache snapshot + curated stations + sign-in state → the exact
rows and sections the CarPlay Radio tab should show. No CarPlay types, no
singletons, no I/O (D13).

---

## Why a struct layer instead of building `CPListSection` directly

`CPInterfaceController` cannot be instantiated in a test. `CPListSection` and
`CPListItem` probably *can* be, but they expose almost nothing readable — there is
no stable public accessor for a section's items, and `handler` is write-only. You
would be asserting on values you cannot read back.

~30 lines of plain structs makes every branch assertable, and gives a weak model a
spec it cannot misread: *given these inputs, return this array of structs.* The
CarPlay adapter (M11.6) then becomes mechanical enough to be near-unfailable.

---

## Done when

### 1. The model

New file `podcasts/CarPlay/RadioCarPlayRowBuilder.swift`.

```swift
/// One row in the CarPlay Radio tab, independent of CarPlay types.
struct RadioCarPlayRow: Equatable {
    let stationId: String
    let title: String
    let detail: String?         // city/country, nil when unknown
    let logoAsset: String?      // bundle asset name (curated)
    let faviconUrl: String?     // remote favicon (radio-browser)
    let streamUrl: String
    let isPlaying: Bool
}

struct RadioCarPlaySection: Equatable {
    let header: String
    let rows: [RadioCarPlayRow]
}

enum RadioCarPlayRowBuilder {
    /// - Parameters:
    ///   - favorites: `RadioFavoritesCache.snapshot()`
    ///   - curated: `CuratedStationsLoader.load()`
    ///   - isSignedIn: `ServerSettings.userId != nil`
    ///   - nowPlayingStationId: `PlaybackManager.liveStation(for: nil)?.uuid`
    ///   - maxRowsPerSection: `Constants.Limits.maxCarplayItems` (100)
    static func sections(
        favorites: [CachedFavoriteStation],
        curated: [CuratedStation],
        isSignedIn: Bool,
        nowPlayingStationId: String?,
        maxRowsPerSection: Int
    ) -> [RadioCarPlaySection]
}
```

### 2. The rules

- [ ] Favorites section first, then Curated. Order is fixed.
- [ ] Headers: `L10n.carplayRadioFavorites` ("Favorites") and
      `L10n.carplayRadioStations` ("Stations"). New keys — see below.
- [ ] **Omit the Favorites section entirely** when `isSignedIn == false` **or**
      `favorites.isEmpty` (D10). No placeholder row, no error row: a driver cannot
      act on it, and an untappable row in a CarPlay list reads as a broken button.
- [ ] Curated section is **always** present. Bundle-local, so the tab is never
      empty — that is the whole point of D2.
- [ ] **No dedupe** (D4). A favorited curated station appears in both sections.
- [ ] Each section independently capped at `maxRowsPerSection` via `prefix`.
- [ ] `isPlaying` is `stationId == nowPlayingStationId` — for rows in **both**
      sections when duplicated.
- [ ] Favorites rows map straight from `CachedFavoriteStation`.
- [ ] Curated rows map from `CuratedStation`: `title` = `name`, `detail` =
      `description`, `logoAsset` = `logoAsset`, `faviconUrl` = nil,
      `streamUrl` = **empty string**.

**On the empty `streamUrl` for curated rows:** `CuratedStation` has no stream URL —
it carries `defaultSeedUUID` and `radioBrowserUUIDs`, which must be resolved through
`RadioBrowserAPI`. The builder stays pure and does not resolve. M11.6's tap handler
uses `RadioPlaybackStarter.play(stationId:source:)` (the async resolving overload)
whenever `streamUrl` is empty, and the synchronous `play(station:source:)` when it
is populated. Document this at both ends.

### 3. Localization

Add to `podcasts/en.lproj/Localizable.strings` with translator comments and
snake_case keys, per the project convention:

```
/* CarPlay — title of the Radio tab in the CarPlay tab bar */
"carplay_radio_tab" = "Radio";

/* CarPlay — section header above the user's favorite radio stations */
"carplay_radio_favorites" = "Favorites";

/* CarPlay — section header above the curated built-in radio stations */
"carplay_radio_stations" = "Stations";

/* CarPlay — shown when the radio tab has no stations to display */
"carplay_radio_empty" = "No stations available";
```

- [ ] Use the generated `L10n` enum (`L10n.carplayRadioTab`, etc.). Never
      `LocalizedStringKey`, never string interpolation.

### 4. Tests

New file `PocketCastsTests/Tests/CarPlay/RadioCarPlayRowBuilderTests.swift`.
Pure — no `import CarPlay`, no simulator UI, no network.

- [ ] `testSignedOutOmitsFavoritesSection` — one section, header "Stations"
- [ ] `testEmptyFavoritesOmitsFavoritesSection` — signed in, `favorites: []` → one section
- [ ] `testBothSectionsWhenFavoritesPresent` — order is Favorites, then Stations
- [ ] `testCuratedSectionAlwaysPresent` — signed out **and** empty favorites → still
      exactly one Stations section with all curated rows
- [ ] `testNoDedupe` — a curated station also in favorites appears **twice**, once
      per section
- [ ] `testIsPlayingSetOnBothCopies` — when that duplicated station is playing,
      `isPlaying` is true in both sections
- [ ] `testIsPlayingFalseWhenNilNowPlaying`
- [ ] `testFavoritesCappedAtMax` — 150 favorites, `maxRowsPerSection: 100` → 100 rows
- [ ] `testFavoriteRowFieldsMapped` — name, city→detail, logoAsset, faviconUrl,
      streamUrl all carried through
- [ ] `testCuratedRowHasEmptyStreamUrlAndNilFavicon` — locks in the contract M11.6
      depends on
- [ ] `testCuratedDetailUsesDescription`

---

## Files

| File | Change |
|---|---|
| `podcasts/CarPlay/RadioCarPlayRowBuilder.swift` | **new** — needs `project.pbxproj` registration |
| `podcasts/en.lproj/Localizable.strings` | 4 new keys |
| `PocketCastsTests/Tests/CarPlay/RadioCarPlayRowBuilderTests.swift` | **new** — auto-discovered |

---

## Verification

```bash
cd pocket-radio-ios
make format
make build_staging
make test_staging ONLY_TESTING=PocketCastsTests/RadioCarPlayRowBuilderTests
```

No manual step — nothing is wired to UI yet. That happens in M11.6.

> If SwiftGen has not regenerated `L10n` yet, `make build_staging` triggers it.
> A "cannot find `L10n.carplayRadioTab`" error from SourceKit alone is a stale-index
> artifact — trust the build, per `AGENTS.md`.

---

## Out of scope

- Any `CPListItem` / `CPListSection` construction (M11.6)
- Artwork resolution — the builder only carries `logoAsset` / `faviconUrl` hints (M11.7)
- Resolving curated `streamUrl` (M11.6 tap handler)

---

## Commit

`b9ea839`

## Amended during M11.6

Curated rows originally used `CuratedStation.id` as `stationId`. That id is a
human slug (`"kexp"`); every other radio surface keys on the radio-browser UUID
(`RadioStation.uuid`, `RadioStationRegistry`, `RadioBrowserAPI.station(uuid:)`).
The slug made curated taps unresolvable and `isPlaying` permanently false.
Curated rows now carry `defaultSeedUUID`, locked in by
`testCuratedRowUsesSeedUUIDNotSlug`.
