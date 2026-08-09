# iOS M11.4 — `RadioFavoritesCache` + `RadioFavoritesService`

**Status**: COMPLETED (`a2b5c75`)
**Depends on**: nothing (M11 umbrella: `milestone_11.md`)
**Parallel-safe with**: M11.1, M11.2, M11.3
**Required by**: M11.5, M11.6, M11.7

---

## Goal

A **synchronous, cold-start-safe** snapshot of the user's favorites — id, display
name, stream URL, artwork hints, in display order — plus a single async resolve
path that keeps it fresh (D5, D6).

---

## Why

`CarPlayListData.SectionDataSource` is `() -> [CPListSection]?` — **synchronous**.
Favorites are async Supabase (`RadioFavoritesManager.loadFavorites()`) plus async
radio-browser metadata (`RadioBrowserAPI.station(uuid:)`). Without a sync cache,
a cold start in a car with no signal shows a permanently empty list — and that is
the *common* case, not the edge case.

Neither existing cache is sufficient:

| Cache | Holds | Why not enough |
|---|---|---|
| App Group widget snapshot (`SharedConstants.GroupUserDefaults.pocketRadioFavorites`) | top-3 favorites | Capped at 3; **no `streamUrl`**; name falls back to raw `stationId` for non-curated |
| `FavoritesViewController.browseCache` (UserDefaults `pocketradio.favoritesBrowseCache`) | `[stationId: RadioBrowserStation]` | `private static`; **no ordered id list**, so it can't render a list alone |

Carrying `streamUrl` in the cache is what lets a cold car start play a favorite
with **zero network round-trips**.

---

## Done when

### 1. `RadioFavoritesCache`

New file `podcasts/Radio/RadioFavoritesCache.swift`.

```swift
/// One favorite, fully resolved for display and playback without further I/O.
struct CachedFavoriteStation: Codable, Equatable {
    let stationId: String
    let name: String
    let streamUrl: String
    let city: String?          // "CA, United States" — CarPlay row detailText
    let logoAsset: String?     // curated bundle asset name, nil for radio-browser
    let faviconUrl: String?    // remote favicon, nil when absent/empty
    let bitrate: Int?
}

/// Persisted, synchronously-readable favorites snapshot. Written by
/// `RadioFavoritesService`; read by CarPlay and anything else needing an
/// instant list. Stored in `UserDefaults.standard` — the CarPlay scene runs in
/// the main app process, so no App Group is involved.
final class RadioFavoritesCache {
    static let shared = RadioFavoritesCache()
    init(defaults: UserDefaults = .standard)

    /// Never throws, never blocks. Returns `[]` on cold start or corrupt data.
    func snapshot() -> [CachedFavoriteStation]
    func write(_ rows: [CachedFavoriteStation])
    func clear()
}
```

- [x] Single UserDefaults key: `"pocketradio.favoritesCache.v1"`. Version suffix so a
      future shape change is a cache miss, not a decode crash.
- [x] `snapshot()` returns `[]` — never throws — on missing key, corrupt data, or
      decode failure. A car screen must not depend on well-formed cached JSON.
- [x] Array order **is** display order. Do not sort inside the cache.
- [x] `init(defaults:)` injectable for tests.

### 2. `RadioFavoritesService`

New file `podcasts/Radio/RadioFavoritesService.swift`.

```swift
/// The one place favorites are resolved from Supabase + radio-browser into
/// display-ready rows. Writes `RadioFavoritesCache` and posts
/// `.radioFavoritesChanged` on success.
final class RadioFavoritesService {
    static let shared = RadioFavoritesService()

    /// Loads favorite ids from Supabase, resolves metadata (cache-first,
    /// network for misses), persists, notifies. Returns [] when signed out or
    /// on failure — never throws.
    @discardableResult
    func resolvedFavorites() async -> [CachedFavoriteStation]
}
```

- [x] Ids + order from `RadioFavoritesManager.shared.loadFavorites()` (which already
      applies the local order key).
- [x] Name resolution mirrors `FavoriteRow.displayName` in
      `FavoritesViewController.swift:8` exactly:
      `CuratedStationsLoader.enhancementsByUUID[id]?.name ?? browse?.name ?? id`.
