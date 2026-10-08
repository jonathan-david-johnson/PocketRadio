# Bug 6 — Late radio artwork overwrites the display after an episode switch

**Status:** Open. Reproduced in M13.2's real-playback simulator harness on 2026-10-07. No fix or device observation.
**Evidence:** [M13.2 unmarked baselines](../experiments/2026-10-07_m13_2_baselines.md#late-artwork-races), `carplay_races.feature` scenarios “Switching stations prevents the old station's artwork from publishing” and “Switching to a podcast prevents radio artwork from publishing over it”.

## Symptom

The listener switches from a station while its artwork is downloading. The new station or podcast appears correctly. When the old download finishes, the display's title remains the new item but artwork changes to the old radio song's image.

Individual harness observations, relative to the old artwork request:

| Switch | Identity changed | Old response finished | Old red artwork observed |
|---|---:|---:|---:|
| Another local station | +7.748 s | +20.011 s | +20.049 s |
| Local podcast episode | +7.768 s | +20.009 s | +20.046 s |

The output step failed with diagnostic `display.race.no-red-artwork`. Both individual runs proved the delayed request and changed playback identity before observing its response and polling through callback delivery. A later combined run had an unrelated readiness timeout; suite-level stability is not yet established.

## Cause

`PlaybackManager.resolveRadioArtworkForLockScreen` checks the current episode before starting Kingfisher. After the image download, its completion checks only `lastResolvedRadioKey`, then dispatches an unconditional `NowPlayingHelper.setArtworkImage` call to the main queue.

Switching away to an unenhanced station or podcast can leave the old dedupe key unchanged. The download passes that key check even though the current episode no longer owns it. The main-queue write does not recheck the episode or song identity.

This is a different hole from the stale-song hypothesis in M13 E7: changing to another enhanced song updates the key and the song-to-song guard passed in M13.2.

## Test boundary

The harness reads `MPNowPlayingInfoCenter`, not CarPlay rendering. The podcast fixture plays actual loopback MP3 media and cleans up its synthetic database rows. The assertion tests radio artwork interference, not upstream podcast behavior. Polling can detect observed stale publication; it cannot rule out unsampled instants.

## Next step

Keep fixes in `fix/stream-presentation`. Before shipping an iOS expected-failure entry, repeat the unmarked station/podcast scenarios under stable host conditions, then associate only their designated no-stale-art assertion with this bug. Never suppress readiness or network failures.

## Harness update — 2026-10-08 UTC

The repeat/registration work above is now verified. Both scenarios map only their
`display.race.no-red-artwork` output check to bug 6; identity/readiness/network
failures remain ordinary. Completion evidence includes the old request, new
identity, delayed server response, downloaded client-cache entry and a callback
hold after completion.

[Final verification](../experiments/2026-10-08_m13_2_verification.md) records three
consecutive full 128-test passes, with both designated defects reproduced in each
and no host sleep. This establishes observed suite stability under those conditions,
not a proof against unsampled transient writes. The stale-callback bug is not fixed.
