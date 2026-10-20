# 0010 — Timing is one skew per station, set by a ShazamKit heal and fine-tuned by hand

**Decision:** Accepted 2026-10-14 for the iOS `experiment/unified-skew` branch (not yet merged to `trunk`). Proven on KCRW Eclectic24. KEXP is built on the same design with a media-time clock and not yet tested on the phone (see [KEXP media clock](../experiments/2026-10-14_kexp_media_clock.md)). Replaces the frozen `+160 s` constant in [ADR 0004](0004-kcrw-playback-clock-on-ios.md) and the per-occurrence lyric nudge in [ADR 0008](0008-kcrw-lyrics-follow-the-media-clock-in-apply.md).

## What the device showed

Measured on "Jonathan iPhone" (iPhone 15), StagingDebug, KCRW on the phone's speaker, over about 6 hours. (The heal does not depend on the speaker: see the last row.) Evidence: `docs/ios/experiments/2026-10-12_unified_skew.md` (device logs, `[anchor]` and `[heal]` lines).

| Question | Result |
|---|---|
| Does one heal, from any starting skew, find the skew? | Yes. From skew 0 it saved 158.7 in 21 s (three anchors). From saved values (157.2, 157.5, 158.4) it moved by 0.2 to 1.8 s. The user judged titles and lyrics "dead on" after the heal. |
| Is the skew constant per station? | Not quite. Six songs gave 158.7, 158.0, 158.4, 158.6, 156.8 and 155.8. The spread is 2.9 s. Anchors within one song agree within 0.1 s, so the spread is between songs. The likely causes are the feed's stamp for each song and each recording's edit. Not confirmed. |
| Does the heal have a constant bias against the user's ear? | No. Of five heals the user judged, three were left as healed, one of them "dead on". Two were nudged by −0.5 and −1.5. A constant would have made the three worse. |
| Do wrong versions fool the heal? | Yes, before the fix. A feed title "(Liza Richardson remix)" against ShazamKit's plain title gave anchors 99 s off; "(radio edit - clean)" gave 8 s off. Anchors from one song agree with each other, so agreement can't catch it. |
| Does ShazamKit accept back-to-back sessions? | No. A session opened right after another closes is refused with "Missing entitlements" (an inaccurate message), as it was when a cancelled heal ran its waits at once. |
| Does the heal hear the room, or the phone's own audio? | The phone's own audio. On 2026-10-20 a heal on KEXP matched the station's song with the phone in a drawer, then with the headphone volume at zero (both confidence 1.00). With the phone playing Liz Phair on headphones and a Mac playing Beck loudly beside it, the heal named Liz Phair. During the listen the app's audio session stayed on `Playback` with no input. A microphone check in the same room read −34 dBFS whether headphones, speaker or silence, so the room's sound had no part in it. Apple's SDK interface says nothing about the source, so this is inferred from behavior, not documented. |
| Does the skew survive a relaunch? | Yes. Sessions started at 159.0, 158.6 and 156.8 from the saved value. |

## Design choices

| Choice | Reason | Alternatives not selected |
|---|---|---|
| **One number per stream, the skew:** a song the feed stamps at `T` starts in the stream at `T + skew`. Everything the aligned session shows reads it. Saved in `UserDefaults` on this device under the stream's key (`AlignmentProfile.key`), so every list entry for one stream shares it (the KCRW MP3 and AAC entries did not before: seen on the device). Seed: KCRW 160, anything else 0. A saved 0 counts as saved. | The title, artwork, song position, lyrics, lock screen and widget have to move together. The value depends on this device and speaker, so it is not shared across devices. | Keep three inputs (a constant, a Debug skew, a per-song nudge). Save to Supabase for all devices. |
| **The heal solves the skew from the tracklist**: `skew = P − s − T`, where `P` is the stream's program date at the anchor, `s` is ShazamKit's position, and `T` is the matching row's stamp. | It works from any starting skew, so a new station needs no known constant. | Measure a delta against the song already selected, which needs the right song to be selected and a clamp of ±10 s. |
| **One anchor if it is within 3 s of the skew in use (and a change under 0.5 s is ignored); otherwise two anchors within 1 s of their median. Then replace the skew.** A result beyond ±600 s changes nothing. A heal replaces a fine-tune. | A wrong-section match (seen 20 to 130 s off) has no second anchor to agree with. In 8 of 8 heals on 2026-10-20 the first anchor was within 0.2 s of the last. This rule replaced "three anchors always" on 2026-10-20 (a heal drops from about 30 s to about 4 s). One number, one meaning. | Three anchors always (it did not catch a wrong value that three anchors agreed on, see KEXP). Keep the fine-tune across a heal. |
| **Skip an anchor when the feed title has a version word (remix, mix, edit, version, live, acoustic, extended, instrumental, demo, reprise) that the heard title lacks.** "Clean", "explicit" and "remastered" don't count. | Seen on the device: 99 s and 8 s errors. The heal says it can't use an edit and tries again. | Use them at lower trust. Allow all. |
| **Wait 5 s between listens, and stop when cancelled.** The heal belongs to the session, not the screen: leaving the station screen does not cancel it. | ShazamKit refuses back-to-back sessions. | Retry at once. Tie the heal to the screen. |
| **No bias constant and no lead.** | The device data didn't support one (see above). | A constant of −1.0 s, or a 0.5 s lead. |
| **One switch, Alignment Off or On.** Observe, the Self-heal picker, the automatic loop, the Debug feed skew and the poll-driver setting are removed. The `+` and `−` move the skew 0.5 s per tap (`+` lowers it, so the song position moves forward). For an aligned station the nudge is the skew and the old per-song lyric nudge is gone. A station that is not aligned keeps the old whole-second saved lyric offset (restored 2026-10-14). | Fewer flags. For an aligned station the nudge is the same thing as the skew. | Remove the saved offset everywhere: it left KEXP, which has no skew, with no way to correct lyrics 10 s early. |

## Consequences

- **Per-song spread remains.** After a heal the skew is right for the song heard. The next song can be about 1 to 1.5 s off. A heal on each song change would fix that. The microphone can't do that quietly, so the direct-stream idea (`docs/ios/experiments/2026-10-14_direct_stream_heal.md`, a stub) is the next step.
- **The heal works on any output.** It hears the phone's own playback, so headphones, Bluetooth and a muted phone all work (checked on headphones). Because it hears the audio before the output, the skew leaves out the output's delay: a Bluetooth delay of a few tenths of a second, and AirPlay's about 2 s, are not in it. For headphone listeners the lyrics would run that much early. Not measured.
- **KCRW only, Debug only.** Alignment is eligible for KCRW alone, and the switch and the heal button are Debug-only.
- **A station that is not aligned keeps the saved lyric offset**, so it loses nothing. KEXP is the second station: it aligns with a media-time clock instead of a program date, because its ICY stream has none. That is built, with unit tests, and not yet tested on the phone.
- **A media-time stream needs a heal on each play.** The clock is the media position plus the wall time at which playback first advanced, so the skew also holds that play's startup delay. A pause in this app stops and restarts the stream, which is a new play. A stall does not move the skew, because media time stops with the audio.
- The `lyric_offsets` table in Supabase is no longer read or written by iOS. What else uses it was not checked.
- Not covered: the size of a Bluetooth or AirPlay delay, a Release build, and CarPlay with alignment on.

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
