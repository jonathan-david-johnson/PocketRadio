# PocketRadio Web

PocketRadio's own web player for a Pocket Casts account: podcasts, Up Next,
playlists, and radio Streams with direct HTTPS playback. Track titles and
lyrics require a separate, permitted metadata source and are not generic
playback capabilities. Navigation
follows the Layout the user sets on iOS. Terms are defined in
[CONTEXT.md](CONTEXT.md).

## Architecture

| Piece | Where | Decision |
|---|---|---|
| App | Vite + React + TypeScript, React Router, TanStack Query | Our own app, not a fork or extension of Pocket Casts' proprietary web player ([ADR 0001](adr/0001-own-web-player-not-fork-or-extension.md)) |
| Hosting and server code | Cloudflare Pages and Pages Functions, one origin | [ADR 0002](adr/0002-cloudflare-hosts-web-player-supabase-is-database.md) |
| Database | Supabase, the same tables as iOS where data is shared | [ADR 0002](adr/0002-cloudflare-hosts-web-player-supabase-is-database.md) |
| Sign-in | Pairing: approve a QR code in the PocketRadio iOS app | [ADR 0003](adr/0003-sign-in-by-phone-pairing.md) |
| Radio playback | Station → browser over HTTPS; no audio relay/native helper; HTTP-only and generic ICY titles unavailable | [ADR 0006](adr/0006-direct-https-playback-without-an-audio-relay.md), superseding ADR 0004 |
| Pocket Casts data | Functions speak protobuf to the Pocket Casts server; the browser gets JSON from us | [ADR 0007](adr/0007-protobuf-for-pocket-casts-account-data.md) |
| Navigation | Sidebar that mirrors the iOS tab settings list, with the Bar line | [ADR 0005](adr/0005-sidebar-mirrors-the-ios-tab-settings-list.md) |
| Tests | Vitest, Wrangler local runtime, Playwright; shared fixtures in `contracts/nav_layout/` | — |

How the pieces communicate, with a diagram: [architecture/communication.md](architecture/communication.md). The Pocket Casts calls: [architecture/pocket-casts-api.md](architecture/pocket-casts-api.md). Staging and deploying: [architecture/deployment.md](architecture/deployment.md).

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
- Station resolution accepts an ID, never a client URL. The server validates
  a bounded fixed metadata lookup but never opens station audio. The browser
  receives the public HTTPS URL; initial URL checks do not pin DNS/redirects.
- The station sees the listener's IP. Suppress the app referrer and never attach
  Pocket Casts/database credentials to media requests. Local sign-out stops
  audio; a public station URL in another browser is not revocable.

## Repo

`pocket-radio-web/` — own git repo (`jonathan-david-johnson/pocket-radio-web`).
M1 is merged into its `main` (Pairing, sessions, direct HTTPS playback). M2 is
on `feature/m2-shell-nav`. A private staging Pages project
(`pocket-radio-web-m1-staging`) runs behind email-only Cloudflare Access with a
separate Free staging database; see [deployment](architecture/deployment.md).
What M1 verified, and how, is in
[Verified in M1](architecture/communication.md#verified-in-m1).

Normal build/dev/Pages configuration has no relay Worker or Durable Object. The
four old relay routes return 410. The relay's source and tests were deleted;
its SQL tables remain in the applied migration. The authenticated station
resolver uses radio-browser UUIDs; `curated_stations` and the finished Streams
UI remain future work.

## Known risks after M1

M1's checks were mostly user-reported, with no browser versions recorded; see
[Verified in M1](architecture/communication.md#verified-in-m1). Still untested:

- Production `.com` Pairing, and the web UUID matching iOS's on `.com`. On
  staging (`.net`) the two matched after a phone sign-out and sign-in fixed a
  stale cached id (M2, 2026-10-23). The match depends on that cache being
  current, not only on the server.
- Live token refresh against Pocket Casts.
- QR routing: camera recognition of `pktc://`, prefill, and a collision with the
  official Pocket Casts app.
- Linux, and signed-in requests to each Function from outside a browser.
- Protobuf calls from the Functions other than the playlist list. That read
  ran live on staging in M2 (2026-10-23).
- Written permission from Radio Paradise. It publishes its stream URLs for
  other players but shows no terms page.
- Whether the staging deployment's bundle equals the committed code.

## Milestones

| Milestone | What | User checkpoint |
|-----------|------|-----------------|
| M1 (`archive/web-m1`) | Prove Pairing, direct HTTPS playback and Cloudflare deployment | Pair, play a permitted HTTPS station directly, and reject HTTP without fallback |
| [M2](./milestones/milestone_2.md) | App shell and navigation from the synced Layout *(in progress)* | Sidebar matches the iPhone's tabs and More, with the Bar line |
| [M3a](./milestones/milestone_3a.md) | Now Playing resolver *(planned; precedes M3's Now Playing card)* | Open `/api/now-playing` for KEXP, KCRW and an AzuraCast station; titles match the iPhone, and an ended song shows `between` |
| [M3](./milestones/milestone_3.md) | Streams, the player, and the installable app *(planned)* | Install, play a favorite, control it from media keys and Now Playing |
| [M4](./milestones/milestone_4.md) | Lyrics for radio Tracks *(planned; metadata source/timing gate)* | A supported station has verified metadata/timing; lyric nudge survives reload |
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
