# Web M6 — Playlists and playlist tabs

**Status**: PLANNED
**Depends on**: Web M2 (playlist slots in the Sidebar), Web M5 (episode rows, play now)
**Required by**: none in the first release

## Where the work happens

| | |
|---|---|
| Plan | Shell `main`: this file |
| Code | `pocket-radio-web`, branch `feature/m6-playlists` from `main` after M5 merges |
| Worktree | `pocket-radio-web/` |
| Shell changes | None expected |

**Goal:** Fill the Playlists Destination and the playlist tabs. Playlists lists
all of the user's playlists. A Manual playlist shows its episodes in the
server's order and plays them like any episode list. A Smart playlist shows the
Smart playlist placeholder until Smart playlist evaluation ships: its name, a
summary of its rules, and a pointer to the iPhone. A `playlist:<uuid>` tab
opens the same screen.

**User checkpoint:** Click New Releases, Tech, and News in the Sidebar. Each
either lists its episodes (Manual playlist) or shows the placeholder with a
readable rule summary (Smart playlist). Open Playlists: every playlist from the
iPhone is listed, and each opens the same screen.

## Scope

- **Playlist client (`functions/api/pc/playlists`).** Reads `user/playlist/list`
  through the M1-decided client. It returns, per playlist, the uuid, title,
  icon, `manual`, `isDeleted`, rule fields, and for Manual playlists the
  episodes ordered by `episodeOrder`. Deleted playlists are dropped.
- **Playlists UI (`src/playlists/`).** List screen, Manual playlist episode
  list (reusing M5 rows, play now, play next, play last), and the Smart
  playlist placeholder.
- **Rule summary (`src/playlists/ruleSummary.ts`).** Plain-language summary
  of a Smart playlist's rules: podcasts, played state, downloaded state,
  starred, release window, duration, and audio/video.

## Behaviors to test (red -> green, one at a time)

1. Manual playlists list their episodes in `episodeOrder`; missing episodes are
   skipped.
2. A Smart playlist renders the placeholder, never an episode list.
3. Each rule combination in a fixture set produces its expected summary
   sentence.
4. Deleted playlists don't appear, and a tab for one is dropped from the
   Sidebar (M2 rule).
5. `/playlist/:uuid` and Playlists → playlist render the same screen.

## Out of scope

- Smart playlist evaluation (later). Start by checking whether Pocket Casts'
  own web player gets New Releases and In Progress from the server.
- Creating, editing, or deleting playlists.

## Docs impact

- **Docs this changes or makes stale:** `docs/web/CONTEXT.md` (Manual
  playlist, Smart playlist, Smart playlist placeholder, if the definitions
  change).
- **Questions this must settle:** Does `user/playlist/list` return Manual
  playlist episodes with enough metadata to play them, or does each need a
  further lookup?

## Hand-performed interactions

- none — click navigation only, covered by Playwright
