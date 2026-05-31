# M5: Up Next Lifecycle + New Releases + Detail

**Status**: NOT STARTED

## Goal

Complete the podcast experience: finish→complete→remove→auto-advance, playNow reorder, New Releases (last 14 days), and detail screens (episode show notes, station metadata).

## Done when

- On natural end (`state="finished"`): episode marked completed, removed from Up Next, queue auto-advances to the next episode — in that order (see ordering below)
- Picking a non-top episode sends playNow and it becomes current
- New Releases lists subscribed-podcast episodes from the last 14 days, sorted newest-first; selecting one plays it (via playNow)
- Episode detail: show notes rendered as readable plain text + episode image
- Station detail: country / language / genre / codec·bitrate / votes / homepage
- Back returns from any detail screen

## What to Build

### Finish → complete → remove → advance (relay, atomic + ordered)
Add a relay `finishEpisode` action that performs, **in order**: `updateEpisode status=3` (completed) **then** `upNextChange remove`. Doing both server-side in one call guarantees the order (complete before remove) and one Roku round-trip. Roku then advances to the new top of queue.

### playNow reorder
Relay `upNextChange` with `change="playNow"`. **Optimism:** start local playback only after the relay returns success, so local and server state can't diverge on failure. (Latency is one quick round-trip.)

### New Releases (relay `newReleases`, server-side merge)
Add a relay `newReleases` action: `podcastList` (protobuf) → for each podcast `GET cache.pocketcasts.com/mobile/podcast/full/{uuid}` (follows 302) → keep `published >= now-14d`, sort desc, merge across podcasts → return clean JSON. **All fan-out + the ISO-8601 date filtering happen in Deno** (trivial `Date` parsing), not BrightScript (no `roDateTime` ISO headaches, no dozens of large-feed parses on the device).

### Detail screens
- Episode show notes (HANDOFF §6.8): `GET cache.pocketcasts.com/mobile/show_notes/full/{podcastUUID}` is **plain JSON → call direct from Roku** (no relay). Find episode by uuid → `show_notes` (html) + `image`. Strip HTML: drop tags, decode `&amp; &lt; &gt; &quot; &#39; &nbsp; &hellip;`, collapse blank lines.
- Station detail: render the radio-browser fields already fetched in M3 (country/language/tags/codec/bitrate/votes/homepage).

## Implementation Strategy

1. Relay `finishEpisode` (ordered complete→remove); wire `state="finished"` → call → advance.
2. playNow reorder (await relay ack, then play).
3. Relay `newReleases` (server-side 14d merge); New Releases list + play.
4. Show-notes detail (direct cache JSON + HTML strip); station detail.

## User Checkpoint

Let an episode finish → it's removed and the next starts. Pick a lower episode → it jumps to play. Open New Releases → last-14-day episodes → play one. Open an episode → readable show notes + image. Open a station → metadata shown.

## Commit
TBD.
