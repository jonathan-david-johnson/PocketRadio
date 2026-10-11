# Web M2 — App shell and navigation from the synced Layout

**Status**: PLANNED
**Depends on**: Web M1 (Pairing, session, JSON API client decisions); web ADR 0005
**Required by**: Web M3–M8

## Where the work happens

| | |
|---|---|
| Plan | Shell `main`: this file |
| Code | `pocket-radio-web`, branch `feature/m2-shell-nav` from `main` after M1 merges |
| Worktree | `pocket-radio-web/` |
| Shell changes | Additive: `contracts/nav_layout/` fixtures and README; a `supabase/migrations/` file creating and seeding `curated_stations`; iOS ADR 0002 consequence updated |

**Goal:** Build the signed-in app shell and its navigation. The web player reads
the user's Layout from `nav_layout` and renders it the way the iOS settings
screen lists it. On a wide window, the Sidebar shows every Destination with the
Bar line where the phone's tab bar ends. On a narrow window, it shows the
iPhone's tab bar: up to four tabs plus More. Each Destination has its own URL
and, for now, a placeholder screen. The render rules become shared fixtures so
the TypeScript port and iOS can't drift.

**User checkpoint:** Sign in by Pairing. The Sidebar reads New Releases, Tech,
Streams, News, then the Bar line, then Podcasts, Playlists, Discover, Profile,
Up Next, matching the iPhone's tab bar and More tab. Narrow the window: four
tabs and More appear, and More lists the rest in the same order. Reorder tabs
on the iPhone, then focus the browser tab again: the Sidebar follows.

## Scope

- **Shared contract (shell).** `contracts/nav_layout/README.md` and fixtures
  `*.json`. Each fixture holds `slots` (wire ids, as stored in `nav_layout`),
  `capacity`, `available_playlists`, and the expected `bar`, `more`, and
  `sidebar` with `bar_line_after`. Cases: iOS default (epoch), the primary
  user's layout, all core placed, more than five slots, an unknown future id,
  a deleted playlist, duplicate slots, and an empty slot list.
- **Render rules (`src/nav/`).** A pure TypeScript port of
  `TabLayout.renderPlan(capacity:isAvailable:)`. It drops unresolvable and
  unavailable slots, applies the More rule, and derives the complement in core
  order `podcasts, playlists, discover, streams, profile, upNext`. It also
  derives the Sidebar order and the Bar line index. Vitest loads
  `../contracts/nav_layout/*.json`.
- **Layout read (`functions/api/layout`).** `GET` returns `{slots, updated_at}`
  from `nav_layout`, using the anon key plus a server-set `x-user-uuid`
  (ADR 0002). With no row, it returns iOS `TabLayout.default`. The client
  re-fetches on window focus and on visibility change.
- **Playlist titles.** The Worker reads the user's playlists through the
  M1-decided client, so `playlist:<uuid>` slots show the playlist's name, and
  a playlist missing or deleted on the server counts as unavailable.
- **Shell UI (`src/app/`).** React Router routes per Destination
  (`/podcasts`, `/playlists`, `/playlist/:uuid`, `/discover`, `/streams`,
  `/profile`, `/up-next`, `/more` on narrow), Sidebar and narrow tab bar
  components, an account menu (email, Sign out, Sign out everywhere), and
  placeholder screens. Starts on the first Sidebar item. The player bar slot
  is reserved but empty.
- **Curated stations (shell).** Migration creating `curated_stations`, seeded
  from `pocket-radio-ios/podcasts/Radio/curated_stations.json`, readable with
  the anon key. `GET /api/stations/curated` serves it.

## Behaviors to test (red -> green, one at a time)

1. Every `contracts/nav_layout` fixture produces its expected `bar`, `more`,
   `sidebar`, and `bar_line_after`.
2. Unknown ids and unavailable playlist slots are dropped without reordering
   the rest; duplicates render once.
3. `GET /api/layout` returns the stored row for the session's user, returns
   the iOS default when no row exists, and returns 401 without a session.
4. A request with no session can't reach `nav_layout` or `curated_stations`
   through the Worker. The browser bundle contains neither the anon key nor
   the user's id.
5. Wide viewport renders the Sidebar with the Bar line in the right place.
   Narrow viewport renders capacity-5 tabs with More last.
6. Each Destination route renders its placeholder. An unknown `/playlist/:uuid`
   shows "This playlist isn't available".
7. Focusing the window after a Layout change re-renders the Sidebar without a
   reload, and keeps the selected Destination if it still exists.
8. `GET /api/stations/curated` returns the seeded rows.

## Out of scope

- Editing the Layout (M7).
- Screen content for any Destination (M3–M6, M8).
- Moving iOS, the menubar, and the console to read `curated_stations` (tracked
  in `docs/todo.md`).
- iOS adopting the `contracts/nav_layout` fixtures in its own tests (tracked in
  `docs/todo.md`).

## Docs impact

- **Docs this changes or makes stale:** `docs/ios/adr/0002-supabase-for-nav-layout-sync.md`
  (its "not readable by other surfaces" consequence); `docs/ios/architecture/configurable-tab-bar.md`
  §4 (one shared layout now spans web too); `contracts/README` index if one
  exists; `docs/web/CONTEXT.md` if new terms appear.
- **Questions this must settle:** Should the narrow-window breakpoint follow
  the iPhone's capacity exactly, or allow more tabs on a tablet-width browser?
  (Default: exactly 5, per ADR 0005.)

## Hand-performed interactions

- [ ] Resize the window across the breakpoint — the Sidebar becomes the tab bar and back, keeping the current Destination
- [ ] Click each Sidebar item and the More tab's rows — each opens its own URL and the browser Back button returns
