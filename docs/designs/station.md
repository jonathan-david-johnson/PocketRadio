# Station Design

## Station Card (list view)

Static — no live data, no polling. Navigation only, same pattern as PC podcast grid.

```
┌─────────────────────────────────┐
│ [logo]  KCRW                   │
│         Santa Monica, CA       │
└─────────────────────────────────┘
```

| Field | Source |
|-------|--------|
| Logo | `curated_stations.json` `logoAsset` (curated) or radio-browser.info `favicon` (browse) |
| Name | `name` |
| Location | `city, state` from radio-browser.info, or hardcoded for curated |

Tap card → Station Detail.

---

## Station Detail Page

Live data loads on open. Same concept as PC podcast page.

```
┌─────────────────────────────────────┐
│                                     │
│           [station logo]            │
│           KCRW                      │
│           Santa Monica, CA          │
│                                     │
│   [ ▶ Play ]  [ ♥ Favorite ]       │
│   [ Donate to KCRW ↗ ]             │
│                                     │
├─────────────────────────────────────┤
│ NOW PLAYING                         │
│   Meshell Ndegeocello               │
│   Comfort Woman                     │
│                                     │
├─────────────────────────────────────┤
│ RECENT TRACKS                       │
│   Arooj Aftab — Mohabbat            │
│   Floating Points — LesAlpx        │
│   ...                               │
└─────────────────────────────────────┘
```

### Behaviors

- **Play/Pause** — starts/stops stream. Button state reflects current playback.
- **Favorite** — toggles; persisted to Supabase `radio_favorites`. Heart filled when favorited.
- **Donate** — opens `donate_url` in system browser.
- **Now Playing** — polls tracklist API on open, refreshes every 60s while detail is visible.
- **Recent Tracks** — same API response, shows previous entries below now playing.
- **NPR Hourly** — no tracklist API; "Now Playing" section hidden, replaced with "Live News" label.

### Tracklist API per station

| Station | Endpoint | Now Playing field | Filter |
|---------|----------|-------------------|--------|
| KCRW | `https://tracklist-api.kcrw.com/Music/all/1?page_size=10` | `results[0].title` + `artist` | none |
| KEXP | `https://api.kexp.org/v2/plays/?limit=10` | `results[0].song` + `artist` | `play_type == "trackplay"` |
| NPR Hourly | — | — | — |

### Data model

```swift
struct CuratedStation: Codable {
    let id: String
    let name: String
    let description: String
    let streamUrl: String
    let tracklistUrl: String?
    let donateUrl: String
    let homepageUrl: String
    let logoAsset: String
}

struct NowPlaying {
    let title: String
    let artist: String
}
```

---

## Browse Results Card (radio-browser.info)

Same visual as curated card. No tracklist, no donate URL. Favorite still available on detail.

```
┌─────────────────────────────────┐
│ [favicon]  WNYC                │
│            New York, US        │
└─────────────────────────────────┘
```

Browse detail page: Play, Favorite only. No tracklist, no donate link (no donate URL in radio-browser.info data).
