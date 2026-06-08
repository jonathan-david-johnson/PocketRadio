# M5 — Lists: Up Next, New Releases, Browse / Favorites

**Goal:** Fill in the full TUI's bottom section to reach menubar parity for
browsing and queue management: the podcast tabs, the radio panel, and the detail
panes.

**User checkpoint:** In the full TUI you can scroll Up Next (with total + per-
episode time remaining), switch to New Releases and play one, open Browse /
Favorites, search stations, favorite/unfavorite, reorder favorites, and open a
detail pane (episode show notes / station metadata).

## Scope

- `internal/pocketcasts/client.go`: `PodcastList`, `FullEpisodes`, `ShowNotes`
  (+ HTML→plain-text), all ported from the menubar.
- `internal/radio/directory.go`: `AddFavorite`, `RemoveFavorite` (Supabase
  upsert/delete); favorites reorder persisted to `state.json`.
- `internal/radio/artwork.go`: iTunes Search artwork fallback (used by list rows
  + tracklist entries lacking art).
- Full TUI:
  - podcast section: **Up Next** tab (list + total time remaining + per-row date
    / time-left) and **New Releases** tab (last 14 days, play on select);
  - radio panel: **Favorites** + **Browse** tabs, debounced search, heart
    toggle, reorder (key-based move, e.g. `[`/`]` or drag-equivalent);
  - detail pane: episode (artwork + meta + show notes) and station (artwork +
    location/genre/quality/popularity/homepage), opened with `i`, closed `esc`.
  - art in list rows + detail panes.

## Behaviors to test (red → green, one at a time)

1. New Releases pipeline: `PodcastList` → fan-out `FullEpisodes` → filter to last
   14 days → sorted desc (mock both endpoints; assert the cutoff + order).
2. `ShowNotes` decode + `htmlToPlainText`: tags stripped, common entities
   decoded, whitespace collapsed (port the menubar's cases as fixtures).
3. `AddFavorite`/`RemoveFavorite` hit Supabase with the right method + headers
   (`apikey`, `x-user-uuid`, upsert `Prefer`) against `httptest`.
4. Reorder: moving a favorite persists the new order to `state.json` and
   re-applying it on reload preserves the order (with unknown stations appended).
5. Engine `PlayTarget(NewestRelease)` plays the newest release and bubbles it via
   `PlayNow`.
6. Up Next list view: total-time-remaining string and per-episode "X left" /
   "Finished" strings match the menubar's formatting rules (port those cases).
7. Browse search debounce: rapid query changes collapse to a single `Search`
   call after the debounce window (injected clock).

## Out of scope

Lyrics + ACR + final polish (M6).
