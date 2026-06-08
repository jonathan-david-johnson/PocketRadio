# PocketStreams for Roku

Roku channel companion for PocketRadio. Plays the user's Pocket Casts **Up Next** podcast queue (with resume + progress sync) and **favorite radio streams** (Supabase → radio-browser.info). Target: **feature parity with the macOS menubar app** (not the full iOS app).

The macOS menubar app is the reference implementation. Treat `../pocket-radio-menubar/PocketRadio/Services/APIService.swift` as the canonical API spec and `PocketRadio/View Models/PlayerViewModel.swift` as the canonical playback/state logic. The full self-contained build spec — every endpoint, protobuf wire format, key, and credential — lives in `../pocket-radio-roku/HANDOFF.md`.

## Architecture

```
pocket-radio-roku/
├── manifest                       # channel metadata (title, icons, splash, ui_resolutions=fhd)
├── source/
│   └── main.brs                   # Sub Main() -> create screen + SceneGraph scene
├── components/
│   ├── MainScene.xml(.brs)        # root SceneGraph scene
│   ├── *.xml(.brs)                # sub-views (Up Next, Radio, Browse, Now Playing, Detail)
│   └── tasks/*.xml(.brs)          # Task nodes — ALL network I/O
└── images/                        # channel icons (HD 290x218, FHD 336x210) + splash
```

> **Architecture decision (2026-05-31):** Roku **cannot** read binary protobuf responses — `roUrlTransfer` truncates them at the first NUL byte and there's no `AsyncPostToFile` (proven in [`spikes.md`](./spikes.md), Spike 1). So all Pocket Casts traffic goes through **`pc-relay`**, a Supabase Edge Function that translates JSON↔protobuf. Roku speaks **only JSON**. radio-browser + Supabase are already JSON → called directly from Roku.

### Data Flow

1. **Auth**: email/password → relay `login` → Bearer token + userId → `roRegistrySection`
2. **Up Next**: token → relay `upNext` → episodes (JSON); fill playedUpTo/duration via relay `podcastEpisodes`
3. **Position sync**: relay `updateEpisode` every ~30s + on pause/stop; on finish → completed + relay `upNextChange` (remove)
4. **Favorites**: userId → `x-user-uuid` header → Supabase `radio_favorites` (direct) → resolve via radio-browser.info (direct)
5. **Playback**: `Audio` SceneGraph node — seek to `playedUpTo` for podcasts; play/pause-only for live streams
6. **Tracklist**: poll KCRW/KEXP APIs while their stream is active (direct)

The relay (`pc-relay`) lives in the meta repo at `supabase/functions/pc-relay/`; it ports the manual-protobuf wire logic from menubar `APIService.swift` into Deno.

### Platform Notes (vs menubar/iOS)

| Aspect | Menubar/iOS (Swift) | Roku (BrightScript/SceneGraph) |
|--------|---------------------|--------------------------------|
| UI | SwiftUI/AppKit | SceneGraph XML + render thread, 10-foot D-pad UX |
| Network | URLSession async | `roUrlTransfer` on `Task` nodes (never render thread) |
| Protobuf | SwiftProtobuf / manual | manual encode/decode over `roByteArray`, file-based POST/GET |
| Token store | Keychain | `roRegistrySection` (no Keychain) |
| Audio | AVPlayer | `Audio` SceneGraph node |
| Testing | Xcode build/run | sideload zip + `telnet 10.99.99.50 8085`; no emulator |

### Critical Roku gotchas

See HANDOFF §3. Top hazards: all network I/O on `Task` nodes; protobuf is binary so use file-based POST/GET (string methods corrupt bytes ≥0x80); radio-browser requires `User-Agent: PocketRadio/1.0`.

---

## Spikes (de-risk first)

Before milestones, [`spikes.md`](./spikes.md) settles the pivotal unknown: **can Roku speak Pocket Casts protobuf natively, or do we need a JSON↔protobuf relay?** Gated experiments (toolchain → binary byte-fidelity → real protobuf round-trip). The relay design is parked behind these gates. Milestones below assume the native path; if a spike gate fails, M2/M3/M5 collapse to JSON against a relay.

## Milestones

| Milestone | What | User Checkpoint |
|-----------|------|-----------------|
| [Spikes](./spikes.md) ✅ | De-risk protobuf — native-vs-relay decision | DONE → relay (pc-relay) proven E2E |
| [M1](./milestones/milestone_1.md) | Skeleton + audio — plays hardcoded KCRW stream | Channel installs → launch → hear audio |
| [M2](./milestones/milestone_2.md) | Login + persistence (via relay) | Log in → relaunch → still logged in |
| [M3](./milestones/milestone_3.md) | Radio favorites + Browse/Search (tracer bullet) | See favorites → play → add/remove → search |
| [M4](./milestones/milestone_4.md) | Up Next — list + play + resume + position save | See queue → play → resumes + syncs position |
| [M5](./milestones/milestone_5.md) | Up Next lifecycle + New Releases + detail | Finish→advance, playNow; last-14d list; show notes |
| [M6](./milestones/milestone_6.md) | Polish — skip settings, scrub, tracklist, Now Playing | Scrub seekable, tracklist shows, artwork/title |
| [M7](./milestones/milestone_7.md) ✅ | UI scaffold — 3-section layout, nav bar, MarkupGrid | Nav bar tabs, grid scrolls, focus moves |
| [M8](./milestones/milestone_8.md) ✅ | Bug fixes — nav, grid rows, backdrop, layout | Back works, 2 rows visible, backdrop shows |
| [M9](./milestones/milestone_9.md) ✅ | Now Playing panel — progress, backdrop fade, NOW badge | Progress bar updates, backdrop fades, NOW badge shows |
| [M10](./milestones/milestone_10.md) | Tile redesign — episode metadata + progress strip | Progress strip per tile, podcast name, time-left |
| [M11](./milestones/milestone_11.md) | Polish — nav animation, error states, fav dialog, debug cleanup | Underline slides, errors graceful, browse fav dialog |

**Ordering rationale:** Radio (M3) comes before Up Next (M4/M5) on purpose — it's all JSON (Supabase + radio-browser, direct) and builds the generic list UI + dynamic-URL playback + live-vs-seekable gating on the easy path. Up Next then layers resume/sync/lifecycle on proven UI. Server-side-heavy work (gap-fill, 14-day new-releases merge, atomic finish→remove) lives in the relay, not BrightScript.

## Build & Run (sideload)

```bash
# Zip channel at repo root (manifest + source/ + components/ + images/ — no wrapping folder)
cd pocket-radio-roku && zip -r channel.zip manifest source components images

# Install via Development Application Installer (digest auth)
curl -s --user "rokudev:PASSWORD" --digest \
  -F "mysubmit=Install" -F "archive=@channel.zip" \
  http://10.99.99.50/plugin_install | grep -o 'Install Success\|Identical\|Failed'

# Debug console (print output + crash backtraces)
telnet 10.99.99.50 8085
```
