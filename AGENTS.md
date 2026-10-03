# PocketRadio

Monorepo shell. Each sub-project is its own nested git repo with its own
`AGENTS.md` and Makefile.

| Directory | What | Language | Docs |
|-----------|------|----------|------|
| `pocket-radio-ios/` | iOS app — fork of `Automattic/pocket-casts-ios` | Swift | `docs/ios/` |
| `pocket-radio-menubar/` | macOS menubar player | Swift / SwiftUI | `docs/menubar/` |
| `pocket-radio-console/` | Terminal radio player | Go | `docs/console/` |
| `pocket-radio-roku/` | Roku channel (PocketStreams) | BrightScript | `docs/roku/` |
| `pocket-radio-web/` | Browser SPA — *not scaffolded* | TS / React | `docs/web/` |
| `pocket-radio-android/` | Android TV + mobile — *not scaffolded* | Kotlin | `docs/android/` |
| `supabase/` | Shared backend — radio favorites, listen-time sync, `pc-relay` | SQL / Deno | `docs/global/` |

**Before touching a sub-project:** read its `AGENTS.md`, then
`docs/<project>/current_milestone.md`. Both are authoritative over this file.

## Conventions

- **`CLAUDE.md` is a one-line `@AGENTS.md` pointer in every repo — never more.**
  All real content goes in `AGENTS.md`. Enforced by a pre-commit hook scoped to
  this repo and its nested repos; run `make hooks` after cloning.
- **Write-through symlink trap:** `docs/<project>/current_milestone.md` →
  `milestones/milestone_N.md`. Writing through it overwrites the previous
  milestone's archive. Create a new numbered file and repoint the symlink.
- **The shell stays on `main`; code happens on platform branches.** Commit
  docs and additive contracts straight to `main`. A parallel branch in the
  same platform goes in a sibling worktree, `pocket-radio-<platform>-<topic>/`,
  at the same depth as the main checkout so `../contracts` and `../.githooks`
  resolve. Each milestone's **Where the work happens** table names the repo,
  branch, and worktree. Details: `docs/REPO_STRUCTURE.md` § Branches and
  parallel work.
- **Stage explicit paths in the shell.** Several sessions share this checkout.
  Never use `git add -A`, `git add .`, `git add docs/`, or `git commit -a`.
  Check `git diff --cached --name-only` before committing.

## Cross-cutting facts

- **The menubar app is the canonical spec** for the Pocket Casts API, protobuf
  wire format, and playback/state logic. `APIService.swift` and
  `PlayerViewModel.swift` are what every other surface is ported from.
- **Supabase rows are scoped by the `x-user-uuid` header.** Clients that can't
  keep a secret must not set it themselves — see `docs/web/README.md` § Auth
  model for why web proxies this and iOS doesn't.

## Task routing

| If you need to… | Read or use… | Evidence boundary |
|---|---|---|
| Inspect raw ICY headers/metadata blocks, check whether a station feed is stale, or compare upstream ICY and feed titles | `tools/stream-probe.py` (`python3 tools/stream-probe.py --help`); background in `docs/menubar/ACR_track_fingerprinting.md` | Opens its own HTTP stream connection and discards audio. It diagnoses upstream transport/feed behavior, not what AVPlayer or the listener received. |
| Measure metadata, media time, buffering, feed observations, and human markers on the macOS AVPlayer path, then replay them offline | `pocket-radio-menubar/Tools/StreamLab/README.md` and `docs/menubar/current_milestone.md` | Uses the application playback framework. A parallel connection from another tool is not the same audio timeline. |

## Pointers

- Build/test/run targets — `make help` (top level delegates; real logic lives
  in each sub-project's Makefile).
- Repo + docs + milestone conventions — `docs/REPO_STRUCTURE.md`, or invoke the
  `meta-repo` skill.
- Cross-platform work (specs, milestones spanning surfaces) — `docs/global/`.
  Platform-local bugs — `docs/<project>/bugs/`.
