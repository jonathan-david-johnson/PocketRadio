# M7: UI Rebuild — New Scaffold

**Status**: NOT STARTED

## Goal

Replace the current flat-list MainScene with the new 3-section layout from `ui.md`: top panel, nav bar, tile grid. All existing auth/relay/playback/favorites logic stays untouched — only the visual layer is replaced. End of this milestone: new layout renders, nav bar responds to input, grid is empty placeholder.

## Done when

- Scene renders: `BG_DEEP` background + full-bleed backdrop Poster + scrim overlay
- Top panel: artwork Poster (200×200), title/subtitle/description Labels, progress bar (hidden), controls hint (hidden) — static placeholder data for now
- Nav bar: four tabs (Up Next / New Releases / Radio Favs / Browse), Left/Right moves between tabs, active tab shows `ACCENT` underline + bold label
- MarkupGrid renders (empty ContentNode); exists in scene tree at correct position
- Key hint bar at y=1026
- Up from grid → focus moves to nav bar; Down from nav bar → focus returns to grid; Back from nav bar → go back (logout / exit)
- Old `UpNextList`, `StationList`, `NowPlaying`, `DetailScreen` components **removed from MainScene.xml** (logic in MainScene.brs kept but rewired)
- Channel installs and no compile errors

## What to Build

### MainScene.xml
Full rewrite:
- `bg` Rectangle (BG_DEEP, 1920×1080)
- `backdrop` Poster (1920×380, opacity 0.2)
- `scrim` Rectangle (1920×380, BG_SCRIM)
- Top panel group: `artwork` Poster, `topTitle`/`topSubtitle`/`topDesc` Labels, `progressBg`/`progressFill` Rectangles (visible=false), `controlsHint` Label (visible=false)
- `navBg` Rectangle (1920×60, BG_ELEVATED, y=390)
- Four nav tab Labels with underline Rectangles
- `tileGrid` MarkupGrid (itemComponentName="TileItem", 6 cols, translation=[80,470])
- `keyHints` Label

### NavBar navigation (MainScene.brs)
- `m.navIndex` = 0..3 (current tab)
- Left/Right in nav mode: update `m.navIndex`, move underline, update tab label weights
- OK or Down on nav: jump focus to grid
- Up from grid: jump focus to nav bar

### TileItem stub
New component `components/TileItem.xml` + `TileItem.brs`:
- Rectangle bg (270×200, BG_SURFACE unfocused / BG_SELECTED focused)
- Poster (270×150)
- Title Label (SmallSystemFont, 1 line)
- Meta Label (SmallestSystemFont, TEXT_SECONDARY)
- 2px ACCENT border Rectangle (visible only when focused)

## Implementation Strategy

1. Write TileItem stub (renders placeholder, focus state works).
2. Rewrite MainScene.xml with new layout; keep all existing `<script>` tags.
3. Rewrite `init()` to find new nodes; stub out `showSection(index)` called on nav OK.
4. Wire Up/Down/Left/Right key handling for nav↔grid transitions.
5. Verify no compile errors; verify nav bar responds.

## User Checkpoint

Launch → see new dark layout. Nav bar at top shows 4 tabs. Left/Right moves tab highlight. Down enters empty grid. Up returns to nav bar.

## Commit

TBD.
