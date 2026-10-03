# M10 — Stream Lab: capture and deterministic observation replay

**Status:** Complete. Stream Lab feature commit `0d6653e` was merged and pushed to menubar `main` by `a3787ff`. No production playback changes.

**Execution tracking:** [current handoff, phase status, and open decisions](milestone_10_handoff.md).

**Goal:** measure KCRW/KEXP playback metadata and station-feed timing on the menubar app's AVPlayer stack before selecting an automatic lyric alignment policy. Keep observations separate from claims about what is audible.

**User checkpoint:** run a macOS command with an explicit stream URL, hear the station, mark an audible change, then replay its exported trace without network access. Compare player metadata and feed-top candidates on one timeline.

## Branch model

These are independent nested repositories, not branches of one application repo:

- iOS configurable-tab-bar work is complete and synchronized. Feature commit `66e670f0b` was merged into `trunk` by `0751918f8`; local `trunk` and `origin/trunk` both point to that merge. Do not carry the completed feature branch into Stream Lab work. Branch retirement is separate from this milestone.
- Menubar `feature/stream-monitoring-lab`, from clean `main` at `a995f06`: this milestone only. Merge after capture/replay testing and user approval.
- Later menubar `feature/stream-session-model`, from updated `main`: current-occurrence reconciliation and media-clock lyric anchors informed by captures.
- Later iOS `fix/stream-presentation`, from completed `trunk`: artwork rebuild/late-result guards and lyric-screen lifecycle defects.
- Later iOS `feature/stream-session-model`, from updated `trunk`: integrate the tested model and verify Bluetooth/CarPlay/background behavior.
- Shell repository: review/plan documents are separate from app code. Commit only explicitly selected stream documents when approved. No console branch is needed for this slice.

Avoid a long-lived cross-platform integration branch. Share a versioned trace contract and fixtures, then merge small platform branches independently.

## Scope

- `pocket-radio-menubar/Tools/StreamLab/Package.swift`: dependency-free Swift package with a Foundation-only diagnostics library, macOS AVPlayer executable, and isolated tests. Does not modify the Xcode app target or existing `PlayerViewModel`.
- `Sources/StreamDiagnostics/`: versioned trace events, bounded private trace file, feed decoding that retains breaks and provider IDs, deterministic observation snapshots, and URL redaction. No account lookup, defaults, or Supabase writes.
- `Sources/StreamLab/`: explicit-URL capture; AVPlayer timed metadata, status/buffer/media-time samples; serial feed polling; marker/pause/resume/quit commands; offline replay.
- `Tests/StreamDiagnosticsTests/`: synthetic data only; no real stations, account state, preferences, or copyrighted audio.
- Package README and menubar Makefile targets: build, test, capture, replay, trace limitations and manual procedure.

## Behaviors to test (red -> green, one at a time)

1. Trace write/read/replay produces identical observation snapshots; captures require a start, ordered sequence/elapsed time, and an explicit end. Persisted UTC dates use millisecond resolution; corrupt or incomplete traces fail clearly.
2. File recording is bounded, refuses overwrite, and strips URL credentials/query/fragment. Limits or write failures cannot silently look like complete captures.
3. KCRW/KEXP parsers preserve music/break observations, source time, and KEXP play IDs. Feed observations do not overwrite the separate player metadata candidate.
4. Replays reject events for another session, backward sequence/elapsed time, unsupported schema, and events after stop. Wall-clock corrections may move backward; multiple metadata items and their media ranges remain observable.
5. A local synthetic audio capture yields player state samples and a complete replayable trace without using an account or contacting a real feed. Verify the live recorder manually on KCRW/KEXP before merge.

## Out of scope

- Correcting production titles, artwork, or lyric clocks in this first slice.
- Claiming feed time or first ICY arrival equals an audible song boundary.
- Recording or uploading audio, ACR integration, stream proxies, custom decoders, or a revived TUI.
- Output-device latency calibration, physical CarPlay validation, and automatic sync guarantees.
- Additional iOS tab-bar work or feature-branch cleanup; M10 does not modify the iOS checkout.

## Design reference

[Stream-monitoring review and proposed model](../../ios/architecture/reviews/stream-monitoring-review-2026-09-16.md).
