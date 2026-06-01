# M8 Pre-Work: Known Bugs from M7

These bugs were identified during M7 verification and must be fixed before or during M8.

---

## Bug 1: Cannot navigate from tile grid to nav bar

**Symptom:** Pressing Up or Back from the tile grid does not return focus to the nav bar. User is stuck in the grid and cannot switch tabs.

**Expected:** Back (or Up) from grid → focus returns to nav bar → Left/Right switches tabs → Down/OK enters grid.

**Root cause:** `m.tileGrid.setFocus(true)` is called in `enterGrid()`. Once MarkupGrid has OS focus, it appears to consume ALL key events including Back, preventing MainScene's `onKeyEvent` from firing. The print statement `"[MainScene] grid back/up -> enterNav"` never appears in the log.

**Relevant code:** `MainScene.brs` — `enterGrid()`, `onKeyEvent()` grid branch.

**Fix approaches (pick one):**

**Option A (recommended):** Remove `m.tileGrid.setFocus(true)`. Keep `m.top.setFocus(true)` always. MainScene handles all D-pad navigation manually:
- Track `m.gridIdx` (current focused tile index, 0-based)
- Left/Right: `m.gridIdx ±1`, clamp to content bounds, call `m.tileGrid.animateToItem = m.gridIdx`
- Down: `m.gridIdx + numColumns`, clamp
- Up from row > 0: `m.gridIdx - numColumns`
- Up from row 0: `enterNav()`
- OK: fire `onTileSelected()` manually using `m.gridIdx`
- For focus highlight without MarkupGrid OS focus: add `isFocused` boolean field to `TileItem.xml` with `onChange="onManualFocus"`. In `TileItem.brs`, `onManualFocus()` mirrors the visual logic of `onFocus()` (bg color + border). In MainScene: when gridIdx changes, set previous ContentNode's `isFocused = false` and new one's `isFocused = true` via `content.getChild(idx).isFocused`. Note: ContentNode fields are accessible this way; TileItem must observe `itemContent` changes that include this field OR use a direct interface field approach.

**Option B:** Keep MarkupGrid focus but add a custom wrapper component `FocusGrid` that extends MarkupGrid and overrides `onKeyEvent` to explicitly pass Up (and Back) to parent when at top row.

**Option C (quick hack):** Add a floating "Back to tabs" label at top of grid area that is always visible. When OK is pressed on it (detected by itemFocused == -1 or a separate Button node above the grid), switch to nav mode. Not clean but unblocks the user.

---

## Bug 2: Only one row of tiles visible

**Symptom:** The tile grid only shows one row of tiles. The screen has space for 2 rows but the second row is clipped or not rendered.

**Expected:** 2 full rows of tiles visible simultaneously (each row 200px tall + 20px gap = 220px; two rows = 440px; grid starts at y=470, so two rows end at y=910, well within 1080px).

**Root cause (theories):**
- The MarkupGrid may have a default `maxRows` or height constraint
- The grid might need an explicit `numRows` or `height` field to render more than one row
- The `translation=[80, 470]` + 2 rows ending at y=910 should fit above keyHints at y=1026, so clipping is unlikely — more likely the grid just isn't rendering row 2

**Fix:** Try setting explicit height on the MarkupGrid, or verify `numRows` is not constrained. In Roku SceneGraph, MarkupGrid's visible height is determined by its `translation` + available space. It may need `numRows` explicitly set or a `height` field. Check Roku docs for MarkupGrid height/numRows behavior.

In `MainScene.xml`:
```xml
<MarkupGrid id="tileGrid"
            translation="[80,470]"
            itemSize="[270,200]"
            itemSpacing="[20,20]"
            numColumns="6"
            numRows="2"         <!-- add this -->
            itemComponentName="TileItem"
            drawFocusFeedback="false" />
```

Or set explicit `height` field if numRows isn't supported.

---

## Bug 3: Backdrop not visible behind top panel

**Symptom:** The top panel shows a dark solid background. The artwork of the focused tile is not faintly visible as a backdrop behind the top panel.

**Expected:** The focused tile's artwork appears at ~20% opacity as a full-bleed background behind the top panel area (y=0 to y=390), giving depth to the UI (similar to Moonfin's backdrop pattern).

**Root cause:** `m.backdrop.uri` is being set in `updateTopPanelMeta()` but the Poster may not be loading because:
- The `backdrop` Poster node in `MainScene.xml` has `opacity="0.2"` which may be rendering before `uri` is set (shows nothing, not a dark placeholder)
- The `scrim` Rectangle (`color="0x000000CC"` = 80% black) is rendering on top and may be too opaque, fully obscuring a 20% opacity backdrop

**Fix:**
1. Verify `m.backdrop.uri` is actually being set (add `print "[backdrop] uri="; artUrl` in `updateTopPanelMeta`)
2. Reduce scrim opacity: `0x000000AA` (67% black) or `0x00000099` (60%)
3. Increase backdrop opacity to `0.3` or `0.35` for more visibility
4. Ensure `backdrop` Poster comes BEFORE `scrim` Rectangle in the XML child order (it does in current code — verify this hasn't changed)

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

**Fix:** Reduce top panel height. Move nav bar up to y=300 (or wherever the content naturally ends + ~20px breathing room). Update all downstream y-coordinates accordingly:
- Nav bar: `translation="[0,300]"`, underlines at y=357
- Tile grid: `translation="[80,380]"` (instead of 470) → gains 90px for the grid → fits more rows
- gridStatus, keyHints: adjust accordingly

Or: keep top panel taller but add more content (e.g., show episode description always, not just as topDesc).

---

## Summary Table

| # | Bug | Priority | Suggested Fix |
|---|-----|----------|---------------|
| 1 | Can't navigate to nav bar | **P0 — blocks all tab switching** | Option A: manual grid nav, no setFocus on MarkupGrid |
| 2 | Only one tile row visible | P1 — reduces content visibility | Add `numRows="2"` to MarkupGrid |
| 3 | Backdrop not visible | P2 — visual polish | Reduce scrim opacity, verify uri set |
| 4 | Top panel dead space | P2 — layout tightening | Reduce top panel height, move nav bar up |
