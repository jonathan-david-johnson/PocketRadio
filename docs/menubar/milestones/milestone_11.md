# M11 — KCRW playback-aligned tracklist and lyrics experiment

**Status:** M11-A offline validation is complete and awaiting user review after approved M10 merge `a3787ff`. M11-B still requires separate approval. No production endpoint change, M11 commit, or M11 merge is authorized by this index.

**Goal:** Evaluate KCRW's measured AAC/HLS media-clock relationship without allowing the experiment to grow into an unreviewed production refactor. First prove and report the occurrence-selection rule offline. Only after a separate user approval may the menubar app expose the rule behind reversible experimental controls.

## Milestone split

| Slice | Status | Purpose | Approval gate |
|---|---|---|---|
| [M11-A](milestone_11a.md) | Offline result complete; awaiting review | Replay the retained KCRW traces and measure the fixed `+160s` occurrence-selection rule | Review the derived decisions, residuals, pause behavior, exclusions, and sensitivity analysis with the user |
| [M11-B](milestone_11b.md) | Planned; not approved to implement | Put the frozen candidate behind opt-in AAC/HLS controls in the menubar app and run fresh attended sessions | Requires explicit approval after M11-A; rollout remains a later decision |

M11-A is not evidence from a new listening session. The same two captures motivated the candidate and test it, so they are development evidence rather than an independent holdout. M11-B supplies fresh attended evidence on a recorded output route.

## Shared evidence and constraints

- Nine identified KCRW song changes in two attended captures had `programDate − playedAt = 158.863–163.171s`, including changes after 11s and 31.367s pauses.
- The measured endpoint is exactly `https://streams.kcrw.com/e24_aac/playlist.m3u8`. MP3, another AAC variant, KEXP, iOS, and another output route do not inherit this calibration.
- Feed entries arrived before the listener reached the matching audio. Feed receipt and HTTP cache age describe availability, not the transition clock.
- The s2 marker at 246.879s was a station ID; “Fools in Love” began at the 304.635s marker. The feed omitted the break. Neither slice may count the commercial as a song start or claim to recognize it.
- The captures contain no lyric-landmark markers. Track-selection results cannot establish lyric-recording identity or line-level accuracy.
- `+160s` is an experimental feed-to-program-date parameter. It is separate from any recording-specific lyric correction and from existing saved station offsets.

## Cross-slice approval boundaries

1. M11-A branch `feature/stream-session-model` starts at M10 feature head `0d6653e`. M10 was later merged to `main` by `a3787ff`; M11-A commits remain separately gated.
2. M11-A may add offline core/replay code and tests only. It ends with a user review; it does not flow automatically into app work.
3. M11-B requires explicit approval after that review. It may not change default endpoints, favorite rows, curated station data, or saved lyric offsets.
4. A successful M11-B attended experiment still does not authorize a default rollout, commit, merge, or iOS port. Those remain separate decisions.
5. `docs/menubar/current_milestone.md` points to M11-A. Repoint the symlink for later milestones rather than writing through it.

## Out of scope for all of M11

- KEXP or MP3 calibration.
- Automatic ad recognition, audio capture/upload, ACR alignment, stream proxies, or custom decoders.
- Guaranteed lyric precision from station timestamps.
- iOS, background, Bluetooth, CarPlay, or route-parity claims.
- A general lyric-catalog rewrite, new artwork pipeline, or unrelated application refactor.
