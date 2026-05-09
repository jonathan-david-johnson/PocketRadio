# Navigation Design

## Home Nav (default)

```
[ Podcasts ]  [ Streams ]  [ Profile ]
```

## Podcasts World

Tap Podcasts → existing PC nav, unchanged.

```
[ ← ]  [ Podcasts ]  [ Playlists ]  [ Discover ]  [ Up Next ]
```

`←` returns to Home Nav.

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
