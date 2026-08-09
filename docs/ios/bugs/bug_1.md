# Bug 1 — No artwork for non-curated stations (detail screen + widget)

**Status:** Open

---

## Symptom A: Station detail screen shows generic radio glyph

Curated stations (KCRW, KEXP) show their real logo on
`StationDetailViewController`. Any other station (e.g. MangoRadio) shows the
generic `radio` SF Symbol placeholder — even though the same station renders
correct favicon artwork in the Favorites list row.

### Root cause

`StationDetailViewController.swift:160`:

```swift
if let asset = station.logoAsset, let image = UIImage(named: asset) {
    logoView.image = image
} else {
    logoView.image = UIImage(systemName: "radio")
    logoView.tintColor = AppTheme.colorForStyle(.primaryIcon02)
}
```

Only checks `station.logoAsset` — a bundled asset-catalog image name that
only curated stations have (`CuratedStationsLoader.enhancementsByUUID`).
Never falls back to fetching the favicon URL radio-browser returns for
non-curated stations, unlike whatever code path renders the Favorites list
cell.

---

## Symptom B: Home-screen widget favorites row shows generic radio glyph for non-curated favorites

Confirmed via screenshot: podcast art and a curated station (KCRW) render
fine in the widget's favorites row; two other favorite slots show the
generic radio glyph placeholder.

### Root cause

`podcasts/WidgetHelper.swift:295-317`, `publishPocketRadioFavorites()`:

```swift
let top = favorites.prefix(3).map { row -> PocketRadioFavoriteSnapshot in
    let enhancement = CuratedStationsLoader.enhancementsByUUID[row.station_id]
    return PocketRadioFavoriteSnapshot(
        stationId: row.station_id,
        name: enhancement?.name ?? row.station_id,
        logoAssetName: enhancement?.logoAsset,
        faviconUrl: nil
    )
}
```

`faviconUrl` is hardcoded `nil` unconditionally — never populated from
radio-browser metadata. `PocketRadioFavoriteSnapshot.faviconUrl` exists as a
field but nothing ever writes a real value into it. This has been true since
the field was introduced in the M8 widget commit (`56cbced`), so it isn't a
regression from any single recent change — the widget has never had favicon
art for non-curated favorites in this codebase's history.

### Not caused by

M11.3 (`RadioPlaybackStarter` extraction) — neither `StationDetailViewController`'s
logo rendering nor `WidgetHelper.swift` were touched by that milestone; this
bug pre-dates it and was noticed during M11.3 manual verification.

---

## Fix direction (not yet scoped into a milestone)

Both symptoms are already flagged as known gaps in `milestones/milestone_11.md`:

- M11.7 ("Artwork: non-curated baseline + favicon prefetch") is scoped to
  cover the non-curated artwork problem generally — likely the right place
  for Symptom A.
- M11.4 introduces `RadioFavoritesCache`, explicitly called out as "tempting"
  to also use for replacing the widget's top-3 App Group snapshot — that
  replacement would be the natural fix for Symptom B's `faviconUrl: nil`,
  but the umbrella doc says to resist folding it into M11.4 itself ("a
  separate milestone").

### Files likely involved in a fix

| File | Role |
|---|---|
| `podcasts/Radio/StationDetailViewController.swift` | Symptom A — logo rendering |
| `podcasts/WidgetHelper.swift` | Symptom B — `publishPocketRadioFavorites()` |
| `WidgetExtension/Data/WidgetFavoriteStation.swift` | Symptom B — widget-side consumption of the snapshot |
| Whatever populates the Favorites list row art (favicon fetch/cache) | Reference implementation for a shared fetch path |
