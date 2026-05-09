# PocketRadio — Milestones

## M1: Player Integration Proof

**Goal**: A hardcoded KCRW stream plays inside PC's existing player with no crashes.
No UI, no Supabase, no navigation changes. Just audio.

**Done when**:
- `RadioStation("kcrw", streamUrl: "https://streams.kcrw.com/e24_mp3")` conforms to `BaseEpisode`
- `PlaybackManager.shared.load(episode: station, autoPlay: true)` starts audio
- Mini player appears, shows "KCRW", play/pause works
- Backgrounding the app → audio continues
- No crashes, no "urlForEpisode returned nil" failure

**What to build**:
1. `podcasts/Radio/RadioStation.swift` — BaseEpisode conformer (see `docs/designs/player_integration.md`)
2. Patch `podcasts/EpisodeManager.swift` — add RadioStation URL fallback
3. Test harness: a temporary button in `ProfileViewController` (or anywhere) that calls `playStation(kcrw)`

**What NOT to build yet**: nav, Supabase, UI, tracklist.

**Risk resolved**: PC's `urlForEpisode` returns nil for unknown `BaseEpisode` types. M1 patch + `sizeInBytes = Int64.max` for cache-skip is the solution. Everything else follows from this working.

---

## M2: Streams Tab + Station List

**Goal**: Streams tab appears in tab bar. Curated stations listed. Tapping plays (via M1).

**Done when**:
- Streams tab visible in PC tab bar
- KCRW, KEXP, NPR Hourly listed as station cards
- Tap card → Station Detail with Play button
- Play → audio starts (M1 player)
- Donate button → opens donate URL in Safari

**What to build**:
- `pcTabs` change in `MainTabBarController.swift` + `PCTab` enum
- `StreamsHostViewController` (segmented control host)
- `StationsViewController` (curated list)
- `RadioStationCell` (logo + name + location)
- `StationDetailViewController` (play, favorite stub, donate)
- `CuratedStationsLoader` (parse `curated_stations.json`)

---

## M3: Supabase + Favorites

**Goal**: Favorites persist to Supabase. Favorites tab populated.

**Done when**:
- Heart button on Station Detail saves/removes favorite
- Favorites tab shows saved stations
- Sign out → sign in → favorites still present (Supabase-backed)
- Swipe-to-delete on Favorites tab works

**What to build**:
- Add Supabase Swift SDK via SPM
- `SupabaseClient.swift` init (see `docs/designs/supabase_client.md`)
- `RadioFavoritesManager.swift`
- `FavoritesViewController`
- Heart button state in `StationDetailViewController`

---

## M4: Browse Tab

**Goal**: Search 90k+ stations via radio-browser.info. Play any result.

**Done when**:
- Browse tab shows top-100 stations by default
- Search returns results within 500ms (debounced 300ms)
- Tap result → Station Detail (play, favorite)
- Favorite a browse station → appears in Favorites tab

**What to build**:
- `RadioBrowserAPI.swift`
- `BrowseViewController`
- Favicon loading + cache

---

## M5: Listen Time + Usage Screen

**Goal**: Usage & Donations screen shows accurate listen time and supports donation self-reporting.

**Done when**:
- Listen time accumulates while streaming
- Usage & Donations screen shows per-station hours + estimated cost
- Inline donation amount saves to Supabase
- Support ratio displays

**What to build**:
- `ListenTimeTracker.swift`
- `UsageDonationsViewController`
- Donation input + Supabase write

---

## M6: macOS Menubar App

**Goal**: Standalone menubar app plays favorites, shows now-playing track.

**Done when**:
- Menubar icon appears
- Click → popover with favorites list
- Tap station → stream plays via AVPlayer
- KCRW/KEXP show current track title
- Media keys (play/pause) work

**What to build**: everything in `PocketRadioMenubar/` (see `docs/designs/menubar.md`)

---

## Post-MVP

- Widgets (WidgetKit)
- Ad-skip via SponsorBlock (podcast side)
- Shared Swift package (iOS + macOS code share)
- Android
