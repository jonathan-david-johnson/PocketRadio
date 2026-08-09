# iOS M11.1 — Radio-aware CarPlay Now Playing buttons (bug fix)

**Status**: COMPLETED (`86250a5`)
**Depends on**: nothing (M11 umbrella: `milestone_11.md`)
**Parallel-safe with**: M11.2, M11.3, M11.4

---

## Goal

`CarPlaySceneDelegate.updateNowPlayingButtons` builds a podcast-only button set
unconditionally. When a live radio stream is playing, the CarPlay Now Playing
screen currently shows controls that are meaningless — and one that is an active
bug. Branch on live-radio and build a radio-appropriate set instead.

---

## The bug

`podcasts/CarPlay/CarPlaySceneDelegate.swift:127-160` — with a `RadioStation`
loaded, the car screen shows:

| Button | Behavior on radio |
|---|---|
| **Mark as played** | **Live bug.** Fires `EpisodeManager.markAsPlayed` against the SQLite shim that `load()` wrote for the station. Reachable in a car right now — the entitlement is signed and installed. |
| **Playback rate** | A 0.5×–3.0× speed picker on a live stream |
| Chapters | Correctly hidden — `chapterCount() > 0` is false. Accidental, but fine. |
| **Star** | `currentEpisode() as? Episode` returns nil for a radio shim → renders a permanently disabled star |
| Up Next button | `isUpNextButtonEnabled = true`; meaningless for a stream |
| Album/artist button | `nowPlayingTemplateAlbumArtistButtonTapped` matches neither branch → dead tap |

---

## Done when

### 1. Pure button-set builder exists

New file `podcasts/CarPlay/CarPlayNowPlayingButtonSet.swift`.

Per D13, this returns **plain enum cases**, never `CPNowPlayingButton` — so it is
testable without `import CarPlay`.

```swift
/// Which Now Playing buttons CarPlay should show, decided purely from state.
/// Order in the array is the order they appear on screen.
enum CarPlayNowPlayingButtonKind: Equatable {
    // Podcast
    case markAsPlayed
    case playbackRate
    case chapters
    case star(filled: Bool)
    // Radio
    case mute(muted: Bool)
    case favorite(isFavorite: Bool)
}

enum CarPlayNowPlayingButtonSet {
    /// - Parameters:
    ///   - isLiveRadio: `PlaybackManager.isLiveStream()`
    ///   - canMute: `PlaybackManager.shouldUseMuteControls()` — live AND unseekable
    ///   - isMuted: `PlaybackManager.isMuted`
    ///   - isFavorite: cached favorite state for the current station
    ///   - chapterCount: `PlaybackManager.chapterCount()`
    ///   - isStarred: `(currentEpisode() as? Episode)?.keepEpisode == true`
    static func buttons(
        isLiveRadio: Bool,
        canMute: Bool,
        isMuted: Bool,
        isFavorite: Bool,
        chapterCount: Int,
        isStarred: Bool
    ) -> [CarPlayNowPlayingButtonKind]

    /// Whether `CPNowPlayingTemplate.isUpNextButtonEnabled` /
    /// `.isAlbumArtistButtonEnabled` should be on.
    static func showsUpNextButton(isLiveRadio: Bool) -> Bool
    static func showsAlbumArtistButton(isLiveRadio: Bool) -> Bool
}
```

Rules to implement:

- [ ] `isLiveRadio == false` → `[.markAsPlayed, .playbackRate]` + `.chapters` when
      `chapterCount > 0` + `.star(filled: isStarred)`. **Identical to today's
      behavior** — podcasts must not regress.
- [ ] `isLiveRadio == true` → `[.favorite(isFavorite:)]`, prefixed by
      `.mute(muted: isMuted)` **only when `canMute == true`**.
- [ ] `isLiveRadio == true` → never `.markAsPlayed`, never `.playbackRate`,
      never `.star`.
- [ ] `showsUpNextButton` / `showsAlbumArtistButton` → `!isLiveRadio`.

**Why `canMute` gates only the mute button and not the whole radio branch:**
`shouldUseMuteControls` additionally requires the stream be unseekable. NPR Hourly
Newscast resolves to a finite MP3 and legitimately keeps real transport controls —
but mark-as-played and the speed picker are wrong for *any* radio item, seekable
or not. So the **radio branch** keys off `isLiveRadio`; the **mute button** keys
off `canMute`.

### 2. `CarPlaySceneDelegate` consumes the builder

- [ ] `updateNowPlayingButtons(template:)` calls
      `CarPlayNowPlayingButtonSet.buttons(...)` and maps each kind to a
      `CPNowPlayingButton`. The mapping is the only CarPlay-aware code.
