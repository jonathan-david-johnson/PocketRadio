# 0001 — The relay owns protobuf, fan-out, and ordering

**Status:** Accepted (2026-05-31, with M2–M5)

## Context

Roku can't read binary protobuf from `roUrlTransfer`. It truncates the body at
the first NUL byte, and there is no usable file-based variant for this
(`spikes.md`, Spike 1). The Pocket Casts API is protobuf, so the channel needs
a translator. Separately, several Up Next operations take more than one API
call, and BrightScript is a poor place to run them: slow, single-threaded per
task, and hard to keep atomic.

## Decision

All `api.pocketcasts.com` traffic goes through `pc-relay`
(`supabase/functions/pc-relay/`), a Supabase Edge Function that speaks JSON to
Roku and protobuf to Pocket Casts. It ports the wire logic from the menubar's
`APIService.swift`.

The relay also owns every operation that fans out or must be ordered:

| Relay action | What it does server-side | Why |
|---|---|---|
| `upNext` | Fills `playedUpTo` and `duration` by calling `/user/podcast/episodes` for each podcast with missing data. | The sync entries are often empty. One JSON call replaces N protobuf round-trips on the device. |
| `finishEpisode` | Runs `updateEpisode status=3` (completed), then `upNextChange remove`, in that order. | Completing before removing must be atomic, and Roku needs one round-trip. |
| `newReleases` | Lists podcasts, fetches each full feed, keeps episodes from the last 14 days, sorts newest first. | Fan-out and ISO-8601 date filtering are trivial in Deno and painful in BrightScript. |
| `namedSettings` | Reads the account's skip amounts. Defaults are back 10 and forward 45. | Read-only. |

Roku calls JSON services directly, with no relay: Supabase `radio_favorites`,
radio-browser.info, the Pocket Casts cache and show-notes endpoints, and the
KCRW and KEXP tracklist APIs.

Two client rules go with this:

- **`playNow` waits for the relay's success reply** before local playback
  starts. A failure then can't leave the device and the server disagreeing
  about the current episode.
- **Resume uses `content.PlayStart` before play.** `m.audio.seek` after
  `state="playing"` is only a fallback, because it forces a re-buffer.

## Consequences

- The relay must stay in step with menubar `APIService.swift`, which remains
  the wire-format reference.
- Roku has no protobuf code and no Pocket Casts decoding to test. Its
  testing is on the device.
- A relay change can break the channel without a Roku release.

## Rejected alternatives

- **Native protobuf on Roku.** Failed Spike 1: binary responses are truncated.
- **Fan-out in BrightScript.** Would cost N round-trips per Up Next load and
  can't make complete-then-remove atomic.
- **Optimistic `playNow`** (play first, reconcile later). Saves one round-trip
  and risks divergent state on failure.

Evidence: `archive/roku-m4:docs/roku/milestones/milestone_4.md` and
`archive/roku-m5:docs/roku/milestones/milestone_5.md`.
