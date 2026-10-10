# In Apply, one aligned adapter is the only writer of KCRW's current song

**Decision:** Accepted 2026-10-10. With the Debug alignment mode set to Apply, an eligible KCRW Eclectic24 station's current song comes only from `AlignedNowPlayingPublisher`, driven by the player-clock session of [ADR 0004](0004-kcrw-playback-clock-on-ios.md). ICY, the tracklist's newest row, the lyric album line and ACR do not reach Now Playing or the players for that station. Off and Observe keep the previous behavior; Release is always Off.

## What the device showed

On "Jonathan iPhone", speaker, Wi-Fi, 2026-10-10, the user confirmed by ear that the lock-screen title and artwork changed when the song audibly changed, over at least two transitions. That means the `+160 s` feed-to-program offset measured on the menubar holds on iOS for this route. The user also confirmed:

- full player, mini player and station detail named the same song, and station detail marked it;
- pause and resume from the lock screen kept the title;
- stop and restart showed the station name briefly, then the right song;
- another station, a podcast and mode Off behaved as before.

Evidence: `archive/ios-m14.2:docs/ios/milestones/milestone_14.2.md` (hand-performed interactions). Bluetooth, CarPlay and a backgrounded app are not yet validated (M14.4).

## Design choices

| Choice | Reason | Alternatives not selected |
|---|---|---|
| **One Debug picker, Off / Observe / Apply**, stored as `PocketRadio.alignment.mode` (`-PocketRadio.alignment.mode apply` at launch). | Two toggles would allow a meaningless Observe-and-Apply state. Debug gating keeps Release unchanged until routes are validated. | A second toggle; ordinary playback for KCRW now, as the menubar did. |
| **Fail-closed publish gate.** A song is published only from a player-sample decision with a program date, a selected occurrence equal to the candidate, kind `trackplay`, non-empty title and artist, and finite song seconds ≥ 0. No selection publishes "unavailable" (station name, no song). A feed receipt never publishes. | Ported from the menubar's `RadioApplySelection`. The feed runs about 160 s ahead of the audio, so publishing on receipt would show the next song early. | Falling back to the feed's newest row when the clock or history is missing. |
| **Publish on change, comparing the whole song.** | A feed correction to the current song's title, artist, album or art republishes it; the same song across samples does not. | Comparing occurrence ids only, which leaves corrections stale until the next song. |
| **Ownership by session generation.** `AlignedNowPlayingState` belongs to one station and generation. A late stop of an older session cannot clear a newer one; posts and images after the session ends are dropped. | Station switches and restarts overlap with in-flight callbacks. | Clearing state on any stop. |
| **Consumers ask `isApplying(stationId:)`** (`AlignedConsumers`). `TrackArtworkResolver.bestResolveEntry` returns the aligned song, or nil when unavailable, while applying. That one change moves the lock-screen artwork, the full-player labels and art, the mini-player art and the widget onto the aligned song. | Smallest upstream diff; one switch point. | Editing each consumer to read the session. |
| **Standing down in Apply:** `RadioMetadataObserver` is not attached (no ICY); `handleRadioTrackChanged` honors only aligned posts and never borrows the tracklist album; `handleRadioTracklistRefreshed` does nothing; station detail does not write Now Playing from its tracklist poll or lyric album line, and hides Identify (ACR); the CarPlay-disconnect album restore uses the aligned song. | Every other writer would overwrite the aligned title ("last writer wins"). | Keeping ICY as a tiebreaker. |
| **Lyrics stay on today's wall clock (D11 b′)**: lyrics show in the app, but in Apply they do not write the lock screen's album field. | The aligned title runs about 160 s behind the feed-driven lyrics; the album field would name a different song. Media-clock lyrics are M14.3. | Hiding lyrics in Apply; leaving the album-field write. |
| **Artwork names the same song as the title.** On a song change the lock screen shows the station logo until the new song's art loads; the loaded image is stored for that occurrence only and survives a full Now Playing rebuild; a late image for another occurrence is dropped. Art comes from the feed row's image, then the iTunes lookup, then the logo. | Title and art from one song. Fixes [bug 5](../bugs/bug_5.md) and [bug 6](../bugs/bug_6.md) for the applying station only. | Keeping the previous song's art until the new one loads (art and title disagree for a moment). |
| **A plain pause keeps the session.** Lock-screen or Control Center pause leaves the session, its clock and the published song in place. Stop or a station reload tears it down; the next session republishes from its first valid sample. | `DefaultPlayer.pause()` only pauses the player. Earlier wording that "pause tears the session down" was wrong. | Tearing down on pause (not how the iOS player works). |

## Consequences

- **Bug 9 stays open.** The mini player and the home-screen widget showed the station logo while the full player showed album art (user, 2026-10-10). The widget passes only the feed row's art URL, without the iTunes fallback; the mini player's cause is unconfirmed. See [bug 9](../bugs/bug_9.md).
- **Testing boundary.** Aligned publication is covered by unit tests at the adapter and consumer boundaries (`AlignedNowPlayingTests`, `AlignedConsumersTests`). The CarPlay output harness streams loopback ICY, not HLS, so it does not exercise Apply end to end ([ADR 0003](0003-carplay-output-test-boundary.md)). The `PlaybackManager` radio handlers are tested only through the extracted decision `AlignedConsumers.trackWrite`; their wiring was checked on the device.
- **Other stations.** The adapter is keyed by station and could serve any station with a clock and a timed feed (M14 D3); it is enabled for the eligible KCRW variants only.
- **Threading.** `AlignedConsumers` reads main-actor state directly on main and by `DispatchQueue.main.sync` otherwise. All traced callers run on main; the sync hop is safe only while main never waits on the calling thread.
- **Station detail** still runs its own tracklist poll in Apply, for its history list and the wall-clock lyrics.

## Verification

| Behavior | Covered by |
|---|---|
| Mode resolution; endpoint only in Observe or Apply | `KCRWEndpointResolutionTests`, `AlignmentObserveViewModelTests` |
| No early publication; publish on change; corrections republish; same-item and generation guards; unavailable; lifecycle; pause keeps the song | `AlignedNowPlayingTests` |
| One writer; artwork follows the song; unavailable display; station detail marks the row; Off and Observe unchanged | `AlignedConsumersTests` |
| Default Off unchanged | Full `PocketCastsTests` (1,133 tests) and CarPlay output suite (128) with the mode Off |
| Timing by ear and every checkpoint step | User on the device, 2026-10-10 |
