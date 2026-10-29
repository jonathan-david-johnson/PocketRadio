# Real-browser checks, 2026-10-29

Chrome 155.0.0.0 (macOS), driven by Playwright, page origin `https://example.com/`. `fetch` with `referrerPolicy: "no-referrer"`.

## Now-playing APIs, direct `fetch` (24 endpoints)

OK (20): somafm, kexp, kcrw, nts, azuracast_demo, laut, radioco, triton, radiojar, live365, iheart,
radioking (`api.radioking.io/widgets/api/v1/…`; the older `www.radioking.com/widgets/…` URL 301-redirects
without CORS headers and fails), airtime, npr_composer, sr, abc, radiofrance, npo, icecast_status
(`ice1.somafm.com/status-json.xsl`), zeno_sse (first event read, then aborted).

FAIL (4): radioparadise API (no CORS), tunein OPML (no CORS), wnyc (no CORS),
shoutcast `7.html` (`http://` from an `https` page: mixed content).

## ICY from a browser (46 `https` streams, default port; first 4 are KEXP, KCRW, SomaFM, Radio Paradise, then 42 from the E3 sample whose URL was under 130 characters)

| Request | Result |
|---|---|
| `fetch` with header `Icy-MetaData: 1` | 15 of 46 succeed (preflight allowed); `icy-metaint` readable in 10 of 46 |
| `fetch` with no custom header | 42 of 46 succeed; `icy-metaint` readable in 0 of 46 |
| KEXP, KCRW | fail with the header (preflight rejects it); succeed without it |
| SomaFM | succeeds with the header, `icy-metaint` readable |

The sample is not uniform: it excludes long tokenised URLs, so it over-represents plain hosts.

## Native audio element

- `canPlayType`: `probably` for MP3, AAC, AAC-in-MP4, Ogg Opus, Ogg Vorbis, FLAC, FLAC-in-MP4; `maybe` for HLS.
- `new Audio()` loaded HLS from `stream.radiofrance.fr` (event `loadedmetadata`).
- SomaFM HLS (`hls.somafm.com/.../program.m3u8`) played for 14 s (`currentTime` 14.4), but exposed no
  `textTracks` and no cues, though the segments carry ID3 `TIT2` (see the E3 HLS section of the landscape report).
- `navigator.mediaSession` present.
