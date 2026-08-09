# iOS M11.7 — Artwork: non-curated baseline + favicon prefetch

**Status**: COMPLETED — ff0bce8
**Depends on**: M11.4, M11.6

---

## Goal

Stop showing a grey podcast placeholder on the car display for non-curated
stations, and put real logos in the CarPlay Radio list rows.

---

## What already works (verify, don't rebuild)

Per-track album artwork **already reaches CarPlay**. It is published by
`PlaybackManager`, not by any view controller:

`PlaybackManager.swift:99-104` (observers on the app-lifetime singleton) →
`handleRadioTrackChanged` / `handleRadioTracklistRefreshed` →
`resolveRadioArtworkForLockScreen` → `NowPlayingHelper.setArtworkImage`.

CarPlay's `CPNowPlayingTemplate` reads the same `MPNowPlayingInfoCenter` as the
lock screen, so phone screen state is irrelevant. **No work needed — confirm it
on a car display and record the result.**

---

## The two real gaps

### Gap 1 — per-track art is gated on a curated `tracklistUrl`

`resolveRadioArtworkForLockScreen` (`PlaybackManager.swift:459`) early-returns
unless `CuratedStationsLoader.enhancementsByUUID[stationId]?.tracklistUrl != nil`.

Of the 3 curated stations, only **KCRW** and **KEXP** have one. NPR Hourly
Newscast's is `null`, and arbitrary radio-browser favorites have no enhancement at
all. Correct as designed — no tracklist means no track to resolve art for.

### Gap 2 — non-curated stations show the podcast placeholder

Baseline artwork comes from `NowPlayingHelper.stationLogoImage(for:)`
(`NowPlayingHelper.swift:74`), which returns nil without a `logoAsset`, falling
through to `UIImage(named: "noartwork-page")!` — a podcast-shaped grey square,
rendered full-screen on a car display.

Since M11.4, `CachedFavoriteStation.faviconUrl` is available. Use it.

---

## Done when

### 1. Baseline Now Playing artwork for non-curated stations

- [ ] New `RadioArtworkSource` (in `podcasts/Radio/RadioArtworkSource.swift`) — a
      pure resolver:
      ```swift
      enum RadioArtworkSource: Equatable {
          case bundleAsset(String)   // curated logoAsset
          case remote(URL)           // radio-browser favicon
          case placeholder           // neither available
      }

      extension RadioArtworkSource {
          static func resolve(logoAsset: String?, faviconUrl: String?) -> RadioArtworkSource
      }
      ```
- [ ] Precedence: `bundleAsset` > `remote` > `placeholder`. Curated art is
      hand-picked and always beats a scraped favicon.
- [ ] Treat empty strings as absent — radio-browser returns `""` for a missing
      favicon, not null (see `FavoriteRow.faviconUrl` in
      `FavoritesViewController.swift:20`, which already guards this).
- [ ] Reject non-`http(s)` and unparseable favicon URLs → `.placeholder`.
- [ ] `NowPlayingHelper.setAllNowPlayingInfo`'s live-radio branch
      (`NowPlayingHelper.swift:47-56`) uses the resolver. For `.remote`, set the
      placeholder synchronously, then fetch via `KingfisherManager.shared` into
      `ImageManager.sharedManager.radioAlbumArtCache` and call
      `NowPlayingHelper.setArtworkImage(image)` on the main thread when it lands.
- [ ] Guard the async swap the way `resolveRadioArtworkForLockScreen` does: bail if
      `currentEpisode()?.uuid` has changed since the fetch started. Otherwise a fast
      station switch paints the wrong logo.
- [ ] Favicon URL for the currently-playing station comes from
      `RadioFavoritesCache.shared.snapshot()`. Not a favorite and not curated →
      `.placeholder`. Do not add a network lookup on the playback path.

### 2. Favicon artwork in CarPlay list rows

