# PocketRadio

A fork of [Pocket Casts](https://github.com/Automattic/pocket-casts-ios) adding live public radio streaming, podcast listening, and a donation nudge system to support the stations you love.

## What's different from Pocket Casts

- **Radio streams** — curated NPR/public radio stations (KCRW, KEXP, NPR Hourly) + search 90k+ stations via [radio-browser.info](https://radio-browser.info)

## Platforms

| Platform | Status | Language | Code | Docs |
|----------|--------|----------|------|------|
| **iOS** | Fully implemented — used daily | Swift | [`pocket-radio-ios/`](pocket-radio-ios/) | [`docs/ios/`](docs/ios/) |
| **Apple CarPlay** | Fully implemented — used daily | Swift | `pocket-radio-ios/podcasts/CarPlay/` | [`docs/ios/`](docs/ios/) |
| **macOS menubar** | Fully implemented — used daily | Swift / SwiftUI | [`pocket-radio-menubar/`](pocket-radio-menubar/) | [`docs/menubar/`](docs/menubar/) |
| **Roku** (PocketStreams) | Implemented, buggy | BrightScript | [`pocket-radio-roku/`](pocket-radio-roku/) | [`docs/roku/`](docs/roku/) |
| **Console (TUI)** | In progress — playback + radio work, Up Next incomplete | Go | [`pocket-radio-console/`](pocket-radio-console/) | [`docs/console/`](docs/console/) |
| **Windows** | Early — systray player, minimal | Go | [`pocket-radio-windows/`](pocket-radio-windows/) | — |
| **Android** | Planned — docs only, no code | Kotlin | — | [`docs/android/`](docs/android/) |
| **Web** | Planned — repo empty | TS / React | — | [`docs/web/`](docs/web/) |

CarPlay ships inside the iOS app rather than as a separate target — it has no
repo of its own.

Each platform's active task is `docs/<platform>/current_milestone.md` (a symlink
to the live milestone). Build and run targets for all of them: `make help`.

## Curated Stations

| Station | Stream | Donate |
|---------|--------|--------|
| KCRW | Music + NPR news, Santa Monica | [join.kcrw.com](https://join.kcrw.com) |
| KEXP | Music, Seattle | [kexp.org/donate](https://www.kexp.org/donate) |
| NPR Hourly News | Newscast, updated hourly | [npr.org/donations](https://www.npr.org/donations/support) |

Any station from [radio-browser.info](https://radio-browser.info) can be added via Browse.

## License

[Mozilla Public License 2.0](LICENSE.md) — same as upstream Pocket Casts.

Any distributed fork must preserve working donation links from `curated_stations.json` in a visible UI location. See `NOTICE` for details.

## Backend

Radio favorites, listen time, and donation self-reports sync via [Supabase](https://supabase.com). Uses your existing Pocket Casts account as identity — no separate login.

Local dev:
```bash
brew install supabase/tap/supabase
supabase start
```

## Upstream

This project tracks `Automattic/pocket-casts-ios`. To pull upstream changes:
```bash
git fetch upstream
git merge upstream/trunk
```
