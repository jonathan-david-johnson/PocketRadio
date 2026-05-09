# Browse Tab Design

## Overview

Search 90k+ stations via radio-browser.info. No API key required.

## Layout

```
┌─────────────────────────────────────────┐
│ 🔍 Search stations...                   │  ← UISearchBar
├─────────────────────────────────────────┤
│                                         │
│  [Default content when empty]           │
│  • Top stations by vote                 │
│    (radio-browser.info /stations/topvote)│
│                                         │
├─────────────────────────────────────────┤
│ Search results (UITableView)            │
│                                         │
│  [favicon] WNYC                         │
│            New York, US                 │
│                                         │
│  [favicon] BBC Radio 4                  │
│            London, UK                   │
│                                         │
└─────────────────────────────────────────┘
```

## Behavior

- Empty state: show top-100 stations by vote (loaded on tab open, cached 1hr)
- Typing: debounce 300ms, call search API
- Min 2 chars to trigger search
- Results: stream directly on tap (no favorites auto-added)
- Favorite button on Station Detail adds to Supabase favorites

## radio-browser.info API

Base URL: `https://de1.api.radio-browser.info/json` (DNS round-robin, no auth)

| Action | Endpoint |
|--------|----------|
| Search | `GET /stations/search?name={query}&limit=40&hidebroken=true` |
| Top stations | `GET /stations/topvote?limit=100&hidebroken=true` |

Response fields used:
```json
{
  "stationuuid": "...",
  "name": "WNYC",
  "url_resolved": "http://...",   // use this, not url
  "favicon": "https://...",
  "country": "US",
  "state": "New York",
  "tags": "news,talk",
  "votes": 1234
}
```

Always use `url_resolved` (not `url`) — the API resolves redirects for us.
`hidebroken=true` filters stations with recent failures.

## RadioBrowserStation model

```swift
struct RadioBrowserStation: Codable {
    let stationuuid: String
    let name: String
    let url_resolved: String
    let favicon: String
    let country: String
    let state: String
    let tags: String
    let votes: Int

    func toRadioStation() -> RadioStation {
        let city = state.isEmpty ? country : "\(state), \(country)"
        return RadioStation(
            stationId: stationuuid,
            name: name,
            streamUrl: url_resolved,
            donateUrl: nil,       // radio-browser.info has no donate URLs
            tracklistUrl: nil,
            city: city
        )
    }
}
```

## Station cell (Browse)

Same `RadioStationCell` as curated list. Favicon loaded via `URLSession` + disk cache (no third-party image lib needed for MVP).

## No-results state

"No stations found for '\(query)'" centered label. No retry button — user can modify search.

## Error state

"Couldn't reach station directory. Check your connection." — shown if API call fails. Retry button.

## Rate limits

radio-browser.info: no documented rate limit. Mirror selection DNS (`de1`, `nl1`, `at1`) for redundancy if needed post-MVP.
