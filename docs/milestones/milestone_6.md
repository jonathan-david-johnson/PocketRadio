# M6: Streams page cleanup + ICY-only now playing

**Status**: NOT STARTED
**Builds on**: M5.1 (committed at `cf4ef1d`).

## Goal

Clean up the Streams page.
- Go from Stations, Favorites, Browse to just Favorites and Browse.
- Make Streams header work like Up Next / Playlists. Have Favorites and Browse as clickable with a `/` in between.
- Do not need a back button because bottom nav is persistent.
- Strip out any refs for KEXP and KCRW to the tracklist feed URL. Just use ICY metadata from the audio stream.
- Show the station logo (e.g. KCRW: `/Users/jdj/Documents/code/KCRW-Menu-Bar-App/KCRW MenuBar Player/Assets.xcassets/KCRW_logo_black.imageset/logo-kcrw.png`) by default; if/when album art arrives for the current track, show that instead.
- Show bitrate on the station detail screen (e.g. `192 kbps`). Inspired by the OpenCasts player layout but votes are not relevant here — bitrate alone.

Stations of interest: KCRW, KEXP, NPR Hourly News. NPR is already in `curated_stations.json`. BBC World Service deferred to a later milestone. With the Stations tab gone, these three are surfaced by seeding the user's Favorites on first launch for **signed-in users only** — signed-out installs are unsupported in this milestone.

## Done when

- Streams tab shows exactly one nav bar with a `Favorites / Browse` segmented title view (M5.1 pattern). No Stations tab visible.
- Tapping the inactive segment label bolds it, swaps the visible child, and swaps left/right bar buttons.
- `StationDetailViewController`'s Now Playing labels are populated **only** from ICY / in-band timed metadata emitted by AVPlayer on the live stream. No HTTP polling of a side-channel tracklist endpoint. Labels start blank and stay blank until the first metadata frame arrives — no placeholder character.
- `tracklistUrl` is removed from `CuratedStation`, `RadioStation`, and `curated_stations.json`. `parseKCRW`, `parseKEXP`, `pollTracklist`, and `pollTimer` are removed from `StationDetailViewController`.
- Station detail screen shows the station's bitrate below the city/country line. Format: `<B> kbps`. Label hidden when bitrate is nil.
- Station logo image view shows the station logo by default (curated bundled asset for KCRW/KEXP/NPR; favicon URL for radio-browser results). If an album-art URL ever arrives for the currently playing track (future hook — see Risks), the image view swaps to that art. M6 ships with logo-only behavior; the album-art swap path is wired but inactive until a source is plumbed in.
- On first launch with a signed-in user (one-shot UserDefaults flag), KCRW, KEXP, and NPR Hourly News are seeded into Favorites. Signed-out installs: seeder no-ops; the flag is not set so it will run on a future launch once signed in.
- `StationsViewController.swift` is deleted; no references remain.

## Architecture

