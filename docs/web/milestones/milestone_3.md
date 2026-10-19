# Web M3 — Streams, the player, and the installable app

**Status**: PLANNED
**Depends on**: Web M1 (direct HTTPS feasibility, Pages plan), Web M2 (shell, `curated_stations`); web ADR 0006
**Required by**: Web M4, M5

## Where the work happens

| | |
|---|---|
| Plan | Shell `main`: this file |
| Code | `pocket-radio-web`, branch `feature/m3-streams-player` from `main` after M2 merges |
| Worktree | `pocket-radio-web/` |
| Shell changes | None expected |

**Goal:** Make Streams work and give the web player its player. Streams shows
Favorites and Browse, as on iOS. HTTPS stations play directly in the browser
(ADR 0006), with HTTP-only entries clearly unsupported and no relay/native
helper. A persistent player bar keeps playing across navigation. Now Playing
shows station information; Track details/tracklists require a supported,
permitted metadata source and must not pretend to observe the audio timeline.
Media keys control playback, and supported browsers can install the web player,
including Chromium-based browsers on Linux.

**User checkpoint:** Install from Chromium on Linux without another package or
helper, and check Safari installation separately on macOS. Open
Streams, play a favorite, and leave the window in the background. Press the
keyboard's play/pause key: it pauses. Control Center's Now Playing shows the
station and any supported metadata. Search Browse for a station, favorite it, and see it in the
iPhone's Streams Favorites.

## Scope

- **Direct resolution/playback.** Harden M1's station-ID lookup; resolve future
  curated IDs from the actual schema and other IDs through radio-browser.
  Return validated public HTTPS URLs without server audio fetches, automatic
  upgrades or relay fallbacks. Keep unsupported HTTP visible in Favorites/Browse.
- **Listener-facing errors.** M1's station errors show developer text, for
  example "Request failed (400). Check server bindings and the experiment
  notes." Replace each with a message a listener can act on.
- **Metadata availability.** No generic ICY/title channel exists. Investigate
  station-supported feeds only with verified permission and CORS. Label feed
  observations separately from audio-aligned Track state; do not infer track
  timing merely by adding the browser's buffered duration to feed arrival.
- **Favorites (`functions/api/favorites`).** List, add, remove, and reorder if
  iOS stores an order, against `radio_favorites`, with the server-set user id.
  Station metadata comes from radio-browser in the browser (CORS allows any
  origin).
- **Streams UI (`src/streams/`).** Favorites and Browse switch, mirroring iOS
  `StreamsHostViewController`. Browse starts with top stations, then searches.
  Favorite toggle on each row.
- **Player (`src/player/`).** One `<audio>` element owned above the router.
  Player bar with artwork, Track or station, and play/pause. Now Playing view
  with station information and optional supported metadata. KCRW/KEXP feeds need
  permission/CORS checks and explicit availability/timing semantics before use;
  port parsing fixtures from iOS `RadioTracklistService`, not timing assumptions.
- **Media Session (`src/player/mediaSession.ts`).** Metadata (station, Track,
  artwork) and play/pause/stop handlers.
- **Installable app.** Web app manifest, icons, and a service worker that
  caches only the app shell. Never caches audio or API responses.

## Behaviors to test (red -> green, one at a time)

1. A validated HTTPS URL is the audio source; no server audio fetch, SSE,
   metadata-only stream or relay fallback occurs. HTTP-only entries explain why
   they cannot play. Stop/switch/sign-out/unmount release the old source.
2. Resolution rejects missing sessions, unknown IDs, URL-shaped input and unsafe
   initial stream addresses; DNS/redirect limitations remain explicit.
3. Unsupported metadata shows station-only information and no lyrics. A station
   change clears old metadata; late feed responses cannot revive it.
4. Favorites add and remove round-trip through the Worker and are visible in a
   direct `radio_favorites` query for that user only.
5. Navigating between Destinations doesn't interrupt playback.
6. Media Session metadata updates on station and Track change; its play/pause
   handlers drive the player.
7. The manifest and service worker pass an installability check (Playwright
   plus a manifest audit), including Chromium on Linux without a helper; the
   service worker never caches/intercepts audio or responds to `/api/*`.
8. KCRW and KEXP tracklist parsers match iOS `RadioTracklistService` on the
   same captured payloads.

## Out of scope

- Lyrics (M4).
- KCRW alignment of the tracklist to the audio, and ACRCloud (later).
- Podcast playback (M5).
- Custom streams (`custom_streams` isn't used by iOS).

## Docs impact

- **Docs this changes or makes stale:** `docs/web/README.md` (features);
  `docs/web/CONTEXT.md` (player terms such as Now Playing, if needed).
- **Questions this must settle:** Does `radio_favorites` carry an order that
  iOS respects? Does the web need it? Which lookup mirror is used on failover?
  Which browsers install on Linux, and which metadata sources are actually
  permitted and available without an audio relay?

## Hand-performed interactions

- [ ] Install from Chrome and from Safari ("Add to Dock") — the app opens in its own window
- [ ] Press the keyboard play/pause key with the window in the background — playback toggles
- [ ] Open system Now Playing — station and available artwork/metadata appear; unsupported Track details are not invented
- [ ] Toggle a favorite in Browse — it appears in Favorites, and on the iPhone after refresh
