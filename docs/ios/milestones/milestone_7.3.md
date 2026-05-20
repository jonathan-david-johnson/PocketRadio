# M7.3: Light/dark theme adaptation for radio surfaces

**Status**: COMPLETED 2026-05-20 — shipped on `pocket-casts-ios` trunk in commit `3a23c22`.
**Builds on**: M7.2 (committed at `057cbfb`).

## Goal

All M5–M7 radio surfaces (Favorites, Browse, Streams host, Station Detail, Tracklist cells, player chrome that shows station logos) render legibly in both light and dark mode. Station logos invert per system appearance — black glyph on light background, white glyph on dark background.

## Done when

- Toggling iOS Appearance (Settings → Display → Light/Dark, or simulator ⌘⇧A) updates all radio screens without restart: backgrounds, separators, primary/secondary text, and station logos all flip.
- KCRW, KEXP, NPR Hourly, and any other curated station logo: black-glyph variant in light mode, white-glyph variant in dark mode.
- Station logos in the **player** (always-dark chrome via `PlayerColorHelper`) use the dark-mode variant regardless of system appearance.
- `StationDetailViewController`, `FavoritesViewController`, `BrowseViewController`, `StreamsHostViewController`, `TracklistCell`, `RadioStationCell` all read legibly in both modes — no hard-coded white/black/grey colours that would invert poorly.
- Player's tracklist icon (`music.note.list` in skipFwdBtn) stays visible against player background in both modes (player is always dark; icon tint = `playerContrast01`).

## Architecture

**Backgrounds + text**: every radio surface already uses semantic UIKit colours (`.systemBackground`, `.secondarySystemBackground`, `.label`, `.secondaryLabel`). Verify none drift to literal colours during this milestone. SwiftUI surfaces (none currently in radio) would use `Color(.systemBackground)`.

**Logos**: Asset Catalog Appearances. Each curated station's `imageset` gets two image entries:
- `Any Appearance` (existing PNG — black glyph).
- `Dark Appearance` (new PNG — white glyph, transparent background).

UIKit picks the right variant based on the resolving `UITraitCollection`. The player view tree already runs `overrideUserInterfaceStyle = .dark` (verify via `PlayerColorHelper` / `themeOverride = .dark` on player VCs), so the player's `episodeImage.image = UIImage(named: asset)` will resolve to the dark variant automatically — no code change in player chrome required. The rest of the app respects system appearance via the default trait.

**Plate around the logo**: `applyRadioBaseArtwork` paints `episodeImage.backgroundColor = .secondarySystemBackground` and `cornerRadius = 12` as a readable plate. In always-dark player chrome, that resolves to a dark plate behind a white-glyph logo. In system-following surfaces (Station Detail header logo), it resolves to a light or dark plate matching mode. Net effect: glyph always contrasts the plate.

Reference: existing app uses Asset Catalog Appearances in `Onboarding.xcassets`, `Appearance.xcassets`, etc. (grep `"appearances"` to see).

## Files

### NEW
- `podcasts/CommonImages.xcassets/kcrw_logo.imageset/logo-kcrw-dark.png` — white-glyph variant.
- `podcasts/CommonImages.xcassets/kexp_logo.imageset/kexp_logo-dark.png` — white-glyph variant.
- `podcasts/CommonImages.xcassets/npr_logo.imageset/npr_logo-dark.png` — white/inverted variant. NPR's logo currently a JPG — convert to PNG with transparent background.
- Any other curated logos missing dark variants — sweep `podcasts/CommonImages.xcassets/*_logo.imageset/`.

### EDIT
- `podcasts/CommonImages.xcassets/kcrw_logo.imageset/Contents.json` — add `appearances: [{appearance: "luminosity", value: "dark"}]` entry for the dark PNG.
- `podcasts/CommonImages.xcassets/kexp_logo.imageset/Contents.json` — same.
- `podcasts/CommonImages.xcassets/npr_logo.imageset/Contents.json` — same (+ change filetype).
- Radio VCs only if hard-coded colours are found during sweep. Default expectation: NO code change needed since current code already uses semantic colours.

### NO CHANGE
- Player chrome (`NowPlayingPlayerItemViewController`, `MiniPlayerViewController`): UIImage(named:) auto-resolves via trait. No code change.
- `PlayerColorHelper`: untouched. Player remains always-dark by design.
- Tab bar icons / system controls — already adapt.

## Risks / Edge cases

