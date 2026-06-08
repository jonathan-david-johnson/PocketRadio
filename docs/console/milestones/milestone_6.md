# M6 — Lyrics + ACR + polish

**Goal:** Land the last menubar features and round off the experience: synced
lyrics, the ACRCloud identify affordance (gated on credentials), and the polish
pass (refresh, logout, error/empty states).

**User checkpoint:** While KCRW/KEXP plays, lyrics appear and the current line
highlights/advances in time; pressing `i` runs ACR (or shows a friendly "add
ACRCloud keys to config" no-op); refresh, logout, and error states all behave.

## Scope

- `internal/lyrics`: lrclib fetch + LRC parse + `currentLine(at offset)` (binary
  search), with an in-memory cache. Ported from the menubar's `LyricsService`.
- Engine: drive a lyric line from the playing track's `playedAt` offset; expose
  `State().CurrentLyric` + line index; lyrics bar in now-playing and a scrollable
  lyrics detail view (synced highlight, plain fallback, "no lyrics").
- `internal/acr`: ACRCloud one-shot fingerprint — second HTTP connection captures
  ~15s of stream bytes, HMAC-SHA1 signed multipart `POST /v1/identify`, parse
  result. Gated on `config.toml [acrcloud]`; absent → friendly message (mirrors
  the menubar's blocked-on-creds state).
- Polish: context-aware refresh, logout (clear `state.json` + stop playback),
  loading/empty/error states across panes, mpv-missing and network-error
  messaging.

## Behaviors to test (red → green, one at a time)

1. LRC parser: a synced-lyrics blob → ordered `[]LyricLine{timestamp,text}`;
   malformed lines skipped.
2. `currentLine(at:)`: returns the last line whose timestamp ≤ offset (boundary
   cases: before first, exactly on a timestamp, after last).
3. Lyrics fetch against `httptest`: synced present → `hasSynced`; only plain
   present → plain; `404` → nil; second call for the same track is served from
   cache (one HTTP hit).
4. Engine lyric advance: with synced lyrics and an injected clock, advancing the
   offset moves `State().CurrentLyric` to the expected line.
5. ACR signing: `stringToSign` + HMAC-SHA1 → the expected base64 signature for a
   fixed key/secret/timestamp (golden value); multipart body has the required
   fields.
6. ACR parse: a captured ACRCloud success body → `{title, artist, album, score}`;
   a no-match body → typed no-match error.
7. ACR gating: with no `[acrcloud]` config, `Identify` returns
   `ErrNoCredentials` and the UI shows the hint (no network call).
8. Logout clears the cached token/state file and stops the player.

## Out of scope

Nothing deferred past here — this completes menubar parity. Post-M6 candidates
(not committed): listen-time/donation features (Supabase `listen_time`,
`donations`), Linux packaging, config for custom tracklist stations.
