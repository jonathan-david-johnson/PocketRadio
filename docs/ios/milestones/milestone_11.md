# iOS M11 — CarPlay Radio (umbrella)

**Status**: ACTIVE
**Depends on**: M7.1 (mute/stop remote commands, complete), M7.2 (per-track artwork, complete), M8 (widget favorites snapshot, complete), Global M1 CarPlay entitlement (complete, uncommitted on `remoteplay`)

> This file is the **umbrella / shared reference** for M11. It contains no
> executable checklist of its own. Work happens in the numbered slices
> `milestone_11.1.md` … `milestone_11.7.md`, each independently shippable and
> each gated on at least one automated test.

---

## Goal

Make radio a first-class CarPlay citizen: a **Radio tab** listing curated stations
and the user's favorites, tappable to play, plus a Now Playing screen whose
controls make sense for a live stream instead of a podcast episode.

---

## Why now

The `com.apple.developer.carplay-audio` entitlement was restored and verified on
device (see `../../global/milestones/milestone_1.md`, "Pending on merge"). That
unlocks the CarPlay scene, but **no radio work has ever been done in
`podcasts/CarPlay/`** — all 7 files there are upstream and unmodified.
`grep -rl -i radio podcasts/CarPlay/` returns nothing.

Today, radio reaches CarPlay only indirectly:
- `MPNowPlayingInfoCenter` — station/track title + artwork (M7.2)
- `MPRemoteCommandCenter` — mute/stop instead of skip (M7.1)

There is no radio browse UI, and the CarPlay Now Playing screen shows
podcast-only buttons that are wrong (and in one case actively harmful) for radio.

---

## Decisions already made

These were settled in a design review. **Do not re-litigate them; implement them.**

| # | Decision | Rationale |
|---|---|---|
| D1 | Radio is a **5th top-level tab**, not a row under "More" | CarPlay caps `CPTabBarTemplate` at 5; current root has exactly 4. Radio is the fork's headline feature and drive-time is its best use case — 2 taps to play, not 3. |
| D2 | Tab shows **two sections: Favorites + Curated Stations** | `CuratedStationsLoader.load()` is synchronous bundle JSON, so the tab is never empty even when signed out / offline / cache-cold. |
| D3 | **No search / browse** in CarPlay | `CPSearchTemplate`'s keyboard is locked while the vehicle is moving — near-zero drive-time value for significant work. |
| D4 | **No dedupe** between sections | A favorited curated station appears in both. Sections are labelled; max 3 duplicates; suppression would make stations mysteriously vanish from "Stations". |
| D5 | Favorites are served from a **synchronous cache + async refresh** | `CarPlayListData.SectionDataSource` is `() -> [CPListSection]?` — synchronous. Favorites are async Supabase + async radio-browser metadata. Async-only means a cold start with no signal shows a permanently empty list; that is the *common* case in a car. |
| D6 | One resolve path: **`RadioFavoritesService`**, two callers | CarPlay's refresh needs the same Supabase-load + metadata-resolve that `FavoritesViewController` does. Duplicating it guarantees drift. |
| D7 | **`RadioPlaybackStarter`** extraction for all station playback | Three call sites already exist and two have already drifted. See "The register-before-load invariant" below. |
| D8 | Radio Now Playing buttons: **mute + favorite**; drop mark-as-played, speed, star | Mark-as-played on a live stream is a live bug (see M11.1). Speed on a stream is meaningless. |
| D9 | **No lyric lines in CarPlay** | `setRadioAlbumTitle` currently overwrites the album field with the live lyric line, but only while `StationDetailViewController` is alive — so behavior depends on what the phone happened to be showing at plug-in. Nondeterministic; suppress it. |
| D10 | Signed-out / empty / offline → **omit the Favorites section silently** | A driver cannot act on "sign in on your phone", and an untappable info row in a CarPlay list reads as a broken button. |
| D11 | Refresh favorites on **every `didAppear`**, no throttle | One Supabase query on a tab switch. Throttling adds state and a staleness bug class for no measurable win. |
| D12 | Icons are **SF Symbols**, not new imagesets | `podcasts/Carplay.xcassets` is podcast-only. CarPlay accepts any `UIImage`; the existing `car_*` assets predate reliable SF Symbol support. Avoids authoring 3 scales per icon. |
| D13 | Pure-struct seam: builders return **plain Swift structs**, never `CPListSection` | `CPInterfaceController` can't be instantiated in a test, and `CPListItem` exposes almost nothing readable (`handler` is write-only). Tests assert on structs and never `import CarPlay`. |

---

## Architecture reference

### Existing pieces you will use (do not reinvent)

