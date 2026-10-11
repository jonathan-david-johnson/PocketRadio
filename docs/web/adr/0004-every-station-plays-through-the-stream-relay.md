# Every station plays through the stream relay

Status: accepted (2026-10-11)

The web player plays every radio station through a Cloudflare Worker relay,
including stations that already serve `https://`. The relay requests the
station with `Icy-MetaData: 1`, strips the ICY metadata blocks from the audio
it forwards, and publishes each track title to the page. Browsers can't read
ICY metadata, and they block `http://` audio on an `https://` page. Track
titles from a separate connection would not follow the same audio timeline the
listener hears (see `tools/stream-probe.py`'s evidence boundary in the shell
`AGENTS.md`). A relay on the listener's own connection fixes both problems.

## Considered Options

- **Relay every station (chosen).** One playback path. Titles follow the
  listener's audio, offset only by the browser's buffer.
- **Relay only `http://` stations.** This leaves `https://` stations without
  ICY titles, and so without lyrics, except where a tracklist API exists.
- **Separate metadata-only connection.** This is a different audio timeline,
  so titles would drift from the listener's audio by an unknown amount.

## Consequences

- The relay must not be an open proxy. It serves only signed-in sessions, and
  accepts a station id, never a URL. It looks up the stream URL itself: from
  the `curated_stations` table, or from radio-browser by station UUID for
  favorites and Browse results.
- Podcast episodes play directly when their audio URL is `https://`. Only
  `http://` episode audio goes through the relay, which must resolve the URL
  from an episode the Pocket Casts API returned for the user, not from a
  URL the browser supplies.
- All radio audio passes through Cloudflare. Before relying on this,
  confirm Cloudflare's terms for proxying audio and the Workers CPU limits
  (see ADR 0002).
- KCRW tracklist alignment (the M12 port) and ACRCloud fingerprinting are
  not part of the first release. Each needs its own milestone.
