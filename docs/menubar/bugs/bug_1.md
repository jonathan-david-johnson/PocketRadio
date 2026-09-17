# Bug 1 — CFNetworkDownload temp files accumulate indefinitely, ~24 GB leaked

**Status:** Open (found 2026-09-13, via an unrelated borg backup investigation —
see [`TIMEMACHINE_TO_BORG_SPEC.md`](../../../../pop/TIMEMACHINE_TO_BORG_SPEC.md)
in the `pop` repo for the context that surfaced this).

Found, not fixed. Root cause is a reasonable hypothesis grounded in the code
below, not a confirmed diagnosis — no repro has been run against a debug build
yet.

---

## Symptom: 248,000+ leaked temp files, ~24 GB, growing since at least May

`~/Library/Containers/com.jdj.pocketradio/Data/tmp/` contains 248,031 files
matching `CFNetworkDownload_*.tmp`, totaling roughly 23.5 GB (the container's
`tmp` dir is 24 GB total; `MediaCache` inside it is only 480 MB, so the rest is
essentially all loose `CFNetworkDownload_*.tmp` files). Sampled file dates go
back to at least May 2026.

`com.jdj.pocketradio` is the **menu bar app** specifically (`PRODUCT_BUNDLE_IDENTIFIER`
in `pocket-radio-menubar/PocketRadio.xcodeproj/project.pbxproj`), installed at
`/Applications/PocketRadio.app`. Not the iOS app — that target uses a different
bundle ID root (`au.com.shiftyjelly.podcasts.*`, inherited from the Pocket Casts
codebase it's built on). Whether every leaked file came from the installed copy
specifically, versus also from debug builds during development, isn't
determinable after the fact — sandbox containers are shared by bundle ID
regardless of which build launched the process.

### Why this matters beyond disk space

`CFNetworkDownload_*.tmp` is macOS's own staging mechanism for in-flight HTTP
transfers — normally short-lived, cleaned up automatically once the transfer
completes. A healthy app's `tmp/` should stay small and self-pruning. This
container growing unbounded for months means whatever's creating these files
is not being given the chance to clean up after itself, or something is
holding a reference that prevents CFNetwork's own cleanup from running.

### Evidence

| Check | Result |
|---|---|
| Container size | 24 GB (`du -sh ~/Library/Containers/com.jdj.pocketradio/Data/tmp`) |
| Leaked file count | 248,031 (`find ... -type f \| wc -l`) |
| `MediaCache` (the one deliberate cache dir in there) | 480 MB — not where the size is |
| Sample file ages | May–June 2026 dates present in a spot check; not a recent regression |
| Bundle ID owner | `pocket-radio-menubar` only, confirmed via `project.pbxproj`; iOS target uses a different ID root entirely |
| `downloadTask` (explicit temp-file API) used anywhere in the app | No — grepped the full menubar source, zero hits |

### Root cause (hypothesis, not confirmed)

No code in the menubar target explicitly requests a temp-file-backed download
(`URLSession.downloadTask` isn't used anywhere — confirmed by grep). All
networking goes through `URLSession.shared.data(from:/for:)` (`APIService.swift`,
`LyricsService.swift`, `TrackFingerprinter.swift`) or through `AVPlayer`/
`AVURLAsset`/`AVPlayerItem` for stream playback (`PlayerViewModel.swift`). So
these files are coming from CFNetwork's own internal transfer/caching layer,
not an app-level "write to temp, forget to delete" bug in the literal sense.

The strongest lead is how aggressively the player cycles `AVPlayerItem`
instances for live radio specifically. `PlayerViewModel.pausePlayback()`
(`PlayerViewModel.swift:1409`) deliberately tears down the entire item on every
pause for radio sources and reconnects fresh on resume — the comment there
says pausing a live stream instead of tearing down causes tracklist/lyrics sync
drift on resume, so this is intentional, not an oversight:

```swift
// PlayerViewModel.swift:1409
private func pausePlayback() {
    if currentSource?.isRadio == true {
        stopPlayback()
        return
    }
    ...
}
```

`stopPlayback()` (`PlayerViewModel.swift:1568`) releases the item the standard
way, `audioPlayer.replaceCurrentItem(with: nil)` — nothing obviously wrong with
the teardown code itself. The hypothesis is that AVFoundation's underlying
CFNetwork layer doesn't always synchronously flush its own staging files at
that point, and a menu-bar radio app — where pause/resume is a very frequent,
low-friction action — cycles through this create/destroy pattern often enough
that a small per-cycle leak compounds into hundreds of thousands of files over
months. Not verified against a debug build or Instruments session; this is the
lead worth chasing first, not a proven mechanism.

### Suggested next steps for whoever picks this up

1. **Confirm the trigger empirically** before assuming the hypothesis above:
   watch `Data/tmp/` file count while repeatedly pausing/resuming a live radio
   stream in a debug build, and compare against podcast playback (which does
   *not* tear down on pause, per the same function) to see if the leak is
   radio-specific or applies to both.
2. **Root-cause fix**, if confirmed: investigate whether there's an
   AVFoundation/URLSession API to force synchronous cleanup on
   `replaceCurrentItem(with: nil)`, or whether the rapid teardown is racing
   CFNetwork's own async cleanup.
3. **Defensive fix either way**: purge `Data/tmp/CFNetworkDownload_*.tmp` files
   above some age threshold (e.g. 1 hour) on app launch. Doesn't require
   root-causing the exact mechanism, and caps the damage regardless of cause.
4. Once fixed, the borg-mac backup's exclude list
   (`~/.config/borg-mac/excludes.txt` on the Mac) should have its
   `com.jdj.pocketradio/Data/tmp` exclusion pattern removed again if the app is
   fixed to self-clean — no reason to permanently special-case it if it stops
   leaking.

## Files involved

- `pocket-radio-menubar/PocketRadio/View Models/PlayerViewModel.swift:1409` —
  `pausePlayback()`, tears down `AVPlayerItem` on every radio pause
- `pocket-radio-menubar/PocketRadio/View Models/PlayerViewModel.swift:1568` —
  `stopPlayback()`, the actual teardown (`replaceCurrentItem(with: nil)`)
- `pocket-radio-menubar/PocketRadio/View Models/PlayerViewModel.swift:1534` —
  `AVPlayerItem(url:)`, where a fresh item is created on resume
- `pocket-radio-menubar/PocketRadio/Services/APIService.swift` — all
  `URLSession.shared.data(...)` calls (not the likely source, but ruled in/out
  alongside the player code during triage)
