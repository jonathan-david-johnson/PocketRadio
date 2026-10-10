# 0001 — A pill tap stages a source; the play button starts it

**Status:** Accepted (2026-05-24)

## Context

The popover has one podcast pill and three stream pills. The first design
(M6.1) played a source the moment its pill was tapped. That interrupted
whatever was playing just because the user was looking at another pill.

## Decision

Tapping a pill only **stages** it: the pill shows as selected and the tracklist
is prefetched. Nothing changes in playback. The play button then starts the
staged source, or stops the current one.

The same rule is used by the console TUI and described in
`docs/console/CONTEXT.md` as *Pill*.

## Consequences

- Browsing the pills never interrupts audio.
- Starting a different source takes two taps (pill, then play).
- Any new surface that has source pills should follow this rule.

## Rejected alternatives

- **Play on tap** (M6.1). Shipped first, then replaced because browsing
  interrupted playback.

Evidence: `archive/menubar-m6.1:docs/menubar/milestones/milestone_6.1.md`
§ Corrections, and menubar commit `f9f4316`.