- [ ] `RadioFavoritesService.resolvedFavorites()` prefetches favicons into
      `CarPlayImageHelper.imageCache` — **only while
      `CarPlaySceneDelegate.isConnected` is true** (M11.2's flag). No point warming a
      CarPlay-sized cache when no car is attached.
- [ ] New `CarPlayImageHelper.imageForStation(logoAsset:faviconUrl:) -> UIImage`,
      mirroring the existing `imageForPodcast` shape: check
      `cachedImage(for:maxSize:)`, else bundle asset, else placeholder. **Stays
      synchronous** — it must never download inline.
- [ ] Cache key: `"station_\(stationId)"`, matching the existing
      `"\(key)_\(maxSize.width)"` convention.
- [ ] M11.6's adapter switches to `imageForStation`.
- [ ] After a prefetch batch completes, post `.radioFavoritesChanged` so the
      already-wired observer reloads the template and rows pick up the new art.
      No new notification.
- [ ] Placeholder stays SF Symbol `dot.radiowaves.left.and.right`.

Expect partial payoff: radio-browser favicons are frequently 16×16 or dead links.
That is fine — `.placeholder` is a correct outcome, not a failure.

### 3. Tests

New file `PocketCastsTests/Tests/Radio/RadioArtworkSourceTests.swift`. Pure.

- [ ] `testBundleAssetWinsOverFavicon` — both present → `.bundleAsset`
- [ ] `testFaviconUsedWhenNoLogoAsset`
- [ ] `testPlaceholderWhenNeitherPresent`
- [ ] `testEmptyStringsTreatedAsAbsent` — `logoAsset: ""`, `faviconUrl: ""` →
      `.placeholder`
- [ ] `testWhitespaceOnlyFaviconTreatedAsAbsent`
- [ ] `testInvalidFaviconUrlFallsBackToPlaceholder` — `"not a url"`
- [ ] `testNonHttpSchemeRejected` — `"ftp://example.com/f.ico"` → `.placeholder`
- [ ] `testHttpsFaviconAccepted`

---

## Files

| File | Change |
|---|---|
| `podcasts/Radio/RadioArtworkSource.swift` | **new** — needs `project.pbxproj` registration |
| `podcasts/NowPlayingHelper.swift` | live-radio branch uses the resolver + async remote swap |
| `podcasts/CarPlay/CarPlayImageHelper.swift` | add `imageForStation(logoAsset:faviconUrl:)` |
| `podcasts/CarPlay/CarPlaySceneDelegate+Radio.swift` | adapter uses `imageForStation` |
| `podcasts/Radio/RadioFavoritesService.swift` | favicon prefetch when CarPlay connected |
| `PocketCastsTests/Tests/Radio/RadioArtworkSourceTests.swift` | **new** — auto-discovered |

---

## Verification

```bash
cd pocket-radio-ios
make format
make build_staging
make test_staging ONLY_TESTING=PocketCastsTests/RadioArtworkSourceTests
```

Manual — **Simulator → I/O → External Displays → CarPlay**:

1. Play KCRW → CarPlay Now Playing shows the **KCRW logo**, then swaps to
   **per-track album art** when a tracklist tick resolves one (confirms the
   already-working M7.2 path on a car display — record the result)
2. Play NPR Hourly Newscast → NPR logo, no per-track art (expected — no `tracklistUrl`)
3. Favorite an arbitrary radio-browser station on the phone, play it in CarPlay →
   shows its **favicon**, or the radio-waves placeholder. **Never** the grey podcast
   square.
4. Radio tab list → curated rows show their logos; favorite rows show favicons once
   prefetched
5. Switch stations rapidly → artwork never shows the previous station's logo

Also closes the never-run manual check from `milestone_7.1.md` step 11 ("CarPlay:
confirm radio shows stop, not skip"):

6. While radio plays, confirm CarPlay transport shows **stop**, not skip-forward /
   skip-back. Record the outcome in `milestone_7.1.md`.

---

## Out of scope

- Extending per-track artwork to stations without a curated `tracklistUrl` — that
  needs a tracklist source, not an artwork change
- Disk-caching favicons into the App Group for the widget
- Replacing `noartwork-page` for podcasts

---

## Two corrections to the plan, found during implementation

**1. SF Symbol placeholder crashed CarPlay.** `CarPlayImageHelper.imageForStation`
originally ran the radio-waves placeholder through the same
`UIImageAsset`-registration + resize pipeline as raster art. `UIImageAsset.image(with:)`
hands back a zero-size image for a symbol, which NaNs out `resizeProportionally`
(`0 * .infinity`) and crashes `UIGraphicsBeginImageContextWithOptions`. Even after
guarding the zero-size case, the processed symbol image didn't survive the XPC
round-trip to CarPlay's out-of-process render host (`Could not cast ... to
UIImage`). Fix: the placeholder is returned unprocessed, exactly like the tab
bar icon and M11.6's inline fallback already did.

**2. CarPlay's Radio tab dropped the curated "Stations" section entirely**,
collapsing to a single Favorites list. Curated stations (KCRW, KEXP, NPR) reach
the list the same way any station does — by being favorited — with their
logo/name/tracklist enhancement merged in by UUID (`RadioFavoritesService`,
unchanged). `RadioCarPlayRowBuilder.sections()` dropped its `curated` parameter;
`RadioCarPlayRouting.needsResolution` stays, since a favorited curated station
can still land with an empty `streamUrl` if radio-browser metadata fails to
resolve.

## Commit

`ff0bce8` — feat(carplay): M11.7 — Radio artwork + single favorites list
