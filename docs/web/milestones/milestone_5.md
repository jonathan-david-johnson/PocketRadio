# Web M5 — Podcasts, Up Next, and episode playback

**Status**: PLANNED
**Depends on**: Web M1 (E3: Pocket Casts JSON calls), Web M3 (player, relay)
**Required by**: Web M6

## Where the work happens

| | |
|---|---|
| Plan | Shell `main`: this file |
| Code | `pocket-radio-web`, branch `feature/m5-podcasts` from `main` after M3 merges |
| Worktree | `pocket-radio-web/` |
| Shell changes | None expected |

**Goal:** Play podcast episodes and keep them in sync with the phone. The
player gains seek, skip back and forward (using the user's Pocket Casts skip
times), and playback speed. Playback position is saved to Pocket Casts, so the
phone resumes where the web stopped. Up Next supports play now, remove,
drag-to-reorder, play next, and play last. The Podcasts Destination lists
subscriptions, then a show's episodes with show notes and mark as played. The
menubar's `APIService.swift` and `PlayerViewModel.swift` are the reference.

**User checkpoint:** Open Up Next and play the second episode. It moves to the
top. Skip forward, change speed, and pause after a few minutes. Open Pocket
Casts on the iPhone: the episode resumes within a few seconds of where the web
stopped. Open Podcasts, pick a show, choose "Play last" on an older episode,
and see it at the bottom of Up Next on the phone.

## Scope

- **Pocket Casts client (`functions/api/pc/`).** Worker routes for Up Next
  (read and change), subscriptions, a podcast's episodes, show notes, episode
  position and played state, and skip settings. Use the JSON or protobuf
  decision from M1 E3. Tokens come from `pc_tokens`; refresh on 401.
- **Episode audio.** `https://` enclosure URLs play directly. `http://` ones
  go through the relay by episode UUID, and the Worker resolves the URL from
  Pocket Casts (ADR 0004).
- **Player (`src/player/`).** Seek bar, skip back and forward, speed, and
  remaining time. Saves position every 30 seconds while playing, plus on pause,
  seek, and page hide (`sendBeacon`). Media Session gains seek and skip
  handlers. Behavior at an episode's end: match the menubar (mark played,
  remove from Up Next, start the next one).
- **Up Next (`src/upNext/`).** List with total remaining time, play now,
  remove, and drag reorder. Episode rows elsewhere offer play next and play
  last.
- **Podcasts (`src/podcasts/`).** Subscription grid or list, then a show's
  episodes, newest first, with played state. Episode detail shows show notes
  as sanitized HTML.

## Behaviors to test (red -> green, one at a time)

1. Position saving: one save per 30 seconds of playing, one on pause, one on
   seek, and one on page hide; none while paused.
2. Play now on any episode puts it first in Up Next and syncs the change.
3. Remove, reorder, play next, and play last each produce the expected Up Next
   order locally and on the server.
4. At an episode's end the next Up Next episode starts, and the finished one
   is marked played and removed.
5. Skip intervals come from the user's Pocket Casts settings, with menubar
   defaults if they're missing.
6. `http://` episode audio plays through the relay; a URL-shaped id is
   rejected.
7. An expired access token is refreshed once and the request retried; a failed
   refresh signs the user out with a message.
8. Show notes render without running scripts or loading remote trackers.

## Out of scope

- Chapters, transcripts, bookmarks, starring, archiving (later).
- Subscribe and unsubscribe (with Discover, M8).
- Downloads and offline playback (never).
- Remote control between devices (later global milestone).

## Docs impact

- **Docs this changes or makes stale:** `docs/web/README.md` (features).
- **Questions this must settle:** Is Up Next changed through `up_next/sync`
  actions, as the menubar does, or through the endpoints Pocket Casts' web
  player uses? Does the episode-end behavior match iOS or only the menubar?

## Hand-performed interactions

- [ ] Drag an Up Next episode to a new position — the order changes and matches on the iPhone
- [ ] Drag the seek bar — playback jumps and the phone resumes from the new position
- [ ] Use the keyboard media keys during an episode — play/pause and skip work