- **Streams host:** mirror the M5.1 host pattern. New `StreamsHostViewController` rewrite uses `SegmentedTitleView` (from M5.1) as `navigationItem.titleView`, with `Segment` cases `.favorites` and `.browse`. Children added directly to the host's view (no inner `UINavigationController`). Bar buttons routed via `effectiveNavigationItem` (children's `navigationItem.{left,right}BarButtonItem` writes already land on the host). See `AGENTS.md` "In-repo patterns" row: "Two-segment header in the nav bar itself".
- **ICY metadata pipeline:** new `RadioMetadataObserver` class. `AVPlayerItemMetadataOutputPushDelegate`. Attached to `AVPlayerItem` in `DefaultPlayer.play(episode:...)` (after line ~85, where `AVPlayer(playerItem: playerItem)` is created) **only when the episode is a `RadioStation`**. Observer parses `StreamTitle` from `AVMetadataItem.stringValue`, splits on first ` - ` for artist/title, posts `Notification.Name.radioStationNowPlayingDidChange` with `(stationId, title, artist, albumArtURL?)` in `userInfo`. `albumArtURL` is reserved for future use and left nil for now.
- **Detail VC:** `StationDetailViewController` subscribes to `radioStationNowPlayingDidChange` in `viewDidLoad`, unsubscribes in deinit. Updates `trackTitleLabel` / `trackArtistLabel` only when the notification matches the displayed station. Both labels are initialized to empty string and remain blank until the first matching metadata frame arrives.
- **Logo + album art image view:** the existing `logoView` is reused. On `viewDidLoad`, load the station logo (curated bundled asset by `logoAsset` name, or favicon URL for radio-browser stations). On every `radioStationNowPlayingDidChange` notification, if `userInfo["albumArtURL"]` is non-nil, swap the image to the loaded art; if nil, leave the logo in place. (`albumArtURL` source isn't implemented in M6 — placeholder for the future hook.)
- **Bitrate label:** new `UILabel` (`bitrateLabel`) added between the city/country line and the play button on `StationDetailViewController`. Source: `RadioStation.bitrate: Int?` (kbps). Render: `"\(bitrate) kbps"` when present; hidden when nil. Set once in `viewDidLoad` from the station's static metadata — no live updates.
- **Favorites seeding:** new helper `RadioFavoritesSeeder` reads curated entries marked `seedAsFavorite: true` from `curated_stations.json`. Runs at most once per install, gated by `Constants.UserDefaults.radioFavoritesSeeded` (bool flag). Calls `RadioFavoritesManager.shared.addFavorite(stationId:)` for each entry. Invoked from `AppDelegate.application(_:didFinishLaunchingWithOptions:)`. If `SyncManager.isUserLoggedIn()` is false, the seeder returns immediately and does **not** set the flag, so it will try again on the next launch.

## Files

### NEW
- `podcasts/Radio/RadioMetadataObserver.swift` — `AVPlayerItemMetadataOutputPushDelegate`. Parses ICY / in-band ID3 metadata. Filters preroll-ad frames (empty `StreamTitle` or `adw_ad='true'`). Posts notification.
- `podcasts/Radio/RadioFavoritesSeeder.swift` — one-shot first-launch seeder.

### EDIT
- `podcasts/Radio/StreamsHostViewController.swift` — rewrite per M5.1 pattern. Two segments: Favorites, Browse. Drop the segmented control row + container view layout. Install `SegmentedTitleView`.
- `podcasts/DefaultPlayer.swift` — after `player = AVPlayer(playerItem: playerItem)` (~line 85), if `episode is RadioStation`, attach a `RadioMetadataObserver` configured with the station's id. Store the observer in a `DefaultPlayer` instance property so its lifetime matches the player item.
- `podcasts/Radio/StationDetailViewController.swift` — delete `pollTimer`, `pollTracklist()`, `parseKCRW`, `parseKEXP`, `KCRWResponse`, `KEXPResponse`, and any references to `station.tracklistUrl`. Add NotificationCenter observer for `radioStationNowPlayingDidChange`. Add `bitrateLabel` rendered between the city/country line and the play button. Leave Now Playing labels blank on first load.
- `podcasts/Radio/CuratedStation.swift` — drop `tracklistUrl` property. Add `seedAsFavorite: Bool` (default false). Add `bitrate: Int?` (default nil).
- `podcasts/Radio/RadioStation.swift` — drop `tracklistUrl` property if no other consumer remains. Ensure `bitrate: Int?` is populated from radio-browser response (Browse) or curated JSON (curated path).
- `podcasts/Radio/curated_stations.json` — remove `tracklistUrl` keys. Set `seedAsFavorite: true` on KCRW, KEXP, NPR Hourly News. Add `bitrate` for each (KCRW = 192, KEXP = 160, NPR = whatever the stream serves; verify against the `icy-br` response header if uncertain).
- `podcasts/Radio/RadioBrowserAPI.swift` — drop the `tracklistUrl: nil` arg passed to the `RadioStation` initializer if the property is removed. Wire `bitrate` from the radio-browser response into the constructed `RadioStation`.
- `podcasts/AppDelegate.swift` (or wherever post-launch bootstrap runs) — invoke `RadioFavoritesSeeder.seedIfNeeded()` once on launch.
- `podcasts/Constants.swift` — add `radioFavoritesSeeded` UserDefaults key.

### DELETE
- `podcasts/Radio/StationsViewController.swift` — no longer referenced after Streams host rewrite.

### NO CHANGE
- `podcasts/Radio/BrowseViewController.swift`, `podcasts/Radio/FavoritesViewController.swift` — still used as children in the rewritten host.
- `podcasts/Radio/RadioFavoritesManager.swift` — seeder calls the existing `addFavorite(stationId:)` API.
- `podcasts/Main/MainTabBarController.swift` — Streams tab wiring unchanged; only the host VC's internals change.
- `podcasts/PlaylistsHostViewController.swift`, `podcasts/SegmentedTitleView.swift`, `podcasts/Common Components/View Controllers/UIViewController+EffectiveNavigationItem.swift` — M5.1 infrastructure reused as-is.

## Risks / Edge cases

- **iHeart preroll ads.** Frames like `StreamTitle='';adw_ad='true';insertionType='preroll';` precede real track metadata. Filter: ignore frames where `StreamTitle` is empty after stripping quotes, OR where `adw_ad='true'` appears. Real track frames arrive after preroll completes (15–60s).
- **`StreamTitle` format variance.** Common: `Artist - Title`. Sometimes `Title` alone. Sometimes station ID strings ("KCRW 89.9 FM"). Heuristic: split on first ` - `. If no separator, treat full string as title with empty artist. Don't try to be clever.
- **No metadata at all.** Some stations never emit. UI must stay blank, not crash, not retry forever.
- **First-launch seeder + sign-in.** If `SyncManager.isUserLoggedIn()` is false, seeder no-ops and leaves the flag unset so a later launch (once signed in) can complete. If `addFavorite` throws mid-seed, do NOT set the flag for that station; let the next launch retry the missing ones (idempotent on Supabase upsert).
- **`RadioStation` type identity.** `DefaultPlayer.play(episode:)` receives a `BaseEpisode`. The check `if let radio = episode as? RadioStation` must use the concrete class — verify that `PlaybackManager.load(episode:...)` passes the actual `RadioStation` instance.
- **Observer lifetime.** `AVPlayerItemMetadataOutput.setDelegate` holds the delegate weakly. `DefaultPlayer` must retain the `RadioMetadataObserver` for the player item's lifetime and drop it when `player` is replaced or nilled.
- **Album-art swap path is dormant.** No source is plumbed in this milestone. The notification payload includes a nil `albumArtURL` slot; detail VC code handles a non-nil value but never receives one. Avoid wiring an external album-art lookup in M6 — out of scope.
- **Bitrate field accuracy.** `bitrate` on curated stations is hardcoded in JSON. If a station migrates to a different bitrate, the displayed value drifts. For radio-browser stations, `bitrate` comes from the station owner's self-report and is also stale-able. Accept this; do not attempt live measurement via `AVPlayerItemAccessLog`.

## Reference sweep

```bash
grep -rn "tracklistUrl\|parseKCRW\|parseKEXP\|pollTracklist\|StationsViewController" \
  podcasts/ PocketCastsTests/
```

Confirm zero hits before declaring done.

## Automated tests

NEW `PocketCastsTests/Tests/Radio/RadioMetadataObserverTests.swift`
- Parse `StreamTitle='Artist - Track';` → emits notification with `(artist: "Artist", title: "Track")`.
- Parse `StreamTitle='Title only';` → emits `(artist: "", title: "Title only")`.
- Parse `StreamTitle='';adw_ad='true';` → no notification.
- Parse two identical consecutive frames → only one notification (dedupe by last-emitted value).

NEW `PocketCastsTests/Tests/Radio/StreamsHostViewControllerTests.swift`
- Default segment is `.favorites`.
- `selectBrowse()` swaps the visible child to `BrowseViewController`.
- `navigationItem.titleView is SegmentedTitleView`.

NEW `PocketCastsTests/Tests/Radio/RadioFavoritesSeederTests.swift`
- Seeder runs only once when the user is signed in (idempotent via `radioFavoritesSeeded` flag).
- Seeder no-ops when signed out and does NOT set the flag (next launch retries).
- Seeds only curated entries marked `seedAsFavorite: true`.

Edits to existing tests: none expected. M5.1 host tests + Tab tests continue to pass.

## Manual smoke

1. `make run_sim`.
2. Streams tab: confirm single nav bar with `Favorites / Browse` segmented title view. `Favorites` bold by default.
3. Fresh install (wipe sim), signed-in user: confirm KCRW, KEXP, NPR Hourly News appear in Favorites.
4. Fresh install, signed-out user: confirm Favorites is empty and no seeding happened. Sign in. Launch again. Confirm seeding now ran.
5. Tap `Browse` segment: bolding flips, Browse content appears, right bar button (if any) swaps.
6. Tap `Favorites`: reverses cleanly.
7. Tap KCRW from Favorites → detail screen pushes onto outer (tab) nav controller. Logo visible. Bitrate label shows `192 kbps` (or station-stated value).
8. Tap Play → labels remain blank during preroll → metadata arrives after preroll → Now Playing labels populate with Artist + Track text.
9. Tap KEXP → same behavior; bitrate label shows `160 kbps`.
10. Tap NPR Hourly → may or may not emit metadata. UI stays blank, doesn't crash.
11. Network log (Charles Proxy or `xcrun simctl spawn ... log stream`): confirm no HTTP requests to `tracklist-api.kcrw.com` or `api.kexp.org`.
12. Background the app while playing → ICY observer keeps running. Foreground again → labels still match what was last received.

## Agentic plan

Sequential phases. Each agent reads this file as ground truth.

### Phase 1 — Strip tracklist plumbing + add bitrate to model
- Agent: `general-purpose`, model: Sonnet 4.6.
- Files allowed: `podcasts/Radio/StationDetailViewController.swift`, `podcasts/Radio/CuratedStation.swift`, `podcasts/Radio/RadioStation.swift`, `podcasts/Radio/RadioBrowserAPI.swift`, `podcasts/Radio/curated_stations.json`.
- Drop `tracklistUrl` everywhere. Drop `pollTracklist`, `pollTimer`, `parseKCRW`, `parseKEXP`. Leave the `nowPlayingSection` and labels (still rendered, populated by ICY in Phase 2). Add `bitrate: Int?` to model + JSON. Populate from radio-browser response in `RadioBrowserAPI`. Add `bitrateLabel` to detail VC.
- Verify: `make build_staging` succeeds.

### Phase 2 — ICY observer + DefaultPlayer hook
- Agent: `general-purpose`, model: Sonnet 4.6.
- Files allowed: `podcasts/Radio/RadioMetadataObserver.swift` (NEW), `podcasts/DefaultPlayer.swift`, `podcasts/Radio/StationDetailViewController.swift`, `PocketCastsTests/Tests/Radio/RadioMetadataObserverTests.swift` (NEW).
- Detail VC subscribes to `radioStationNowPlayingDidChange`; updates labels only when stationId matches.
- Verify: `make test_staging ONLY_TESTING=PocketCastsTests/RadioMetadataObserverTests` then `make build_staging`.

### Phase 3 — Streams host rewrite (M5.1 pattern)
- Agent: `general-purpose`, model: Sonnet 4.6.
- Files allowed: `podcasts/Radio/StreamsHostViewController.swift`, `PocketCastsTests/Tests/Radio/StreamsHostViewControllerTests.swift` (NEW). Delete `podcasts/Radio/StationsViewController.swift`.
- Verify: `make test_staging ONLY_TESTING=PocketCastsTests/StreamsHostViewControllerTests` then `make build_staging`.

### Phase 4 — Favorites seeder
- Agent: `general-purpose`, model: Sonnet 4.6.
- Files allowed: `podcasts/Radio/RadioFavoritesSeeder.swift` (NEW), `podcasts/Radio/curated_stations.json` (set `seedAsFavorite: true` for KCRW/KEXP/NPR), `podcasts/Constants.swift`, `podcasts/AppDelegate.swift`, `PocketCastsTests/Tests/Radio/RadioFavoritesSeederTests.swift` (NEW).
- Verify: `make test_staging ONLY_TESTING=PocketCastsTests/RadioFavoritesSeederTests` then `make build_staging`.

### Phase 5 — Review
- Agent: `caveman:cavecrew-reviewer`, model: Sonnet 4.6.
- Focus: observer lifetime in `DefaultPlayer`; notification subscribe/unsubscribe in detail VC; seeder idempotency and signed-out branch; reference-sweep cleanup; bitrate label hidden state.

### Phase 6 — Manual smoke
- Human runs Manual smoke list. Sign off before commit.

## Notes

- Probe results from session: curl ICY probe confirmed KCRW + KEXP emit ICY (preroll ads visible in the sample window). Swift macOS AVPlayer probe was inconclusive (macOS CLI doesn't request `Icy-MetaData: 1` the way iOS does). Real validation happens during Phase 6 manual smoke in the sim.
- BBC World Service deferred to a later milestone (HLS metadata path needs separate vetting).
- Album-art swap is wired but dormant — the source needs to be plumbed in a follow-up (Apple Music search, MusicBrainz, etc.). Not in M6 scope.