| Need | Use | Location |
|---|---|---|
| Is the current item live radio? | `PlaybackManager.shared.isLiveStream(_:)` | `podcasts/PlaybackManager.swift:366` |
| Should skip be swapped for mute? (live **and** unseekable) | `PlaybackManager.shared.shouldUseMuteControls(for:)` | `podcasts/PlaybackManager.swift:380` |
| Get the `RadioStation` behind the current item | `PlaybackManager.shared.liveStation(for:)` | `podcasts/PlaybackManager.swift:390` |
| Toggle / read mute | `PlaybackManager.shared.toggleMute()`, `.isMuted` | `podcasts/PlaybackManager.swift:502,508` |
| Stop a stream (tears down connection) | `PlaybackManager.shared.stopRadioPlayback()` | `podcasts/PlaybackManager.swift:516` |
| Curated station metadata | `CuratedStationsLoader.load()`, `.enhancementsByUUID` | `podcasts/Radio/CuratedStation.swift` |
| Favorites CRUD (async, Supabase) | `RadioFavoritesManager.shared` | `podcasts/Radio/RadioFavoritesManager.swift` |
| Station metadata by UUID (async) | `RadioBrowserAPI.station(uuid:)` | `podcasts/Radio/RadioBrowserAPI.swift` |
| In-memory station registry | `RadioStationRegistry.shared` | `podcasts/Radio/RadioStationRegistry.swift` |
| CarPlay list template + reload plumbing | `CarPlayListData` | `podcasts/CarPlay/CarPlayListData.swift` |
| CarPlay image sizing/caching (sync only) | `CarPlayImageHelper` | `podcasts/CarPlay/CarPlayImageHelper.swift` |

### The register-before-load invariant

`RadioStationRegistry`'s own doc comment states the trap: `PlaybackQueue` reloads
episodes from SQLite by UUID after queuing. `RadioStation` is **not in SQLite**,
so without registering first, the queue holds a dead stub.

```swift
RadioStationRegistry.shared.register(station)          // MUST come first
PlaybackManager.shared.load(episode: station, autoPlay: true, overrideUpNext: false)
```

This is also why `PlaybackManager.liveStation(for:)` exists — after `load()`,
`currentEpisode() as? RadioStation` **fails**, because the item round-tripped
through SQLite and came back as an `Episode` shim with the same uuid. Never write
`episode as? RadioStation`; always go through `liveStation(for:)`.

### Existing caches, and why neither is sufficient

| Cache | Holds | Why not enough |
|---|---|---|
| App Group widget snapshot (`SharedConstants.GroupUserDefaults.pocketRadioFavorites`) | top-3 favorites | Capped at 3; **no `streamUrl`**; name falls back to raw `stationId` for non-curated stations |
| `FavoritesViewController.browseCache` (UserDefaults `pocketradio.favoritesBrowseCache`) | `[stationId: RadioBrowserStation]` | `private static`; holds **no ordered id list**, so it can't render a list on its own |

M11.4 replaces both readers' needs with `RadioFavoritesCache`.

### Process note

The CarPlay scene runs **in the main app process**. `UserDefaults.standard`,
`RadioStationRegistry.shared`, and `PlaybackManager.shared` are all directly
reachable from `CarPlaySceneDelegate`. **No App Group is needed** for anything in
M11 — that's a widget concern only.

---

## Slice order

Ordered so the live bug ships first and each slice only depends on earlier ones.

| Slice | Title | Depends on | Automated test |
|---|---|---|---|
| **M11.1** | Radio-aware CarPlay Now Playing buttons (**bug fix**) | — | `CarPlayNowPlayingButtonSetTests` |
| **M11.2** | CarPlay connection flag + lyric suppression | — | `CarPlayConnectionStateTests` |
| **M11.3** | `RadioPlaybackStarter` extraction (pure refactor) | — | `RadioPlaybackStarterTests` |
| **M11.4** | `RadioFavoritesCache` + `RadioFavoritesService` | — | `RadioFavoritesCacheTests` |
| **M11.5** | `RadioCarPlayRowBuilder` (pure structs) | 11.4 | `RadioCarPlayRowBuilderTests` |
| **M11.6** | Radio tab wiring (the visible feature) | 11.3, 11.4, 11.5 | `RadioCarPlayAdapterTests` + manual |
| **M11.7** | Artwork: non-curated baseline + favicon prefetch | 11.4, 11.6 | `RadioArtworkSourceTests` |

M11.1–M11.4 are mutually independent and can be done in any order or in parallel.

---

## Testing CarPlay manually

Simulator: run the app on the sim, then **Simulator menu → I/O → External Displays
→ CarPlay**. A CarPlay window opens alongside. This exercises `CarPlaySceneDelegate`
end to end without hardware.

```bash
make run_sim   # then enable the CarPlay external display as above
```

Physical head unit requires `make run_device` and a wired, unlocked iPhone — see
`../../global/milestones/milestone_1.md` for the signing and transport gotchas.

---

## Out of scope for M11

- CarPlay search / radio-browser browse (D3)
- Station detail screen in CarPlay (tracklist, lyrics, donate link)
- Reordering favorites from CarPlay
- Cross-device favorites ordering sync
- Replacing the widget's top-3 App Group snapshot with `RadioFavoritesCache`
  (tempting once 11.4 lands — resist; it's a separate milestone)
- watchOS / Sonos parity

---

## Commit

TBD.
