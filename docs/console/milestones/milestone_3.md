# M3 — Podcast position fidelity

**Goal:** Bring podcast playback to full parity with the menubar: resume at the
saved position, write progress back to Pocket Casts, auto-advance and remove
finished episodes, and honor the user's synced skip amounts.

**User checkpoint:** Play a podcast, quit partway, run `pocket-radio up_next`
again → it resumes where you left off. Let an episode finish → the next one
starts and the finished episode disappears from your phone's Up Next.

## Scope

- `internal/pocketcasts/client.go`: `PodcastEpisodes`, `UpdateEpisode`,
  `PlayNow`, `RemoveFromUpNext`, `SkipSettings` (all ported from the menubar).
- Engine playback fidelity:
  - merge `playedUpTo`/`duration` from `PodcastEpisodes` into Up Next episodes;
  - resume seek to `playedUpTo` on load;
  - throttled position save (≥30s apart, only on change), via `UpdateEpisode`
    `status=inProgress`;
  - on natural end or pause-near-end: save `status=completed`, `RemoveFromUpNext`,
    advance to the next episode and auto-play;
  - `PlayNow` when an episode is selected out of order (bubbles to top + syncs).
  - skip amounts from `SkipSettings` (default 10/45 until fetched).

## Behaviors to test (red → green, one at a time)

1. `PodcastEpisodes` decoder: captured `user/podcast/episodes` body →
   `[]PlaybackInfo{uuid, playedUpTo, duration}` (note the **top-level** int32
   fields 3/6, not the wrapped Int32Value form used in `up_next/sync`).
2. `UpdateEpisode` encodes the request with the position wrapped as an
   `Int32Value` submessage (field 3) and `status`/`duration` as varints — exact
   golden bytes.
3. Engine resume: loading an episode with `playedUpTo=120` seeks the fake player
   to ~120s before playing.
4. Engine throttle: two ticks <30s apart trigger **one** `UpdateEpisode`; a tick
   ≥30s later with a changed position triggers another.
5. Engine finish: a `Player` `Ended` event → one `UpdateEpisode(completed)` +
   one `RemoveFromUpNext` + `State()` advances to the next episode.
6. Engine pause-near-end: pausing with ≤10s remaining saves `completed` and
   removes; pausing mid-episode saves `inProgress` and keeps it.
7. `SkipSettings` parse: captured `named_settings` body → `{back, forward}`;
   engine uses them for `SkipForward/Back`.

> The throttle and finish logic are the deep, bug-prone core (they were in the
> menubar too) — favor behavior tests through the engine over testing private
> helpers.

## Out of scope

Full TUI, lists, art, lyrics, ACR.
