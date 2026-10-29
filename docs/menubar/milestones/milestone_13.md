# Menubar M13 — NowPlayingFeed package (Swift port of the contract)

**Status**: IN PROGRESS — started 2026-10-29. The package is built and committed on its separate `feature/now-playing-feed` worktree (menubar `d9ac655`, unmerged and unpushed). `swift test` was rerun on 2026-10-29 and passes: 41 contract cases, 28 junk cases, and the time, boundary and schema checks (18 tests). A deliberately broken fixture made the suite fail, then was restored. Open: whether to land it on `main`, and the iOS adoption milestone
**Parent**: [Global M4](../../global/milestones/milestone_4.md)
**Depends on**: shell contract `contracts/now_playing_feed/` (on `main`)
**Required by**: iOS adoption of the contract (not opened)

## Where the work happens

| | |
|---|---|
| Plan | Shell `main`: this file |
| Code | `pocket-radio-menubar`, branch `feature/now-playing-feed` from `main` (`8f71eb4`) |
| Worktree | `pocket-radio-menubar-nowplaying/`, a sibling of the main checkout, so `../contracts` resolves |
| Shell changes | None. The package only reads `contracts/now_playing_feed/` |

**Goal:** Prove the shared Now Playing contract in Swift. A new package, `Packages/NowPlayingFeed`, parses each adapter's raw response and applies the contract's rules (UTC times, combined-title splitting, the junk filter, `between` and `stale`). It sits beside `StreamSession` so iOS can later depend on it by path, as it does for `StreamSession`. **It is not integrated.** No app target imports it, and no iOS project references it.

**User checkpoint:** In the worktree, `swift test --package-path Packages/NowPlayingFeed` passes every case in `contracts/now_playing_feed/cases/` and every case in `junk_filter.json`. `git diff main --stat` shows changes only under `Packages/NowPlayingFeed/`.

## Scope

- **Package (`Packages/NowPlayingFeed/`).** Swift tools 5.9, macOS 13 and iOS 16, like `StreamSession`. No dependencies beyond Foundation.
- **Record and rules.** `NowPlaying` (Codable, equal to `schema.json`); the status rules; the junk filter; the title splitters.
- **Adapters.** One parser per adapter in the contract: KEXP, KCRW, AzuraCast, laut.fm, Radio.co, Triton, Live365, RadioJar, iHeart, RadioKing, Airtime Pro, Sveriges Radio, ABC, Radio France, NPO, NPR Composer, Icecast, SHOUTcast, Zeno, and ICY. Parsers take a response body and return a result. They make no network call.
- **Contract runner (`Tests/`).** Loads the fixtures from the shell's `contracts/now_playing_feed/` and compares each produced record to `expected`.

## Behaviors to test (red -> green, one at a time)

1. Every case file produces its `expected` record, per adapter group.
2. Every junk case returns its `expected_kind`.
3. Every expected record passes the schema's required keys and enums.
4. Time converters: epoch seconds and milliseconds; ISO with and without a colon in the offset; fractional seconds; naive local time with a named zone; `/Date(ms)/`; `MM-DD-YYYY HH:MM:SS` in a zone.
5. The ended and stale rules at their boundaries (60 s, 900 s).
6. `git diff main --stat` touches only `Packages/NowPlayingFeed/`.

## Out of scope

- Importing the package into the menubar app or iOS. The user said not to integrate yet.
- Fetching from the network.
- Adapters not in the contract (Radio Paradise, NTS, TuneIn).
- A change to the contract. A disagreement between the port and a fixture is reported, not patched silently.

## Docs impact

- **Docs this changes or makes stale:** `contracts/now_playing_feed/README.md` (first independent port: update its "Status of the reference" section); the menubar README roadmap.
- **Questions this must settle:** whether the fixtures' expected values hold under a second implementation; whether any rule in the contract README is ambiguous (each ambiguity found is a defect in the README).
