# now_playing_feed contract

Golden fixtures for turning a station's raw "now playing" response into one normalized record. The web player's resolver, iOS, and the menubar should each produce every case's `expected` from its `raw` and `now`. The record shape is in [`schema.json`](schema.json).

## Status of the reference

The expected values were produced by a research prototype (`docs/global/experiments/traces/2026-10-29_now_playing/scripts/np_adapters.py`) and then **read case by case by a person**.

**Swift port (2026-10-29):** `pocket-radio-menubar` branch `feature/now-playing-feed`, package `Packages/NowPlayingFeed`, passes all 41 cases and all 28 junk cases, and its time-converter checks were verified against Python's `datetime`. The same person wrote it from the Python reference, so it shows the fixtures are consistent and the rules port cleanly. It is not an independent reading of the rules. The TypeScript port (web M3a) is the next check. Disagreements the Swift port exposed are written into the rules below.

Raw bodies were recorded from live services on 2026-10-29 and trimmed. Several carry a few hand edits, each named in the case's `description`. The services' terms of use were not reviewed for fixture use. No audio is involved.

## Case shape

```json
{
  "id": "laut__song",
  "description": "what the case pins",
  "adapter": "laut",
  "params": { "name": "odessa" },
  "now": 1793273672,
  "raw": { "api.laut.fm": "<response body as a string>" },
  "expected": { "...": "a NowPlaying record" }
}
```

- `adapter`: which adapter parses `raw`. `icy` and `zeno` take a pasted block in `params.block`.
- `params`: what the adapter needs to build its request (station id, mount, host, zone).
- `now`: the clock, in epoch seconds. Every time rule uses it, never the machine clock.
- `raw`: response bodies keyed by a substring of the URL the adapter requests. A port serves them in place of the network.
- `expected`: the full record, including `provenance.observedAt` (= `now`) and `pollAfterSec`.

[`junk_filter.json`](junk_filter.json) is a separate list of `(title, artist) -> kind` cases.

## Rules every port must apply

1. **Times are UTC.** Each adapter converts its source's format and zone (epoch seconds or milliseconds, ISO with or without a colon in the offset, naive local time with a zone named elsewhere, `/Date(ms)/`). `startedAt` is `null` when the source gives no stamp.
2. **Combined titles are split.** `Artist - Title` in one string splits at the first ` - `, unless the adapter already marked the item `station_id` or `show`. The star format `Song*TITLE*ARTIST*YEAR*ID` splits into title and artist. A leading `#123:` counter is removed (NPO).
   - **Automation attributes in an ICY title** (iHeart): `Artist - text="Title" song_spot="M" … amgArtworkURL="…" length="00:03:23"`. `text` is the title, the prefix is the artist, `amgArtworkURL` is the artwork, a non-zero `length` is the duration. `song_spot="M"` is a song; any other value is a `station_id`. A `text` that matches an ad marker is an `ad`.
3. **Junk is removed.** After parsing, the title and artist pass the junk filter. `ad`, `station_id`, `placeholder` and `unknown` give `status: "between"`, `item: null`, and `provenance.suppressed` set to that kind.
   - Structural junk always counts: a template token such as `{cartNumber}`, a file extension, an automation slate id (`XYZ_ID6`), an HTML fragment, an empty-ish title (`-`), the artist `Unknown Artist`.
   - Bare status words (`Live`, `Searching`, `Unknown`, `On Air`) count only when the title has **no artist**.
   - Known slate phrases count when they are the title (with no artist) or the artist.
   - A title equal to the station's name counts as `station_id` (ICY only, when the station name is known).
4. **Ended is not playing.** With `startedAt` and `durationSec`: if `now` is more than 60 s past `endsAt`, status is `between` (suppressed `ended`) up to 900 s past, then `stale`. With no duration, a song whose `startedAt` is more than 900 s old is `stale`. A show is never `stale` for lack of a duration.
5. **`timing`** is `stamped` when `startedAt` is present and `observed` when it is not. It is `none` when there is no item and no stamp. A stamp is the station's clock, not the listener's audio position.
6. **A show** has `item.kind: "show"`, its title as `item.title`, no artist, and `show.title` set.
7. **`pollAfterSec`** is 10, or 30 when `stale`.
   **Several matching steps (Radio France):** when more than one song step spans `now`, take the one with the latest `start`. The prototype took the last in the response's key order, which a JSON reader cannot rely on.
8. **Artwork is `https` or `null`.** An `http://` artwork URL is rewritten to `https://`. This is for artwork only; audio URLs are never rewritten (web ADR 0006). The rewrite was checked for one host (iHeart's image host).

## Cases

| Group | Files | What they pin |
|---|---|---|
| Station APIs | `kexp__*`, `kcrw__*` | Offset-aware stamps; airbreak is `between` |
| Hosting platforms | `azuracast__*`, `laut__*`, `radioco__*`, `triton__*`, `live365__*`, `radiojar__*`, `iheart__*`, `radioking__*`, `airtime__*`, `zeno__*` | Per-platform time formats; slates, file names, empty bodies, ended and stale items |
| Broadcaster networks | `sr__*`, `abc__*`, `radiofrance__*`, `npo__*`, `npr_composer__*` | `/Date(ms)/`, steps tree, naive local time, MM-DD-YYYY in a station zone, show-only |
| Server status pages | `icecast__*`, `shoutcast__*` | Combined and star-format titles; no stamp |
| In-band ICY | `icy__*` | Empty, station-name echo, ad marker, iHeart automation attributes (song and promo), junk in `StreamUrl` |

## What this does not cover yet

- **History and next.** The record has no history list. Several adapters provide one (KEXP, KCRW, AzuraCast, ABC). Add it when a surface needs it.
- **HLS timed metadata** (`channel: "hls-id3"`). No case yet.
- **Artwork size and fallback.** `artworkUrl` is passed through at whatever size the source sends. No case covers a host that fails over `https`.
- **Encoding repair.** A source that sends `?` for non-ASCII characters (seen on Icecast and Zeno) is passed through as received.
- **Adapters not yet recorded:** Radio Paradise, NTS, TuneIn.
