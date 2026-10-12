# Bug 13 — After the app is killed and reopened, the player offers KCRW but says "File not uploaded, unable to play"

**Status:** Open. Reported by the user on 2026-10-12 on the device. Not fixed. The cause below is read from the code and fits the symptom; no log was captured for the reopen, so it is unconfirmed.
**Evidence:** User report. `PlaybackManager.clearStaleRadioFromUpNext` (`podcasts/PlaybackManager.swift`, called from `AppDelegate.swift`), `RadioStationRegistry` (`podcasts/Radio/RadioStationRegistry.swift`), and the error text in `PlayerCell.updateDownloadStatus`.

## Symptom

While KCRW was playing, the app was killed. After reopening, the mini player and full player show KCRW as the item to play, with the message "File not uploaded, unable to play". Tapping play does nothing. Going to the Streams list and starting KCRW again works.

## Root cause (unconfirmed)

- A live station is a `RadioStation` shim saved into the episode table as the current queue item, so it survives an app kill.
- The "is this a live station" test uses `RadioStationRegistry`, which is **in memory only**. After a relaunch it is empty, so the restored current item is no longer recognized as radio. Its uuid is not in the registry and `liveStation()` returns nil.
- The shim is stored as a `UserEpisode` with `uploadStatus` "missing". With no registry entry the player treats it as a user file that was never uploaded, and `PlayerCell` shows `download_error_not_uploaded` ("File not uploaded, unable to play"). It has no playable file URL, so play does nothing.
- `clearStaleRadioFromUpNext` drains stale radio shims at launch, but only from positions 1 and up. Position 0, the current item, is left alone ("that may legitimately be a radio station mid-playback"), which is wrong after a relaunch because nothing is playing.

## Proposed fix

At launch, if the current queue item is a station shim and no player is running, remove it (the same rule as for the rest of the queue), using the curated station ids and the saved favorites to recognize a shim, since the registry is empty. A stopped-station entry from ADR 0006 is in memory only and is not affected.

A softer alternative: re-register curated and favorite stations at launch so the restored item is recognized, and let play reload it. That keeps "resume KCRW" across a kill, at the cost of an automatic reconnect.

## To find it

Reproduce on the device: play KCRW, kill the app from the switcher, reopen, and read the log at launch (`PlaybackManager`, `Loading` lines). Check the queue's current item: `DataManager.sharedManager.allUpNextEpisodes()` after launch. If the item is a `UserEpisode` with the station's uuid, the cause is confirmed.

## Files involved

- `podcasts/PlaybackManager.swift` (`clearStaleRadioFromUpNext`), `podcasts/AppDelegate.swift`, `podcasts/Radio/RadioStationRegistry.swift`.
- Tests under `PocketCastsTests/Tests/Radio/`: a queue with a station shim at position 0 and an empty registry ends with the shim removed.
