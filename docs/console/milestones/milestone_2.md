# M2 — Mini-mode radio + arg resolver + tracklist now-playing

**Goal:** Make mini mode play radio and resolve arbitrary args, with the one line
showing the live track for stations that publish a tracklist.

**User checkpoint:** `pocket-radio kcrw` plays KCRW and the one line updates to
`▶ <Song> — <Artist>  [KCRW]`; `pocket-radio --list` prints resolvable names;
`pocket-radio zzzz` errors with "did you mean" suggestions.

## Scope

- `internal/radio/directory.go`: `Favorites` (Supabase `radio_favorites` →
  radio-browser `byuuid` lookup, parallel), `Top` (topvote), `Search`.
- `internal/radio/tracklist.go`: KCRW + KEXP parsers; 30s poller in the engine.
- **Arg resolver** (its own deep, pure-ish module): reserved words → favorite
  name substring → radio-browser search top hit → `NoMatchError{Suggestions}`.
- Engine: `PlayTarget(Station)`; live-vs-seekable detection from mpv
  `duration`/`seekable` → mute controls (no skip) for live streams.
- mpv ICY `metadata` surfaced as a fallback now-playing title when no tracklist.

## Behaviors to test (red → green, one at a time)

1. **Resolver — reserved word**: `up_next`/`new` resolve to their Targets without
   touching the network.
2. **Resolver — favorite hit**: `"kcrw"` resolves to the favorite whose name
   contains it (case-insensitive), no search call made.
3. **Resolver — fav miss → search**: an arg matching no favorite calls
   `RadioDirectory.Search` and returns the top hit.
4. **Resolver — no match**: returns `NoMatchError` whose suggestions are the
   nearest favorite names.
5. `Favorites` against `httptest`: Supabase IDs → station lookups → sorted
   `[]Station` (mock both hosts).
6. KCRW parser: a captured `tracklist-api.kcrw.com` body → ordered `[]Track`,
   dropping `[BREAK]` entries; KEXP parser: only `trackplay` rows.
7. Engine: while a `Station` plays, a tracklist tick sets
   `State().Title == "Song — Artist"`; an empty tracklist falls back to the
   station name.
8. Engine: a live stream (mpv `duration == 0`) sets `State().IsLive == true` and
   `SkipForward()` is a no-op.

## Out of scope

Add/remove favorites + reorder (M5), iTunes art fallback (M6 — text only here),
podcast position write-back (M3), full TUI (M4).
