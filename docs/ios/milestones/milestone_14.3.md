# iOS M14.3 — KCRW lyrics on the media clock

**Status**: PLANNED
**Depends on**: [M14](milestone_14.md); M14.2 closed (`archive/ios-m14.2`, [ADR 0005](../adr/0005-kcrw-aligned-now-playing-single-writer.md)) and merged to `trunk`. The mini player, widget art, clock-fault hold and lock-screen Stop fixes are committed on `trunk`.
**Required by**: M14.4 (routes and background), which checks lyrics on each route.

## Where the work happens

| | |
|---|---|
| Plan and reports | Shell `main`: this file, `docs/ios/experiments/`, `docs/ios/bugs/` |
| Code | `pocket-radio-ios`, branch `feature/kcrw-lyrics` from `trunk`. Created after those fixes were committed, so the two don't mix. |
| Worktree | `pocket-radio-ios-alignment/`, reused. Credentials and generated files are already copied. |
| Shell changes | Docs only |

**Goal:** With Apply on, live lyrics for KCRW follow the audio. Today the line is chosen from broadcast wall time, so a pause, a stall or opening full-screen lyrics puts it out of step. After this milestone the position is the song's seconds on the player's own clock. Station detail and full-screen lyrics read the same position and pick the same line. Opening full-screen lyrics and coming back no longer resets the correction. Other stations, podcasts and the Off and Observe modes keep today's behavior.

**User checkpoint:** Play KCRW with Apply on, on the speaker, and open station detail during a song that has synced lyrics. The highlighted line follows the audio for the whole song. Pause for 15 seconds and resume: it is still right. Let the song change: the next song's lyrics start in the right place. Open full-screen lyrics from the current song's row, nudge once, go back and return: the line is still right and the nudge is still there.

## Scope

- **Position source.** For a station in Apply, lyric position is `songSeconds` from the session's selected occurrence, not `Date() − playedAt + saved offset`. The station's session already carries `songSeconds`, `mediaSeconds` and `programDate` in `RadioAlignmentSnapshot`. The adapter that publishes the song (`AlignedNowPlayingState`) gains a read for "song seconds now". Between player samples it advances only while the player is playing, so a pause holds the line. Between samples the position is extrapolated from the last sample while the player is playing (decided 2026-10-10).
- **One clock, one index.** `LyricSyncController` (station detail) and `LyricsViewController` (full screen) both read that position. A shared function turns a position and a lyric list into a line index. Equal timestamps pick one line. The full-screen view's own timer and its `initialOffset` reconstruction go away for an applying station.
- **Correction** (the `−` and `+` buttons). In Apply it is held in memory, keyed to the current occurrence. It resets for a new occurrence and for a station change. It does not read the saved `lyric_offsets` values and does not write them (M14 scope).
- **Navigation.** Pushing full-screen lyrics calls station detail's `viewDidDisappear`, which stops `LyricSyncController` and zeroes its offset. In Apply that must neither reset the correction nor the clock, and the full-screen buttons must adjust the same correction as station detail.
- **Late work.** A lyric fetch or position callback for an earlier occurrence, station or generation is dropped. A repeat play of the same song is a new occurrence and reloads its lyrics.
- **Unavailable.** When the session has no selected song or no valid clock, lyrics show no timed highlight. Station detail shows the station name, as it does for the title. Plain (unsynced) lyrics and "No lyrics found" are unchanged.
- **Unchanged on purpose.** In Apply the lyrics still don't write the lock screen's album field (D11 b′ from 14.2). CarPlay and Bluetooth lyric display is [bug 7](../bugs/bug_7.md) and stays out of scope.

## Behaviors to test (red -> green, one at a time)

Tests use the `PocketCastsTests` host. Inject the clock, the lyric loader and the saved-offset store. Never write `UserDefaults.standard` or the real `lyric_offsets` table.

