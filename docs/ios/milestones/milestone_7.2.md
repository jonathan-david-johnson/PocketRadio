# M7.2: Per-track artwork for enhanced live streams

**Status**: COMPLETED 2026-05-20 — shipped on `pocket-casts-ios` trunk in commit `057cbfb`.
**Builds on**: M7.1 (committed at `dad2b1d`).

## Goal

When a curated, tracklist-enriched live stream (e.g. KCRW Eclectic 24) plays a song, swap the displayed artwork from the station logo to the current track's album/cover art. Apply in three surfaces: main player, mini player, and `MPNowPlayingInfoCenter` (lock screen / Control Center / CarPlay). When no track art is available, fall back to the station logo. Streams with no `tracklistUrl` (NPR, generic radio-browser stations) keep the station logo unchanged.

## Done when

- Playing a KCRW (or any curated station with `tracklistUrl`) shows the current track's artwork in the main player.
- Mini-player artwork matches.
- Lock-screen `MPNowPlayingInfoCenter` artwork matches.
- When the track changes (next ICY metadata tick → new top-of-tracklist), all three surfaces update.
- When the tracklist returns a track with no image URL, the surfaces fall back to the station logo (do NOT keep the previous track's art — stale state risk).
- When the iTunes Search API fallback kicks in (no image from tracklist), the resulting cover art is shown; if iTunes returns nothing, station logo again.
- A station without `tracklistUrl` (e.g. NPR Hourly) keeps the station logo throughout. No tracklist fetch, no iTunes call.
- Image fetches are cached in memory keyed by URL — no re-download every metadata tick.
- No artwork flicker on rapid track changes (debounce or coalesce — confirm by manual smoke).

## Architecture

**Data flow** (in order of preference per track):
1. Tracklist API response (already fetched by `RadioTracklistService`) → does it include an `image` / `image_url` / `artwork_url` field per track? If yes, use it directly.
2. Fallback: iTunes Search API (`https://itunes.apple.com/search?term=<artist+title>&entity=song&limit=1`) → use `artworkUrl100` upgraded to `600x600bb`.
3. Fallback: station logo (`RadioStation.imageAsset` / `imageUrl`).

**New piece**: `TrackArtworkResolver` — single responsibility: given a `TracklistEntry`, return a `UIImage` (or URL) for its artwork via the preference chain. Owns the in-memory cache. Reuses any existing image-loading helper in the app for the actual fetch (don't reinvent).

**Where to bind**:
- Main player + mini player already observe the same item-change / metadata-update notifications from M6. Hook the artwork update into the existing tracklist-tick observer rather than adding a new one.
- `MPNowPlayingInfoCenter`: PlaybackManager already updates `nowPlayingInfo` with `MPMediaItemArtwork`. Add a branch: if `isLiveStream(current)` AND tracklist has a current track AND that track resolves to an image, use the track artwork; else station logo.

**Predicate reuse**: `PlaybackManager.shared.isLiveStream(_:)` already exists from M7.1.

**Curated check**: a station is "enhanced" if `CuratedEnhancement` exists for its UUID — that's where `tracklistUrl` is keyed. Use the existing `CuratedEnhancementsIndex`.

## Files

### NEW

- `podcasts/Radio/TrackArtworkResolver.swift` — given a `TracklistEntry`, returns the artwork URL via tracklist → iTunes → nil chain. Caches by URL. Optional struct/class — keep it small.

### EDIT

- `podcasts/Radio/RadioTracklistService.swift` — extend `KCRWTrack` (and any other source-specific structs) to decode an image URL field if present. Map into `TracklistEntry`. (Check the actual KCRW JSON shape — see Risks below.)
- `podcasts/Radio/TracklistEntry` (wherever defined) — add `imageUrl: URL?` optional field.
- `podcasts/Radio/RadioMetadataObserver.swift` — already emits notifications on metadata change. Verify it fires when the displayed track changes; if not, that's where the trigger goes.
- `podcasts/NowPlayingPlayerItemViewController.swift` (or its `+Update` extension) — subscribe to track-change notification; resolve artwork; set image. Fall back to station logo when nil.
- `podcasts/MiniPlayerViewController.swift` — same subscription + artwork swap.
- `podcasts/PlaybackManager.swift` — `MPNowPlayingInfoCenter` `nowPlayingInfo[MPMediaItemPropertyArtwork]` branch for live streams.

### NO CHANGE

- `podcasts/Radio/curated_stations.json` — no schema change needed.
- `Modules/DataModel/**` — no persistence; artwork is ephemeral, cached in memory only.
- Stations without `tracklistUrl` — code path skips them entirely via the `CuratedEnhancement` check.

## Risks / Edge cases

- **KCRW JSON shape unknown for image field**: before writing the decoder, hit the live endpoint once and confirm whether tracks include an image. If not, jump straight to iTunes Search. Document the shape in a code comment.
- **iTunes Search rate limit**: ~20 req/min unauthenticated. Cache aggressively. If we exceed, fall back to station logo silently — never block playback.
- **Artwork flicker**: `RadioMetadataObserver` may fire spuriously (re-parses on every ICY tick). Coalesce: only swap artwork when artist+title actually change, not on every tick.
- **Slow iTunes lookup blocks UI**: do all network on background queue, dispatch image-set to main. Standard.
- **Track changes between fetch start and finish**: cancel/discard stale fetches. Compare current artist+title against the in-flight request's target before applying.
- **Station logo restore on stop**: when playback ends or item changes to a non-radio episode, the player artwork must reset (M7.1 has the item-change observer hook — extend the same callback).
- **Memory cache unbounded**: cap at N entries (e.g. 50) with LRU eviction. Or `NSCache` — it auto-purges on memory warnings.
- **Image format mismatch**: iTunes returns JPEG; tracklist may return PNG/WebP. `UIImage(data:)` handles all. Don't pre-validate format.

## Reference sweep

```bash
# Existing artwork-loading helpers — reuse, don't reinvent
grep -rn "MPMediaItemArtwork\|nowPlayingInfo\|UIImage(data\|loadImage\|ImageManager\|imageView\.image = " podcasts/ Modules/ | head -40

# Existing tracklist + ICY metadata flow (where the trigger should hook in)
grep -rn "RadioTracklistService\|RadioMetadataObserver\|TracklistEntry\|tracklistUrl" podcasts/ Modules/

# Curated enhancement lookups (the "is this an enhanced station" check)
grep -rn "CuratedEnhancement\|CuratedEnhancementsIndex" podcasts/ Modules/

# Station logo / image binding (the fallback)
grep -rn "RadioStation.*image\|logoAsset\|stationLogo" podcasts/

# Current nowPlayingInfo wiring in PlaybackManager
grep -n "nowPlayingInfo\|MPNowPlayingInfoCenter" podcasts/PlaybackManager.swift
```

## Automated tests

- `PocketCastsTests/Tests/Radio/TrackArtworkResolverTests.swift` (new) — given a `TracklistEntry` with `imageUrl`, returns that URL. Given an entry without one, returns the iTunes-Search-shaped URL. Stub the network layer.
- Decoder test: feed a captured KCRW JSON response with + without image fields, assert `TracklistEntry.imageUrl` populates correctly.
- No UIKit-binding tests — manual smoke covers UI.

## Manual smoke

1. `make run_sim`
2. Play KCRW Eclectic 24 from Favorites.
3. Wait for the first tracklist tick (artist/title appear).
4. Confirm the main player artwork switches from the KCRW logo to the current song's cover art.
5. Confirm the mini player matches.
6. Lock the device — lock-screen art also matches.
7. Wait for the next song. All three surfaces update.
8. Play a track the iTunes API likely lacks (super obscure DJ set / one-off remix). Confirm fallback → KCRW logo, not stale previous art.
9. Switch to NPR Hourly (no `tracklistUrl`). Confirm: artwork stays as NPR logo, no tracklist fetch happens (check console / FileLog).
10. Switch to a regular podcast. Player artwork = podcast episode art (no regression).
11. Re-open KCRW after the podcast. Artwork picks up current track again on first metadata tick.

## Agentic plan

Sequential phases. Each agent reads this file as ground truth.

### Phase 1 — Investigate KCRW JSON shape
- Tool: `Bash` (curl) directly, NOT an agent. Hit `https://tracklist-api.kcrw.com/Music/all/1?page_size=10`, save shape to a code comment in `RadioTracklistService.swift`. Decide: tracklist-provides-image OR iTunes-fallback-only.
- ~5 min of work; cheaper to do inline than spin an agent.

### Phase 2 — Implementation
- Agent: `general-purpose`, model: Sonnet 4.6
- Files allowed: every file in the EDIT list + the new files in the NEW list + the test file. Hard refuse expansion.
- First action: run the Reference sweep grep block; reconcile against the EDIT list before writing code.
- Verify: `make build_staging` + `make test_staging ONLY_TESTING=PocketCastsTests/TrackArtworkResolverTests`.

### Phase 3 — Review
- Agent: `caveman:cavecrew-reviewer`, model: Sonnet 4.6
- Focus:
  - Cancellation: are stale in-flight image fetches discarded on rapid track change?
  - Cache: is the in-memory cache bounded (NSCache or capped LRU)? Unbounded would leak.
  - Fallback chain order: tracklist → iTunes → station logo, exactly. No silent stuck-on-previous-art.
  - Non-enhanced stations: confirm zero network calls, no behavior change.
  - Thread safety: image set on main, fetch off main.
  - Lock-screen `MPMediaItemArtwork` accepts a closure that's called repeatedly — verify lifecycle (no retain cycle on PlaybackManager).

### Phase 4 — Manual smoke
- Human runs the Manual smoke list. Sign off before commit.
