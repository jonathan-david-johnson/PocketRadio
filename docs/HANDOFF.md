# PocketRadio — Handoff Document

## What this is

**PocketRadio** — fork of `Automattic/pocket-casts-ios` adding:
- Live public radio streaming (KCRW, KEXP, NPR Hourly + 90k via radio-browser.info)
- Usage & Donations screen (listen-time tracking, self-reported donations, payback ratio)
- macOS menubar app (native SwiftUI, AVFoundation)
- Lightweight Supabase backend for radio-specific sync

Podcast functionality from Pocket Casts is **untouched**. We extend, not replace.

---

## Repo

**GitHub**: https://github.com/jonathan-david-johnson/PocketRadio  
**Local**: `/Users/jdj/Documents/code/PocketRadio`

Reference repos (local only, gitignored):
- `/Users/jdj/Documents/code/PocketRadio/other_apps/pocketcasts/pocket-casts-ios` — upstream source
- `/Users/jdj/Documents/code/PocketRadio/other_apps/KCRW-Menu-Bar-App` — prior art, has KCRW + KEXP stream URLs and tracklist API research

---

## What's done

- [x] Design docs: `docs/designs/navigation.md`, `station.md`, `usage.md`
- [x] Plan: `docs/plans/plan_2.md` (symlinked at `docs/plan.md`)
- [x] Supabase project created, linked, schema migrated to prod
- [x] `supabase/migrations/20260509000001_initial_schema.sql` — 4 tables live
- [x] `curated_stations.json` — KCRW, KEXP, NPR Hourly with stream URLs + donate URLs
- [x] Git repo initialized, pushed, history clean (no secrets)

## What's NOT done (next steps in order)

1. **Add Supabase Swift SDK** to `pocket-casts-ios` fork via SPM
2. **Fork pocket-casts-ios** into this repo (or add as upstream remote)
3. **Navigation** — add Home nav (Podcasts / Streams / Profile) and Streams world (Stations / Favorites / Browse tabs)
4. **RadioBrowserAPI.swift** — client for radio-browser.info
5. **Station list + detail screens** — per `docs/designs/station.md`
6. **RadioFavoritesManager.swift** — read/write Supabase
7. **ListenTimeTracker.swift** — accumulate + sync listen time
8. **Usage & Donations screen** — per `docs/designs/usage.md`
9. **macOS menubar target** — SwiftUI NSStatusItem app
10. **NOTICE file** — donation link preservation requirement

---

## Key decisions made

**License**: MPL 2.0 (matches upstream PC). Donation URLs embedded in `curated_stations.json` + NOTICE file — removal = license breach.

**Identity**: `ServerSettings.userId` (`String?`, `UserDefaults`) from PC iOS.  
File: `Modules/Sources/PocketCastsServer/Public/ServerSettings.swift`  
```swift
guard let userId = ServerSettings.userId else { return }
```

**Navigation pattern**: Contextual bottom nav.
- Home: `[ Podcasts ] [ Streams ] [ Profile ]`
- Podcasts world: `[ ← ] [ Podcasts ] [ Playlists ] [ Discover ] [ Up Next ]`
- Streams world: `[ ← ] [ Stations ] [ Favorites ] [ Browse ]`
- Mini player floats above nav in all states. Streams never enter Up Next queue.

**Streams do not go in Up Next** — live radio has no end, no queue position.

**Station card** = static (logo + name + location only, no live data). Live data loads on Station Detail only.

**Tracklist APIs**:
- KCRW: `https://tracklist-api.kcrw.com/Music/all/1?page_size=10`
- KEXP: `https://api.kexp.org/v2/plays/?limit=10` (filter `play_type == "trackplay"`)
- NPR Hourly: no tracklist API — show "Live News" label

**macOS menubar**: fresh SwiftUI `NSStatusItem` target — NOT based on PocketCastsOSX (deprecated WebView, broken JS hooks, discarded).

**Backend**: Supabase. Local dev via `supabase start` (Docker required). Swap via `SUPABASE_URL` env var.

**Multi-agent / multi-context**: Implementation phase should use parallel agents once specs are tight. Design phase (done) was linear.

---

## Supabase schema (prod + local)

```sql
radio_favorites (user_uuid, station_id, added_at)
custom_streams  (user_uuid, id, name, url, donate_url, added_at)
donations       (user_uuid, station_id, amount_cents, donated_at)
listen_time     (user_uuid, station_id, seconds, date)
```

RLS enabled on all tables. Policy: `user_uuid = current_setting('app.user_uuid', true)`.

---

## Curated stations

See `curated_stations.json`. Three stations for MVP:

| ID | Name | Stream | Donate |
|----|------|--------|--------|
| `kcrw` | KCRW | `https://streams.kcrw.com/e24_mp3` | https://join.kcrw.com |
| `kexp` | KEXP | `https://kexp.streamguys1.com/kexp160.aac` | https://www.kexp.org/donate |
| `npr_hourly` | NPR Hourly News | `http://pd.npr.org/anon.npr-mp3/npr/news/newscast.mp3` | https://www.npr.org/donations/support |

---

## Market context

- **Closest competitor**: OpenTune (iOS only, partially proprietary, no donate links, no widgets)
- **Gap we fill**: open-source, cross-platform, donation-aware, widgets planned
- **Podcast base**: Pocket Casts (MPL 2.0, Automattic) — industry standard, CarPlay, Watch, widgets already built
- **Station database**: radio-browser.info — 90k+ stations, public domain, no API key

---

## Prior art in repo

`/Users/jdj/Documents/code/KCRW-Menu-Bar-App` — owner's own prior macOS menubar app for KCRW/KEXP. Contains:
- Verified stream URLs for KCRW + KEXP
- KEXP API research (`KEXP.md`) — field mapping, pagination, `play_type` filter
- `KCRWSong` + `KEXPSong` models — reusable as reference
- `Webservice.swift` — basic URLSession fetch pattern
