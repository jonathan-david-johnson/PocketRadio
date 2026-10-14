# 0010 — Timing is one skew per station, set by a ShazamKit heal and fine-tuned by hand

**Decision:** Accepted 2026-10-14 for the iOS `experiment/unified-skew` branch (not yet merged to `trunk`). KCRW Eclectic24 on the phone's speaker only. Replaces the frozen `+160 s` constant in [ADR 0004](0004-kcrw-playback-clock-on-ios.md) and the per-occurrence lyric nudge in [ADR 0008](0008-kcrw-lyrics-follow-the-media-clock-in-apply.md).

## What the device showed

Measured on "Jonathan iPhone" (iPhone 15), StagingDebug, KCRW on the phone's speaker, over about 6 hours. Evidence: `docs/ios/experiments/2026-10-12_unified_skew.md` (device logs, `[anchor]` and `[heal]` lines).

| Question | Result |
|---|---|
| Does one heal, from any starting skew, find the skew? | Yes. From skew 0 it saved 158.7 in 21 s (three anchors). From saved values (157.2, 157.5, 158.4) it moved by 0.2 to 1.8 s. The user judged titles and lyrics "dead on" after the heal. |
| Is the skew constant per station? | Not quite. Six songs gave 158.7, 158.0, 158.4, 158.6, 156.8 and 155.8. The spread is 2.9 s. Anchors within one song agree within 0.1 s, so the spread is between songs. The likely causes are the feed's stamp for each song and each recording's edit. Not confirmed. |
| Does the heal have a constant bias against the user's ear? | No. Of five heals the user judged, three were left as healed, one of them "dead on". Two were nudged by −0.5 and −1.5. A constant would have made the three worse. |
| Do wrong versions fool the heal? | Yes, before the fix. A feed title "(Liza Richardson remix)" against ShazamKit's plain title gave anchors 99 s off; "(radio edit - clean)" gave 8 s off. Anchors from one song agree with each other, so agreement can't catch it. |
| Does ShazamKit accept back-to-back sessions? | No. A session opened right after another closes is refused with "Missing entitlements" (an inaccurate message), as it was when a cancelled heal ran its waits at once. |
| Does the skew survive a relaunch? | Yes. Sessions started at 159.0, 158.6 and 156.8 from the saved value. |

## Design choices

| Choice | Reason | Alternatives not selected |
|---|---|---|
| **One number per station, the skew:** a song the feed stamps at `T` starts in the stream at `T + skew`. Everything the aligned session shows reads it. Saved in `UserDefaults` on this device, with a seed (KCRW 160, anything else 0). A saved 0 counts as saved. | The title, artwork, song position, lyrics, lock screen and widget have to move together. The value depends on this device and speaker, so it is not shared across devices. | Keep three inputs (a constant, a Debug skew, a per-song nudge). Save to Supabase for all devices. |
| **The heal solves the skew from the tracklist**: `skew = P − s − T`, where `P` is the stream's program date at the anchor, `s` is ShazamKit's position, and `T` is the matching row's stamp. | It works from any starting skew, so a new station needs no known constant. | Measure a delta against the song already selected, which needs the right song to be selected and a clamp of ±10 s. |
| **Three anchors within 1 s of their median, then replace the skew.** A result beyond ±600 s changes nothing. A heal replaces a fine-tune. | A wrong-section match (seen 20 to 130 s off) can't get through. One number, one meaning. | Keep the fine-tune across a heal. Average all anchors. |
| **Skip an anchor when the feed title has a version word (remix, mix, edit, version, live, acoustic, extended, instrumental, demo, reprise) that the heard title lacks.** "Clean", "explicit" and "remastered" don't count. | Seen on the device: 99 s and 8 s errors. The heal says it can't use an edit and tries again. | Use them at lower trust. Allow all. |
| **Wait 5 s between listens, and stop when cancelled.** The heal belongs to the session, not the screen: leaving the station screen does not cancel it. | ShazamKit refuses back-to-back sessions. | Retry at once. Tie the heal to the screen. |
| **No bias constant and no lead.** | The device data didn't support one (see above). | A constant of −1.0 s, or a 0.5 s lead. |
| **One switch, Alignment Off or On.** Observe, the Self-heal picker, the automatic loop, the Debug feed skew and the poll-driver setting are removed. The `+` and `−` move the skew 0.5 s per tap (`+` lowers it, so the song position moves forward). The old per-song lyric nudge and its Supabase save are removed; in Off there is no nudge. | Fewer flags. The nudge is now the same thing as the skew. | Keep the old nudge in Off. |

## Consequences

- **Per-song spread remains.** After a heal the skew is right for the song heard. The next song can be about 1 to 1.5 s off. A heal on each song change would fix that. The microphone can't do that quietly, so the direct-stream idea (`docs/ios/experiments/2026-10-14_direct_stream_heal.md`, a stub) is the next step.
- **Speaker only.** The heal needs the microphone to hear the audio. Headphones and Bluetooth can't be healed.
- **KCRW only, Debug only.** Alignment is eligible for KCRW alone, and the switch and the heal button are Debug-only.
- **Other stations lose the lyric nudge** on this branch, with nothing to replace it until they are aligned. The branch merges only if that is accepted or a second station is aligned.
- The `lyric_offsets` table in Supabase is no longer read or written by iOS. What else uses it was not checked.
- Not covered: a second station, a route other than the speaker, Release build, and CarPlay and Bluetooth with alignment on.

## Verification

| Behavior | Covered by |
|---|---|
| Skew store: seed, saved wins, zero is saved, limit, notification, rounding | `AlignmentSkewStoreTests` |
| Solver: skew from song, position, program date and row; any starting skew; repeats; versions | `SkewSolverTests` |
| Probe: found, not in feed, different version, session change, timeout | `SkewProbeTests` |
| Heal: three anchors, replaces a fine-tune, gaps between listens, give up, cancel, out of range | `SkewHealerTests` |
| Heal against simulated stations: any starting skew, wrong sections, noise, repeats, edits | `SkewSimulationTests` |
| Session selects with the skew and takes a sample when it changes | `AlignedNowPlayingTests`, `RadioPlaybackSessionTests` |
| Lyrics read the same position, and the nudge moves the skew | `LyricSyncControllerTests`, `LyricsViewControllerTests`, `StationDetailLyricsTests` |
| A heal survives leaving the screen | `StationDetailRecalibrateTests` |
| Titles, lyrics and a heal's result on a real phone | Device runs; not automatable |
