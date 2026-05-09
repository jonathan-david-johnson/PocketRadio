# Favorites Tab Design

## Overview

User-saved stations, backed by Supabase `radio_favorites` table. Persists across devices via `ServerSettings.userId`.

## Layout

```
┌─────────────────────────────────────────┐
│                                         │
│  [logo]  KCRW                           │
│          Santa Monica, CA               │
│                                         │
│  [logo]  WNYC                           │
│          New York, US                   │
│                                         │
└─────────────────────────────────────────┘
```

Same `RadioStationCell` as Stations tab.

## Empty state

```
♥  No favorites yet.
   Tap ♥ on any station to save it here.
```

## Behavior

- Loaded from Supabase on tab open (or on app launch if user is logged in)
- Tap cell → Station Detail (same as curated stations)
- Swipe-to-delete → removes from Supabase `radio_favorites`
- No reorder (sorted by `added_at DESC`, newest first)
- Offline: show cached list, disable swipe-delete with "No connection" toast

## Favoriting flow (from Station Detail)

Heart button on Station Detail:
- Not favorited: outline heart → tap → filled heart, INSERT to Supabase
- Favorited: filled heart → tap → outline heart, DELETE from Supabase

`RadioFavoritesManager` handles both curated and radio-browser.info stations.

For curated stations: `station_id` = `kcrw` / `kexp` / `npr_hourly`
For browse stations: `station_id` = `stationuuid` from radio-browser.info

## RadioFavoritesManager

File: `podcasts/Radio/RadioFavoritesManager.swift`

```swift
class RadioFavoritesManager {
    static let shared = RadioFavoritesManager()

    func loadFavorites() async throws -> [FavoriteStation]
    func addFavorite(stationId: String) async throws
    func removeFavorite(stationId: String) async throws
    func isFavorite(stationId: String) async throws -> Bool
}
```

`FavoriteStation` is a struct with `stationId` + `addedAt`. Full station data (name, URL, favicon) fetched separately on demand:
- Curated stations: looked up in `curated_stations.json`
- Browse stations: fetched from `radio-browser.info/json/stations/byuuid/{uuid}`

## Not-logged-in state

If `ServerSettings.userId == nil`, favorites tab shows:
```
Sign in to Pocket Casts to save favorites across devices.
```
No local-only fallback for MVP.
