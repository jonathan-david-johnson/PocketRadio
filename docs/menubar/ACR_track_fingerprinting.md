# ACR Track Fingerprinting — Menubar App

**Status**: BLOCKED on ACRCloud credentials (support ticket open as of 2026-06-03)
**Branch**: `feature/acr-track-fingerprinting` in `pocket-radio-menubar`

---

## What This Is

A toggle button in the menubar controls row that switches track identification
from the station's native tracklist API to ACRCloud audio fingerprinting.
Motivated by two KCRW-specific failure modes:

1. Title out of sync — tracklist API lags behind what's actually playing
2. Tracklist stalls for hours (server-side KCRW issue) — no fallback exists

ACRCloud gives ground-truth identification from the stream audio itself,
independent of the station's API.

---

## Stream Investigation Findings (`tools/stream-probe.py`)

Run `python3 tools/stream-probe.py kcrw` or `kexp` to monitor ICY vs API sync.

| Station | ICY StreamTitle | Tracklist API | Notes |
|---------|----------------|---------------|-------|
| KCRW    | **Dead** — always `''` across 100+ blocks | Only source of track info | When API stalls (hours), zero fallback |
| KEXP    | Works after ~14s Adswizz pre-roll | Works | ICY format: `"Song - Artist - Album"` |

KCRW's ICY is permanently empty — the stream carries no embedded metadata.
ACRCloud is the only way to independently verify what's playing.

---

## Architecture

No AVPlayer tapping needed. `TrackFingerprinter` opens a **second HTTP
connection** to the stream URL, reads ~15s of raw MP3/AAC bytes, and sends
them to ACRCloud (which accepts raw encoded bytes, not PCM).

Tracklist polling keeps running in ACR mode — ACR result just overrides
`nowPlayingTitle` when confidence >= 70. On mode switch back to Tracklist,
the tracklist title is immediately restored.

---

## What's Already Built (on the branch)

### New file: `PocketRadio/Services/TrackFingerprinter.swift`

- `TrackIdentificationMode` enum: `.tracklist` / `.acr`
- `ACRCloudCredentials` struct: `host`, `accessKey`, `accessSecret`
- `TrackFingerprintResult` struct: `title`, `artist`, `album`, `confidence`
- `TrackFingerprinter` class:
  - `start()` / `stop()` — polls every 30s
  - `captureAudioBytes()` — second URLSession connection, reads `bitrate × 15s` bytes
  - `recognize(audioData:)` — **stubbed**, ACRCloud SDK call is commented in
  - `parseACRCloudResult(_:)` — parses ACRCloud JSON response
  - `minConfidence` gate (default 70)

### `PlayerViewModel.swift` additions

- `@Published var trackIdMode: TrackIdentificationMode = .tracklist`
- `var showTrackSourceToggle: Bool` — true when `currentSource?.isRadio == true`
- `func toggleTrackIdMode()` — switches mode, starts/stops fingerprinter
- `startFingerprinter(for:)` / `stopFingerprinter()` — lifecycle management
- Fingerprinter stopped + mode reset on `stopPlayback()` and `logout()`

### `ContentView.swift` additions

- `trackSourceToggle` view — pill button, dim when Tracklist, accent-colored when ACR
- Appears right of play/pause in controls row when live stream is playing
- Tooltip explains current mode

---

## How to Resume (when creds arrive)

### 1. Get ACRCloud credentials

Sign up at acrcloud.com → Projects → Create Project → copy:
- `host` (e.g. `identify-eu-west-1.acrcloud.com`)
- `access_key`
- `access_secret`

Free tier: ~1000 recognitions/month. Fine for personal polling at 30s intervals
(~2880/day for one stream = paid tier needed for all-day use; free is fine for
diagnostic/occasional use).

### 2. Add the SDK

Download `ACRCloudSDK.xcframework` from acrcloud.com → SDK Reference → Mobile SDK.

In Xcode:
1. Drag `ACRCloudSDK.xcframework` into the `pocket-radio-menubar` project
2. General → Frameworks, Libraries, and Embedded Content → set to "Embed & Sign"
3. Add `NSMicrophoneUsageDescription` to Info.plist if the SDK requires it even
   for file-based (non-mic) recognition — check the SDK release notes.

### 3. Wire up credentials

In `PocketRadioApp.swift` init (or wherever app startup happens):

```swift
TrackFingerprinter.credentials = ACRCloudCredentials(
    host: "identify-eu-west-1.acrcloud.com",   // your region
    accessKey: "YOUR_ACCESS_KEY",
    accessSecret: "YOUR_ACCESS_SECRET"
)
```

Keep these out of git — use a gitignored `Secrets.swift` or environment plist.

### 4. Uncomment the SDK call

In `TrackFingerprinter.swift`, find the `recognize(audioData:)` method.
The `// ─────── TODO ────────` block has the exact SDK code ready to uncomment.
Delete the `await fireError("ACRCloud SDK not yet integrated...")` line below it.

### 5. Build and test

```bash
make menubar   # build + launch
```

With KCRW playing:
1. Wait for tracklist to show a title
2. Click "Tracklist" button → it turns accent-colored "ACR"
3. After ~30s, ACRCloud result should override the title in the menu bar scroll
4. Compare with tracklist API title — they should match when API is fresh,
   ACR wins when API is stale

---

## Known Gotchas

- ACRCloud `recognizeWithAudio(_:withPCMSampleRate:)` — pass `0` for sample rate
  when sending encoded (MP3/AAC) bytes, not PCM.
- The second HTTP connection to the stream is independent of AVPlayer's buffer,
  so it may be a few seconds ahead/behind the actual playing position. Fine for
  track identification; not suitable for millisecond-sync.
- ACRCloud free tier rate-limits. At 30s poll interval, ~2880 calls/day per
  stream. Free tier is 1000/month → needs paid plan for continuous monitoring.
  For occasional/diagnostic use, 1000/month is plenty.
- The KCRW tracklist API sometimes stalls for hours — this is the main
  motivating use case. The `stream-probe.py --stale-warn 5` flag catches this.

---

## Related Files

| File | Notes |
|------|-------|
| `pocket-radio-menubar/PocketRadio/Services/TrackFingerprinter.swift` | New — core fingerprinter |
| `pocket-radio-menubar/PocketRadio/View Models/PlayerViewModel.swift` | Edited — mode state + lifecycle |
| `pocket-radio-menubar/PocketRadio/ContentView.swift` | Edited — toggle button |
| `tools/stream-probe.py` | Diagnostic tool — ICY vs API monitor |
| `docs/roku/spikes.md` | Background on ICY investigation approach |
