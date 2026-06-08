# PocketRadio Console

The terminal (TUI) surface of PocketRadio. Shares the Pocket Casts + radio
domain with the iOS, menubar, and Roku surfaces; adds terminal-specific terms.

## Language

**Source**:
The thing currently playing or staged to play — either an Up Next *Episode* or a
radio *Station*. The one piece of state both UIs render around.
_Avoid_: "track" (that means a song), "channel".

**Target**:
What a play command resolves to before it becomes the *Source*: one of
`UpNextTop`, `NewestRelease`, a `Station`, or a specific `Episode`. Mini-mode
argument resolution produces a Target.
_Avoid_: "destination".

**Mini mode**:
The one-line run mode entered by `pocket-radio <arg>`. Single row, text only, no
alt-screen. Plays immediately and shows compact transport controls.
_Avoid_: "flag mode", "compact mode", "headless".

**Full mode** (a.k.a. **Full TUI**):
The alt-screen run mode entered by bare `pocket-radio` (or `--full`). Mirrors the
menubar layout: pills, now-playing with art, lists, detail panes.
_Avoid_: "GUI", "rich mode".

**Reserved word**:
A mini-mode argument with fixed meaning rather than a name lookup. Currently
`up_next` and `new`.

**Up Next**:
The user's Pocket Casts play queue. "Top of Up Next" is the first/currently-cued
episode.
_Avoid_: "queue" alone (ambiguous), "playlist".

**Episode**:
A single podcast episode with a playable URL, `playedUpTo` (progress, seconds),
and `duration`.

**Station**:
A radio stream from radio-browser.info, identified by its station UUID, with a
resolved stream URL and optional logo/metadata.
_Avoid_: "channel".

**Favorite**:
A Station the user has saved (stored in Supabase `radio_favorites`, keyed by
`user_uuid`). The first three favorites map to the full-TUI stream pills.

**Tracklist**:
The now-playing song history for stations that publish one (KCRW, KEXP). Distinct
from ICY metadata and from ACR identification — all three are *track-identification
sources*.

**New Release**:
An episode published within the last 14 days by a subscribed podcast. Not the
same as an Up Next episode.

**Pill**:
A full-TUI source selector at the top of the layout: one podcast pill + three
stream pills. Selecting a pill stages a *Source*; it does not start playback by
itself (carried over from the menubar's interaction model).

**Engine**:
The non-UI orchestration core (`internal/library`). Owns the *Source*, drives the
*Player*, throttles position saves, and emits the `NowPlaying` state both UIs
render. The Go equivalent of the menubar's `PlayerViewModel`.

**Player**:
The mpv driver (`internal/player`). The only component that talks to mpv. Exposes
load/pause/resume/seek plus a position/duration/metadata event stream.
