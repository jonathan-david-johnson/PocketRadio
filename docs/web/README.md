# PocketRadio Web

PocketRadio's own web player for a Pocket Casts account: podcasts, Up Next,
playlists, and radio Streams with live Track titles and lyrics. Navigation
follows the Layout the user sets on iOS. Terms are defined in
[CONTEXT.md](CONTEXT.md).

## Architecture

| Piece | Where | Decision |
|---|---|---|
| App | Vite + React + TypeScript, React Router, TanStack Query | Our own app, not a fork or extension of Pocket Casts' proprietary web player ([ADR 0001](adr/0001-own-web-player-not-fork-or-extension.md)) |
| Hosting and server code | Cloudflare Pages and Pages Functions, one origin | [ADR 0002](adr/0002-cloudflare-hosts-web-player-supabase-is-database.md) |
| Database | Supabase, the same tables as iOS where data is shared | [ADR 0002](adr/0002-cloudflare-hosts-web-player-supabase-is-database.md) |
| Sign-in | Pairing: approve a QR code in the PocketRadio iOS app | [ADR 0003](adr/0003-sign-in-by-phone-pairing.md) |
| Radio playback | Every station through the Stream relay, which also reports Track titles | [ADR 0004](adr/0004-every-station-plays-through-the-stream-relay.md) |
| Navigation | Sidebar that mirrors the iOS tab settings list, with the Bar line | [ADR 0005](adr/0005-sidebar-mirrors-the-ios-tab-settings-list.md) |
| Tests | Vitest, Wrangler local runtime, Playwright; shared fixtures in `contracts/nav_layout/` | — |

## Security model

Supabase RLS on shared tables trusts the `x-user-uuid` header, and the anon key
is extractable from the iOS binary. So:

- The browser never talks to Supabase or Pocket Casts directly. Workers set
  `x-user-uuid` from the session. The browser holds neither the anon key nor
  the user's id.
- The session is a first-party, httpOnly cookie, rolling 90 days, with
  **Sign out** and **Sign out everywhere**.
- Pocket Casts tokens and sessions live in tables with no anon-key policy.
  Only the Worker reaches them, with the service-role key.
- The Stream relay accepts a station or episode id, never a URL.

## Repo

`pocket-radio-web/` — own git repo (`jonathan-david-johnson/pocket-radio-web`).
Scaffold committed on `main` as `9ea6c56`; M1 experiments live on
`feature/m1-spikes`. Pairing, sessions, JSON probes, and the restricted relay
have local automated coverage. Live approval, deployment, browser cookies,
relay permission, and hour-long playback remain unverified.

The relay uses a SQLite Durable Object deployed by a separate Worker and bound
to Pages. Browser routes stay on the Pages origin. The spike restricts upstreams
to two SomaFM hosts; curated-ID resolution and arbitrary Browse playback are
not implemented. This is a test restriction, not a change to ADR 0004.

## Milestones

| Milestone | What | User checkpoint |
|-----------|------|-----------------|
| [M1](./milestones/milestone_1.md) | Prove pairing, the stream relay, and the Cloudflare deploy *(in progress; live checks pending)* | Pair from the phone, play an `http://` station through the relay, see its title change |
| [M2](./milestones/milestone_2.md) | App shell and navigation from the synced Layout *(planned)* | Sidebar matches the iPhone's tabs and More, with the Bar line |
| [M3](./milestones/milestone_3.md) | Streams, the player, and the installable app *(planned)* | Install, play a favorite, control it from media keys and Now Playing |
| [M4](./milestones/milestone_4.md) | Lyrics for radio Tracks *(planned)* | Lyrics follow KEXP; a nudge survives reload |
| [M5](./milestones/milestone_5.md) | Podcasts, Up Next, and episode playback *(planned)* | Pause on the web, resume on the phone where it stopped |
| [M6](./milestones/milestone_6.md) | Playlists and playlist tabs *(planned)* | New Releases, Tech, and News open as lists or Smart playlist placeholders |
| [M7](./milestones/milestone_7.md) | Edit the Layout from the Sidebar *(planned)* | Reorder on the web; the iPhone's tab bar matches |
| [M8](./milestones/milestone_8.md) | Discover and Profile *(planned; scope open)* | — |

M1–M7 are the first release.

### Later, not yet numbered

- Smart playlist evaluation. Start by checking whether Pocket Casts' own web
  player gets New Releases and In Progress from the server.
- KCRW media-clock alignment: port menubar M12 using HLS program date-time
  (`hls.js` or Safari's native HLS).
- Remote control and presence: a global milestone that moves iOS, the menubar,
  and the web player to private Realtime channels.
- ACRCloud Track identification.
- Chapters, transcripts, bookmarks, starring, archiving.
