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
  iOS uses. M1 checked that they match for the tested account (E1).

## Signing in (Pairing)

1. The browser asks a Function to start Pairing.
2. The Function asks Pocket Casts for a device code. The browser shows it as a QR
   code.
3. The user scans the QR in the iOS app and approves. The approval goes to
   Pocket Casts.
4. The Function polls Pocket Casts until it receives the tokens, stores them in
   Supabase, and sets the session cookie in the browser.

## Formats

| Leg | Format |
|---|---|
| Browser to Functions | JSON over HTTPS, with a cookie |
| Functions to Pocket Casts, Pairing and tokens | JSON (proven in M1 staging) |
| Functions to Pocket Casts, account data | Protobuf (ADR 0007). Not yet run from the web; M2's first call confirms it |
| Functions to Supabase | PostgREST over HTTPS |
| Browser to station | Audio stream over HTTPS |

## Current state

Built in M1: Pairing, sessions, the JSON probes and direct playback. Planned:
the protobuf account-data client (M2 onward), `/api/layout` (M2), and the full
Streams UI (M3).
