# M1: Skeleton + Audio — Play a Hardcoded Stream

**Status**: NOT STARTED

## Goal

A Roku channel ("PocketStreams") that installs, boots a SceneGraph scene, and plays one hardcoded radio stream through the `Audio` node. No auth, no API, no lists — validates the full sideload → telnet-debug → audio loop on the physical device.

## Done when

- Channel zip sideloads via the Development Application Installer (`Install Success`)
- Channel launches from the Roku home screen and shows the SceneGraph scene
- Audio auto-plays (or plays on OK) `https://streams.kcrw.com/e24_mp3` via the `Audio` node
- Audio `state` transitions are printed to the telnet debug console (`8085`)
- OK / Play toggles play ↔ pause; Back exits cleanly
- Channel icons + splash present (no missing-asset placeholders)

## What to Build

### Project layout
```
pocket-radio-roku/
├── manifest                       # title=PocketStreams, major_version, icons, splash, ui_resolutions=fhd
├── source/main.brs                # Sub Main() -> screen + MainScene
├── components/MainScene.xml(.brs) # root scene: create Audio node, play hardcoded URL
└── images/                        # icon_hd 290x218, icon_fhd 336x210, splash_hd 1280x720, splash_fhd 1920x1080
```

### `source/main.brs`
```brightscript
Sub Main()
    screen = CreateObject("roSGScreen")
    port = CreateObject("roMessagePort")
    screen.setMessagePort(port)
    scene = screen.CreateScene("MainScene")
    screen.show()
    while true
        msg = wait(0, port)
        if type(msg) = "roSGScreenEvent" and msg.isScreenClosed() then return
    end while
End Sub
```

### `MainScene` (.brs `init`)
```brightscript
m.audio = m.top.createChild("Audio")
content = createObject("roSGNode","ContentNode")
content.url = "https://streams.kcrw.com/e24_mp3"
content.streamformat = "mp3"
m.audio.content = content
m.audio.observeField("state", "onAudioState")
m.audio.control = "play"
```
Observe `state`; `print "audio state: "; m.audio.state` so transitions show on telnet. Map OK/Play key to toggle `control` between `"play"`/`"pause"`.

### `manifest` essentials
`title=PocketStreams`, `major_version=1`, `mm_icon_focus_hd=pkg:/images/icon_hd.png` (290x218), `_fhd` (336x210), `splash_screen_hd`/`_fhd`, `ui_resolutions=fhd`.

## Implementation Strategy

1. Scaffold minimal layout (manifest + main.brs + MainScene + placeholder icons).
2. Sideload, confirm install + launch + telnet output.
3. Add `Audio` node, play hardcoded stream, verify audio.
4. Wire OK/Play toggle; verify pause/resume.

## User Checkpoint

Install channel → launch from home screen → hear KCRW Eclectic 24; OK pauses/resumes.

## Commit
TBD — after sideload + audio verified on device.
