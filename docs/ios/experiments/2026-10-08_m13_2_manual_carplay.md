# M13.2 — manual CarPlay observations

**Status:** User completed four songs / three transitions on 2026-10-08, then accepted the recorded discrepancies and explicitly approved committing the test/docs baseline. This is not an all-policy pass. No app fixes or physical-device run.
**Code:** Normal app from `pocket-radio-ios-carplay/`, `feature/carplay-harness`, uncommitted on `2358aab83` at observation time; subsequently committed as `12c3cfb60`. Harness not enabled.
**Device:** Dedicated signed-out simulator, `6565636E-BB8D-4C34-A9EB-56F2BB638400`, iOS 26.5; KCRW Eclectic 24 live playback.
**GUI:** Xcode 26.5 Simulator from `~/Downloads/Xcode.app`. Active developer directory stayed `/Applications/Xcode.app/Contents/Developer` (Xcode 27).

## Display boundary

The user reports that this CarPlay simulator does not draw a cover image, but uses an artwork-color gradient. The user's actual car shows artwork. These screenshots confirm the simulator's cover omission, not physical-car rendering.

Do not classify the missing visible cover as an artwork-publication failure. Conversely, phone tracklist covers and approximate background colors do not prove the exact artwork in `MPNowPlayingInfoCenter`. Automated artwork checks still read that record; their assertions are unchanged.

## Observations

| Song / screenshot | User report | Visible output |
|---|---|---|
| [Anyone Else But You](traces/2026-10-08_m13_2_manual/01-anyone-else-but-you.png) — Rubblebucket, 05:45 | Playing on launch; cover visible in tracklist, not CarPlay | Tracklist and phone miniplayer have the song image. CarPlay still shows KCRW Eclectic 24 in its title/artist/third lines rather than the song identity; LIVE is present. |
| [Carnival](traces/2026-10-08_m13_2_manual/02-carnival.png) — Natalie Merchant, 05:47 | Audio changed roughly 10 seconds before the tracklist switched; lyrics not synchronized | CarPlay shows Carnival / Natalie Merchant, with a lyric sentence in the third line rather than Tigerlily. Phone tracklist/miniplayer show the Tigerlily cover; CarPlay background is blue/teal. |
| [A Good Day (Clean)](traces/2026-10-08_m13_2_manual/03-a-good-day.png) — Anderson Paak, 05:52 | No album art found; no lyrics in CarPlay | Tracklist uses the station logo; CarPlay third line is A Good Day, with a muted gray/brown background. The phone miniplayer has a different small red/white image; its origin is not established by the screenshot. Do not infer that all artwork sources missed. |
| [A Good Day lyric page](traces/2026-10-08_m13_2_manual/04-a-good-day-lyric-offset.png), 05:53 | Manual offset of -37 seconds brought lyrics into alignment | Phone lyric page displays -37s. CarPlay retains the album-like third line A Good Day, not a lyric. No lyric-timing diagnosis performed. |
| [Simetachin (featuring Derib Zenebe and Dexter Story)](traces/2026-10-08_m13_2_manual/05-simetachin.png) — Cut Chemist, 05:54 | Artwork correct; CarPlay background appears to follow its colors | Matching beige artwork appears in tracklist/miniplayer. CarPlay background is brown/beige; title is truncated, artist is Cut Chemist, third line is Simetachin, and LIVE remains visible. |

All screenshots show the phone's Pause control while CarPlay shows a Play glyph. This is a visible control-state discrepancy, not proof of playback stopping; the user reports hearing playback. No transport-state probe was attached.

## Policy follow-up, not lyric-sync work

Carnival's visible lyric in the CarPlay third line conflicts with approved S7 (no lyric album writes while connected). This is separate from whether lyrics are synchronized. Record the counterexample without debugging lyric timing or fixing production code.

The automated S7 tests pass at the modeled connection flag / real publishing boundary and shared disconnect handler. They do not prove that system CarPlay activity and the app's connection flag agree through every scene lifecycle. No flag snapshot, raw Now Playing dictionary, or scene callback trace was captured during this manual run; the cause is unresolved. Do not relabel the entire real-world S7 path as passing or add a broad expected-failure marker from these images alone.

The startup station-only identity, approximately 10-second transition lag, control glyph discrepancy and uncertain fallback image are also recorded without assigning a cause. A still image cannot establish event ordering, callback delivery, metadata provenance or artwork continuity.

Lyric retrieval/synchronization and the -37-second adjustment remain deferred at the user's request. These observations alone did not authorize an app fix, test-contract weakening, device tests or a commit. The subsequent explicit approval covers baseline commits only.

## Simulator setup findings

- Xcode 27's frontend is Device Hub, not the legacy `Simulator.app`; the normal `make run_sim` launch helper's `open -a Simulator` failed on this machine.
- The user downloaded and expanded Xcode 26.5 into `~/Downloads`. Its Simulator provided **I/O → External Displays → CarPlay** without changing `xcode-select`.
- Initially both frontends were attached and input did not work. Quitting Device Hub while keeping devices running alone did not restore Home input.
- Restarting only the dedicated simulator and launching the legacy UI with its own `DEVELOPER_DIR` restored Home input, verified both before and after reopening CarPlay. No erase occurred. The user then completed the observations above.
- Coexisting frontends or toolchain routing may have contributed, but the restart did not isolate their individual causes.

## Approval and remaining work

After the observations were documented, the user explicitly approved committing
the regression baseline with these limitations deferred. iOS baseline commit:
`12c3cfb60`. No app fix, test weakening, device run, push, merge or milestone
closure was approved. The discrepancies still require separately scoped follow-up;
this is not a clean app-output sign-off.
