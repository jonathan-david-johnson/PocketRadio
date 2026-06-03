# M6.4: Browse/Search + Favorites Tabs

**Status**: PLANNED  
**Depends on**: M6.1 (layout foundation), M6.2 + M6.3 (avoids conflicts in bottom section)

## Goal

The ⋮ (three-dot) button opens a Favorites/Browse tabbed view in the bottom section.
Favorites tab shows the user's saved stations with management. Browse tab offers
full radio-browser.info search with a search bar and top stations.

## Done when

### Three-dot button
- Clicking ⋮ opens Favorites/Browse tabs in bottom section
- Clicking ⋮ again or selecting a source pill dismisses the tabs and restores bottom section
- Initial tab is Favorites (first tab active)

### Favorites tab
- Shows list of favorite stations from Supabase
- Each row: station logo (AsyncImage), station name (bold), location (gray), drag handle
- First row has a remove (✕) button
- Tapping a station plays it and dismisses the tabs
- Reorder supported via drag handles (or skip for MVP — just list)

### Browse tab
- Search bar with magnifying glass icon, placeholder "Search stations..."
- On empty search: shows top voted stations from radio-browser.info (`/stations/topvote?limit=50`)
- On search: debounced (300ms) call to `/stations/search?name={query}&limit=40&order=votes`
- Each row: station logo (AsyncImage), station name (bold), location (gray), right chevron (>)
- Tapping a station adds it to favorites in Supabase and plays it
- Loading state shows ProgressView while fetching

### Theming
- Dark background (`.black` or `.ultraThinMaterial` in dark mode)
- Text colors: primary = white, secondary = gray
- Follows macOS system dark/light appearance automatically via SwiftUI

## Layout

### Favorites tab
```
┌──────────────────────────────────┐
│ 📻 Podcast │ KCRW │ ... │ ... │⋮│   ← top row
├──────────────────────────────────┤
│        Favorites / Browse        │   ← tab bar
├──────────────────────────────────┤
│ [KCRW] KCRW Eclectic 24       ≡ │
│        California, The Unite...  │
│ [NPR]  NPR Hourly Newscast    ≡ │
│        The United States Of...   │
│ [KEXP] KEXP                   ≡ │
│        Seattle Washington...     │
└──────────────────────────────────┘
```

### Browse tab
```
┌──────────────────────────────────┐
│        Favorites / Browse        │
├──────────────────────────────────┤
│ 🔍 Search stations...            │
├──────────────────────────────────┤
│ [🥭] MANGORADIO               > │
│      Rheinland-Pfalz, Germany    │
│ [🪩] Dance Wave!              > │
│      Hungary                     │
│ [📺] REYFM - #original        > │
│                                  │
└──────────────────────────────────┘
```

## Implementation

### Tab Switching
```swift
enum BrowseTab: String, CaseIterable {
    case favorites = "Favorites"
    case browse = "Browse"
}
```
- Picker or custom segmented control at top of bottom section
- Active tab highlighted in white, inactive in gray
- Switching tabs preserves scroll position

### Browse API
Same endpoints as iOS `RadioBrowserAPI`:
```
GET /stations/topvote?limit=50&hidebroken=true
GET /stations/search?name={query}&limit=40&hidebroken=true&order=votes&reverse=true
```
- User-Agent: `PocketRadio/1.0`
- Response: `[RadioBrowserStation]` — decoded with JSONDecoder

### Station Model
```swift
struct RadioBrowserStation: Decodable {
    let stationuuid: String
    let name: String
    let url_resolved: String
    let favicon: String?
    let country: String?
    let state: String?
}
```

### Location Formatting
- If `state` and `country` both present: "State, Country"
- If only `country`: "Country"
- Truncated with `...` if too long

### Favorites Management
- Remove: DELETE to Supabase `/rest/v1/radio_favorites?station_id=eq.{id}`
  with `x-user-uuid` header
- Add: POST to Supabase with `{user_uuid, station_id}`
- After add/remove, refresh favorites list and stream pills

## Files

### NEW
- `View Models/BrowseViewModel.swift` — search state, tab state, favorites CRUD
- `Views/BrowseTabsView.swift` — Favorites/Browse tabbed content
- `Views/StationRow.swift` — reusable station row (used in Favorites + Browse)

### EDIT
- `ContentView.swift` — ⋮ button toggles bottom section between M6.2/M6.3 content and BrowseTabsView
- `PlayerViewModel.swift` — favorites CRUD methods
- `Services/APIService.swift` — add browse search + favorites add/remove endpoints

## Manual smoke
1. Click ⋮ → Favorites tab opens showing saved stations
2. Tap a favorite → plays it, tabs dismiss
3. Click ⋮ → switch to Browse tab → top stations list loads
4. Type in search bar → results filter after 300ms debounce
5. Tap a browse result → station added to favorites, starts playing
6. In Favorites tab, tap ✕ on first row → station removed, pills update
7. Switch to light mode (System Settings → Appearance → Light) → UI adapts
