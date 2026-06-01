# PocketStreams Roku — Styling Guide

Theme derived from iOS dark palette (`ThemeColor.swift`). Roku uses `0xRRGGBBAA` (alpha last, `FF` = opaque).

---

## Color Palette

| Token | Roku Hex | iOS Source | Use |
|-------|----------|------------|-----|
| `BG_DEEP` | `0x0D0E10FF` | near-black | Scene background, Now Playing bg |
| `BG_SURFACE` | `0x1A1B1DFF` | `primaryUi02Dark` | Top panel, tile bg unfocused |
| `BG_ELEVATED` | `0x1E2124FF` | `primaryUi06Dark` | Nav bar bg, section headers |
| `BG_SELECTED` | `0x1E333DFF` | `primaryUi02SelectedDark` | Focused tile, focused nav tab |
| `BG_SCRIM` | `0x000000CC` | — | Dark overlay over backdrop (80% black) |
| `TEXT_PRIMARY` | `0xFFFFFFFF` | `primaryText01Dark` | Titles, tile labels |
| `TEXT_SECONDARY` | `0x9C9FA4FF` | `primaryText02Dark` | Metadata, duration, hints |
| `TEXT_MUTED` | `0x4A4D54FF` | `primaryText02Dark` dim | Key hint bar |
| `ACCENT` | `0x00A0E8FF` | `primaryIcon01Dark` approx | Progress fill, NOW badge, active tab underline |
| `PROGRESS_BG` | `0x3A3D42FF` | `primaryUi05Dark` | Progress bar track |
| `DIVIDER` | `0x2A2D30FF` | `primaryUi05Dark` | Section dividers |

---

## Typography

Roku system fonts only.

| Role | Font | Use |
|------|------|-----|
| Top panel title | `font:LargeBoldSystemFont` | Focused item title |
| Top panel meta | `font:MediumSystemFont` | Podcast name, duration, bitrate |
| Top panel body | `font:SmallSystemFont` | Description excerpt |
| Nav tab | `font:MediumBoldSystemFont` | Active tab |
| Nav tab inactive | `font:MediumSystemFont` | Inactive tab |
| Tile title | `font:SmallSystemFont` | Below tile artwork |
| Tile meta | `font:SmallestSystemFont` | Duration, "NOW" badge |
| Key hints | `font:SmallSystemFont` | Bottom hint bar |

---

## Layout Grid (FHD 1920×1080)

| Zone | Y | Height | Notes |
|------|---|--------|-------|
| Top panel | 0 | ~380 | Artwork + metadata + progress/controls |
| Nav bar | ~390 | 60 | Horizontal section tabs |
| Tile grid | ~470 | ~560 | MarkupGrid, scrollable |
| Key hint bar | 1020 | 60 | Static, always visible |

| Zone | X | Width | Notes |
|------|---|-------|-------|
| Left margin | 80 | — | Safe area |
| Content width | 80 | 1760 | 80px margins both sides |
| Artwork in top panel | 80 | 200×200 | Left-aligned |
| Metadata in top panel | 310 | 1450 | Right of artwork |

---

## Component Specs

### Scene Background + Backdrop

```xml
<!-- Base background — always first child -->
<Rectangle id="bg" width="1920" height="1080" translation="[0,0]" color="0x0D0E10FF" />

<!-- Backdrop poster: artwork at low opacity, full bleed, behind top panel -->
<Poster id="backdrop" width="1920" height="380" translation="[0,0]"
        loadDisplayMode="scaleToZoom" opacity="0.2" />

<!-- Scrim over backdrop for readability -->
<Rectangle id="scrim" width="1920" height="380" translation="[0,0]" color="0x000000CC" />
```

Backdrop crossfade on focus change: Animation 0.3s `inOutQuad` on `backdrop.opacity` 0→0.2.

---

### Top Panel

Full-width, ~380px tall. Contains artwork, metadata, progress (episodes) or metadata only (stations).

