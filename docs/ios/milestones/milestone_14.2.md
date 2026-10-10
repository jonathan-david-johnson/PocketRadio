# iOS M14.2 — KCRW aligned titles and Now Playing

**Status**: CLOSING — 2026-10-10. Checkpoint passed on the device; merged to `trunk` at `a8254b8c4`. Knowledge moved to ADR 0005.
**Depends on**: [M14](milestone_14.md); M14.1 closed (`archive/ios-m14.1`) with the Observe-only session on `trunk`; [ADR 0004](../adr/0004-kcrw-playback-clock-on-ios.md).
**Required by**: M14.3 (lyrics on the media clock) and M14.4 (routes and background).

## Where the work happens

| | |
|---|---|
| Plan and reports | Shell `main`: this file, `docs/ios/experiments/`, `docs/ios/bugs/` |
| Code | `pocket-radio-ios`, branch `feature/kcrw-apply` from `trunk` at `d29d7fad4` |
| Worktree | `pocket-radio-ios-alignment/` (sibling of `pocket-radio-ios/`; the untracked credential and generated files are already copied) |
| Shell changes | Docs only, unless the test boundary question below adds shared contracts |

**Goal:** For an eligible KCRW Eclectic24 station with Apply on, everything that shows the current song follows the player's clock: the lock screen, the full and mini players, and station detail. One adapter writes the radio fields of the system Now Playing record, from the selected song only. ICY, ACR and the feed's newest row can no longer overwrite it. Other stations, podcasts and the Off and Observe modes keep today's behavior.

**User checkpoint:** Play KCRW with Apply on. With the phone on the speaker, the lock screen title and artwork change when you hear the song change. The full player, mini player and station detail show the same song, and station detail highlights it in the history. Pause and resume from the lock screen, and the title stays right; stop and restart, and it is right again within a few seconds.

## Scope

- **Mode.** Replace the Observe toggle with one Debug picker, Off / Observe / Apply, stored under one key (`PocketRadio.alignment.mode`, launch argument `-PocketRadio.alignment.mode apply`) (D9). Observe stays a comparison mode that publishes nothing.
- **Publication adapter** (new, `podcasts/Main/Alignment/`). Turns a session decision into radio title, artist, album and artwork for `NowPlayingHelper`. It publishes only from a player-sample decision for the session's own item and generation, as the menubar's `RadioApplySelection` gate does. A feed receipt alone never publishes.
- **One writer.** For an eligible station in Apply, the radio writes from `RadioMetadataObserver` (ICY), `ACRFingerprinter`, and the feed-top paths in `PlaybackManager` and `StationDetailViewController` are skipped. Today's writers to check: `NowPlayingHelper.setRadioTrackInfo`, `setRadioAlbumTitle`, `setRadioArtwork`, `PlaybackManager.resolveRadioArtworkForLockScreen`, and the `radioStationNowPlayingDidChange` notification path.
- **Artwork** for the selected song only (D10). A full Now Playing rebuild keeps the selected artwork instead of reverting to the logo. Late artwork for an earlier song, item or station is rejected.
- **Unavailable state.** When the session has no selection, show the station name and no song. Never fall back to the feed's newest row. Show it only while this station is the active, playing item (menubar bug 2).
- **UI consumers.** Full player, mini player and station detail read the session snapshot. Station detail keeps feed order and highlights the selected song, not row zero. It no longer needs its own poll while Apply is on.
- **Lyrics** in 14.2 (D11 b′): today's lyrics stay in the app, but in Apply their album-field write (`StationDetailViewController` → `NowPlayingHelper.setRadioAlbumTitle`) is skipped. The media-clock lyrics are 14.3.
- **Endpoint.** Unchanged from 14.1: the measured HLS endpoint is used only for an eligible station with Observe or Apply on.

## Behaviors to test (red -> green, one at a time)

Tests use the `PocketCastsTests` host. Inject the clock, feed, and publication boundaries. Never write `UserDefaults.standard`.

