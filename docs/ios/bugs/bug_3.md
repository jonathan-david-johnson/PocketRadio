# Radio inherits podcast playback speed

Status: fixed. User reported the device issue appears resolved and approved commit (2026-09-12).

## Evidence (2026-09-12)

KCRW/KEXP sounded degraded and intermittently stuttered on the physical device.
The user compared the KCRW app on the same speaker, then resumed PocketRadio
and heard music playing faster. Retrieved device preferences showed
`SJGlobalSpeedSetting = 1.1`. `PlaybackManager.loadEffects()` falls back to
global podcast effects for radio, and `DefaultPlayer` applies that speed.

Consuming a live stream at 1.1× can exhaust initial buffering; pitch-preserving
speed changes can degrade music. These explain the symptoms plausibly, but
neither the actual running AVPlayer rate nor the buffer depletion was measured.
Routing problems may be separate.

Device logs also showed the shelved experimental `RadioStreamLoader`, absent
from the simulator's current source. Bluetooth, AirPlay, and HEOS were mixed
during comparisons, so earlier output comparisons were not controlled.

## Fix

`PlaybackManager.effects()` resolves radio to fresh neutral effects before
consulting cached/global podcast settings: 1.0×, no silence trimming, no volume
boost. Registry-based radio identification covers SQLite Episode shims.
`changeEffects` ignores radio speed/effect commands before preference writes.
Podcast settings remain unchanged.

Five regression tests cover neutral effects, lazy preference lookup, restoring
podcast effects, mutation isolation, and registered radio shims.
Full simulator suite: 847 passed, 0 failures, from
`Test-Pocket Casts Staging-2026.09.12_21-01-56--0400.xcresult`.
Device build/install/launch succeeded. User confirmed the apparent fix after testing.

## Manual check

Play KCRW/KEXP for 10–15 minutes over explicitly selected Bluetooth. Confirm
normal tempo, quality, and uninterrupted playback; switch outputs; then return
to a podcast and confirm its configured speed remains intact.

The installed build also removes the shelved stream-loader experiment, so a
successful device run alone cannot isolate which symptoms that loader caused.
Original logs are preserved locally under `/tmp/pocketradio-device-audio/`.
