# Experiment: can KEXP, an ICY stream with no program date, align with the same skew and heal?

**Status**: FIRST PHONE RUN — 2026-10-14. Built, unit tests pass, and one device run found two problems, both fixed (see "First device run"). The heal has not yet saved a KEXP skew. Follows the [unified skew experiment](2026-10-12_unified_skew.md) and [ADR 0010](../adr/0010-timing-is-one-skew-per-station-healed-with-shazamkit.md). Belongs to [M14](../milestones/milestone_14.md). This is Phase 4 of the unified skew plan, and the answer to the stream-agnostic question for a stream without HLS.
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
