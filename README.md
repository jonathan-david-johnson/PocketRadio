# PocketRadio

A fork of [Pocket Casts](https://github.com/Automattic/pocket-casts-ios) adding live public radio streaming, podcast listening, and a donation nudge system to support the stations you love.

This repo is organized as a monorepo shell per the
[`meta-repo`](https://github.com/jonathan-david-johnson/dotfiles/tree/main/.pi/agent/skills/meta-repo)
skill — my standing convention for multi-platform projects: nested repos per
platform, `docs/<platform>/` with milestones and bugs, ADRs.

## What's different from Pocket Casts

- **Radio streams** — curated NPR/public radio stations (KCRW, KEXP, NPR Hourly) + search 90k+ stations via [radio-browser.info](https://radio-browser.info)

## Platforms

| Platform | Status | Language | Code | Docs |
|----------|--------|----------|------|------|
| **iOS** | Fully implemented — used daily. Supports [remote play](#remote-play) | Swift | [`pocket-radio-ios/`](pocket-radio-ios/) | [`docs/ios/`](docs/ios/) |
| **Apple CarPlay** | Fully implemented — used daily | Swift | `pocket-radio-ios/podcasts/CarPlay/` | [`docs/ios/`](docs/ios/) |
| **macOS menubar** | Fully implemented — used daily. Supports [remote play](#remote-play) | Swift / SwiftUI | [`pocket-radio-menubar/`](pocket-radio-menubar/) | [`docs/menubar/`](docs/menubar/) |
| **Roku** (PocketStreams) | Implemented, buggy | BrightScript | [`pocket-radio-roku/`](pocket-radio-roku/) | [`docs/roku/`](docs/roku/) |
| **Console (TUI)** | In progress — playback + radio work, Up Next incomplete | Go | [`pocket-radio-console/`](pocket-radio-console/) | [`docs/console/`](docs/console/) |
| **Android** | Planned — docs only, no code | Kotlin | — | [`docs/android/`](docs/android/) |
| **Web** | Planned — repo empty | TS / React | — | [`docs/web/`](docs/web/) |

CarPlay ships inside the iOS app rather than as a separate target — it has no
repo of its own.

Each platform's active task is `docs/<platform>/current_milestone.md` (a symlink
to the live milestone). Build and run targets for all of them: `make help`.

## Remote Play

Like Spotify Connect: keep listening on one device while controlling it from
another, even when they're on different networks. Pick up your phone and pause
what's playing on the Mac, or push a station from the Mac to your phone.

Devices announce themselves on a shared Supabase Realtime channel scoped to your
Pocket Casts account, then exchange playback commands (`play`, `pause`, `stop`,
`load_station`) over it. There's no pairing step and nothing to configure —
anything signed into the same account finds everything else automatically. Wire
formats live in [`contracts/remote/`](contracts/remote/).

| Platform | Remote play |
|----------|-------------|
| iOS | ✅ |
| macOS menubar | ✅ |
| Apple CarPlay | ✅ — via the iOS app |
| Web | Next up |
| Roku | Planned |
| Console (TUI) | Planned |
| Android | Planned |

Currently one-directional: iOS sends commands and the menubar executes them.
Bidirectional control, a Spotify-style device picker, and "Playing on {device}"
indicators in both players are in progress — see
[`docs/global/current_milestone.md`](docs/global/current_milestone.md).

## Curated Stations

| Station | Stream | Donate |
|---------|--------|--------|
| KCRW | Music + NPR news, Santa Monica | [join.kcrw.com](https://join.kcrw.com) |
| KEXP | Music, Seattle | [kexp.org/donate](https://www.kexp.org/donate) |
| NPR Hourly News | Newscast, updated hourly | [npr.org/donations](https://www.npr.org/donations/support) |

Any station from [radio-browser.info](https://radio-browser.info) can be added via Browse.

## License

[Mozilla Public License 2.0](LICENSE.md).

The iOS app is a fork of Automattic/pocket-casts-ios and stays under MPL 2.0,
inherited from upstream. The menubar, console, and Roku apps are original works,
released under MPL 2.0 for consistency rather than by obligation.

If you fork this project, please keep the donation links from
`curated_stations.json` working and reachable from the UI. That's a request, not
a license condition — see [`NOTICE`](NOTICE).

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
