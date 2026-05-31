# M1: Skeleton + Audio — Play a Hardcoded Stream

**Status**: ✅ DONE (2026-05-31)

Channel plays `https://streams.kcrw.com/e24_mp3` via the `Audio` node (`buffering`→`playing` confirmed on device); physical-remote OK pauses/resumes; state prints to telnet. Note: ECP `/keypress` is blocked by the device's "Control by mobile apps" network setting, so on-device key testing uses the physical remote — ECP `launch/dev` + telnet capture still work for everything else.

## Goal

Channel boots a SceneGraph scene and plays one hardcoded radio stream through the `Audio` node, with OK toggling play/pause. Establishes the audio foundation every later milestone builds on.

## Done when

- Channel launches to a simple scene (title + a play/pause state label)
- Audio plays `https://streams.kcrw.com/e24_mp3` via the `Audio` node
- OK (and the remote Play/Pause key) toggles play ↔ pause
- `Audio` `state` transitions print to telnet (`buffering`/`playing`/`paused`/`finished`/`error`)
- Back exits cleanly

## What to Build

Already in place from Spike 0 (`manifest`, `source/main.brs`, `MainScene`, the `Task` + `roUrlTransfer` pattern, placeholder icons/splash, the `make build`/`install`/`telnet` loop). M1 swaps the spike's relay code in `MainScene` for an `Audio` node.

### `Audio` playback (HANDOFF §7)
```brightscript
m.audio = m.top.createChild("Audio")
content = createObject("roSGNode","ContentNode")
content.url = "https://streams.kcrw.com/e24_mp3"
content.streamformat = "mp3"          ' see streamformat note below
m.audio.content = content
m.audio.observeField("state", "onAudioState")
m.audio.control = "play"
```
- Map OK / `Play` key (`onKeyEvent`) to toggle `control` between `"play"` and `"pause"`.
- Print `m.audio.state` on change.

### streamformat (carry forward to M3)
Hardcode `"mp3"` here. Real inference (extension/`codec` → `mp3`/`aac`/`hls`) lands in M3 when stream URLs become dynamic — a wrong `streamformat` is a silent no-audio failure, so do not assume mp3 once URLs vary.

## Implementation Strategy

1. Replace `MainScene` relay-spike body with the `Audio` node + hardcoded stream.
2. Verify audio + state prints on device.
3. Wire OK/Play toggle; verify pause/resume.

## User Checkpoint

Install → launch → hear KCRW Eclectic 24; OK pauses/resumes.

## Commit
TBD — after audio verified on device.
