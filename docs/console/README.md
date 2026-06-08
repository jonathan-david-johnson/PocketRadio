# PocketRadio Console (TUI)

A terminal companion to the PocketRadio **menubar** app. Plays your Pocket Casts
Up Next queue and favorite radio streams from the terminal, with full feature
parity to the macOS menubar app.

Distributed as a single binary named **`pocket-radio`** (project/repo:
`pocket-radio-console`).

## Two run modes

| Invocation | Mode | What you get |
|------------|------|--------------|
| `pocket-radio` | **Full TUI** | Alt-screen layout that mirrors the menubar: source pills, now-playing pane (with album art), Up Next / New Releases, Browse / Favorites, scrub bar, lyrics, detail panes. |
| `pocket-radio <arg>` | **Mini mode** | One line. Resolves `<arg>` to a station/queue, starts playback, shows `▶ Title — Artist  [source]` plus inline controls. |

### Mini-mode argument grammar

```
pocket-radio                 -> full TUI
pocket-radio up_next         -> play top of Up Next        (reserved word)
pocket-radio new             -> play newest release         (reserved word)
pocket-radio kcrw            -> favorite whose name matches "kcrw"
pocket-radio "radio paradise"-> fav miss -> radio-browser search, top hit
pocket-radio zzzz            -> error + "did you mean: KEXP, KCRW?"

flags:
  --full     force full TUI even with an arg
  --list     print all resolvable names (reserved words + favorites) and exit
```

Resolution order for a non-reserved arg: **favorite name substring → radio-browser
search top hit → error with suggestions**.

Mini-mode keys: `space` play/pause · `←`/`→` skip back/forward · `f` upgrade to full TUI · `q` quit.

