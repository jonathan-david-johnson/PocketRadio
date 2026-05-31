# M5: New Releases + Detail Screens

**Status**: NOT STARTED

## Goal

New Releases list (subscribed-podcast episodes from the last 14 days) with play, plus detail screens: episode show notes and station metadata. Mix of protobuf (podcast list) + JSON (cache + radio-browser).

## Done when

- New Releases list: subscribed podcasts (`/user/podcast/list`) × cache full-feed, episodes from last 14 days, sorted by published desc, merged across podcasts
- Selecting a New Release plays it (via `playNow`, like Up Next)
- Episode detail screen shows stripped-to-plain-text show notes + episode image
- Station detail screen shows country / language / genre / codec·bitrate / votes / homepage
- Back returns from any detail screen to its list

## What to Build

### New Releases (HANDOFF §6.7)
1. **UserPodcastListTask** — `POST /user/podcast/list` (Bearer, `f1="2"`,`f2="mobile"`). Decode `f1` repeated `{f1=uuid, f4=title}`.
2. **CacheFullFeedTask** — `GET https://cache.pocketcasts.com/mobile/podcast/full/{uuid}` (no auth, follows 302). JSON `podcast.episodes[] {uuid,title,url,duration,published}`. Keep `published >= now-14d`, sort desc, merge.

### Show notes detail (HANDOFF §6.8)
- **ShowNotesTask** — `GET https://cache.pocketcasts.com/mobile/show_notes/full/{podcastUUID}`. Find episode by uuid → `show_notes` (html) + `image`.
- HTML→text: drop tags, decode `&amp; &lt; &gt; &quot; &#39; &nbsp; &hellip;`, collapse blank lines.

### Station detail (HANDOFF §6.10)
- Reuse radio-browser fields already fetched in M4; render metadata screen. OK from a station row (or `*`/Options) pushes detail; Back returns.

## Implementation Strategy

1. UserPodcastListTask + per-podcast CacheFullFeedTask → merged 14-day list.
2. Play New Release via playNow (reuse M3 path).
3. ShowNotesTask + HTML-strip → episode detail screen.
4. Station detail screen from M4 data.

## User Checkpoint

See last-14-day episodes from subscribed podcasts → play one. Open an episode → readable show notes + image. Open a station → country/language/genre/codec/votes/homepage shown.

## Commit
TBD.
