# M4: Browse Tab

**Status**: COMPLETE 2026-05-10

## Goal

Search 90k+ stations via radio-browser.info. Play any result.

## Done when

- Browse tab shows top-100 stations by default ✓
- Search returns results within 500ms (debounced 300ms) ✓
- Tap result → Station Detail (play, favorite) ✓
- Favorite a browse station → appears in Favorites tab ✓

## What was built

- `RadioBrowserAPI.swift` — `topStations()`, `search(query:)`, `station(uuid:)`; always `hidebroken=true`, uses `url_resolved`
- `BrowseViewController.swift` — `UISearchBar` with 300ms debounce (min 2 chars), top-100 default, error state with Retry, no-results state
- `FavoritesViewController.swift` — updated to resolve browse favorites via `RadioBrowserAPI.station(uuid:)` in a `TaskGroup`; curated stations still resolved from bundle
- `StreamsHostViewController.swift` — Browse segment wired to real `BrowseViewController`

## Commits

- `f7e4f43` — M4: Browse tab — radio-browser.info search + top stations

## Lessons learned

- **TaskGroup for parallel lookups**: fetching radio-browser.info metadata for multiple unknown favorites runs concurrently via `withTaskGroup`, then a second `reloadData()` updates cells once all lookups complete. Two-phase render: curated shows instantly, browse fills in after.
- **Debounce via Task.sleep**: `searchTask?.cancel()` + `Task.sleep(nanoseconds: 300_000_000)` is idiomatic Swift concurrency debounce — no Timer needed.
- **`url_resolved` not `url`**: radio-browser.info `url` field may be a redirect; `url_resolved` is the final stream URL. Always use `url_resolved`.
