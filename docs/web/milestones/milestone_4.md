# Web M4 — Lyrics for radio Tracks

**Status**: PLANNED
**Depends on**: Web M3 (relay titles, Track timing, Now Playing)
**Required by**: none in the first release

## Where the work happens

| | |
|---|---|
| Plan | Shell `main`: this file |
| Code | `pocket-radio-web`, branch `feature/m4-lyrics` from `main` after M3 merges |
| Worktree | `pocket-radio-web/` |
| Shell changes | Additive: a `supabase/migrations/` file for web Lyric offsets |

**Goal:** Show synced lyrics for the current radio Track, as iOS does. The web
player fetches lyrics from lrclib and highlights the current line, timed from
when the listener heard the title change. A per-station web Lyric offset lets
the user nudge lines earlier or later. Offsets are saved for the user's
browsers, separately from the iOS and menubar offsets.

**User checkpoint:** Play KEXP. When a song with synced lyrics starts, Now
Playing shows lyrics and highlights the current line. Nudge it by a few seconds
until it matches the audio. Reload and play KEXP again: the nudge is still
applied, and the iPhone's lyric timing for KEXP is unchanged.

## Scope

- **Lyrics fetch (`src/lyrics/lyricsService.ts`).** Port iOS `LyricsService`:
  title and album sanitizing, exact `get` with and without the album, then
  `search`, plus LRC parsing and the plain-text fallback. Called from the
  browser (lrclib allows any origin). In-memory LRU cache.
- **Line timing (`src/lyrics/lyricClock.ts`).** Position is the time since
  the Track's applied title change (M3 Track timing) plus the web Lyric offset.
  Port iOS `LyricSyncController`'s intro grace, end grace, and between-tracks
  states.
- **Web Lyric offsets.** Migration for `web_lyric_offsets` (`user_uuid`,
  `station_id`, `offset_seconds`, `updated_at`) with the same header RLS as
  `lyric_offsets`. Worker `GET` and `PUT` at `/api/lyric-offsets`. The client
  debounces saves.
- **UI.** Lyrics panel in Now Playing with the current line highlighted, the
  offset nudge controls, and states for searching, none found, and plain text.

## Behaviors to test (red -> green, one at a time)

1. Sanitizing and lookup order match iOS `LyricsService` on shared cases.
2. LRC parsing yields timed lines; a missing timing falls back to plain text
   with no highlight.
3. The current line follows the applied title time plus offset; before the
   first line and after the song's end, the between-tracks state shows.
4. A new Track resets the lyric state; a late lrclib response for the previous
   Track is ignored.
5. Nudging saves one debounced `PUT`; reload restores it; `lyric_offsets` (iOS)
   is never written.
6. When the relay gives no title, the tracklist's top entry is used if the
   station has one; otherwise no lyrics are fetched.

## Out of scope

- KCRW media-clock alignment (later milestone; port of menubar M12).
- Merging web and iOS offsets.
- ACRCloud identification.

## Docs impact

- **Docs this changes or makes stale:** `docs/web/CONTEXT.md` (Lyric offset
  definition, if it changes); `supabase/` schema docs, if any.
- **Questions this must settle:** When a station has both relay titles and a
  tracklist, which wins for the current Track? Match iOS precedence, and record
  it if it isn't documented.

## Hand-performed interactions

- [ ] Click the lyric nudge buttons — the highlighted line moves immediately and survives a reload
