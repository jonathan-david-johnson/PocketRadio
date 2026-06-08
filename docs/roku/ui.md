# PocketStreams UI Design

## Main Screen

```
╔══════════════════════════════════════════════════════════════════════════════╗
║  POCKETSTREAMS                                                               ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  ┌──────────────────────────────────────────────────────────────────────┐   ║
║  │  TOP PANEL                                                           │   ║
║  │  ┌──────────┐  Episode Title / Station Name                         │   ║
║  │  │          │  Podcast Name  •  42 min left  •  In Progress         │   ║
║  │  │ ARTWORK  │                                                        │   ║
║  │  │ 200×200  │  Description excerpt or Country • Format • Bitrate    │   ║
║  │  │          │                                                        │   ║
║  │  └──────────┘  ████████████████░░░░░░░░░  32:14 / 58:42            │   ║
║  │                << 15s     ▶ / ❚❚     30s >>     [Mark Done]         │   ║
║  └──────────────────────────────────────────────────────────────────────┘   ║
║                                                                             ║
║  ┌──────────────────────────────────────────────────────────────────────┐   ║
║  │  [ Up Next ]    [ New Releases ]    [ Radio Favs ]    [ Browse ]    │   ║
║  └──────────────────────────────────────────────────────────────────────┘   ║
║                                                                             ║
║  ┌──────────────────────────────────────────────────────────────────────┐   ║
║  │  ┌───────┐  ┌───────┐  ┌───────┐  ┌───────┐  ┌───────┐  ┌───────┐  │   ║
║  │  │       │  │       │  │  ══╗  │  │       │  │       │  │       │  │   ║
║  │  │  art  │  │  art  │  │  ▶ ║  │  │  art  │  │  art  │  │  art  │  │   ║
║  │  │       │  │       │  │  ══╝  │  │       │  │       │  │       │  │   ║
║  │  │ Title │  │ Title │  │ Title │  │ Title │  │ Title │  │ Title │  │   ║
║  │  │ 42min │  │ 58min │  │  NOW  │  │ 28min │  │ 1h05m │  │ 45min │  │   ║
║  │  └───────┘  └───────┘  └───────┘  └───────┘  └───────┘  └───────┘  │   ║
║  │  ┌───────┐  ┌───────┐  ┌───────┐  ┌───────┐  ┌───────┐  ┌───────┐  │   ║
║  │  │  ...  │  │  ...  │  │  ...  │  │  ...  │  │  ...  │  │  ...  │  │   ║
║  └──────────────────────────────────────────────────────────────────────┘   ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

## Navigation Model

```
Left/Right in grid      → move tile focus → top panel updates
Up from grid            → focus jumps to nav bar
Down from nav bar       → focus jumps back to grid
OK on nav tab           → switch section, grid reloads
OK on tile              → play (top panel becomes Now Playing state)
Left/Right in nav bar   → change tab
Back                    → return focus to grid from nav bar
```

## Tile Card Design (M10 target)

Artwork is a full-bleed faded background (like the top panel backdrop), freeing the entire tile
surface for text. Three metadata rows at the bottom over a dark scrim.

### Episode tile (270×200)

```
┌──────────────────────────────┐  ← focus border: 274×204 ACCENT rect at -2,-2
│ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░│
│ ░░  faded artwork backdrop  ░│  Poster 270×200, opacity=0.35, scaleToZoom
│ ░░  + dark scrim overlay    ░│  Rectangle 270×200, #000000AA on top
│ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░│
│ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░│
│▓▓▓▓▓░░░░░░░░░░░░░░░░░░░░░░░│  y=138  h=3  progress strip (ACCENT fill over dim track)
│ Monday                       │  y=144  h=22  SmallSystemFont  white
│ The Daily                    │  y=166  h=22  SmallSystemFont  dim (#9C9FA4)
│ 47:30  (20:00 left)          │  y=188  h=20  SmallestSystemFont  dim / accent for "(left)"
│                         NOW  │  NOW badge top-right: 52×22 ACCENT rect at x=214,y=4
└──────────────────────────────┘
```

- Progress strip width = `int((playedUpTo / duration) * 270)`. Hidden entirely if `duration = 0`.
- Day label: `published` Unix timestamp → `roDateTime` → `GetDayOfWeek()` → "Monday" etc.
- Duration row: `"47:30"` always shown. `" (20:00 left)"` appended in ACCENT only if `playedUpTo > 0`.
  - Format: `MM:SS` if under 1h, `H:MM:SS` if ≥ 1h.

### Station tile (270×200)

```
┌──────────────────────────────┐
│ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░│
│ ░░   faded station logo     ░│  Poster 270×200, opacity=0.35
│ ░░   + dark scrim overlay   ░│  Rectangle 270×200, #000000AA
│ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░│
│ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░│
│                              │  y=138  (no progress strip)
│ KCRW                         │  y=144  h=22  SmallSystemFont  white
│ AAC / 128k                   │  y=166  h=22  SmallSystemFont  dim
│ ● LIVE                       │  y=188  h=20  SmallestSystemFont  ACCENT
└──────────────────────────────┘
```

### Current tile (before M10) — for reference

```
┌──────────────────────────────┐
│                              │
│       podcast artwork        │  150px — opaque, scaleToZoom
│                              │
│ Episode / Station Title      │  y=155  h=26  SmallSystemFont  white
│ 42min  /  AAC 128k           │  y=178  h=22  SmallestSystemFont  dim
└──────────────────────────────┘
```

Key changes from current:
- Artwork → full-bleed faded background (opacity 0.35 + dark scrim), not a visible image
- All vertical space now available for text
- Three text rows: day-of-week / podcast name / duration+left
- Progress strip above text rows (hidden for stations and unstarted episodes)
- `published` Unix timestamp required in description JSON — relay already returns it, needs to be stored

## Open Questions

1. Top panel controls (progress bar, skip, mark done) — show when something is
   **currently playing**, or always show for the **focused tile**?

2. For Radio Favs/Browse tiles — no progress bar. Top panel shows logo + metadata.
   Station tiles: logo image + name only, no duration. Good?
