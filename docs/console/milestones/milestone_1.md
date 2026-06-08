# M1 — Auth + config + mini-mode podcast

**Goal:** First end-to-end user-facing slice. Log in to Pocket Casts, fetch Up
Next, and play the top episode in mini mode with a live one-line status.

**User checkpoint:** `pocket-radio up_next` logs in (from `config.toml` or one
prompt), then plays your top podcast episode showing
`▶ <episode title>  m:ss / m:ss` with working `space` / `←` / `→` / `q`.

## Scope

- `internal/pocketcasts/protobuf.go`: port the menubar's varint encode/decode.
- `internal/pocketcasts/client.go`: `Login`, `UpNext` (request + response decode).
- `internal/config`: load/save `config.toml` + `state.json` at mode 0600; XDG
  config dir resolution; interactive prompt when creds absent.
- Auth flow: cached token → use it; `401` → re-login from creds → re-cache;
  no creds → prompt once.
- `internal/library` (engine, minimal): `PlayTarget(UpNextTop)`,
  `TogglePlayback`, `SkipForward/Back`, `State() NowPlaying`.
- `internal/ui/mini`: one-line Bubble Tea model bound to the engine; reserved
  word `up_next`.
- `cmd`: arg dispatch — bare = (stub) full TUI placeholder; `up_next` = mini.

## Behaviors to test (red → green, one at a time)

1. **protobuf login round-trip**: `encodeLoginRequest` produces the exact bytes
   the menubar sends (golden fixture), and `decodeLoginResponse` parses a captured
   response into `{token, uuid, email}`.
2. `decodeUpNextResponse` parses a captured `up_next/sync` body into ordered
   episodes with `playedUpTo`/`duration` merged from the sync records.
3. `Login` against an `httptest` server: `200` → `Session`; `401/403` →
   `ErrInvalidCredentials`.
4. Config: save then load returns the same struct; written files are mode `0600`.
5. Auth flow: with a cached token the engine does **not** call `Login`; on a
   simulated `401` it re-logs-in once and retries.
6. Engine: `PlayTarget(UpNextTop)` loads the first episode's URL into the
   (fake) `Player` and `State().Title` is that episode's title.
7. `SkipForward()` seeks the player by the configured amount (default 45s until
   M3 wires synced settings).

> Boundaries mocked: HTTP via `httptest.Server`, `Player` via fake, filesystem via
> a temp dir, clock via an injected `now func() time.Time`. Nothing else.

## Public interface

```go
type NowPlaying struct {
    Title    string   // episode title or "Song — Artist"
    Subtitle string   // "Up Next" | "Live Stream" | podcast/station name
    Playing  bool
    Position, Duration time.Duration
    IsLive   bool
}
type Target interface{ isTarget() }
type UpNextTop struct{}
```

## Out of scope

Radio/stations, tracklist, position write-back, new releases, full TUI, art.
