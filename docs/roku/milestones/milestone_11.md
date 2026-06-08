# M10: UI Rebuild — Polish + Error States

**Status**: NOT STARTED

## Goal

Final pass: nav tab slide animation, loading states, all error/empty/offline cases handled gracefully, key hint bar updates per context, tracklist in top panel subtitle for KCRW/KEXP, and favorites add/remove flow from Browse.

## Done when

- Nav tab switch: ACCENT underline slides horizontally (0.2s `inOutCubic`); label weight changes
- Grid loading state: status text "Loading..." replaces grid while data fetches; grid appears when content is ready
- Empty section: "No episodes in Up Next" / "No favorites" message centered in grid area
- Network error: "Could not load. Check network." message in grid area; retry on OK
- 401 mid-session: auto-logout as before
- Audio error: progress bar hides, error message in top panel subtitle area, brief then clears
- Tracklist (KCRW/KEXP): updates top panel subtitle while that station plays — replaces static station meta
- Browse tab: Right arrow on focused station tile = add/remove favorite (confirm with small Dialog); no separate detail screen
- Key hint bar shows context-correct hints:
  - Grid (episodes): `"OK  Play   Right  Add to Favs   Up  Tabs"`  ← only for stations
  - Grid (episodes): `"OK  Play   Up  Tabs"`
  - Nav bar: `"Left/Right  Switch   Down  Grid   Back  Exit"`
  - Playing seekable: `"Play/Pause   FF/REW  Skip   Mark Done"`
  - Playing live: `"Play/Pause   Mark Done"`
- `m.isCurrentlyLive` gating preserved (no skip on live streams)
- All `print` debug statements removed or gated behind a `DEBUG` constant

## What to Build

### Nav tab slide animation
- `m.underline` Rectangle tracks active tab x-position
- Animation moves underline `translation.x` on tab switch

### Loading / empty / error states
- `m.gridStatus` Label, centered in grid area, visible when grid is empty
- Hidden once content loads; shown on error or empty result

### Tracklist subtitle wiring
- `onTracklistLoaded()` updates `m.topSubtitle.text` (reuses existing tracklist poll logic)
- On stream change: subtitle resets to station meta

### Browse favorite action
- `onTileFocused` in Browse mode: key hint shows `Right = Add Favorite`
- Right arrow on Browse tile: Dialog "Add [station name] to Favorites? [Yes] [No]"
- Yes → `addFavorite(stationId)`

### Debug cleanup
```brightscript
const DEBUG = false  ' flip to true during dev
if DEBUG then print "[MainScene] ..."
```

## Implementation Strategy

1. Nav underline animation.
2. Loading/empty/error label in grid area.
3. Browse favorite confirm dialog.
4. Key hint bar updates per mode.
5. Tracklist subtitle wiring.
6. Debug cleanup pass.

## User Checkpoint

Launch on slow network → "Loading..." visible then tiles appear. Switch tabs → underline slides. Pull network → error message. Play KCRW → subtitle updates with track. Browse → Right on station → confirm dialog → added to Favs. Key hints always match current context.

## Commit

TBD.
