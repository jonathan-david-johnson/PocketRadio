# Live lyric text can appear in CarPlay Now Playing

**Status:** Open. Observed on 2026-10-08 in the normal app on the signed-out CarPlay simulator; source path investigated, connection-state cause unresolved. No production fix or physical-car verification.
**Evidence:** `archive/ios-m13.2:docs/ios/experiments/2026-10-08_m13_2_manual_carplay.md` and the screenshots under `archive/ios-m13.2:docs/ios/experiments/traces/2026-10-08_m13_2_manual/`.

## Observed behavior

During real KCRW Eclectic 24 playback, CarPlay displayed Carnival / Natalie Merchant with a lyric sentence in the third line rather than the album Tigerlily. The user heard playback and completed four songs / three transitions. The normal app had no harness enablement. This violates Apple's CarPlay Developer Guide, page 4, “Additional guidelines for CarPlay audio apps,” rule 1: “Never show song lyrics on the CarPlay screen.” It also violates the app's lyric-suppression policy.

## Code path

Live lyric lines are emitted by `LyricSyncController.tick(at:)` in `pocket-radio-ios/podcasts/Radio/LyricSyncController.swift`. For each current lyric line it calls the delegate's `didUpdateNowPlayingAlbum` callback with `line.text`. `StationDetailViewController` implements that callback in `pocket-radio-ios/podcasts/Radio/StationDetailViewController.swift` and forwards the text to `NowPlayingHelper.setRadioAlbumTitle`.

`NowPlayingHelper.setRadioAlbumTitle` in `pocket-radio-ios/podcasts/NowPlayingHelper.swift` writes the lyric text to `MPNowPlayingInfoCenter.default().nowPlayingInfo[MPMediaItemPropertyAlbumTitle]`. Its only CarPlay protection is an early return when `CarPlaySceneDelegate.isConnected` is true. The system Now Playing record is shared with CarPlay, so if that guard is missed, the lyric becomes the car's album/third line.

`CarPlaySceneDelegate` sets that flag in the CarPlay scene's `didConnect` callback and clears it during `handleDisconnect()`. Existing unit and output-policy tests exercise the writer with the flag manually set (`CarPlayConnectionStateTests.testAlbumTitleSuppressedWhenConnected`) and the shared disconnect path (`CarPlayPolicyTests` / `carplay_policy.feature`). They do not establish that Apple's real scene lifecycle callbacks always keep the flag synchronized with CarPlay's visible connection state. The most likely failure boundary is therefore connection-state/lifecycle synchronization, but the manual observation did not capture the flag or callback timeline, so the precise cause remains unproven.

The accepted publication policy forbids lyric album writes while CarPlay is connected. Automated `CarPlayPolicyTests` pass at the modeled connection flag and real publishing boundary; `PolicyStepsTests` also exercises the shared disconnect cleanup with a genuinely published pre-connect lyric. Neither proves that system scene callbacks keep the app's flag in agreement with visible CarPlay activity.

No connection-flag snapshot, raw Now Playing dictionary, or scene callback trace was captured during the manual run. The screenshot proves the visible lyric, not which writer or callback caused it. Do not label the complete real-world policy path as passing or add a broad expected-failure marker from this observation.

## Related observations, not established as the same bug

| Observation | Evidence and limit |
|---|---|
| Station-only identity at startup | Anyone Else But You had phone artwork, while CarPlay showed KCRW identity. No startup event timeline was captured. |
| Tracklist transition lag | The user reported audio preceding the Carnival tracklist change by roughly 10 seconds. This is a listener estimate, not a measured clock offset. |
| Transport glyph disagreement | Phone showed Pause while CarPlay showed Play throughout the screenshots; playback was audible. No transport-state probe was attached. |
| Uncertain fallback artwork | For A Good Day (Clean), tracklist used the station logo but miniplayer showed a different small red/white image. Its source was not established; do not claim all artwork sources missed. |
| Lyric correction | The user reported that a −37-second adjustment aligned A Good Day phone lyrics. Retrieval/synchronization work remains deferred; this is not a diagnosis. |

In this simulator setup, artwork-derived gradients without visible covers are expected. Phone covers and approximate CarPlay colors do not prove the exact artwork published in `MPNowPlayingInfoCenter`. The user's actual car displays covers, but no physical-car check was performed for this baseline.

## Next investigation

Capture scene connect/disconnect events, app connection state, publication provenance and the raw Now Playing fields during the same audible playback timeline. Keep transport-state and timing observations distinguishable. Do not conflate the lyric-publication policy discrepancy with lyric synchronization.

The user accepted the regression baseline with these discrepancies deferred. That approval was not an all-policy app sign-off. The harness boundary is documented in [ADR 0003](../adr/0003-carplay-output-test-boundary.md); manual simulator setup is in the harness README.
