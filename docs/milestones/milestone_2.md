# M2: Streams Tab + Station List

**Status**: NOT STARTED

## Goal

Streams tab appears in tab bar. Curated stations listed. Tapping plays (via M1).

## Done when

- Streams tab visible in PC tab bar
- KCRW, KEXP, NPR Hourly listed as station cards
- Tap card → Station Detail with Play button
- Play → audio starts (M1 player)
- Donate button → opens donate URL in Safari

## What to build

- `StreamsHostViewController` — segmented control host (Stations / Favorites / Browse tabs)
- `StationsViewController` — curated list
- `RadioStationCell` — logo + name + location cell
- `StationDetailViewController` — play, favorite stub, donate button
- `CuratedStationsLoader` — parses `curated_stations.json` from bundle

## Notes

- `StreamsHostViewController` M1 stub already exists — replace with segmented control version
- Station cards are static (no live polling in list) — live data only on detail page
- `pcTabs` change + `.streams` Tab enum already done in M1
- See `docs/designs/station.md` for card and detail layouts
- See `docs/designs/navigation_impl.md` for tab structure
