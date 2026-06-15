# M9 — Lyric Sync Tuning, Lookup Fixes, Between-Tracks Detection

**Status**: DONE

## Goal

Lyrics sync for radio streams was unreliable: a fixed station-clock offset put
synced lyrics ahead of the audio by a station-dependent amount, decorated
track titles ("Clint Eastwood (Edit) (CLEAN)") failed to resolve on lrclib,
and the lyric line froze on the last line during DJ talk / ads / gaps between
songs.

## Changes

### 1. Per-station live sync offset
- `PlayerViewModel.lyricOffset` (in-memory `TimeInterval`), applied on top of
  the `now - playedAt` correction in `startLyricTimer` / the 1s timer tick.
- `adjustLyricOffset(by:)` nudges the offset, re-evaluates the current line
  immediately, and logs `lyric offset = Xs song=...` (category `Lyrics`).
- UI: `LyricsDetailView` header, right-justified, stacked `[− +]` over the
  offset readout (`+42s` / `-1s`), shown only for the current synced song.

### 2. Supabase persistence (`lyric_offsets`)
- New table `lyric_offsets(user_uuid, station_id, offset_seconds, updated_at)`,
  PK `(user_uuid, station_id)`, header-based RLS matching the other tables
  (migration `20260615000006_lyric_offsets.sql`).
- `PocketCastsAPI.fetchLyricOffsets` / `upsertLyricOffset` — same anon-key +
  `x-user-uuid` + merge-duplicates upsert pattern as `addFavorite`.
- Offsets loaded alongside favorites and applied per-station when synced
  lyrics load; saves are debounced 800ms.

### 3. Lookup fixes (`LyricsService`)
- `sanitize()` strips decoration groups — `(Edit)`, `(CLEAN)`, `[Explicit]`,
  `- Remastered 2010`, etc. — keyed off a qualifier word list, so e.g.
  "Clint Eastwood (Edit) (CLEAN)" → "Clint Eastwood".
- Three-tier fetch: exact `/api/get` with cleaned title+album → retry without
  album → `/api/search` fuzzy fallback (first synced result, else first).

### 4. Between-tracks detection
- lrclib `duration` field now parsed into `LyricsResult.duration`.
- `updateLyricLine` checks the corrected offset against
  `[firstLine.timestamp - 3s, (duration ?? lastLine.timestamp + 12s) + 12s]`;
  outside that window → `.betweenTracks` instead of a frozen last line.
- New `LyricStatus` enum (`.none/.fetching/.found/.notFound/.betweenTracks`)
  drives the tracklist lyrics bar: "Fetching…" / lyric text / "No lyrics
  found" / "♪ {station name}".

## Tuned values

- **KCRW**: -42s (HLS live-buffer delay)
- **KEXP**: +1s (Icecast, near-live)

## Out of scope

- iOS port (same bugs exist in `StationDetailViewController` /
  `LyricsService.swift` on iOS — not yet ported).
- `AVPlayerItem.currentDate()`-based self-correcting offset for HLS stations
  (constant works for now; revisit if KCRW's buffer depth changes).
- Pure `LyricSync` engine extraction for unit testing (original testability
  goal — deferred).
