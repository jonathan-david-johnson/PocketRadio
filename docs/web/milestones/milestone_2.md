# Web M2 — App shell and navigation from the synced Layout

**Status**: IN PROGRESS — started 2026-10-18 on `feature/m2-shell-nav`. Behaviors 1–8 are green in local tests (web `dbf7759`). Playlist names come from the protobuf playlist list, which has not yet run against the live Pocket Casts server. The `curated_stations` migration is written but not applied. The web build uses pnpm since web `8e42079`.
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
  derives the Sidebar order and the Bar line index. When no slot is left, it
  renders the default `podcasts, streams, playlists, discover` (web `dbf7759`). Vitest loads
  `../contracts/nav_layout/*.json`.
- **Layout read (`functions/api/layout`).** `GET` returns `{slots, updated_at}`
  from `nav_layout`, using the anon key plus a server-set `x-user-uuid`
  (ADR 0002). With no row, it returns iOS `TabLayout.default`. The client
  re-fetches on window focus and on visibility change. The database is the
  session database unless `SHARED_SUPABASE_URL` and `SHARED_SUPABASE_ANON_KEY`
  name another one. Staging sets them to the main PocketRadio database, which
  the phone writes to; sessions and tokens stay in the staging database (web
  `c22f783`).
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
   the user's id. **Green:** `/api/layout` and `/api/stations/curated`
   return 401 and make no database call without a session, in unit tests and
   in the local Pages runtime (`tests/pages-runtime.mjs`). `make test` builds
   the bundle and fails if it contains `x-user-uuid`, user uuid fields,
   anon-key, service-role, Supabase or `apikey` strings, a JWT, a Supabase API
   key, or the value of a server secret in the environment or `.dev.vars`
   (`tests/bundle-scan.mjs`, web `942ae1d`).
5. Wide viewport renders the Sidebar with the Bar line in the right place.
   Narrow viewport renders capacity-5 tabs with More last. **Green:**
   `tests/ui/shell.test.ts`. The breakpoint is 720px (`useNarrow`); capacity is
   5 as in ADR 0005. `/more` lists the rest on a narrow window and redirects on
   a wide one.
6. Each Destination route renders its placeholder. An unknown `/playlist/:uuid`
   shows "This playlist isn't available". **Green locally:** `tests/ui/shell.test.ts`,
   `tests/playlists/handler.test.ts`, `tests/pocket-casts/protobuf.test.ts` and
   the Pages runtime (web `490b10a`, `007ede8`). `GET /api/playlists` reads
   `user/playlist/list` in protobuf and leaves out deleted playlists; a slot
   whose playlist isn't listed is dropped. The shell reloads the list on focus
   at most every 30 seconds, and at once (one time per set) when the Layout
   names playlists it lacks. **Pending:** one read-only call against the live
   server (ADR 0007): the request sets `m: "mobile"`, and the accepted response
   content types are a guess.
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
- **Questions this must settle:** Settled: duplicates on
  2026-10-18 (they render as stored and the editor cleans them up) and an empty
  Layout on 2026-10-22 (it shows Podcasts, Streams, Playlists, Discover,
  recorded in `contracts/nav_layout/README.md`; iOS still renders `[]` as an
  empty bar until it adopts the fixtures). Should the narrow-window breakpoint follow
  the iPhone's capacity exactly, or allow more tabs on a tablet-width browser?
  (Default: exactly 5, per ADR 0005.)

## Hand-performed interactions

- [ ] Resize the window across the breakpoint — the Sidebar becomes the tab bar and back, keeping the current Destination
- [ ] Click each Sidebar item and the More tab's rows — each opens its own URL and the browser Back button returns
