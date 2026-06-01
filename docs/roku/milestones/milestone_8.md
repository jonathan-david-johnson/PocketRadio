# M8: UI Rebuild — Tile Data + Top Panel Metadata

**Status**: DONE

All features were already implemented in prior sessions. M8 pre-work bugs (see `m8_bugs.md`) resolved during final polish pass.

## Goal

Wire real data into the tile grid for all four sections. Top panel shows metadata for the focused tile (title, subtitle, description). No backdrop image loading yet — text only. Playback still works (OK on tile plays).

## Done when

- **Up Next** tab: episodes render as tiles — podcast artwork, episode title, duration/time-left
- **New Releases** tab: same tile layout as Up Next
- **Radio Favs** tab: station tiles — favicon logo, station name, no duration line
- **Browse** tab: `topvote` station tiles (same as Radio Favs tile style)
- Focusing any tile updates top panel: title, subtitle (podcast name or station meta), description (show notes excerpt or country/format/bitrate)
- Top panel metadata comes from ContentNode `description` JSON — no extra network calls on focus
- `jumpToItem = 0` + `setFocus` after content load (fixes first-item selection bug from M4)
- OK on tile plays (reuses existing `playEpisode` / `onStationSelected` logic)
- Add/remove favorite: Right arrow on station tile shows a confirm dialog; OK confirms
- `alwaysNotify="true"` on TileItem `itemSelected` field

## What to Build

### TileItem.xml / TileItem.brs (complete)
- `itemContent` field (node, onChange="onContentSet")
- `focusPercent` field (float, onChange="onFocus")
- Poster loads `itemContent.HDPosterUrl`
- Title from `itemContent.title`
- Meta line: parse `itemContent.description` JSON → duration or station codec/country
- Focus: flip bg to BG_SELECTED, show ACCENT border

### Section loading (MainScene.brs)
`showSection(index)`:
- 0 = Up Next → relay `upNext` → populate grid with episode ContentNodes
- 1 = New Releases → relay `newReleases` → populate grid
- 2 = Radio Favs → Supabase + radio-browser resolve → populate grid
- 3 = Browse → radio-browser `topvote` → populate grid

`onTileFocused()` — observer on `tileGrid.itemFocused`:
- Get focused ContentNode
- Parse description JSON
- Set `topTitle.text`, `topSubtitle.text`, `topDesc.text`

### ContentNode shape (consistent across sections)
```
title         = display title
HDPosterUrl   = artwork/logo URL
description   = FormatJSON({
    uuid, podcast, podcastName, playedUpTo, duration,   ← episodes
    stationuuid, codec, bitrate, display,               ← stations
    isStation: true/false
})
```

## Implementation Strategy

1. Complete TileItem component (artwork, title, meta, focus states).
2. Implement `showSection(index)` + data loaders (reuse existing relay/HTTP subs).
3. Wire `tileGrid.itemFocused` observer → `onTileFocused()` → top panel text update.
4. Wire `tileGrid.itemSelected` → play or station-select (reuse existing play logic).
5. Wire nav tab OK → `showSection`.

## User Checkpoint

Launch → Up Next tiles appear. Navigate tiles → top panel title/subtitle update. OK on episode → plays. Switch to Radio Favs tab → station tiles appear. OK on station → plays.

## Commit

TBD.
