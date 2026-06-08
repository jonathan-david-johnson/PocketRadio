# M5 Handoff — Lists: Up Next / New Releases / Browse-Favorites + detail panes

Status snapshot for picking up M5 mid-stream. Read alongside `milestone_5.md`
(the scope/behaviors doc) and `../README.md`.

## Where we are

**Logic layer: 100% done** (all 7 milestone behaviors, red→green, unit-tested).
**TUI layer: ~80% done** — three of four panes built and checkpointed by the
user on iTerm2. One pane left: the **detail pane**.

### Done (committed)

| Area | What | Tests |
|------|------|-------|
| `pocketcasts/lists.go` | `PodcastList`, `FullEpisodes`, `NewReleases` (14-day cutoff + sort desc), `ShowNotes` + `htmlToPlainText` | `lists_test.go` |
| `radio/favorites.go` | `OrderFavorites`, `MoveFavorite`, `FavoriteIDs`; reorder persisted via `config.State.FavoritesOrder` | `favorites_test.go` |
| `radio/artwork.go` | iTunes Search artwork fallback (100→600px) | `artwork_test.go` |
| `radio/directory.go` | `AddFavorite`/`RemoveFavorite` (verified headers) | `favorites_test.go` |
| `library/format.go` | `FormatDuration`, `TotalTimeRemaining`, `EpisodeTimeRemaining`, `RelativeDate` | `format_test.go` |
| `library/engine.go` | targets `UpNextAt`, `PlayRelease`; accessors `UpNextList`, `NewReleases`; `playRelease`/`playNewestRelease`; live `TogglePlayback` reloads from edge | `engine_test.go` |
| `player/mpv.go` | `Load` forces `pause=off` (one-press source switch) | `mpv_integration_test.go` |
| `ui/full/debounce.go` | clock-injected `searchDebouncer` | `debounce_test.go` |
| `ui/full/full.go` | **Up Next tab**, **New Releases tab**, **Browse/Favorites radio panel** w/ debounced search, favorite toggle, reorder; **progress-meter transport** | `full_test.go` |
| `cmd/pocket-radio/main.go` | `radioSvc` adapter implementing `full.RadioService` | — |

All commits are on `pocket-radio-console` `main`. `go build ./... && go vet ./...
&& go test ./...` is green. mpv integration tests: `go test -tags integration
./internal/player/`.

### Not done — the one remaining M5 TUI piece

**Detail pane** (`i` opens, `esc` closes): episode show notes (artwork + meta +
notes) and station metadata (artwork + location/genre/quality/popularity/
homepage). This is the last bullet in `milestone_5.md` scope. After it, M5 is
complete and you move to M6 (lyrics + ACR + polish).

Also deferred / nice-to-have (not blocking M5 close):
- **Art in list rows** (milestone scope mentions it). Inline thumbnails per row
  are hard with the Bubble Tea line model (see the inline-image notes below);
  recommend skipping per-row art or doing it only in the detail pane.
- Spinner/loading affordance for the New Releases fan-out (first load is slow).

## Architecture notes (so you don't relearn them)

### The two service seams
- `full.Engine` interface = playback (the real `*library.Engine`). Drives
  play/pause/skip, targets, `UpNextList`, `NewReleases`.
- `full.RadioService` interface = the radio surface (favorites/browse/search/
  mutations/order). Implemented by `radioSvc` in `main.go`, **not** the engine —
  keep the engine focused on playback. `radioSvc` wraps `*radio.Client` +
  `*config.Store` + the user UUID.

If the detail pane needs show notes, add a method to **one of these seams**, not
a new global. Episode notes → put `ShowNotes(ctx, podcastUUID, episodeUUID)` on
`full.Engine` (wrapping `e.api.ShowNotes`, which already exists on the
`pocketcasts.PocketCasts` interface). Station metadata is already fully present
in the `radio.Station` struct you're rendering — no fetch needed.

### Model + Update conventions (`ui/full/full.go`)
- `Model` is a value type; `Update` returns `(tea.Model, tea.Cmd)`. Methods that
  mutate use **pointer receivers** and are called on the addressable `m`
  parameter (e.g. `moveListSel`, `reorderFavorite`, `searchInput`). Async work
  returns a `tea.Cmd`; the cmd's result comes back as a `Msg` case in `Update`.
- Data loads are lazy `tea.Cmd`s fired on first view (`fetchUpNext`,
  `fetchNewReleases`, `fetchFavorites`, `fetchBrowse`) and land as
  `*Msg` cases that set the slice + a `…Loaded` bool.