- [x] `city` mirrors `FavoriteRow.displayCity` (state/country joining, empty-string
      handling). Do not invent a new format.
- [x] `streamUrl` from `RadioBrowserStation.url_resolved`.
- [x] Metadata lookups are **cache-first**: reuse the existing persisted
      `pocketradio.favoritesBrowseCache` entries before hitting
      `RadioBrowserAPI.station(uuid:)`.
- [x] A station whose metadata cannot be resolved (network down, no cached entry)
      is still emitted, using curated data when available. Drop it only if there is
      no usable `streamUrl` **and** no curated fallback — an unplayable row in a car
      is worse than a missing one.
- [x] Signed out (`ServerSettings.userId == nil`) → return `[]`, **do not clear the
      cache**. A sign-out blip must not wipe a good snapshot.
- [x] Supabase failure → log to `FileLog`, return the existing `snapshot()`, leave
      the cache intact.
- [x] On success, write the cache and post `.radioFavoritesChanged`.

**Reentrancy:** M11.6 refreshes on every `didAppear` (D11). Guard with a single
in-flight `Task` so rapid tab switching cannot stack concurrent Supabase queries —
a second caller awaits the first rather than starting its own.

### 3. `FavoritesViewController` migrated

- [x] Its load path calls `RadioFavoritesService.resolvedFavorites()` instead of
      hand-rolling load + resolve.
- [x] Its `private static browseCache` stays as the radio-browser metadata cache
      (the service reads it), but the VC stops being the only writer of display state.
- [x] **No visible behavior change** — same rows, same order, same reorder handles,
      same cold-start-from-cache feel.

### 4. Tests

New file `PocketCastsTests/Tests/Radio/RadioFavoritesCacheTests.swift`.

Use `UserDefaults(suiteName: "RadioFavoritesCacheTests")` and
`removePersistentDomain(forName:)` in `tearDown`. Never touch `.standard`.

- [x] `testColdStartReturnsEmpty`
- [x] `testRoundTripPreservesAllFields`
- [x] `testOrderIsPreserved` — write A,B,C → read back A,B,C (not sorted, not reversed)
- [x] `testCorruptDataReturnsEmpty` — write `Data("not json".utf8)` under the key →
      `snapshot()` returns `[]` and does not throw
- [x] `testWrongShapeReturnsEmpty` — write valid JSON of the wrong type → `[]`
- [x] `testClearEmptiesSnapshot`
- [x] `testOptionalFieldsSurviveNil` — `city`, `logoAsset`, `faviconUrl`, `bitrate`
      all nil round-trip cleanly

`RadioFavoritesService` is not unit-tested here — it needs Supabase and the network.
Its correctness is covered by M11.5/M11.6 tests operating on cache contents, plus
manual verification below.

---

## Files

| File | Change |
|---|---|
| `podcasts/Radio/RadioFavoritesCache.swift` | **new** — needs `project.pbxproj` registration |
| `podcasts/Radio/RadioFavoritesService.swift` | **new** — needs `project.pbxproj` registration |
| `podcasts/Radio/FavoritesViewController.swift` | migrate load path to the service |
| `PocketCastsTests/Tests/Radio/RadioFavoritesCacheTests.swift` | **new** — auto-discovered |

---

## Verification

```bash
cd pocket-radio-ios
make format
make build_staging
make test_staging ONLY_TESTING=PocketCastsTests/RadioFavoritesCacheTests
```

Manual:

1. Sign in, open Favorites tab → list renders as before
2. Add a favorite from a station detail page → appears in the list
3. Reorder favorites → order persists across app relaunch
4. Force-quit, enable Airplane Mode, relaunch, open Favorites → **cached rows
   still render** (names and artwork, not raw UUIDs)
5. Sign out → Favorites shows the signed-out state; sign back in → list returns

---

## Out of scope

- Replacing the widget's top-3 App Group snapshot with this cache — tempting, but a
  separate milestone
- Cross-device favorites ordering sync
- Removing `FavoritesViewController.browseCache`

---

## Commit

TBD.
