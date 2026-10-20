# Experiment: can KEXP, an ICY stream with no program date, align with the same skew and heal?

**Status**: TWO PHONE RUNS — 2026-10-14 and 2026-10-20. Built, unit tests pass, and one device run found two problems, both fixed (see "First device run"). The heal has not yet saved a KEXP skew. Follows the [unified skew experiment](2026-10-12_unified_skew.md) and [ADR 0010](../adr/0010-timing-is-one-skew-per-station-healed-with-shazamkit.md). Belongs to [M14](../milestones/milestone_14.md). This is Phase 4 of the unified skew plan, and the answer to the stream-agnostic question for a stream without HLS.
**Question**: KCRW's HLS stream gives the player a program date, so the heal can say where in the stream a song began. KEXP's ICY stream gives none. If the clock is the media position plus the wall time at which playback first advanced, does the same heal (three anchors, replaces the skew) put KEXP's titles and lyrics in time, and how stable is the skew from one play to the next?

## Why

Seen on the device on 2026-10-14. KEXP ran on the old path (the feed's play stamp against the phone's wall clock), with two problems:

- **Lyrics 10 s early** on one song, with no way to correct them once the old lyric nudge was removed. (The nudge is back for stations that are not aligned.)
- **The title and tracklist lagged.** A fresh ICY connection at 17:12:53 still said "The Physics - VHS" while the feed had "It's a Shame" since 17:10:39. ICY flipped at 17:13:13, 154 s after the feed. The app seems to refetch the list on an ICY title change, so the list lagged too. Unconfirmed in the code.

The September menubar capture (zero `currentDate()` samples on KEXP; a 14 s ad pre-roll) says a program-date clock is unavailable here.

## The design (built)

- **A profile per station family** (`AlignmentProfile`): its key, its clock, its seed, its tracklist feed, and whether to play another stream. KCRW is `programDate` (the player's own date; plays the measured HLS stream). KEXP is `mediaTime` (plays the saved stream; seed 0).
- **The media-time clock.** The date for a media position is the wall time at which playback *first advanced*, minus that media position (the anchor), plus the media position now. It is nil until playback advances. Media time stops during a stall, so a stall does not move the skew. A new item (a restart) takes a new anchor.
- **KEXP's feed**: `api.kexp.org/v2/plays/?limit=10` (the same shape as the app's own KEXP parser): trackplay rows become songs, airbreaks become breaks, `airdate` is the stamp.
- **The skew key is the stream's**, so the KCRW MP3, AAC and HLS list entries share one skew (they did not).
- **Eligibility**: the station name says KEXP, and the stream's host contains `kexp`, with no credentials or query.
- Everything else is as in ADR 0010: the heal, the version-word skip, the 5 s gap, the `+` and `−`.

## First device run (2026-10-14, speaker)

- **The session starts and the clock works.** The log shows `session start … kexp.streamguys1.com/kexp160.aac`, skew 0.0, the clock valid 3.4 s in, and an aligned decision. At 3.4 s it selected an airbreak stamped 438 s earlier, which was the newest row the feed had.
- **KEXP's plays feed lists a song about 100 to 150 s after its stamp.** A song stamped 00:38:37 UTC was not in the session's rows at 00:40:01 or 00:40:19 and arrived with the 00:40:23 poll. The ICY title lags about the same (154 s earlier the same evening). So for the first two minutes of each song neither source has it, the title shows the previous row, and the heal hears a song that is not listed yet. Alignment can't show a song before the data exists.
  - **Fix:** a song the feed doesn't list yet is now waited for (20 s, up to 8 times) without using up the heal's attempts.
- **The version rule wrongly skipped the right song.** The feed wrote "TIME IS HAPPENING: MUSTAFA & JULIEN BAKER VERSION" and ShazamKit wrote "TIME IS HAPPENING (MUSTAFA & JULIEN BAKER VERSION)". The rule saw the version word only inside brackets.
  - **Fix:** a version word counts anywhere in the title. A word that both titles share is not a difference.

## Second device run (2026-10-20, headphones)

- **The heal hears the phone's own audio, not the room.** With the phone in a drawer, then with the headphone volume at zero, the heal still matched the station's song (confidence 1.00). With a Mac playing Beck loudly beside the phone and Liz Phair on the headphones, it named Liz Phair. During the listen the audio session stayed on `Playback` with no input. A microphone check read −34 dBFS with headphones, speaker or silence (the office air conditioning and keyboard). See [ADR 0010](../adr/0010-timing-is-one-skew-per-station-healed-with-shazamkit.md). The "speaker" in this doc's first run was incidental.
- **Per-song results.** The skew is the feed's stamp lead over the song's real start in the stream:

| Song | Skew | Feed stamp vs real start | Feed listed it | ICY title arrived |
|---|---:|---|---|---|
| Hands All Up (Imperial Teen) | 22.9 | 22.9 s early | 0.8 s after the start | 11.3 s after the start |
| How to Offer a Hand to Hold (Jennifur) | 22.8 | 22.8 s early | | |
| Stigmata (Ministry), two heals | 9.3, 9.5 | 9.3 s early | | |
| Supernova (Liz Phair) | | | | |

  Supernova was skipped by the version rule: the feed said "Supernova (Edit)", ShazamKit said "Supernova".
