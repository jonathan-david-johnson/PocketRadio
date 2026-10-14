# Experiment (STUB): can the heal read the stream's audio directly instead of the microphone?

> **STUB. NOT READY TO EXECUTE.** This page records an idea and what is known about it. Every section marked **TBD** has to be filled in, and the open questions answered or explicitly accepted, before anyone writes code or runs a device test. Nothing here is a decision. The pass criteria are a proposal.

**Status**: STUB — 2026-10-14. No code. Follows the [unified skew experiment](2026-10-12_unified_skew.md), whose heal listens to the speaker with ShazamKit's managed session. Belongs to [M14](../milestones/milestone_14.md).
**Question**: The heal needs ShazamKit to name the song and its position, and it needs the stream's clock at that instant. The microphone supplies the audio today. Can the app instead fetch the stream's own audio segments, build the ShazamKit signature from them, and take the clock from the segments' own timestamps?

## Before this runs

- [ ] The unified skew experiment has a result on the mic heal's bias (heal versus ear), so there is a number to compare against.
- [ ] Every open question below has an answer, or a stated decision to accept the risk.
- [ ] The ShazamKit signature API is read in the current docs (Context7), not from memory.
- [ ] The user agrees the phases and pass criteria.
- [ ] Decide where the spike lives (branch and worktree). **TBD.**

## Why

What the microphone route costs:

- It works only where the mic can hear the audio: the phone's speaker or a car cabin. Not headphones, Bluetooth, or a muted phone.
- It needs the mic permission, a quiet room, and about 7 s of real listening per anchor.
- ShazamKit's managed session refuses a session opened right after another closes (it answers "Missing entitlements"), so anchors need 5 s gaps.
- It measures what reaches the room, which includes speaker delay. That is the right number for the ear and not necessarily for the app's model.

## The idea (a sketch, not a design)

1. Get the stream's media playlist and fetch the last two or three segments, about 12 to 18 s of audio.
2. Decode them to PCM and feed ShazamKit a signature built from that audio.
3. ShazamKit returns the song and the position of the first sample in it (`matchOffset`, if it means what we think).
4. Each segment has a `PROGRAM-DATE-TIME`, so the first sample's stream time is known. The song started in the stream at that time minus `matchOffset`. The skew is that minus the feed's stamp for the matching row, as in `SkewSolver`.

## What is known

Checked with `curl` on 2026-10-14. Nothing here was tested on a device.

- KCRW Eclectic24's `e24_aac` playlist redirects to a variant playlist with `listeningSessionID` in its query.
- That playlist is HLS version 3 with a 7 s target duration, three segments visible (about 18 s), plain `.aac` files of about 6 s each (names like `chW8kzkHgdA-298669024-5990.aac`).
- Every segment has its own `EXT-X-PROGRAM-DATE-TIME` to the millisecond, and consecutive segments are contiguous (`:25.000` plus 5.990 s gives `:30.990`).
- Two sessions started two seconds apart had **different segment boundaries** (`21:53:45.000` and `21:53:49.000`). Each session is segmented from its own start. The media sequence number restarts at 0.
- The app's own session already shows its program date running a constant 5 to 6 s behind wall clock (earlier device runs).

## What it would change

Gains: works on any output, no mic, faster (a few seconds, no real-time listen), no room noise, and possibly no session-spacing problem.

Losses and risks:

- It measures the **stream's** timeline, not the **audible** one. Output delay (speaker about 0.1 s, Bluetooth a few tenths, AirPlay about 2 s) would need its own per-route constant, which the app can't measure without a mic. **TBD:** do we need it.
- A second listening session is a second listener on the station. **TBD:** is that acceptable, and for which stations.
- Only stations with HLS, per-segment timestamps and decodable plain audio qualify. ICY and progressive streams have no timeline to read.

## Alternatives, and why not first

- **Tap the player's own audio** (an audio processing tap). I recall that it doesn't work on HLS. Not verified.
- **Intercept the player's own segment requests** with a custom resource loader. It guarantees the same timeline as playback, but it changes how live playback loads, which was just stabilized (ADR 0007). Higher risk. Worth revisiting only if the separate-session timeline turns out to differ.
- **Capture the system output.** iOS doesn't allow it for a normal app.

## Open questions (must be answered or accepted)

1. **Same timeline across sessions?** Does the same audio carry the same timestamp in a second session as in the player's? If not, the idea fails. **TBD:** how to test. One way: fetch two sessions at once, match the same song in both, and compare the skews. Another: compare against the player's `currentDate()`.
2. **ShazamKit semantics.** What does `matchOffset` mean for a signature we build ourselves, and what does a streaming buffer give? **TBD:** read the docs; the iOS 27 headers are on disk.
3. **Decoding.** Do plain `.aac` (ADTS) segments decode with `AVAudioFile`, or is `AudioFile` or `AVAssetReader` needed? What is the codec priming, and what happens at a discontinuity? Do two segments join without a gap?
4. **Rate limits.** Can signature matches run back to back, or does the entitlement refusal apply here too?
5. **Station-agnostic reach.** How many curated stations have HLS with per-segment timestamps and plain audio? **TBD:** a survey of the list, not yet done.
6. **How to get a fresh session.** The master playlist hands out a new `listeningSessionID` each fetch. Do we need credentials or consent for other stations? **TBD.**
7. **Output latency per route.** Needed? If so, how is it measured and where is it stored?
8. **ADR 0009 said** a second stream connection is "a different audio timeline" from the player's. This idea claims the segment timestamps fix that. If it works, the ADR's reason needs an addendum.
9. **Data cost.** Three 256 kbps segments are about 100 KB per anchor. **TBD:** cellular policy.
10. **Can a Mac script do the offline part?** A command-line check on the Mac (fetch segments, decode, match) would answer 1 to 4 without the phone. ShazamKit on the Mac may need the same App Service entitlement. **TBD.**

## Phases (an outline to detail before executing)

| Phase | What | Pass if (proposed, not agreed) |
|---|---|---|
| 0. Offline feasibility | Answer questions 1 to 4 without shipping anything. Mac script if possible, else a throwaway Debug button | Segments decode, a signature matches the right song, and the offset is sane |
| 1. Debug button | "Heal direct" beside the mic heal, using the separate-session fetch | Returns a skew in a few seconds without the mic |
| 2. Side by side | Run direct and mic heals at the same moment over at least five songs on the speaker | Within about 0.5 s of each other. Record the difference and its sign |
| 3. Other routes | Headphones and Bluetooth, where the mic can't run | Direct heal still works. Output delay measured if possible |
| 4. Decision | Replace, add alongside, or drop | **TBD** |

What Phase 2 tells us beyond pass or fail: if the direct and mic skews agree, the roughly 1 s gap between the mic heal and the user's ear is not from the microphone (it would be the lyric files or taste). If they differ by about 1 s, the mic path is the cause.

## Not covered yet

Where the code would live, how the button is gated (Debug only, like the mic heal), tests, logging, and what the ADR would say. All **TBD**.