1. **Session position.** For an applying station, the lyric position equals the session's song seconds. The wall clock is never read.
2. **Pause holds the line.** While the player is paused, the position doesn't advance. After resume it continues from where it was.
3. **Same line everywhere.** Station detail and full-screen lyrics return the same index for the same position. Equal timestamps pick one line.
4. **Navigation keeps state.** Leaving station detail to open full-screen lyrics and returning changes neither the position nor the correction. There is no second timer.
5. **Correction is per occurrence.** A nudge moves the line. A new occurrence, including a repeat of the same song, resets it. A station change resets it.
6. **Saved offsets are untouched in Apply.** A nudge calls neither the read nor the upsert of `lyric_offsets`. In Off and Observe, today's read and debounced write still happen.
7. **Late results are dropped.** A lyric fetch for an earlier occurrence, station or generation never changes the displayed lines.
8. **Unavailable is explicit.** No selected song or no valid clock gives no timed highlight and no wall-clock fallback.
9. **Off and Observe are unchanged.** The wall-clock path, saved offsets and timer behave as today.
10. **Regression.** Existing lyric, radio, CarPlay output and artwork tests pass. The CarPlay output suite must show no new album-field write in Apply.

## Out of scope

- Bluetooth and CarPlay display of lyrics, background polling, and route delay (14.4).
- Bug 7 (lyric text reaching CarPlay Now Playing).
- Making Apply the default, and removing the `−` / `+` buttons. Hide them only after multi-route validation, per the review.
- Other stations and lyric lookup quality (version matching, search fallback).
- Showing lyrics outside station detail and full-screen lyrics.

## Decisions needed before implementation

| # | Question | Options | Recommendation |
|---|---|---|---|
| D12 (**decided 2026-10-10: a**) | Where does the lyric position come from for consumers? | **(a)** A read on `AlignedNowPlayingState`, which the Apply session keeps current. **(b)** Each screen subscribes to session snapshots itself. | **(a).** One owner, and screens only sample it. It matches the review's rule that a screen never starts or stops the monitor. |
| D13 (**decided 2026-10-10: a**) | Who owns live-lyric state? | **(a)** It stays in `StationDetailViewController` (today), with the clock moved to the session. **(b)** A session-level lyric controller that lives while the station plays, and screens only display it. | **(a).** It is the smaller change. The reset bug comes from the clock and the correction, not from who owns the fetch. Revisit (b) if 14.4 shows leaving station detail still drops lyrics. |
| D14 (**decided 2026-10-10: a**) | How do saved `lyric_offsets` behave in Apply? | **(a)** Ignored and never written (M14 scope). **(b)** Read as a starting correction. | **(a).** The saved values compensate for the old wall-clock error and would double-correct. Confirm by ear in the checkpoint. |

## Docs impact

- **Docs this changes or makes stale:**
  - [ADR 0005](../adr/0005-kcrw-aligned-now-playing-single-writer.md): lyrics become a second consumer of the aligned state, and D11 b′ ends. Extend it, or write a new ADR that supersedes the lyric part.
  - The "KCRW alignment" section of `docs/ios/README.md`.
  - The alignment and lyric rows in `docs/test-architecture.html`.
  - Menubar [ADR 0002](../../menubar/adr/0002-radio-lyrics-sync.md): its note about the KCRW offset gains a pointer to the iOS result. The shared KCRW ADR written when M14 closes finishes that job.
  - The lyric-related sections of the [stream-monitoring review](../architecture/reviews/stream-monitoring-review-2026-09-16.md) that this resolves.
  - Code comments in `podcasts/Main/Alignment/` and the lyric files cite ADRs, never this file.
- **Questions this must settle:**
  1. How the extrapolation behaves at the edges: after a stall, a seek, and a clock discontinuity. (It extrapolates from the last sample while playing; decided 2026-10-10.)
  2. Whether the saved-offset values are ever useful in Apply (D14, by ear).
  3. Whether the lyrics for an applying station should survive leaving station detail (D13).
  4. Whether the correction should persist for the next song once the clock proves accurate, or always start at zero.

## Hand-performed interactions

- [ ] Apply on, speaker: during a song with synced lyrics, the highlighted line follows the audio for the whole song.
- [ ] Across a song change: the next song's lyrics start at the right place within a few seconds.
- [ ] Pause for 15 seconds, then resume: the highlighted line is still right.
- [ ] Open full-screen lyrics from the current song's row, tap `+` once, go back and return: the line is still right and the nudge is kept.
- [ ] Let the song change with a nudge applied: the next song starts at zero correction.
- [ ] Leave station detail and come back mid-song: the line is still right.
- [ ] Apply off: KCRW lyrics behave as before, including the saved offset.
- [ ] Another station and a podcast: lyrics and artwork behave as before.