> Mini mode is text-only (a single row can't hold an image). Album art lives in
> the full TUI, where it is a first-class part of the now-playing and detail panes.

## Stack

| Concern | Choice | Notes |
|---------|--------|-------|
| Language | **Go** | Single static binary, trivial distribution (`brew` / `go install`), strong concurrency for the background pollers. |
| TUI | **Bubble Tea** (+ Lip Gloss, Bubbles) | Elm architecture; one framework renders both the compact mini model and the full alt-screen model. |
| Audio | **mpv** subprocess over **JSON IPC** | mpv handles HTTP/Icecast streams + podcast MP3, seeking, position reporting, and ICY `metadata` events. See [ADR-0002](./adr/0002-mpv-as-audio-engine.md). |
| Album art | terminal graphics, protocol-detected | kitty graphics / iTerm2 inline / sixel, with a `chafa` ANSI-block fallback. Baked in from the first full-TUI milestone. |
| Persistence | `~/.config/pocket-radio/` (mode 0600) | `config.toml` (creds, optional ACR keys) + `state.json` (token, user_uuid, device_id, favorites order). See [ADR-0003](./adr/0003-token-in-config-file.md). |

See [ADR-0001](./adr/0001-go-bubbletea-mpv-stack.md) for why Go/Bubble Tea over
Python/Textual or Rust/Ratatui, and why not Swift (to match the menubar).

## Runtime dependencies

- **mpv** on `PATH` (`brew install mpv`). Hard dependency — the binary checks for
  it on startup and prints an install hint if missing.
- **chafa** (optional) — only used as the album-art fallback when no native
  terminal graphics protocol is detected.

## Architecture

The design follows "deep modules": a single deep **engine** behind a narrow
interface, with thin UI front-ends and all I/O isolated behind mockable
boundary interfaces (HTTP, mpv, filesystem, clock). This mirrors the menubar's
`PlayerViewModel` but split so the engine is testable without a UI.

```
pocket-radio-console/
├── cmd/pocket-radio/main.go      # arg parse, mode dispatch (mini vs full)
├── internal/
│   ├── pocketcasts/              # Pocket Casts API (boundary: HTTP)
│   │   ├── protobuf.go           #   hand-rolled varint enc/dec (port from Swift)
│   │   └── client.go             #   SDK-style: Login, UpNext, PodcastEpisodes,
│   │                             #   UpdateEpisode, PlayNow, RemoveFromUpNext,
│   │                             #   PodcastList, FullEpisodes, ShowNotes, SkipSettings
│   ├── radio/                    # radio-browser + Supabase favorites + tracklist
│   │   ├── directory.go          #   Favorites / Top / Search / Add / Remove
│   │   ├── tracklist.go          #   KCRW + KEXP parsers
│   │   └── artwork.go            #   iTunes Search art fallback
│   ├── lyrics/                   # lrclib fetch + LRC parse + currentLine
│   ├── acr/                      # ACRCloud one-shot fingerprint (gated on creds)
│   ├── player/                   # mpv IPC driver (boundary: subprocess + socket)
│   ├── library/                  # THE ENGINE — orchestration, position-save
│   │                             #   throttle, auto-advance, now-playing state
│   ├── config/                   # config.toml + state.json (0600) load/save
│   ├── art/                      # terminal image detect + render
│   └── ui/
│       ├── theme/                # Lip Gloss styles from the Pocket Casts palette
│       ├── mini/                 # one-line Bubble Tea model
│       └── full/                 # full alt-screen Bubble Tea model
└── go.mod
```

### Boundary interfaces (mock these; nothing else)

```go
// player — the only thing that talks to mpv
type Player interface {
    Load(url string, startAt time.Duration) error
    Pause() error
    Resume() error
    Seek(to time.Duration) error
    State() PlaybackState              // playing?, pos, dur, isLive
    Events() <-chan PlayerEvent        // metadata / ended / tick
    Close() error
}

// pocketcasts — SDK-style, one method per endpoint (easy per-endpoint mocks)
type PocketCasts interface {
    Login(ctx context.Context, email, password string) (Session, error)
    UpNext(ctx context.Context, token, deviceID string) ([]Episode, error)
    PodcastEpisodes(ctx context.Context, token, podcastUUID string) ([]PlaybackInfo, error)
    UpdateEpisode(ctx context.Context, token string, u EpisodeUpdate) error
    PlayNow(ctx context.Context, token string, ep Episode) error
    RemoveFromUpNext(ctx context.Context, token string, ep Episode) error
    PodcastList(ctx context.Context, token string) ([]Podcast, error)
    FullEpisodes(ctx context.Context, podcastUUID, podcastTitle string) ([]Episode, error)
    ShowNotes(ctx context.Context, podcastUUID, episodeUUID string) (ShowNotes, error)
    SkipSettings(ctx context.Context, token string) (Skip, error)
}

type RadioDirectory interface {
    Favorites(ctx context.Context, userID string) ([]Station, error)
    Top(ctx context.Context, limit int) ([]Station, error)
    Search(ctx context.Context, query string) ([]Station, error)
    AddFavorite(ctx context.Context, userID, stationID string) error
    RemoveFavorite(ctx context.Context, userID, stationID string) error
}
```

The **engine** (`library`) takes these as dependencies and exposes a narrow
command/state surface that both UIs render:

```go
func (e *Engine) PlayTarget(t Target) error   // Target = UpNextTop | NewestRelease | Station | Episode
func (e *Engine) TogglePlayback()
func (e *Engine) SkipForward(); func (e *Engine) SkipBack(); func (e *Engine) Scrub(d time.Duration)
func (e *Engine) State() NowPlaying            // single struct both UIs render
func (e *Engine) Subscribe() <-chan NowPlaying // state changes for the UI loop
```

## Data flow (unchanged from the menubar)

1. **Auth** — email/password → `POST api.pocketcasts.com/user/login` (protobuf) → Bearer token + user UUID → cached in `state.json`.
2. **Up Next** — `POST up_next/sync` (protobuf) → episodes; merged with per-podcast `user/podcast/episodes` for `playedUpTo`/`duration`.
3. **Favorites** — `user_uuid` → Supabase `radio_favorites` → radio-browser lookup per station.
4. **Now-playing metadata** — KCRW/KEXP tracklist poll (30s), mpv ICY `metadata`, ACRCloud one-shot (gated), lrclib lyrics.
5. **Playback** — mpv loads the stream/episode URL; resume seek for podcasts; throttled `sync/update_episode` writes; auto-advance + `remove` on finish.

## Milestones

Vertical tracer-bullet slices (red → green → refactor per milestone). Each ends
at a runnable checkpoint.

| # | Milestone | User checkpoint |
|---|-----------|-----------------|
| [M0](./milestones/milestone_0.md) | Spike: mpv IPC + Go skeleton | `pocket-radio --spike <url>` plays audio and prints live position |
| [M1](./milestones/milestone_1.md) | Auth + config + mini-mode podcast | `pocket-radio up_next` plays your top podcast with a live one-line status |
| [M2](./milestones/milestone_2.md) | Mini-mode radio + arg resolver + tracklist | `pocket-radio kcrw` plays the station and the one line shows the current track |
| [M3](./milestones/milestone_3.md) | Podcast position fidelity | Quit mid-episode, replay, it resumes; finishing advances + removes from your phone's Up Next |
| [M4](./milestones/milestone_4.md) | Full TUI shell + now-playing **with art** | `pocket-radio` opens a menubar-like TUI; album art renders; controls work |
| [M5](./milestones/milestone_5.md) | Lists: Up Next, New Releases, Browse/Favorites | Navigate lists, fav/unfav, browse, reorder, open detail + show-notes panes |
| [M6](./milestones/milestone_6.md) | Lyrics + ACR + polish | Lyrics scroll on KCRW/KEXP; `i` runs ACR (or friendly no-op); refresh, logout, error states |

## Build & run

```bash
cd pocket-radio-console
go build -o pocket-radio ./cmd/pocket-radio
./pocket-radio              # full TUI
./pocket-radio up_next      # mini mode
go test ./...               # TDD suite
```