- **Pane routing**: `podcastSelected()` (pill 0), `browseSelected()` (last pill),
  stream pills in between. Sub-tabs: `podcastTab` (Up Next/New Releases),
  `radioTab` (Favorites/Browse). `[`/`]` toggles whichever pane is active.
- **Key dispatch** is context-aware via helpers: `selectedPlayTarget()`,
  `selectedStation()`, `moveListSel()`. Reuse these rather than branching inline.
- **Modal text input**: `inSearch()` + `searchInput()` capture printable keys for
  the Browse search field so `q`/`f`/space type instead of triggering commands;
  only an allow-list (arrows, enter, `[`/`]`, tab, esc, ctrl+f) keeps command
  meaning. The detail pane will need the same discipline: while it's open,
  intercept keys at the top of the `KeyMsg` case and only let `esc`/scroll
  through.

### Rendering gotchas
- **Width math**: rows are built by hand with `strings.Repeat(" ", pad)` and
  `lipgloss.Width(...)` (ANSI-aware). Follow the existing `upNextSection` /
  `radioSection` pattern. The user has flagged interest in refactoring onto
  `lipgloss.JoinHorizontal` + width breakpoints once panes multiply — the detail
  pane is a reasonable place to start that, but not required.
- **List height** uses a magic `visible := m.height - 16`. Brittle; if you touch
  layout, consider computing it from actual rows used above. Low priority.
- **Inline images** (iTerm2/kitty) must paint on their own reserved rows wrapped
  in DECSC/DECRC (`\x1b7…\x1b8`) so Bubble Tea's line count matches the screen —
  see `inlineArtLines` and the M4 ghost-duplication fix. This is why per-row art
  is hard. For the detail pane, art can use the same `inlineArtLines` approach
  since it's a dedicated region.

## How to build the detail pane

Suggested vertical slice (TDD-friendly; mirror how the other panes were built):

1. **State** on `Model`: `detailOpen bool`, plus the data to show. For an
   episode: fetch notes lazily into `detailNotes pocketcasts.EpisodeShowNotes` +
   `detailErr`. For a station: just stash the selected `radio.Station`.
2. **Open/close keys**: `i` (when a list row is selected in any pane) sets
   `detailOpen = true` and, for episodes, fires a `fetchShowNotes` cmd. `esc`
   closes (and must *not* quit while the pane is open — guard at the top of the
   `KeyMsg` case, like `inSearch`).
3. **Engine seam**: add `ShowNotes(ctx, podcastUUID, episodeUUID)
   (pocketcasts.EpisodeShowNotes, error)` to the `full.Engine` interface; the
   real engine just calls `e.api.ShowNotes(...)` (already wired). Add it to the
   test `fakeEngine` too.
4. **Which item**: reuse `selectedStation()` for stations; add a
   `selectedEpisode()` that returns the `pocketcasts.Episode` (Up Next) or builds
   one from the selected `pocketcasts.NewRelease`. You need `PodcastUUID` +
   `UUID` to fetch notes — both are on those structs.
5. **Render**: a full-width overlay region (replace the list area, or render
   below the divider). Episode pane = art (via `inlineArtLines`) + title +
   `library.FormatDuration` + scrollable notes (`pocketcasts` already strips HTML
   in `ShowNotes`). Station pane = art + name + country/language/tags/codec/
   bitrate/votes + homepage. Wrap long notes to `m.width`; add scroll with
   `↑↓` if it overflows (a `detailScroll int` offset, same `scrollWindow` helper).
6. **Tests** (`full_test.go`): `i` on an Up Next row opens the pane and fires the
   notes fetch; feeding the `showNotesMsg` renders the description; `esc` closes
   and does not quit. Station detail: `i` on a Browse row shows the station's
   country/codec without any fetch.

Watch the `esc` precedence: today `esc` is the first `KeyMsg` case (quit). Add a
guard `if m.detailOpen { ... close ...; return }` before the quit case, or fold
it into a top-of-handler check like `inSearch`.

## Verifying

```bash
cd pocket-radio-console
go build ./... && go vet ./... && go test ./...   # unit
go test -tags integration ./internal/player/       # mpv (needs mpv on PATH)
./pocket-radio                                      # full TUI (no-arg launches it)
```

Checkpoint cadence the user prefers: build one pane, they verify on iTerm2, then
commit. Commits are chunked and conventional (`feat(console): …`), co-authored.

## Pointers
- Scope/behaviors: `milestone_5.md`
- Surface overview: `../README.md`, `../CONTEXT.md`
- Menubar is the porting source of truth for API shapes + formatting rules:
  `pocket-radio-menubar/PocketRadio/{Services/APIService.swift,View Models/PlayerViewModel.swift}`
