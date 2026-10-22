# Web M2 — App shell and navigation from the synced Layout

**Status**: IN PROGRESS — started 2026-10-18 on `feature/m2-shell-nav`. Behaviors 1–3, 5, 7 and 8 are green (web `d8f3ac7`); 4 and 6 are partly done; playlist names are not started. The `curated_stations` migration is written but not applied. The web build uses pnpm since web `8e42079`.
**Depends on**: Web M1 (Pairing, session, protobuf client decision, ADR 0007); web ADR 0005
**Required by**: Web M3–M8

## Where the work happens

| | |
|---|---|
| Plan | Shell `main`: this file |
| Code | `pocket-radio-web`, branch `feature/m2-shell-nav`. It branched from `feature/m1-spikes` at `faf4fd7`; M1 has since merged into `main`, and the branch merged `main` at `7a196bd` |
| Worktree | `pocket-radio-web-m2/`, a git worktree of `pocket-radio-web/`, whose main checkout is on `main`. It has its own `node_modules`, installed by pnpm; the main checkout's is still npm's until M2 merges |
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
  protobuf client (ADR 0007), so `playlist:<uuid>` slots show the playlist's name, and
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
   `sidebar`, and `bar_line_after`. **Green:** `tests/ui/nav-render.test.ts` (shell `f00d2fc`, web `3c71bf4`).
2. Unknown ids and unavailable playlist slots are dropped without reordering
   the rest. A duplicate slot renders as stored, as on iOS; the user cleans it
   up from the editor (`contracts/nav_layout/README.md`). **Green:** the
   `unknown_future_id`, `deleted_playlist` and `duplicate_slots` cases in
   `tests/ui/nav-render.test.ts`; behavior 1's suite already covers them.
3. `GET /api/layout` returns the stored row for the session's user, returns
   the iOS default when no row exists, and returns 401 without a session.
   **Green:** `tests/layout/handler.test.ts` (web `cc273d3`). The default's
   `updated_at` is the epoch, as in iOS. A malformed row or a database failure
   returns 502 without the data. The user id comes only from the session; a
   client `x-user-uuid` header is ignored. Needs `SUPABASE_ANON_KEY` in the
   server environment (503 without it).
4. A request with no session can't reach `nav_layout` or `curated_stations`
   through the Worker. The browser bundle contains neither the anon key nor
   the user's id. **Partly done:** `/api/layout` and `/api/stations/curated`
   return 401 and make no database call without a session, in unit tests and
   in the local Pages runtime (`tests/pages-runtime.mjs`). A manual scan of the
   built bundle finds no `x-user-uuid`, anon-key, service-role or Supabase
   strings; the scan isn't automated.
5. Wide viewport renders the Sidebar with the Bar line in the right place.
   Narrow viewport renders capacity-5 tabs with More last. **Green:**
   `tests/ui/shell.test.ts`. The breakpoint is 720px (`useNarrow`); capacity is
   5 as in ADR 0005. `/more` lists the rest on a narrow window and redirects on
   a wide one.
6. Each Destination route renders its placeholder. An unknown `/playlist/:uuid`
   shows "This playlist isn't available". **Partly green:** `tests/ui/shell.test.ts`.
   The routes and the unavailable message work against an injected playlist
   list. The real list needs the protobuf playlist client, so until it exists
   the shell passes `null`, shows a generic "Playlist" label and treats every
   playlist slot as available.
7. Focusing the window after a Layout change re-renders the Sidebar without a
   reload, and keeps the selected Destination if it still exists. **Green:**
   `tests/ui/shell.test.ts` (focus and `visibilitychange`; a failed refresh
   keeps the last Layout).
8. `GET /api/stations/curated` returns the seeded rows. **Green:**
   `tests/stations/curated.test.ts` and `tests/stations/database.test.mjs`
   (web `d8f3ac7`, shell `aaf3f72`). The migration
   `supabase/migrations/20261021000009_curated_stations.sql` seeds the iOS
   list in its order; the PGlite test fails if the seed drifts from
   `curated_stations.json`. Client roles can read every row without
   `x-user-uuid` and cannot write. The route sends no user id. Not applied to
   any database yet.

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
- **Questions this must settle:** What does an empty Layout show? Recorded in
  `contracts/nav_layout/README.md`; the answer changes iOS and the fixtures
  together. (Duplicates were settled on 2026-10-18: they render as stored and
  the editor cleans them up.) Should the narrow-window breakpoint follow
  the iPhone's capacity exactly, or allow more tabs on a tablet-width browser?
  (Default: exactly 5, per ADR 0005.)

## Hand-performed interactions

- [ ] Resize the window across the breakpoint — the Sidebar becomes the tab bar and back, keeping the current Destination
- [ ] Click each Sidebar item and the More tab's rows — each opens its own URL and the browser Back button returns