- **KEXP's stamps are early or late, by tens of seconds.** Across both nights the skews were 22.9, 22.8, 9.5, −28.3, −31.5 and −48.8. They are not a clock. Anchors within a song agree to 0.2 s, so each heal is right for its song and wrong for the next by up to about 70 s.
- **The feed listed rows 24 to 72 s after their stamps** on 2026-10-20, not the 100 to 150 s of 2026-10-14. That lag varies.
- **ICY is not a reliable boundary.** The one clean comparison has the title arriving 11 s after the song began. On 2026-10-14 it was minutes late. Keep collecting.
- **Decision on a per-song correction: withdrawn.** It rested on "KEXP's stamps jitter by tens of seconds". The later data says otherwise (below).

### Why the skews varied (2026-10-20 analysis)

- **Eight heals today, by song:** 22.9, 22.8, 9.3 and 9.5 (Stigmata, two heals), 21.9, 13.3 and 21.6 (Spectral Eyes), 23.3. Five of eight sit within ±1 of 22.5. All songs were on one of two shows (The Morning Show, John Richards; The Midday Show, Greta Rose), so the show does not explain the outliers.
- **The same song gave two answers 23 s apart.** Spectral Eyes (Blondie): 13.3 at 13:58:05 and 21.6 at 13:58:28. Media time ran continuously and the feed row did not change, but ShazamKit's estimate of the song's start moved by 8.3 s. Likely causes, not yet told apart: the broadcast is an edit with a cut in the middle (the reference position jumps by the length of the cut), or ShazamKit matched another recording of the song. Lyric files follow the studio recording, so following the reference position is right for lyrics.
- **Three anchors did not catch it.** All three anchors of the first heal agreed on 13.3, because they matched the same reference. In 8 of 8 heals the first anchor was within 0.2 s of the last.
- **Consequence:** the heal can be wrong for part of a song. The fix to test is re-measuring while the song plays, not a per-song constant.
- **Added to find out:** each anchor now logs the recording ShazamKit matched (`sid=`, `isrc=`, `cands=`), and a Debug toggle "Track every 30 s (measure only)" anchors repeatedly and logs `[track] jump` when two anchors of one song differ by more than 1 s, with both recordings' IDs. It changes nothing.
- **The heal rule changed:** one anchor if close to the skew in use, otherwise two that agree (ADR 0010).

## Tracing (added 2026-10-14)

An aligned session now writes `[trace]` lines, for any stream, so a new station can be understood from one log:

- `[trace] meta`: every timed metadata item the stream delivers (ICY `StreamTitle` and `StreamUrl`, ID3, ad markers), with the stream date it arrived at (`program=`) and the wall time.
- `[trace] feed first poll` and `[trace] feed new`: the newest row's age on the first poll, and each new row with how long after its stamp the feed first listed it (`lag=`).
- `[anchor]` lines now carry `at=`, `start=` (when the song began in the stream: the program date minus ShazamKit's position) and `stamp=`.

`tools/stream-timeline.py <debug_log>` lines these up per song: the stamp, when the feed listed it, and when the stream's own title arrived, all against the measured start. That settles whether KEXP's ICY titles mark the audio boundary: if `icy-start` is within about 1 s, they do; if it is minutes, they don't.

## What this predicts (to check on the phone)

1. **A play of KEXP needs a heal.** The skew holds this play's startup delay (a burst of audio at connect, or the pre-roll). The saved skew from the last play is only a guess.
2. **A restart changes the skew**, by however much the startup delay changes. A pause in this app is a restart.
3. **A stall does not.** Media time stops with the audio.
4. **Within a song** anchors agree to about 0.1 s, as on KCRW.

## Pass criteria (proposed)

| Check | Pass if |
|---|---|
| Heal on KEXP from skew 0 | Three anchors agree and the titles and lyrics match the audio within about 2 s, over at least three plays |
| Skew across restarts | Record each play's healed skew. The spread across plays says how far the saved value is from right at the start of the next play. No threshold set: it is the finding |
| Stall | After a network dip (airplane mode for 10 s), the titles and lyrics are still right without a heal. This is the media-clock claim |
| Pre-roll | A heal during the ad says so and changes nothing, and one after it works |
| Title and list | With alignment On the title comes from the aligned song, not ICY, so the ICY lag no longer shows |
| KCRW | Unchanged: all three list entries start from the same saved skew |

## Open

- **How far apart are the skews from play to play?** If it is a few tenths, the saved value is a good start. If it is 10 s or more, every play needs a heal, and that is the cost of this design. If it is too much, the next idea is an automatic heal a few seconds after each play starts, which needs the microphone.
- **How long a song waits for the feed.** The wait is 100 to 150 s from one night's data. If it varies more, 8 waits of 20 s may not cover it.
- **Does the heal work during the ad pre-roll?** The first song match may be music or an ad.
- **How does the station detail list refresh for KEXP when aligned?** The ICY-lag problem was in the list. I did not change the refresh.
- **Eligibility is by host name.** The curated KEXP station's saved stream URL was not read from the device. If its host does not contain `kexp`, the station will not align, and the Debug screen will show no skew.
- **A Release build** has not been tried.