- [ ] `.mute` → `CPNowPlayingImageButton` calling
      `PlaybackManager.shared.toggleMute()`. Icon: `speaker.slash.fill` when
      muted, `speaker.wave.2.fill` when not.
- [ ] `.favorite` → `CPNowPlayingImageButton` toggling via
      `RadioFavoritesManager.shared.addFavorite(stationId:)` /
      `.removeFavorite(stationId:)` inside a `Task`. Icon: `heart.fill` /
      `heart`. Best-effort — swallow errors to `FileLog`.
- [ ] Station id for the favorite button comes from
      `PlaybackManager.shared.liveStation(for: nil)?.uuid`. **Never**
      `currentEpisode() as? RadioStation` — that cast always fails post-`load()`.
- [ ] SF Symbols via `UIImage(systemName:)` per D12. Keep existing named assets
      (`car_markasplayed`, `car_chapters`, `star_filled`, `star_empty`) for the
      podcast cases — do not churn working podcast UI.
- [ ] `setupNowPlaying()` and `updateNowPlayingButtons` set
      `isUpNextButtonEnabled` / `isAlbumArtistButtonEnabled` from the builder
      rather than hardcoding `true`.

### 3. Favorite state is read without blocking

`RadioFavoritesManager.isFavorite(stationId:)` is `async` and hits Supabase.
`updateNowPlayingButtons` runs on the main thread and cannot await.

- [ ] Hold a `private var currentStationIsFavorite: Bool` on `CarPlaySceneDelegate`,
      defaulted to `false`.
- [ ] On `playbackTrackChanged` / `playbackStarted`, kick a `Task` that resolves
      `isFavorite` for the new station and, on change, re-calls
      `updateNowPlayingButtons`.
- [ ] After a favorite-button tap, flip the local value optimistically and rebuild
      the buttons immediately, then reconcile when the network call returns.

### 4. Tests

New file `PocketCastsTests/Tests/CarPlay/CarPlayNowPlayingButtonSetTests.swift`
(auto-discovered — no `project.pbxproj` edit needed for test files).

- [ ] `testPodcastButtonsUnchanged` — `isLiveRadio: false, chapterCount: 0` →
      `[.markAsPlayed, .playbackRate, .star(filled: false)]`
- [ ] `testPodcastWithChapters` — `chapterCount: 5` inserts `.chapters` before `.star`
- [ ] `testPodcastStarredReflectsState` — `isStarred: true` → `.star(filled: true)`
- [ ] `testRadioNeverShowsMarkAsPlayed` — `isLiveRadio: true` → result contains no
      `.markAsPlayed` and no `.playbackRate` and no `.star`
- [ ] `testRadioSeekableOmitsMute` — `isLiveRadio: true, canMute: false` →
      `[.favorite(isFavorite: false)]` (the NPR case)
- [ ] `testRadioUnseekableShowsMute` — `isLiveRadio: true, canMute: true, isMuted: true`
      → `[.mute(muted: true), .favorite(isFavorite: false)]`
- [ ] `testUpNextAndAlbumArtistDisabledForRadio` — both helpers return `false` when
      `isLiveRadio: true`, `true` otherwise

---

## Files

| File | Change |
|---|---|
| `podcasts/CarPlay/CarPlayNowPlayingButtonSet.swift` | **new** — needs `project.pbxproj` registration (app-side file) |
| `podcasts/CarPlay/CarPlaySceneDelegate.swift` | edit `setupNowPlaying`, `updateNowPlayingButtons`, `starButton`; add favorite-state tracking |
| `PocketCastsTests/Tests/CarPlay/CarPlayNowPlayingButtonSetTests.swift` | **new** — auto-discovered |

Registering a new app-side file in `project.pbxproj`: mirror an existing peer such
as `podcasts/Radio/StreamsHostViewController.swift`.

---

## Verification

```bash
cd pocket-radio-ios
make format
make build_staging
make test_staging ONLY_TESTING=PocketCastsTests/CarPlayNowPlayingButtonSetTests
```

Manual (Simulator → I/O → External Displays → CarPlay):

1. Play a podcast episode → CarPlay Now Playing shows mark-as-played, speed, star. Unchanged.
2. Play KCRW from the phone → CarPlay Now Playing shows **mute + heart only**.
3. Tap mute → audio silences, connection stays up (no rebuffer on unmute), icon flips.
4. Tap heart → station appears in the phone's Favorites tab.
5. Confirm there is **no** mark-as-played button while radio plays.
6. Play NPR Hourly Newscast → heart shows, mute does **not** (seekable MP3).

---

## Out of scope

- The Radio browse tab (M11.6)
- Suppressing lyric lines in the album field (M11.2)
- Artwork changes (M11.7)

---

## Commit

TBD.
