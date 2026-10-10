# 0006 — Stopping a live station keeps a restartable lock-screen entry

**Status:** Accepted (2026-10-10)

## Context

For a live stream the lock screen shows Stop, not pause and skip (`updateRemoteCommandEnabledState`).
A paused live stream resumes on stale buffered audio, so the app ends the session on Stop and makes the
next Play a fresh connection. That was existing behavior (iOS M7.1).

Stop also cleared the Now Playing entry and removed the current item. On the device (2026-10-10) Stop
from the lock screen therefore could not be undone there. Play found no current item and returned "no
actionable item". Three seconds later the app released its audio session, and iOS dropped the app from the
lock screen, widget included. Podcasts were fine because a pause keeps the item and the entry.

## Decision

Stop ends the session as before, then keeps the station:

- `PlaybackManager.stoppedRadioStation` holds the stopped live station while nothing else is loaded.
- A stopped Now Playing entry stays: the station name, no song, rate 0, live-stream markers, and the
  station artwork.
- The lock-screen command set for that state is Play and toggle only (`RadioRemoteCommands.plan`). Skip,
  pause and stop are off.
- Play, or toggle, from the lock screen or headphones reloads the station through
  `RadioPlaybackStarter.reload`: a fresh connection, a fresh preroll, and in Apply a new session and clock.
- `load(episode:)` and `endPlayback` clear the stopped station. A refresh of Now Playing doesn't clear the
  stopped entry while it is held.

## Consequences

- The lock screen can restart a stopped station. The lock-screen widget stays up while the app is open or
  suspended in the background.
- The stopped entry lasts until another item loads or the app is terminated. It is in memory only.
- The stopped entry replaces the empty display that the CarPlay stop-and-replay scenario used to expect. The
  step now expects the station name, rate 0, and `stoppedRadioStation` set. Replay is unchanged.
- The home-screen widget still shows nothing live after a stop. It reads live state, and no station is playing.

## Rejected alternatives

- **Pause instead of Stop on the lock screen.** Resume plays stale buffered audio and can stall or jump. The
  aligned clock keeps titles right, but the audio is still wrong.
- **Keep the item in the queue in a stopped state.** A radio shim would then sit in the persistent queue. The
  app already drains stale radio shims at launch (`clearStaleRadioFromUpNext`). Holding the station in memory
  avoids that.
- **Leave it.** Stop on the lock screen would stay a one-way action.

Evidence: device log 2026-10-10 12:09:35 (`Remote control: stopCommand`, `stopRadioPlayback`,
`cleanupCurrentPlayer permanent? true`, then `deactivateAudioSession` 3 s later), and `RadioRemoteCommandsTests`.
