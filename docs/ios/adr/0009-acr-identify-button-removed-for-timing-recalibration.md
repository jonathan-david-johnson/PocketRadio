# 0009 — The ACR Identify button is removed; its slot recalibrates the timing

**Status:** Accepted (2026-10-12). It records a feature that was built, worked, and is being removed.

## Context

KCRW's ICY stream is empty (`StreamTitle=''` on every block), and its tracklist feed can lag the audio or stall for hours. In June 2026 an Identify button was added to station detail so the listener could ask what was playing from the audio itself, whatever the feed said.

## What it was

- A button in station detail (iOS commit `1ff334195`, 2026-06-03, and the lyric-sync port `539a5a17f`).
- `ACRFingerprinter` opened a **second HTTP connection** to the station's stream URL, read about 15 s of the raw MP3 or AAC bytes (no ICY metadata, which corrupts the fingerprint), and posted them to ACRCloud's `/v1/identify` as a signed multipart request (HMAC-SHA1 over the access key).
- A match with confidence 70 or more became a tracklist row at the top of the list, with iTunes artwork resolved for it, and a toast with the title.
- The menubar app has its own `TrackFingerprinter` for the same service. It is not part of this change.

## What happened

It worked. It identified the song that was playing, from the audio, independent of the feed. It gave a **title only**, never a position in the song.

When KCRW alignment arrived (M14), the title and artwork of the audible song came from the player's own clock, and the button was hidden for a station in Apply (ADR 0005), because an identified row would have competed with the aligned song. From then on it only appeared for stations and modes where alignment is off.

## Decision

Remove it. `ACRFingerprinter`, its tests and the button are deleted. The slot in the button row now holds a **recalibrate** button for KCRW in Apply (Star of Life icon). It runs a short ShazamKit calibration and corrects the feed-to-program offset ([ShazamKit experiment](../experiments/2026-10-10_shazamkit_offset_anchor.md)), with progress shown in the lyric header row.

Reasons:

- **The aligned title already answers "what is playing" for KCRW**, and does so continuously and without a button.
- **The Identify button never gave a position**, so it could not fix timing, which is the real problem for lyrics. ShazamKit's `predictedCurrentMatchOffset` does.
- **A second stream connection is a different audio timeline** from the one the player renders, so it could never serve as ground truth for what the listener hears. The microphone path does.
- **The ACRCloud key and secret were written in source** (`ACRFingerprinter.credentials`) and pushed to GitHub.

## Consequences

- No in-app identification for stations without a tracklist or in Off mode. Nothing else used the result.
- The ACRCloud access key and secret remain in git history. Treat them as exposed and rotate them with ACRCloud.
- The menubar's `docs/menubar/ACR_track_fingerprinting.md` and `TrackFingerprinter` are unchanged.
- ShazamKit replaces it for timing only, and only while the microphone can hear the audio.

## Rejected alternatives

- **Keep both buttons.** The row is narrow, the Identify button is hidden in Apply, and it can't fix timing.
- **Move Identify elsewhere.** Nothing needs it once the aligned title exists.
- **Use ShazamKit for titles too.** The aligned title is continuous and needs no listening.

Evidence: `1ff334195:podcasts/Radio/ACRFingerprinter.swift` and the iOS repo's history of `StationDetailViewController` (the `identifyButton`, removed in this change).
