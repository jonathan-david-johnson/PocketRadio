# 0007 — Live radio resumes after a stall without seeking

**Status:** Accepted (2026-10-10)

## Context

`DefaultPlayer` recovered from `AVPlayerItemPlaybackStalled` by calling `play()`, except for HLS podcasts. `play()` seeks to the episode's saved position. A live radio station keeps a saved position like any episode, and for a live stream that value is stale.

The device log (2026-10-10, 16:18 and 16:20, on a metered connection) showed the effect on KCRW's HLS stream:

| | Stall 1 | Stall 2 |
|---|---|---|
| Playhead before and after | 473.9 s → 396.0 s | 533.8 s → 461.9 s |
| Rewind | 78 s | 72 s |
| Time spent waiting | 6 s | 14 s |

The seek flushed the buffer and refetched older segments, so the audio dropped out for 6 to 14 s, then replayed the last minute or so. The title and artwork showed the previous song because that audio really was playing. The stream also stayed that far behind live for the rest of the session.

## Decision

A live radio station resumes after a stall the way an HLS podcast already does: re-apply the rate and let AVPlayer resume once it has buffered enough, with no seek (`StallRecovery.resumesWithoutSeeking`). Other episodes keep the old recovery.

The stall log line now records the buffer ahead, keep-up, buffer-empty and the preferred forward buffer, and each alignment probe line carries `buf=` and `keepUp=`, so a later dropout can be explained from the log.

## Consequences

- A stall still costs the time to refill the buffer. It no longer rewinds the stream.
- `preferredForwardBufferDuration` is still unset for live radio, so AVPlayer chooses the buffer. If dropouts remain after this change, raise it for live radio (about 30 s) and read the `buf=` series first.
- A stall is not a clock fault. The aligned clock stays valid through a stall that doesn't seek, so the title hold is not involved.

## Rejected alternatives

- **Keep `play()` and reset the saved position first.** A live stream has no position to return to. Skipping the seek is simpler.
- **Raise the buffer now.** It wouldn't stop the rewind, and the data to size it wasn't there yet.

Evidence: device log lines `Received notification of playback stall` and `Trying to recover from stall by playing` at 16:18:02 and 16:20:26, with the media and program-date values in the probe lines either side; `StallRecoveryTests`.
