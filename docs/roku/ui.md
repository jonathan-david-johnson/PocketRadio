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

## Open Questions

1. Top panel controls (progress bar, skip, mark done) — show when something is
   **currently playing**, or always show for the **focused tile**?

2. For Radio Favs/Browse tiles — no progress bar. Top panel shows logo + metadata.
   Station tiles: logo image + name only, no duration. Good?
