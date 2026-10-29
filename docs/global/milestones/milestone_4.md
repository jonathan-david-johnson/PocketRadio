# Global M4 — Now Playing normalization

**Status**: IN PROGRESS — opened 2026-10-29. Research cycle 1 is over, the contract is on `main`, and web ADR 0008 is in force. The first code (menubar M13, a Swift package that is not wired into any app) is built and passes the contract. Web M2 is on `main`; M3a has its branch and worktree.
**Platforms**: web (`pocket-radio-web/`), menubar (`pocket-radio-menubar/`); iOS adopts later
**Depends on**: [web ADR 0006](../../web/adr/0006-direct-https-playback-without-an-audio-relay.md) and [ADR 0008](../../web/adr/0008-now-playing-comes-from-a-server-side-resolver.md)
**Required by**: Web M3 (Now Playing card and Media Session), Web M4 (lyrics)

## Where the work happens

This is a parent milestone. It holds the goal, the slice list, the archetype board and the decisions. Each slice is a normal platform milestone with its own branch.

| Slice | Milestone | Code | State |
|---|---|---|---|
| Shared contract | this milestone | Shell `main`: `contracts/now_playing_feed/` | Done (41 cases, 28 junk cases, schema) |
| Web resolver | [Web M3a](../../web/milestones/milestone_3a.md) | `pocket-radio-web`, branch `feature/m3a-now-playing`, worktree `pocket-radio-web-m3a/` | IN PROGRESS. Contract port, request builders, and resolver Function are committed (`77c513f`, `e918742`, `b4aac07`). Migration `14e5ef2` is unapplied; only KEXP/KCRW are configured |
| Swift port of the contract | [Menubar M13](../../menubar/milestones/milestone_13.md) | `pocket-radio-menubar`, branch `feature/now-playing-feed`, worktree `pocket-radio-menubar-nowplaying/` | Package built and passing (menubar `d9ac655`, unmerged, unpushed). **Not integrated** into the menubar app or iOS |
| iOS adoption | not opened | `pocket-radio-ios` | Not started. Opens after M13, when the user says so |
| Source research | this milestone (Archetype board) | Shell `main`: `docs/global/experiments/` | Cycle 1 done |

**Goal:** Every PocketRadio surface shows the same Now Playing record for a station: one title, artist, artwork and status, no matter which kind of source supplies it. The shared contract defines the record and the rules (time zones, junk filtering, "ended" and "stale"). Each platform proves it with the same fixtures.

**User checkpoint:** On the staging site, `/api/now-playing` gives the iPhone's title for KEXP and KCRW and a correct song for an AzuraCast station (web M3a). `swift test` on the Swift package passes every contract case (menubar M13).

## Archetype board

How far each kind of source has been taken. Levels: L0 named, L1 surveyed (card complete, 10+ instances), L2 spiked (adapter plus fixtures plus timing measured), L3 contracted (fixtures frozen, terms recorded), L4 integrated (shipped behind a flag, 7-day canary), L5 sustained. Rules are in the Now Playing investigation report.

| Archetype | Examples | Level | Terms | First release? |
|---|---|---|---|---|
| A1 station API | KEXP, KCRW | L4 on iOS and menubar; L2 for web | Existing use | Yes |
| A1 station API | Radio Paradise, NTS | L2 (no fixtures yet) | Not found | No (hold) |
| A1 station API | SomaFM | L2 | **Restricted. Skipped by decision 2026-10-29** | **No** |
| A3 platform API | AzuraCast | L2 (fixtures recorded); web code not started | Official docs read | Yes |
| A3 platform API | laut.fm | L2 (fixtures recorded) | Docs site exists; contents unread | Yes, after reading |
| A3 platform API | Triton, iHeart, Airtime Pro, RadioKing, Live365, Radio.co, RadioJar, Zeno | L2–L2 (fixtures recorded) | Public docs not found or unread | No (hold) |
| A2 broadcaster API | Sveriges Radio | L2 (fixtures recorded) | Official docs read; API "no longer maintained" | Yes, with a maintenance risk |
| A2 broadcaster API | Radio France, ABC, NPO, NPR Composer | L2–L2 (fixtures recorded) | Unofficial or unread | No (hold) |
| A4 status page | Icecast, SHOUTcast | L2 | Server feature | No |
| A5 in-band ICY | 97% of progressive streams | L4 on iOS and menubar; web cannot read it (78% of streams) | n/a | No server peek for now |
| A6 HLS timed metadata | SomaFM, iHeart, Amperwave | L1 (hls.js works; native `<audio>` does not expose it) | n/a | No |
| A7 directory-published | TuneIn | L1 | Not found | No |
| A8 schedule only | NTS, WNYC | L1 | — | No |
| A9 fingerprint | ShazamKit | L4 on iOS only | — | Not on web |

## Decisions

| Decision | Outcome | Date |
|---|---|---|
| Server-side resolver for the web | Accepted ([ADR 0008](../../web/adr/0008-now-playing-comes-from-a-server-side-resolver.md)) | 2026-10-29 |
| Pathfinder source | AzuraCast | 2026-10-29 |
| First-release sources | Documented sources only: KEXP, KCRW, AzuraCast, laut.fm, Sveriges Radio | 2026-10-29 |
| SomaFM | Skip. Do not contact them | 2026-10-29 |
| Swift port | Yes, but do not integrate yet | 2026-10-29 |
| M3a branch and worktree | Confirmed as proposed | 2026-10-29 |
| **ICY peek on the server** | **No for now.** The server must not read station audio. Reconsider only through an ADR 0006 amendment after station terms and listener-count effects are checked | 2026-10-29 |
| Local usage metric | Accepted in principle; not built | — |

## Cycle log

| Cycle | Breadth | Depth | State |
|---|---|---|---|
| 0 | Landscape census (62k stations), source taxonomy | — | Done |
| 1 | Terms review; hls.js check; top-100 head sweep | Contract fixtures; ADR 0008; M3a opened | Done 2026-10-29 |
| 2 | Read laut.fm docs; ask Radio France for a key; head sweep of ranks 101–300; find why 9 of 44 AzuraCast hosts returned nothing | Menubar M13 (Swift port); web M3a resolver | In progress |

## Out of scope

- Any adapter outside the first release until a terms entry is recorded.
- SomaFM.
- iOS and menubar app integration of the Swift package.
- A server-side ICY peek, browser-side ICY and hls.js. The server peek is not chosen for now.
- History and next-up lists.

## Docs impact

- **Docs this changes or makes stale:** web ADR 0006 (pointer added); web README, CONTEXT and `communication.md` when M3a lands; `contracts/now_playing_feed/README.md` once a port has checked it; iOS and menubar READMEs when they adopt it.
- **Questions this must settle:** where the Swift package lives long-term (it sits under the menubar's `Packages/` like `StreamSession`, and iOS reaches it by path); whether `station_metadata_sources` belongs in the shared or the web database; the terms table for each adapter.
