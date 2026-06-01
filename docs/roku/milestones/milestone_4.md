# M4: Up Next — List + Play + Resume + Position Save

**Status**: DONE

## Goal

The podcast queue: fetch Up Next via relay, render it (reusing M3's list UI), play with resume-on-start, and save position every ~30s + on pause/stop. Lifecycle (finish/advance/playNow) and discovery (New Releases) are M5.

## Done when

- Up Next list renders episodes (title + artwork) from relay `upNext`
- Each episode has `playedUpTo` + `duration` filled (relay gap-fills server-side — see relay work below)
- Selecting an episode plays it; `playedUpTo > 0` resumes at that position
- Position saved via relay `updateEpisode` every ~30s while playing + on pause/stop
- Now Playing screen: artwork + title + progress; **scrub shown for seekable** podcasts (reusing M3's live-vs-seekable gating)
- Skip back/fwd works with **hardcoded defaults (back 10 / fwd 45)** — real per-account values are M6 (seam called out)

## What to Build

### Relay work (enhance existing `upNext`)
Today `upNext` returns episodes but `playedUpTo`/`duration` are often 0 (sync entries empty — confirmed in spikes). **Move the gap-fill server-side**: in the relay, for each distinct `podcastUUID` with missing data, call `/user/podcast/episodes` and merge, so Roku gets complete episodes in one JSON call. (Avoids N protobuf round-trips on the device; BrightScript never sees `podcastEpisodes`.)

### Playback (Now Playing, HANDOFF §7)
- Resume: set `content.PlayStart = playedUpTo` **before** play (primary). `m.audio.seek` only as a fallback once `state="playing"` — it forces a re-buffer.
- Observe `m.audio.position`/`duration` for the progress bar.
- Artwork: `https://static.pocketcasts.com/discover/images/130/{podcastUUID}.jpg`.

### Position save (relay `updateEpisode`)
- Throttle to ~30s while playing; also fire on pause and stop.
- Status: `2` (inProgress) during playback. (Status `3`/completed + remove is M5's finish handling.)
- `deviceId` = `GetChannelClientId()` (from M2).

## Implementation Strategy

1. Relay: add server-side gap-fill to `upNext`; verify complete JSON.
2. Up Next list (reuse M3 list UI).
3. Play with `PlayStart` resume + Now Playing progress (reuse M3 gating for scrub).
4. Position-save throttle (30s + pause/stop) via relay `updateEpisode`.

## User Checkpoint

See Up Next queue → play top episode → resumes at last position → progress saves (verify by relaunch mid-episode → resumes near where you left off).

## Commit
TBD.
