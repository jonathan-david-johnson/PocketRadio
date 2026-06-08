# M0 — Spike: mpv IPC + Go skeleton

**Goal:** De-risk the single biggest unknown (driving mpv from Go) and stand up
the repo. This is the tracer bullet for the *audio* path: prove Go can start mpv,
control it over the JSON IPC socket, and read back live position/metadata.

**User checkpoint:** `pocket-radio --spike <stream-or-file-url>` plays audio and
prints a ticking `pos / dur` line plus any ICY title, and `space`/`q` on stdin
pause and quit.

## Scope

- Repo init: `pocket-radio-console` (own git repo, pattern matches the other
  surfaces), `go.mod`, `cmd/pocket-radio/main.go`, GitHub Actions running
  `go test ./...` + `go vet`.
- `internal/player`: launch `mpv --idle --no-video --no-terminal
  --input-ipc-server=<tmp socket>`, dial the socket, implement the `Player`
  interface against it.
- mpv startup probe: if `mpv` not on `PATH`, exit with an install hint.
- `--spike` debug entrypoint (throwaway UI; real UIs come later).

## Behaviors to test (red → green, one at a time)

1. `Player.Load(url)` then `State().Playing == true` (integration test: real mpv,
   a short bundled local audio file).
2. `Pause()` / `Resume()` flip `State().Playing`.
3. `Seek(to)` moves `State().Position` to ~`to`.
4. `Events()` emits a position tick at least once while playing.
5. `Events()` emits an `Ended` event when a finite file completes.
6. Missing-mpv path returns a typed `ErrMpvNotFound` (unit test: fake exec lookup).

> mpv calls are a system boundary → the `Player` interface is the seam. Unit
> tests use a fake; the few real-mpv assertions live in one `//go:build
> integration` test so `go test ./...` stays hermetic.

## Public interface (frozen at end of M0)

```go
type PlaybackState struct {
    Playing  bool
    Position time.Duration
    Duration time.Duration // 0 == unknown/live
    IsLive   bool
}
type PlayerEvent struct {
    Kind     EventKind // Tick | Metadata | Ended | Error
    Metadata map[string]string // ICY title etc. for Kind==Metadata
    Err      error
}
type Player interface {
    Load(url string, startAt time.Duration) error
    Pause() error; Resume() error
    Seek(to time.Duration) error
    State() PlaybackState
    Events() <-chan PlayerEvent
    Close() error
}
```

## Out of scope

Pocket Casts API, config, the real UIs, album art. Pure audio-path + repo
plumbing.