```
[80, 40]     Poster 200×200 (artwork)
[310, 40]    Label: title         LargeBoldSystemFont   TEXT_PRIMARY
[310, 100]   Label: subtitle      MediumSystemFont      TEXT_SECONDARY   (podcast name / station meta)
[310, 140]   Label: description   SmallSystemFont       TEXT_SECONDARY   wrap=true, 3 lines max
[80,  290]   Rectangle: progress track  1760×8  PROGRESS_BG
[80,  290]   Rectangle: progress fill   variable  ACCENT
[80,  312]   Label: time          SmallSystemFont       TEXT_SECONDARY   "32:14 / 58:42"
[80,  340]   Label: controls hint SmallSystemFont       TEXT_MUTED       "<< 15s   Play/Pause   30s >>"
```

Progress bar and controls only visible when `isLive = false` and content is loaded.

---

### Nav Bar

Horizontal tab strip. 60px tall, full width, `BG_ELEVATED` background.

```xml
<Rectangle id="navBg" width="1920" height="60" translation="[0, 390]" color="0x1E2124FF" />
```

Tabs: `[ Up Next ]  [ New Releases ]  [ Radio Favs ]  [ Browse ]`

- Inactive: `TEXT_SECONDARY`, `MediumSystemFont`, no underline
- Active/focused: `TEXT_PRIMARY`, `MediumBoldSystemFont`, 3px `ACCENT` underline rectangle below text
- Tab spacing: 60px left margin, 80px between tabs

---

### Tile Grid (MarkupGrid)

```xml
<MarkupGrid id="tileGrid"
            translation="[80, 470]"
            itemSize="[270, 200]"
            itemSpacing="[20, 20]"
            numColumns="6"
            itemComponentName="TileItem"
            drawFocusFeedback="false"
            focusXOffset="0"
            focusYOffset="0" />
```

6 columns × N rows. Tile dimensions 270×200 (FHD). Grid is scrollable vertically.

Clipping rect on grid: `[-10, -10, 1780, 580]` (allows focus ring to bleed 10px).

---

### TileItem Component

```
┌─────────────────────────┐
│                         │   ← Poster 270×150 (top 75%)
│      ARTWORK            │
│                    [▶]  │   ← NOW badge (ACCENT, top-right, if playing)
│                         │
├─────────────────────────┤   ← 2px DIVIDER
│ Title                   │   ← SmallSystemFont TEXT_PRIMARY, 1 line truncated
│ 42 min left             │   ← SmallestSystemFont TEXT_SECONDARY
└─────────────────────────┘
```

Focus state: `BG_SELECTED` background + 2px `ACCENT` border rectangle overlay.
Unfocused: `BG_SURFACE` background.

Station tiles: same layout, no duration line. Logo fills artwork area.

---

### Progress Bar

```xml
<!-- Track -->
<Rectangle id="progressBg" width="1760" height="8" color="0x3A3D42FF" />
<!-- Fill — set width dynamically: Int(1760 * fraction) -->
<Rectangle id="progressFill" width="0" height="8" color="0x00A0E8FF" />
```

---

### Key Hint Bar

```xml
<Label id="keyHints"
       translation="[80, 1026]"
       width="1760"
       font="font:SmallSystemFont"
       color="0x4A4D54FF" />
```

Content varies by focus state:
- Grid focused: `"OK  Play   Right  Detail   Up  Nav bar"`
- Nav bar focused: `"Left/Right  Switch tab   Down  Grid   Back  Previous"`
- Now Playing: `"Play/Pause   Left/Right  Skip   Back  Return"`

---

## Focus Rules

1. Focused tile: `BG_SELECTED` bg + `ACCENT` border. Never rely on Roku default focus bitmap.
2. Active nav tab: `ACCENT` underline, `TEXT_PRIMARY` label.
3. Progress fill `ACCENT` (`0x00A0E8FF`) over `PROGRESS_BG` (`0x3A3D42FF`) — sufficient contrast.
4. All text on dark bg: minimum contrast 4.5:1. `TEXT_PRIMARY` on `BG_SURFACE` = 15:1 ✓
5. `drawFocusFeedback="false"` on `MarkupGrid` — handle focus entirely in `TileItem.brs` via `focusPercent`.

---

## Animations

| Event | Property | Duration | Easing |
|-------|----------|----------|--------|
| Backdrop swap on tile focus | `backdrop.opacity` 0→0.2 | 0.3s | inOutQuad |
| Nav tab underline slide | `underline.translation` | 0.2s | inOutCubic |
| Top panel content swap | `topPanel.opacity` 1→0→1 | 0.15s | linear |
| Grid scroll | handled by MarkupGrid | — | — |
