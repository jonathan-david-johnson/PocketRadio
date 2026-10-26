# How the web player communicates

Who talks to whom in PocketRadio Web, and in what format. Decisions behind it:
[ADR 0002](../adr/0002-cloudflare-hosts-web-player-supabase-is-database.md)
(hosting and database), [ADR 0003](../adr/0003-sign-in-by-phone-pairing.md)
(sign-in), [ADR 0006](../adr/0006-direct-https-playback-without-an-audio-relay.md)
(audio), [ADR 0007](../adr/0007-protobuf-for-pocket-casts-account-data.md)
(Pocket Casts format).

**Pocket Casts** in this document means Automattic's server, not an app. It is
`api.pocketcasts.com` (the staging environment uses `api.pocketcasts.net`) and
holds the account, subscriptions, playlists, Up Next and playback positions.

## Diagram

```
                      YOUR ACCOUNT'S DATA LIVES HERE
                 ┌───────────────────────────────────────┐
                 │  POCKET CASTS SERVER (Automattic)     │
                 │  api.pocketcasts.com  (staging: .net) │
                 └──────────▲──────────────────▲─────────┘
                  protobuf  │                  │ protobuf for account data
                  (native)  │                  │ JSON for Pairing calls
                            │                  │ (ADR 0007)
          ┌─────────────────┴──┐        ┌──────┴──────────────┐
          │ iOS app            │        │ CLOUDFLARE PAGES    │
          │ (your phone)       │        │ Functions: the web  │
          └──┬──────────────┬──┘        │ player's "backend"  │
             │              │           └─▲──────┬─────┬──────┘
             │ approves     │             │      │     └──► radio-browser.info
             │ Pairing      │      JSON + │      │          (station ID -> stream URL)
             │ (scans QR)   │      cookie │      │
             │              │      ┌──────┴────┐ │ service-role key
             │              │      │ BROWSER   │ │ (server only)
             │              │      │ web player│ │
             │ anon key +   │      └─────┬─────┘ ▼
             │ x-user-uuid  │            │   ┌────────────────────────────┐
             │              └────────────┼──►│ SUPABASE (database only)   │
             └───────────────────────────┼──►│ secret tables: pc_tokens,  │
                                         │   │  web_sessions, web_pairings│
                                         │   │ shared tables: radio_      │
                                         │   │  favorites, nav_layout     │
                                         │   └────────────────────────────┘
                                         │ audio, direct over HTTPS
                                         ▼ (no relay; our servers never carry it)
                                ┌─────────────────────┐
                                │ RADIO STATION       │
                                └─────────────────────┘
```

## Who talks to whom

- **Browser.** Talks only to our Functions, using an httpOnly session cookie. It
  never contacts Pocket Casts or Supabase. The one exception is station audio,
  which it fetches directly from the station.
- **Functions.** Hold all secrets. They call Pocket Casts with the user's tokens,
  Supabase with the service-role key, and radio-browser for station lookups.
  They return plain JSON to the browser.
- **iOS app.** Talks directly to Pocket Casts and to Supabase. Supabase rows are
  scoped by the `x-user-uuid` header, so the web player must use the same UUID
  iOS uses. The web takes its UUID from the Pocket Casts token. iOS uses the
  `ServerSettings.userId` it cached at sign-in, so the two match only when that
  cache is current. Web M2 found a stale cache on the phone; signing out and back
  in fixed it.

## Signing in (Pairing)

1. The browser asks a Function to start Pairing.
2. The Function asks Pocket Casts for a device code. The browser shows it as a QR
   code.
3. The user scans the QR in the iOS app and approves. The approval goes to
   Pocket Casts.
4. The Function polls Pocket Casts until it receives the tokens, stores them in
   Supabase, and sets the session cookie in the browser.

## The QR payload and phone routing

From the iOS source (not tested on a device): the fork declares the `pktc`
scheme and routes `pktc://pair?user_code=<code>` to `DeviceApproveView`, which
needs a signed-in account and also accepts the six-character code by hand. The
QR carries only the user-facing code, never a device secret or token.

Not established: camera recognition of the custom scheme, prefill in the
installed build, which app wins if the official Pocket Casts app also claims
`pktc`, and universal-link association for the fork. In M1 the user scanned
fresh codes and reached approval on the staging build, and approved Pairing
successfully, but these routing details were not examined (E2 accepted untested).

## Formats

| Leg | Format |
|---|---|
| Browser to Functions | JSON over HTTPS, with a cookie |
| Functions to Pocket Casts, Pairing and tokens | JSON (proven in M1 staging) |
| Functions to Pocket Casts, account data | Protobuf (ADR 0007). The playlist list ran live on staging in M2 (2026-10-23); the other messages have not |
| Functions to Supabase | PostgREST over HTTPS |
| Browser to station | Audio stream over HTTPS |

## Verified in M1

| What | How | Limit |
|---|---|---|
| Phone approval creates a bound session; reload keeps it; both sign-outs; cross-browser revocation | User-reported on local staging and again on the deployed site; a read-only database check confirmed the consumed Pairing and a live session | No trace or browser versions recorded |
| Three read-only calls (`podcast/list`, `playlist/list`, `named_settings`) | User-reported: HTTP 200, a JSON object | Structure only; protobuf not run from the web |
| The web session's UUID equals the one iOS writes Supabase rows under | M1: read-only query comparing hash prefixes (user-approved), on the `.net` store, which held no iOS rows. M2, 2026-10-23: the phone's cached id differed from the token's UUID, so the Layout did not match until the user signed out and back in on the phone; then the web Sidebar followed phone reorders | `.net` (StagingDebug) only; not checked on `.com`. A stale iOS cache can break the match again |
| Direct HTTPS playback: play, Stop, switch between two different streams, local sign-out stops audio, HTTP-only rejected, invalid ID shows an error | User-reported in Chrome and Safari on macOS, local and deployed | 25+ minute run only; the error text is a developer string |
| Secret tables and RPCs deny the anon key | SQL checks against the staging database: 5 tables, 18 RPCs | — |
| Behavior in code | 159 unit/UI tests, 41 database/handler tests, an offline Pages runtime check (`tests/`) | Mocks and synthetic upstreams, not live Pocket Casts |

Not verified: production `.com` Pairing, live token refresh, QR routing,
Linux, signed-in calls from outside a browser, and Workers Free limits under
load. See the known risks in the [web README](../README.md).

## Current state

Built in M1: Pairing, sessions, the JSON probes and direct playback. Planned:
the protobuf account-data client (M2 onward), `/api/layout` (M2), and the full
Streams UI (M3).
