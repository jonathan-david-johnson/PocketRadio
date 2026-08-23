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

## Cross-cutting facts

- **The menubar app is the canonical spec** for the Pocket Casts API, protobuf
  wire format, and playback/state logic. `APIService.swift` and
  `PlayerViewModel.swift` are what every other surface is ported from.
- **Supabase rows are scoped by the `x-user-uuid` header.** Clients that can't
  keep a secret must not set it themselves — see `docs/web/README.md` § Auth
  model for why web proxies this and iOS doesn't.

## Pointers

- Build/test/run targets — `make help` (top level delegates; real logic lives
  in each sub-project's Makefile).
- Repo + docs + milestone conventions — `docs/REPO_STRUCTURE.md`, or invoke the
  `meta-repo` skill.
- Cross-platform work (specs, milestones spanning surfaces) — `docs/global/`.
  Platform-local bugs — `docs/<project>/bugs/`.
