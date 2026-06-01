# M8 Pre-Work: Known Bugs from M7 — RESOLVED

These bugs were identified during M7 verification and fixed before/during M8. All resolved 2026-06-01.

---

## Bug 1: Cannot navigate from tile grid to nav bar

**Symptom:** Pressing Up or Back from the tile grid does not return focus to the nav bar. User is stuck in the grid and cannot switch tabs.

**Expected:** Back (or Up) from grid → focus returns to nav bar → Left/Right switches tabs → Down/OK enters grid.

**Root cause:** `m.tileGrid.setFocus(true)` is called in `enterGrid()`. Once MarkupGrid has OS focus, it appears to consume ALL key events including Back, preventing MainScene's `onKeyEvent` from firing. The print statement `"[MainScene] grid back/up -> enterNav"` never appears in the log.

**Relevant code:** `MainScene.brs` — `enterGrid()`, `onKeyEvent()` grid branch.

**Fix implemented (Option A):** Removed `m.tileGrid.setFocus(true)`. `m.top.setFocus(true)` always. MainScene handles all D-pad grid navigation manually via `m.gridIdx` + `focusGridItem(idx)`. `focusPercent` on TileItem continues to drive visual focus (no extra `isFocused` field needed).

---

## Bug 2: Only one row of tiles visible

**Symptom:** The tile grid only shows one row of tiles. The screen has space for 2 rows but the second row is clipped or not rendered.

**Expected:** 2 full rows of tiles visible simultaneously (each row 200px tall + 20px gap = 220px; two rows = 440px; grid starts at y=470, so two rows end at y=910, well within 1080px).

**Root cause (theories):**
- The MarkupGrid may have a default `maxRows` or height constraint
- The grid might need an explicit `numRows` or `height` field to render more than one row
- The `translation=[80, 470]` + 2 rows ending at y=910 should fit above keyHints at y=1026, so clipping is unlikely — more likely the grid just isn't rendering row 2

**Fix:** Added `numRows="2"` to `MarkupGrid` in `MainScene.xml`. Two rows (200px + 20px gap each = 440px) now render simultaneously within the available grid area.

---

## Bug 3: Backdrop not visible behind top panel

**Symptom:** The top panel shows a dark solid background. The artwork of the focused tile is not faintly visible as a backdrop behind the top panel.

**Expected:** The focused tile's artwork appears at ~20% opacity as a full-bleed background behind the top panel area (y=0 to y=390), giving depth to the UI (similar to Moonfin's backdrop pattern).

**Root cause:** `m.backdrop.uri` is being set in `updateTopPanelMeta()` but the Poster may not be loading because:
- The `backdrop` Poster node in `MainScene.xml` has `opacity="0.2"` which may be rendering before `uri` is set (shows nothing, not a dark placeholder)
- The `scrim` Rectangle (`color="0x000000CC"` = 80% black) is rendering on top and may be too opaque, fully obscuring a 20% opacity backdrop

**Fix:**
1. Added `print "[backdrop] uri="; artUrl` debug statement in `updateTopPanelMeta`
2. Reduced scrim opacity: `0x000000CC` → `0x000000AA` (67% black)
3. Increased backdrop opacity: `0.2` → `0.35`
4. Confirmed `backdrop` Poster comes before `scrim` Rectangle in XML child order (unchanged)

---

## Bug 4: Top panel has too much dead space

**Symptom:** Large gap between the metadata text and the nav bar. The top panel area feels sparse.

**Layout analysis:**
- Artwork: y=50, h=200 → bottom at y=250
- Title: y=50, h=60 → y=110
- Subtitle: y=120, h=36 → y=156
- Desc: y=162, h=72 → y=234
- Progress bg: y=278 (hidden by default)
- Controls hint: y=340 (hidden by default)
- Nav bar: y=390

When not playing (progress/controls hidden), content ends at y=234 but nav bar doesn't start until y=390. That's 156px of empty dark space.

**Fix:** Nav bar moved to `y=370` (compromise between reducing dead space and preserving room for playback controls). Grid at `y=450`. Playback controls at `y=250/264/288`. Gives the top panel ~370px of space (~25% more than the previous cramped 300px layout) while keeping enough vertical room for the Now Playing progress bar and controls hint.

---

## Summary Table

| # | Bug | Priority | Status | Fix |
|---|-----|----------|--------|-----|
| 1 | Can't navigate to nav bar | **P0** | ✅ Resolved | Manual `m.gridIdx` navigation, no `setFocus` on MarkupGrid |
| 2 | Only one tile row visible | P1 | ✅ Resolved | Added `numRows="2"` to MarkupGrid |
| 3 | Backdrop not visible | P2 | ✅ Resolved | Scrim `0x000000AA`, backdrop `opacity="0.35"` |
| 4 | Top panel dead space | P2 | ✅ Resolved | Nav bar at `y=370`, grid at `y=450`, controls fit above |
