# M3: Up Next — Queue, Resume, Position Save, Advance

**Status**: NOT STARTED

## Goal

Fetch + decode the Up Next queue, render it as a list, play with resume-on-start, save position every ~30s + on pause/stop, mark completed + remove + auto-advance on finish, and `playNow` reorder when the user picks an episode. The protobuf-heavy core.

## Done when

- Up Next list renders episodes (title + artwork) from `/up_next/sync`
- Missing `playedUpTo`/`duration` filled via `/user/podcast/episodes` (per distinct podcastUUID)
- Selecting an episode plays it; podcasts with `playedUpTo > 0` resume at that position
- Position saved via `/sync/update_episode` every ~30s while playing + on pause/stop
- On natural end → status `3` (completed) + `remove` (action 4) from Up Next + auto-advance to next
- Picking a non-top episode sends `playNow` (action 1) and bubbles it to top
- Scrub bar shows progress for seekable podcasts; skip back/fwd works

## What to Build

### Tasks (`components/tasks/`)
- **UpNextTask** — `POST /up_next/sync` (`f1=deviceTime ms`, `f2="2"`, `f6=deviceID`). Decode `Api_UpNextResponse`: `f4` repeated EpisodeResponse (`f1=title`,`f2=url`,`f3=podcast`,`f4=uuid`,`f5=published Timestamp`), `f5` repeated sync (`f1=uuid`,`f6=playedUpTo Int32Value`,`f7=duration Int32Value`). Merge by uuid; first `f4` = top of queue.
- **PodcastEpisodesTask** — `POST /user/podcast/episodes` (`f1="2"`,`f2="mobile"`,`f3=podcastUUID`). Decode `f1` repeated `{f1=uuid, f3=playedUpTo, f6=duration}`. Call once per distinct podcastUUID; fill gaps.
- **UpdateEpisodeTask** — `POST /sync/update_episode` (`f1=uuid`,`f2=podcast`,`f3=position Int32Value`,`f4=status varint 1/2/3`,`f5=duration`). Throttle ~30s + pause/stop.
- **UpNextChangeTask** — `POST /up_next/sync` with `f4=Api_UpNextChanges{f2=Change}`. Change: `f1=uuid`,`f2=action`(1=playNow,4=remove),`f3=modified ms`,`f4=title`,`f5=url`,`f6=podcast`.

### Playback (Now Playing, HANDOFF §7)
- Resume: set `content.PlayStart = playedUpTo` before play (or `m.audio.seek` once `state="playing"`).
- Observe `m.audio.position`/`duration` for scrub; `state="finished"` → completed + remove + advance.
- Artwork: `https://static.pocketcasts.com/discover/images/130/{podcastUUID}.jpg`.

## Implementation Strategy

1. UpNextTask + list render (read-only).
2. Add PodcastEpisodesTask gap-fill.
3. Playback with resume + Now Playing scrub.
4. Position save throttle + finish→remove→advance.
5. playNow reorder on pick.

## User Checkpoint

See Up Next queue → play top episode → resumes at last position → progress saves (verify by relaunch). Let one finish → it's removed + next starts. Pick a lower episode → it jumps to play.

## Commit
TBD.
