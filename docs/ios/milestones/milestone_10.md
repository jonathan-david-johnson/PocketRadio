# iOS M10 — Port Lyric Sync Tuning from Menubar

**Status**: DONE  
**Depends on**: M9 (complete), menubar M9 (complete)

---

## Goal

Port the menubar M9 lyric-sync improvements to iOS. The synced-lyrics header in
`StationDetailViewController` and the full-screen `LyricsViewController` should match
the menubar behavior: per-station live offset controls, decorated-title lookup
fixes, and detection of gaps between tracks so the header doesn't freeze on a
frozen last line during DJ talk / ads.

---

## Done when

### 1. Per-station live sync offset
- [x] `StationDetailViewController` stores a `lyricOffset: TimeInterval` per station.
- [x] Offset is applied on top of `now - playedAt` in the synced-lyrics timer.
- [x] `adjustLyricOffset(by:)` nudges the offset, re-evaluates the current line
      immediately, and logs `lyric offset = Xs song=...` (category `Lyrics`).
- [x] `LyricsViewController` shows +/- buttons in its header when the pushed song is
      the currently-playing synced track. Touch target is at least 44×44 pt.
- [x] Tapping +/- updates the station's offset in real time, persists it after an
      800ms debounce, and immediately re-scrolls the lyrics table.

### 2. Supabase persistence (`lyric_offsets`)
- [x] `RadioFavoritesManager.fetchLyricOffsets()` returns `[stationId: Int]` and
      populates a shared in-memory cache.
- [x] `RadioFavoritesManager.upsertLyricOffset(stationId:seconds:)` upserts to
      `lyric_offsets` using a typed `Encodable` payload (header-based RLS).
- [x] `FavoritesViewController` loads offsets alongside favorites.
- [x] `StationDetailViewController` applies the saved offset when synced lyrics load.
- [x] Offsets work for signed-out users (in-memory only) and persist for signed-in users.

### 3. Lookup fixes (`LyricsService`)
- [x] `LyricsResult` gains `duration: TimeInterval?` from lrclib's `duration` field.
- [x] Three-tier fetch: exact `/api/get` with cleaned title+album → retry without
      album → `/api/search` fuzzy fallback (first synced, else first plain).
- [x] `sanitize(_:)` strips decoration groups such as `(Edit)`, `(CLEAN)`, `[Explicit]`,
      `- Remastered 2010` using a qualifier word list.
- [x] Unit tests cover `sanitize()` and `LyricsResult` parsing (see `LyricsServiceTests.swift`).

### 4. Between-tracks detection
- [x] `StationDetailViewController` has a `LyricStatus` enum: `.none`, `.fetching`,
      `.found`, `.notFound`, `.betweenTracks`.
- [x] Section header text reflects the status:
      - `.fetching` → `"Fetching…"`
      - `.found` → `"♪ " + currentLine.text`
      - `.notFound` → `"No lyrics found"`
      - `.betweenTracks` → `"♪ " + station.name` (or `"On air"` if empty)
      - `.none` → header hidden (height 0)
- [x] Timer detects when the corrected offset falls outside
      `[firstLine - 3s, (duration ?? lastLine + 12s) + 12s]` and switches to
      `.betweenTracks` instead of freezing the last line.
- [x] `LyricsViewController` shows a matching status label when it is the current song
      and the offset is between tracks.

### 5. Repo / planning hygiene
- [x] Create `docs/ios/milestones/milestone_10.md` and repoint
      `docs/ios/current_milestone.md` to it.
- [x] `make build_staging` passes.
- [x] `make format` passes.
- [x] `make test_staging` passes (including the new `LyricsServiceTests`).

---

## Tuned values

- **KCRW**: -42s (HLS live-buffer delay)
- **KEXP**: +1s (Icecast, near-live)

These are defaults the user can refine with the +/- controls. Positive values
advance the lyrics relative to the raw `playedAt` offset to catch up to delayed audio.

---

## File list

| File | Action | Notes |
|------|--------|-------|
| `podcasts/Radio/LyricsService.swift` | Edit | Add duration, sanitize, three-tier fetch, between-tracks helpers |
| `podcasts/Radio/LyricsViewController.swift` | Edit | Offset controls, status label, offset-aware timer, theme observer |
| `podcasts/Radio/StationDetailViewController.swift` | Edit | Offset state, status machine, between-tracks detection, delegate |
| `podcasts/Radio/RadioFavoritesManager.swift` | Edit | `fetchLyricOffsets()` + `upsertLyricOffset()` |
| `podcasts/Radio/FavoritesViewController.swift` | Edit | Load offsets in parallel with favorites |
| `PocketCastsTests/Tests/Radio/LyricsServiceTests.swift` | New | Unit tests for `sanitize()` and `duration` parsing |
| `supabase/migrations/20260615000006_lyric_offsets.sql` | None | Already applied; no change needed |
| `docs/ios/current_milestone.md` | Symlink | Repoint to `milestones/milestone_10.md` |

---

## UI changes

### StationDetail section header

```
┌──────────────────────────────────┐
│  ♪ And I know that you're the…  │  .found
│  Fetching…                       │  .fetching
│  No lyrics found                 │  .notFound
│  ♪ KCRW                          │  .betweenTracks
│  (hidden)                        │  .none
└──────────────────────────────────┘
```

### LyricsViewController header

```
┌─────────────────────────────────┬──────────┐
│  [art]  Track Title             │  [  −  ] │
│         Artist                  │  [  +  ] │
│                                 │  +42s    │
└─────────────────────────────────┴──────────┘
```

The +/- buttons have a 44×44 pt transparent hit area. Controls are shown only for the
current synced song. A status label below the header appears for `.betweenTracks`
(e.g. `♪ KCRW`) so the user sees the state while the full-screen view is open.

---

## Edge cases

| Case | Behavior |
|------|----------|
| Signed-out user | Offsets stay in-memory; no Supabase calls; controls still work |
| No synced lyrics (plain-only) | Offset controls hidden; header shows first line statically |
| Lyric fetch fails | `.notFound` header; no offset controls |
| Offset outside song window | `.betweenTracks` header / label showing station name |
| Rapid +/- taps | Only one Supabase upsert after 800ms silence |
| Station changed while timer running | `stopLyricTimer()` resets offset state for next station |
| User changes theme while LyricsViewController is open | Controls and table cells re-apply theme colors |

---

## Testing

1. Open KCRW detail while a track is playing — header should show current lyric.
2. Tap the top tracklist row — `LyricsViewController` shows +/- controls.
3. Tap `−` repeatedly until lyrics align with audio; note the offset.
4. Kill and reopen the app; reopen KCRW — the saved offset should restore.
5. Wait for a DJ break or ad — header and full-screen view should switch to `♪ KCRW` instead of freezing the last line.
6. Try a decorated track title (e.g. "… (Edit) (CLEAN)") — lyrics should resolve after sanitization.
7. Run the new unit tests:
   ```bash
   cd pocket-radio-ios
   make test_staging ONLY_TESTING=PocketCastsTests/LyricsServiceTests
   ```

```bash
# Verify the migration is present:
supabase migration list | grep lyric_offsets

# Full build and test:
cd pocket-radio-ios
make build_staging
make test_staging
```

---

## Out of scope

- AVPlayerItem-based self-correcting offset for HLS stations (menubar M9 deferred this).
- Extracting a pure `LyricSync` engine for unit testing (menubar M9 deferred this).
- CarPlay / widget lyrics display.
- Cross-device sync of offsets beyond Supabase (already handled by the table).

---

## Commit

`539a5a1` — feat(radio): M10 lyric sync tuning ported from menubar
