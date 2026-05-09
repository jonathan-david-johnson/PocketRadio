# PocketRadio — Plan 2 (MVP: iOS + macOS menubar)

## Vision

Fork of Pocket Casts iOS adding:
- Live radio streams (public radio / NPR focus) via radio-browser.info
- Donation nudge system tied to listen-time
- Lightweight sync backend for radio data, piggybacking PC account identity
- Native SwiftUI macOS menubar app

Android deferred post-MVP.

---

## License

**MPL 2.0** — matches upstream Pocket Casts. File-level copyleft: modified files stay MPL, new files can differ. Add `NOTICE` file requiring donation links preserved in any distributed fork.

---

## Architecture

### Clients

| Client | Base | Notes |
|--------|------|-------|
| iOS | `Automattic/pocket-casts-ios` fork | Swift, UIKit+SwiftUI hybrid |
| macOS menubar | New SwiftUI target in same repo | `NSStatusItem` + `AVFoundation`; no web wrapper |

Pull upstream iOS changes periodically via `git merge upstream/trunk`.

**PocketCastsOSX discarded** — old `WebView` API (deprecated), brittle JS injection into Angular web player. Wrong architecture.

### Backend (PocketRadio sync layer)

PC handles podcast sync. PocketRadio backend handles only radio-specific data.

**Identity**: `ServerSettings.userId` — public `String?` in `UserDefaults`, set on login, cleared on logout. No JWT decode needed.
Located: `Modules/Sources/PocketCastsServer/Public/ServerSettings.swift`

```swift
guard let userId = ServerSettings.userId else { return } // not logged in
// use userId as primary key in all Supabase calls
```

**Prod stack**: Supabase (Postgres + auto REST, free tier).

**Local dev**: Supabase CLI — identical API, no code changes between environments.
```bash
brew install supabase/tap/supabase
supabase init && supabase start  # Postgres on localhost:54322
```
Switch via env var `SUPABASE_URL` / `SUPABASE_ANON_KEY`.

**Schema:**
```sql
radio_favorites (user_uuid, station_id, added_at)
custom_streams  (user_uuid, id, name, url, donate_url, added_at)
donations       (user_uuid, station_id, amount_cents, donated_at)
listen_time     (user_uuid, station_id, seconds, date)
```

### Station Data

- **radio-browser.info API** — 90k+ stations, public domain, no auth required
- **Curated list** (`curated_stations.json` in repo) — hand-picked NPR stations with verified `donate_url`
- Custom streams user-added, stored in PocketRadio backend

---

## Features

### Radio Streams
- Browse/search via radio-browser.info API
- Curated NPR/public radio section (KCRW, WNYC, WBUR, etc.)
- Favorites sync via PocketRadio backend
- Plays inside existing PC player — same queue, same controls
- Each station card shows "Support [Station]" → opens donate URL in browser

### Usage & Donations — see `docs/designs/usage.md`
- Settings screen, passive (no nudge interruptions for MVP)
- Per-station listen-time + estimated cost for radio; listen-time only for podcasts
- Inline self-reported donation field → Supabase `donations` table
- Celebratory support ratio: `total_donated / total_estimated_cost`

### macOS Menubar App
- `NSStatusItem` menubar icon — shows current station + play/pause state
- Dropdown: favorites list, now playing, quick donate link
- Standalone: auth via `userId` + direct Supabase calls (no shared Swift package with iOS for MVP)
- Audio via `AVFoundation` — simpler than full PC playback stack
- Media key support via `MediaPlayer` framework (modern replacement for SPMediaKeyTap)

---

## What NOT to Change (upstream Pocket Casts)
- Podcast sync, subscriptions, episodes — untouched
- Auth flow — untouched (read `ServerSettings.userId`, don't modify)
- Smart rules, filters — leave in (user can ignore)
- Existing UI — extend, don't replace

---

## Key Files to Add/Modify

```
podcasts/
  Radio/
    RadioBrowserAPI.swift           # radio-browser.info client
    RadioFavoritesManager.swift     # read/write PocketRadio Supabase backend
    RadioPlayerIntegration.swift    # hook streams into PC playback queue
    DonationNudgeManager.swift      # listen-time tracking + nudge logic
    ListenTimeTracker.swift         # local accumulation before sync
  Views/Radio/
    RadioBrowseViewController.swift
    RadioStationCell.swift
    DonationNudgeView.swift
    RadioFavoritesView.swift
curated_stations.json               # NPR stations with donate_url
NOTICE                              # donation link preservation requirement

PocketRadioMenubar/                 # new Xcode target (same repo)
  PocketRadioMenubarApp.swift       # NSStatusItem setup
  MenubarPlayerView.swift           # SwiftUI popover
  PocketRadioSyncClient.swift       # Supabase API client
  MenubarAudioPlayer.swift          # AVFoundation stream player

backend/                            # Supabase schema + migrations
  supabase/
    migrations/
      001_initial_schema.sql
    functions/
      upsert_listen_time/index.ts
      get_user_prefs/index.ts
```

---

## Donation Link Enforcement

Each station's `donate_url` embedded in:
1. `curated_stations.json` (data layer — not just UI)
2. `NOTICE` file copyright notice

`NOTICE` states: any distributed fork must preserve working donation links from `curated_stations.json` in visible UI. Removal = license breach.

---

## Open Questions

1. **Donation UX design** — nudge screen layout, payback ratio display, self-report flow TBD
2. **radio-browser.info rate limits** — check before shipping; may need simple cache layer
3. **Upstream merge cadence** — monthly or on major PC releases

---

## Verification

1. Login with PC account → radio tab appears → browse/search stations → play stream in PC player
2. Add favorite → sign out → sign in → favorite present (via Supabase)
3. Listen 1hr → open donation nudge → correct hours + cost estimate shown
4. Self-report donation → payback ratio updates
5. macOS menubar → shows current station → play/pause works → favorites match iOS
6. `supabase start` locally → app hits local DB → swap `SUPABASE_URL` to prod → same behavior
7. Merge upstream PC commit → no conflicts in `Radio/` directory
