# Navigation Design

## Home Nav (default)

```
[ Podcasts ]  [ Streams ]  [ Profile ]
```

## Podcasts World

Tap Podcasts → existing PC nav, unchanged.

```
[ ← ]  [ Podcasts ]  [ Playlists ]  [ Discover ]
```

`←` returns to Home Nav.

### Playlists tab

Header is a segmented title view: `Playlists / Up Next` (active label = bold + primary text color; inactive = regular weight + dimmer; `/` separator is inert).

- **Playlists** segment: list of user playlists / filters.
- **Up Next** segment: current Up Next queue.

Left and right bar buttons swap with the active segment to match that view's actions (e.g. `+` add playlist when Playlists is active; `Select` / `Cancel` etc. when Up Next is active). Tapping the inactive label flips the active segment, swaps the child view, and swaps the bar buttons atomically.

## Streams World

Tap Streams → stream-specific nav.

```
[ ← ]  [ Stations ]  [ Favorites ]  [ Browse ]
```

`←` returns to Home Nav.

### Streams tabs

| Tab | Content |
|-----|---------|
| **Stations** | Curated list (MVP: KCRW, KEXP, NPR Hourly) |
| **Favorites** | User-saved stations, synced via Supabase |
| **Browse** | Search radio-browser.info (90k+ stations) |

## Mini Player

- Floats above bottom nav in all states
- Shows whatever is currently playing (stream or podcast)
- Tapping expands to full player — no nav context switch needed
- Streams never appear in Up Next queue

## Profile

- Accessible from Home Nav only (top-right avatar, not in bottom tab bar)
- Contains Usage & Donations screen (cross-context, relevant to both worlds)
