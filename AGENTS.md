# PocketRadio

Monorepo shell. Each sub-project is its own nested git repo with its own
`AGENTS.md` and Makefile.

| Directory | What | Language | Docs |
|-----------|------|----------|------|
| `pocket-radio-ios/` | iOS app — fork of `Automattic/pocket-casts-ios` | Swift | `docs/ios/` |
| `pocket-radio-menubar/` | macOS menubar player | Swift / SwiftUI | `docs/menubar/` |
| `pocket-radio-console/` | Terminal radio player | Go | `docs/console/` |
| `pocket-radio-roku/` | Roku channel (PocketStreams) | BrightScript | `docs/roku/` |
| `pocket-radio-web/` | Browser player — Cloudflare Pages + Functions | TS / React | `docs/web/` |
| `pocket-radio-android/` | Android TV + mobile — *not scaffolded* | Kotlin | `docs/android/` |
| `supabase/` | Shared backend — radio favorites, listen-time sync, `pc-relay` | SQL / Deno | `docs/global/` |

**Before touching a sub-project:** read its `AGENTS.md`, then
`docs/<project>/current_milestone.md`. Both are authoritative over this file.

## Conventions

- **`CLAUDE.md` is a one-line `@AGENTS.md` pointer in every repo — never more.**
  All real content goes in `AGENTS.md`. Enforced by a pre-commit hook scoped to
  this repo and its nested repos; run `make hooks` after cloning.
- **Write-through symlink trap:** `docs/<project>/current_milestone.md` →
  `milestones/milestone_N.md`. Writing through it overwrites the milestone it
  points at. Use the `new-milestone` skill, which repoints with `ln -sfn`.
- **Milestones are deleted when they close.** Close one with the
  `close-milestone` skill; never mark it complete by hand. Its durable
  knowledge moves to ADRs, README/CONTEXT, tests, and contracts, and git keeps
  the rest under `archive/<platform>-m<id>`. Code cites ADRs, never milestones,
  experiments, or bug docs. The pre-commit hook enforces this. Details:
  `docs/REPO_STRUCTURE.md` § Lifecycle and cleanup.
- **Milestone skills live in the shell** (`.agents/skills/`), not in platform
  repos. Start milestone sessions from the shell checkout so they're found.
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

## Asking for decisions

When asking the user to decide, restate each option in plain words and give a
recommendation. Explain what would change and any important trade-off. Decision
IDs such as “D1–D4” and labels such as “scope exception” are not explanations;
include the actual choice even when the preceding document defines it.

## Task routing

| If you need to… | Read or use… | Evidence boundary |
|---|---|---|
| Inspect raw ICY headers/metadata blocks, check whether a station feed is stale, or compare upstream ICY and feed titles | `tools/stream-probe.py` (`python3 tools/stream-probe.py --help`); background in `docs/menubar/ACR_track_fingerprinting.md` | Opens its own HTTP stream connection and discards audio. It diagnoses upstream transport/feed behavior, not what AVPlayer or the listener received. |
| Line up, song by song, when the feed stamped a song, when the feed listed it, when the stream's own title arrived, and when ShazamKit says it began, from the iOS app's debug log | `tools/stream-timeline.py` (`python3 tools/stream-timeline.py --help`); the lines come from `StreamTrace` in the iOS app's aligned session | Needs a heal (a ShazamKit anchor) on each song to compare. It reports what one phone's session saw. |
| Profile many audio stream URLs at once: reachability, codec, ICY and HLS metadata, CORS | `tools/source-survey.py` (`python3 tools/source-survey.py --help`) | One connection per URL from this machine. It shows what a server sends, not what a player plays or what a listener hears. |
| Measure metadata, media time, buffering, feed observations, and human markers on the macOS AVPlayer path, then replay them offline | `pocket-radio-menubar/Tools/StreamLab/README.md` and `docs/menubar/current_milestone.md` | Uses the application playback framework. A parallel connection from another tool is not the same audio timeline. |

## Pointers

- What is running across all platforms, what each initiative waits for, and what is parked — `docs/INITIATIVES.md`. Refresh its facts with `python3 tools/initiatives.py`.
- Build/test/run targets — `make help` (top level delegates; real logic lives
  in each sub-project's Makefile).
- Repo + docs + milestone conventions — `docs/REPO_STRUCTURE.md`, or invoke the
  `meta-repo` skill.
- Cross-platform work (specs, milestones spanning surfaces) — `docs/global/`.
  Platform-local bugs — `docs/<project>/bugs/`.
