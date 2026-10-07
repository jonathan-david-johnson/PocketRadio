# Shared feature specs

Plain-language [Gherkin](https://cucumber.io/docs/gherkin/) scenarios that describe what a PocketRadio
surface should show or do. They are shared across platforms. Each platform implements its own step
definitions. Today only iOS does.

## Layout

```
contracts/features/<area>/<name>.feature
```

| Area | Files | What it specifies |
|---|---|---|
| `now_playing/` | `smoke.feature` | What the system now-playing display shows for a live radio station. Used by the iOS CarPlay harness (`pocket-radio-ios`, M13.1). |
| `now_playing/` | `carplay_artwork.feature` | **Draft.** The M13 E7 baseline scenarios for iOS bugs 4 and 5. M13.2 will rewrite it as the scenario suite. |

## Vocabulary

Write steps in terms of the listener, the stream, and the display, not in terms of one platform's APIs.

| Phrase | Meaning |
|---|---|
| the system now-playing display | The OS-level now-playing surface. iOS: `MPNowPlayingInfoCenter`, which CarPlay and the lock screen draw from. |
| a station "X" that streams from the local test server | A fake station backed by the platform's local fake world |
| the station's tracklist lists only "T" by "A" with COLOUR artwork | The station's recent-plays feed |
| the station's tracklist takes N seconds to arrive / fails with status N | Fault staging for the fake world |
| the listener starts the station | Playback starts through the app's normal entry point |
| the stream announces "T" by "A" | The station's stream reports a new song |
| the system now-playing display is empty | Precondition: nothing is showing |
| the display shows the title … / COLOUR artwork | Assertions on the display |
| the display is marked as a live music stream | The display presents the station as live music, not a podcast with a scrubber |

A scenario that only makes sense on one platform gets an extra tag, such as `@ios-only`.

## Tags

- `@ios`, `@carplay`, and future platform tags name the platforms that implement the steps.
- `@smoke` marks a short end-to-end check.
- A known bug is **not** marked in these files. A bug on iOS says nothing about another platform, so each
  platform keeps its own table of expected failures in its test code.

## Changing a spec

Specs change **additively**. Adding a scenario or a new step phrase is safe. Rewording or removing a step
that another platform already implements is a breaking change: update every implementing platform in the
same change, or add the new phrase and keep the old one until they migrate.

## Where the iOS steps live

`pocket-radio-ios`: `PocketCastsTests/Tests/CarPlayOutput/Harness/Gherkin/NowPlayingSteps.swift`. The runner
finds this folder through the test file's own path (`../contracts/features/`), so the shell checkout must
sit next to the iOS worktree.