1. **Mode resolution.** Off and Observe never publish; Apply publishes only for an eligible station. Release is always Off.
2. **No early publication.** A feed response alone does not change the published song; the next player sample does.
3. **Same-item guards.** Late feed, artwork or selection callbacks from an earlier item, generation, station or song are rejected at the adapter.
4. **One writer.** In Apply, ICY titles, ACR results and feed-top updates do not reach the radio fields of the Now Playing record. In Off and Observe they still do, unchanged.
5. **Artwork follows the selection.** Title, artist, album and artwork come from one song. A full rebuild keeps the selected artwork.
6. **Unavailable is explicit.** No clock or no history publishes the station name with no song, and no feed-top fallback; nothing is shown for a station that is not the active, playing item.
7. **Lifecycle.** A plain pause keeps the session, its clock and the published song (`testPausedSampleKeepsThePublishedSong`). Stopping or reloading the station tears the session down; the next session starts a new generation and clock, and its first valid sample republishes. Station and podcast switches stop publication for the old station.
8. **UI consumers.** Full player, mini player and station detail show the selected song; station detail highlights it in feed order.
9. **Regression.** Full unit suite and the CarPlay output suite pass with the mode Off. Tests that require feed-top fallback on ICY mismatch change only for the eligible station in Apply.

## Out of scope

- Lyrics on the media clock, the shared line index and removing the second lyric timer (14.3).
- Bluetooth, CarPlay and background validation and route latency (14.4).
- Enabling alignment in ordinary use or in Release (D9).
- Other stations, KEXP, MP3 and direct-AAC calibration; rewriting saved URLs; deleting lyric offsets.
- Replacing the whole artwork pipeline; only the single-writer rule for the eligible station.

## Decisions needed before implementation

| # | Question | Options | Recommendation |
|---|---|---|---|
| D9 (**decided: a, as one Off / Observe / Apply picker**) | How is Apply turned on in 14.2? | **(a)** A third Debug mode, Off by default; making it ordinary playback is decided after 14.4 has validated routes. **(b)** Ordinary playback for eligible stations once 14.2 is accepted, as the menubar did in M12. | **(a).** Lock screen behavior on Bluetooth and CarPlay is unproven until 14.4, and Debug gating keeps Release unchanged until then. The cost is that only a Debug build shows aligned titles for now. |
| D10 (**decided 2026-10-09: a**) | Where does the selected song's artwork come from? | **(a)** The selected row's KCRW artwork, then the existing iTunes resolver keyed on the selected title and artist, then the station logo. **(b)** Station logo only in 14.2. | **(a).** It matches today's look, and the guard against late artwork for an earlier song makes it safe. |
| D11 (**decided: b′**) | What do live lyrics do in Apply before 14.3? | **(a)** Hide live lyrics for the station while Apply is on. **(b)** Leave today's wall-clock lyrics, which follow the feed and will disagree with the aligned title. **(b′)** Keep today's lyrics in the app, but in Apply they do not write the lock screen's album field; the adapter owns it. | **(b′)**, chosen by the user. Today's lyrics stay; the lock screen never shows lyrics from a different song than its title. |

## Docs impact

- **Docs this changes or makes stale:** [ADR 0004](../adr/0004-kcrw-playback-clock-on-ios.md) (Observe only → Apply; publication rules) or a new ADR for the single-writer rule; `docs/ios/README.md` "KCRW alignment"; [bug 5](../bugs/bug_5.md) and [bug 6](../bugs/bug_6.md) for the eligible station; possibly `contracts/features/now_playing/` if aligned publication gets shared scenarios.
- **Questions this must settle:** whether the `+160 s` offset holds by ear on iOS; how to test aligned publication, given that the CarPlay harness streams loopback ICY, not HLS ([ADR 0003](../adr/0003-carplay-output-test-boundary.md)); whether the single-writer adapter should later serve every station (M14 D3).

## Hand-performed interactions

Ticked on the user's behalf on 2026-10-10, from the user's report that timing was correct and all steps passed (artwork differences filed as bug 9).


- [x] Apply on, speaker, screen locked: the lock screen title and artwork change when the song audibly changes, for at least two transitions.
- [x] Full player, mini player and station detail show the same song; station detail highlights it.
- [x] Pause from the lock screen, wait, resume: the title stays correct.
- [x] Stop (or Pause then Play in station detail), then play again: the title shows the station name briefly, then the correct song within a few seconds.
- [x] Switch to another station and to a podcast: their titles behave as before.
- [x] Apply off: KCRW behaves as before.
