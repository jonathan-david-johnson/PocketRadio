# M2: Streams Tab + Station List

**Status**: COMPLETE 2026-05-09

## Goal

Streams tab appears in tab bar. Curated stations listed. Tapping plays (via M1).

## Done when

- Streams tab visible in PC tab bar ✓
- KCRW, KEXP, NPR Hourly listed as station cards ✓
- Tap card → Station Detail with Play button ✓
- Play → audio starts (M1 player) ✓
- Donate button → opens donate URL in Safari ✓

## What was built

- `StreamsHostViewController` — segmented control host (Stations / Favorites / Browse tabs); Favorites and Browse are placeholders for M3/M4
- `StationsViewController` — curated list backed by `curated_stations.json`
- `RadioStationCell` — logo + name + city cell with disclosure indicator
- `StationDetailViewController` — play/pause (reflects live playback state via `Constants.Notifications`), favorite stub (M3), donate button, tracklist polling for KCRW/KEXP every 60s
- `CuratedStation` — Codable model; `CuratedStationsLoader` reads from bundle
- `curated_stations.json` — bundle resource with KCRW, KEXP, NPR Hourly

## Commits

- `249c986` — M2: Streams tab with curated station list and detail page

## Lessons learned

- **`SimpleNotificationsViewController`**: PC's base class for observation. Inherit from it (instead of `UIViewController`) to get `addCustomObserver` / `removeAllCustomObservers`. Pattern used in `StationDetailViewController`.
- **`Constants.Notifications`**: All PC playback notifications live here (`playbackStarted`, `playbackPaused`, `playbackEnded`). Use these, not custom `Notification.Name` extensions.
- **`UIButton.Configuration` lazy var capture**: `donateButton` config captures `station.displayableTitle()` in the lazy closure; this is fine since station is immutable.
- **No `author` on `BaseEpisode`**: Use `station.city` directly. `BaseEpisode` has no author/city concept.
- **Tracklist polling**: Timer started in `viewWillAppear`, invalidated in `viewWillDisappear`. First poll fires immediately in `viewDidLoad` to avoid blank state on open.
