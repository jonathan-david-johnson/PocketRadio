# CLAUDE.md

This file provides guidance to AI when working with code in this repository.

## Repo Layout

This is a monorepo shell holding four sub-projects, each in its own nested git repo:

| Directory | What | Language |
|-----------|------|----------|
| `pocket-radio-ios/` | iOS app — fork of `Automattic/pocket-casts-ios` | Swift |
| `pocket-radio-menubar/` | macOS menubar player | Swift / SwiftUI |
| `pocket-radio-console/` | Terminal radio player | Go |
| `pocket-radio-roku/` | Roku channel (PocketStreams) | BrightScript |

Top-level `Makefile` delegates to each sub-project and provides repo setup targets.

## Common Top-Level Commands

```bash
make checkout        # Clone iOS, menubar, Roku repos (skips if present)
make status          # Branch/sync/dirty status across all sub-projects
make run_sim         # Build + launch iOS app on simulator (delegates to iOS Makefile)
make menubar         # Kill, build Debug, launch menubar app
make install         # Build Release menubar + copy to /Applications
make console-test    # Run Go console tests
make roku-run        # Deploy Roku channel + open BrightScript debug console
```

## iOS App (`pocket-radio-ios/`)

Sub-project has its own `AGENTS.md` (symlinked as `CLAUDE.md` inside that directory) with authoritative build, test, and architecture docs. Always read it before touching iOS code.

Key facts:
- Scheme: **`Pocket Casts Staging`**, configuration: **`StagingDebug`**
- Default sim UDID: `F0042A02-0973-4694-B267-49A1CC21FE19` ("iPhone 17 Pro - No Watch")
- Bundle ID: `au.com.shiftyjelly.podcasts` (not `.staging`)
- Milestone docs: `docs/ios/current_milestone.md` (symlink → active milestone) — check this first when picking up iOS work

```bash
cd pocket-radio-ios
make build_sim       # Build for simulator
make run_sim         # Build + boot Simulator + install + launch
make test_staging    # Run tests (ONLY_TESTING= to filter)
make format          # SwiftLint autocorrect
```

Radio feature files live in `pocket-radio-ios/podcasts/Radio/`. New test files under `PocketCastsTests/Tests/` are auto-discovered; main app files under `podcasts/` still require `project.pbxproj` registration.

## Console App (`pocket-radio-console/`)

Go TUI using Bubbletea + mpv for playback. Requires `mpv` on PATH (`brew install mpv`).

```bash
cd pocket-radio-console
make build           # Compile binary
make run_kcrw        # Build + play KCRW
make test            # Hermetic tests (no mpv required)
make test-integration  # Includes real mpv test
make vet             # go vet
```

Package layout: `cmd/pocket-radio/` (entrypoint), `internal/{config,library,player,pocketcasts,radio,resolver,ui/mini}/`.

Milestone docs: `docs/console/current_milestone.md`.

## Menubar App (`pocket-radio-menubar/`)

```bash
cd pocket-radio-menubar
# or from root:
make menubar         # Kill + build Debug + launch
make menubar-log     # Stream unified logs from running app
make install         # Build Release + install to /Applications
```

Architecture docs: `pocket-radio-menubar/docs/menubar/README.md` (or `docs/menubar/README.md` from root).

## Roku Channel (`pocket-radio-roku/`)

Requires env vars: `ROKU_HOST` (device IP) and `ROKU_PASS` (dev-mode password).

```bash
cd pocket-radio-roku
make deploy          # Build channel.zip + sideload to device
make dev             # deploy + open BrightScript debug console
make telnet          # Open debug console only (nc to port 8085)
make killtelnet      # Kill stale console connections (Roku allows only one)
```

Milestone docs: `docs/roku/current_milestone.md`. Source lives in `source/`, `components/`, `images/`.

## Supabase (Backend)

Radio favorites and listen-time sync. Local dev:

```bash
brew install supabase/tap/supabase
supabase start       # from repo root (config in supabase/)
```

iOS uses Supabase Swift 2.x with `x-user-uuid` header for user scoping. Migrations in `supabase/migrations/`.

## Milestone / Planning Convention

Each sub-project has `docs/<project>/current_milestone.md` (a symlink to the active milestone file). Check this before picking up work in that sub-project. The symlink target is the archive — do NOT write plans through the symlink; create a new numbered milestone file and repoint the symlink.

## Upstream (iOS)

```bash
git -C pocket-radio-ios fetch upstream
git -C pocket-radio-ios merge upstream/trunk
```