- **NPR logo is a JPG with white background, not a transparent PNG**. Light mode looks fine (white-on-white is invisible but the NPR letters show). Dark mode would show a white square. Convert to transparent PNG (both variants) as part of this milestone.
- **MiniPlayer is NOT always-dark** (it sits in the tab bar, inherits system appearance). The station logo in mini player should invert per system. Already covered by Asset Catalog mechanism — no extra code.
- **Lock-screen `MPMediaItemArtwork`**: lock screen is always dark UI. We pass the `UIImage(named: asset)` to `MPMediaItemArtwork.requestHandler` from `NowPlayingHelper.stationLogoImage(for:)`. That call happens with the main app's traitCollection at capture time, NOT the lock screen's. Solution: explicitly resolve the dark variant when handing art to `MPNowPlayingInfoCenter`. Use `image.withConfiguration(image.imageAsset?.image(with: .init(userInterfaceStyle: .dark)))` or simpler: pass `UITraitCollection(userInterfaceStyle: .dark)` to the asset resolution call.
- **Cached track artwork (Kingfisher)** is per-track album art (Spotify CDN / iTunes) — already photographic, doesn't need light/dark variants.
- **TracklistCell row-art for tracks with no album art**: falls back to station logo. Cell sits in StationDetailVC which follows system appearance — already adapts.
- **Curated stations JSON `logoAsset` field** is just a string name; no schema change. The asset catalog handles variant selection by name.

## Reference sweep

```bash
# Confirm radio screens use semantic colours (no literals)
grep -rn "UIColor\.white\|UIColor\.black\|UIColor(red:\|\.systemGray\|#FFFFFF\|#000000" podcasts/Radio/ podcasts/SegmentedTitleView.swift podcasts/PlaylistsHostViewController.swift

# Catalogue every curated station logoAsset that needs a dark variant
grep -n "logoAsset" podcasts/Radio/curated_stations.json

# How existing assets use Appearances (template to mirror)
grep -rln '"appearances"' podcasts/*.xcassets/ | head -5

# Where station logos are read at runtime (verify trait inheritance)
grep -rn "UIImage(named: asset)\|station\.logoAsset" podcasts/
```

## Automated tests

Light/dark rendering is hard to unit-test without snapshot testing (not currently in this project per the test pattern in AGENTS.md). Instead:

- Spot-check via UIKit trait-collection API in a unit test: load `UIImage(named: "kcrw_logo")` with both light and dark `UITraitCollection`, assert the resolved `cgImage` differs (i.e. the asset actually has two variants). Add to `PocketCastsTests/Tests/Radio/StationLogoAppearanceTests.swift` (new file).
- No VC tests — they'd require snapshot infra. Manual smoke covers.

## Manual smoke

1. `make run_sim`
2. Set sim to light mode (⌘⇧A while sim focused, or Settings → Developer → Dark Appearance OFF).
3. Open app → Discover/Streams → Favorites: backgrounds are light. KCRW logo is dark glyph on light background.
4. Tap KCRW → Station Detail: light background; header logo is dark glyph on light plate; tracklist rows readable.
5. Press play → mini player shows dark glyph KCRW logo on light tab bar.
6. Expand to full player → player chrome is always dark → KCRW logo now renders as **white glyph** on dark plate.
7. Lock device → lock-screen artwork: KCRW logo should be the white-glyph variant (lock screen is dark).
8. Switch sim to dark mode (⌘⇧A).
9. Favorites + Station Detail backgrounds become dark; KCRW logo flips to white glyph everywhere.
10. Repeat 4–6 with KEXP and NPR.
11. Tap a tracklist row with album art → confirm album art shows normally (unaffected by appearance).
12. Regression: open a regular podcast episode — player + show notes + chapters all look correct in both modes.

## Agentic plan

Sequential phases. Each agent reads this file as ground truth.

### Phase 1 — Audit + colour-literal sweep
- Agent: `caveman:cavecrew-investigator`, model: Sonnet 4.6
- Run the four greps from the Reference sweep block.
- Output: list of (a) any literal colours found in radio surfaces, (b) every curated `logoAsset` name, (c) one example xcassets `Contents.json` showing the `appearances` format.

### Phase 2 — Dark logo PNGs
- HUMAN task (not agent). Export white-glyph variants from the source logo files (KCRW, KEXP, NPR, any others). Save under existing `*_logo.imageset/` directories. Naming: `<base>-dark.png`.
- Acceptance: each is a transparent-background PNG; visual diff from light variant.

### Phase 3 — Wire Asset Catalog Appearances + lock-screen artwork
- Agent: `general-purpose`, model: Sonnet 4.6
- Files allowed: `podcasts/CommonImages.xcassets/*_logo.imageset/Contents.json` + `podcasts/NowPlayingHelper.swift` (lock-screen trait override).
- Edit Contents.json for each logo: add a second entry with `appearances: [{appearance: "luminosity", value: "dark"}]`.
- In `NowPlayingHelper.stationLogoImage(for:)`, resolve the image against `UITraitCollection(userInterfaceStyle: .dark)` before passing to `MPMediaItemArtwork` (lock screen is always dark).
- Verify: `make build_staging` + `make test_staging`. New `StationLogoAppearanceTests` passes.

### Phase 4 — Code fixes if Phase 1 found any literals
- Agent: `caveman:cavecrew-builder`, model: Sonnet 4.6
- Replace each literal with the closest semantic system colour.

### Phase 5 — Review
- Agent: `caveman:cavecrew-reviewer`, model: Sonnet 4.6
- Focus: no literal colours leak in; every curated logo has both variants; lock-screen artwork uses dark trait; mini player + full player + Station Detail all read the same asset name and let UIKit pick the variant.

### Phase 6 — Manual smoke
- Human runs Manual smoke list. Sign off before commit.
