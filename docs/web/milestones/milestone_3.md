# Web M3 — Streams, the player, and the installable app

**Status**: PLANNED
**Depends on**: Web M1 (relay feasibility, Cloudflare plan), Web M2 (shell, `curated_stations`); web ADR 0004
**Required by**: Web M4, M5

## Where the work happens

| | |
|---|---|
| Plan | Shell `main`: this file |
| Code | `pocket-radio-web`, branch `feature/m3-streams-player` from `main` after M2 merges |
| Worktree | `pocket-radio-web/` |
| Shell changes | None expected |

**Goal:** Make Streams work and give the web player its player. Streams shows
Favorites and Browse, as on iOS. Every station plays through the stream relay
(ADR 0004), which also supplies live Track titles. A persistent player bar
keeps playing across navigation. A Now Playing view shows the current Track
and, for KCRW and KEXP, the station tracklist. Media keys and macOS Now Playing
control playback, and the browser can install the web player as an app.

**User checkpoint:** Install the web player from Chrome or Safari. Open
Streams, play a favorite, and leave the window in the background. Press the
keyboard's play/pause key: it pauses. Control Center's Now Playing shows the
station and Track. Search Browse for a station, favorite it, and see it in the
iPhone's Streams Favorites.

## Scope

- **Relay (`functions/api/relay/`).** Hardens the M1 spike. Takes a station
  id, never a URL. Resolves curated ids from `curated_stations` and other ids
  through radio-browser by UUID. Requires a session. Strips ICY metadata
  blocks, and sends titles with the relay's byte position over Server-Sent
  Events on a paired channel.
- **Track timing (`src/player/trackClock.ts`).** Applies a received title
  when the listener reaches it: `now + (audio.buffered.end − audio.currentTime)`
  at receipt.
- **Favorites (`functions/api/favorites`).** List, add, remove, and reorder if
  iOS stores an order, against `radio_favorites`, with the server-set user id.
  Station metadata comes from radio-browser in the browser (CORS allows any
  origin).
- **Streams UI (`src/streams/`).** Favorites and Browse switch, mirroring iOS
  `StreamsHostViewController`. Browse starts with top stations, then searches.
  Favorite toggle on each row.
- **Player (`src/player/`).** One `<audio>` element owned above the router.
  Player bar with artwork, Track or station, and play/pause. Now Playing view
  with the Track and the KCRW/KEXP tracklist, fetched from the browser (CORS
  allows any origin). Port the parsing from iOS `RadioTracklistService`.
- **Media Session (`src/player/mediaSession.ts`).** Metadata (station, Track,
  artwork) and play/pause/stop handlers.
- **Installable app.** Web app manifest, icons, and a service worker that
  caches only the app shell. Never caches audio or API responses.

## Behaviors to test (red -> green, one at a time)

1. ICY stripping: a fixture stream with known `icy-metaint` produces the exact
   audio bytes and the titles in order, including a metadata block split
   across chunks.
2. The relay rejects a request without a session, an unknown station id, and
   any URL-shaped id.
3. A title received with N seconds buffered is applied N seconds later; a
   newer title cancels a pending older one; a station change clears pending
   titles.
4. Favorites add and remove round-trip through the Worker and are visible in a
   direct `radio_favorites` query for that user only.
5. Navigating between Destinations doesn't interrupt playback.
6. Media Session metadata updates on station and Track change; its play/pause
   handlers drive the player.
7. The manifest and service worker pass an installability check (Playwright
   plus a manifest audit); the service worker never responds to `/api/*`.
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
  iOS respects? Does the web need it? Which radio-browser mirror does the
  relay use, and what happens on failover?

## Hand-performed interactions

- [ ] Install from Chrome and from Safari ("Add to Dock") — the app opens in its own window
- [ ] Press the keyboard play/pause key with the window in the background — playback toggles
- [ ] Open Control Center Now Playing — station, Track, and artwork appear and its controls work
- [ ] Toggle a favorite in Browse — it appears in Favorites, and on the iPhone after refresh
