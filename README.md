# PocketRadio

A fork of [Pocket Casts](https://github.com/Automattic/pocket-casts-ios) adding live public radio streaming, podcast listening, and a donation nudge system to support the stations you love.

## What's different from Pocket Casts

- **Radio streams** — curated NPR/public radio stations (KCRW, KEXP, NPR Hourly) + search 90k+ stations via [radio-browser.info](https://radio-browser.info)
- **Usage & Donations** — see how much you've listened per station, estimated streaming cost, and track your donations back to stations
- **macOS menubar app** — native SwiftUI menubar player for your favorite streams
- **Open source, no ads, no tracking**

## Supported stations (curated)

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

## Plans & Design

- [`docs/plan.md`](docs/plan.md) — current plan
- [`docs/designs/`](docs/designs/) — UI and feature designs

## Upstream

This project tracks `Automattic/pocket-casts-ios`. To pull upstream changes:
```bash
git fetch upstream
git merge upstream/trunk
```
