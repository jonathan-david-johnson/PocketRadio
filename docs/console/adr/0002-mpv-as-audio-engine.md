# mpv as the audio engine, driven over JSON IPC

Audio playback is delegated to an **mpv** subprocess controlled over its JSON IPC
unix socket (`--idle --no-video --input-ipc-server=<socket>`), rather than
binding a native audio/codec library in-process.

## Why

A TUI cannot use AVFoundation the way the menubar does. mpv already solves every
hard part of this app's playback: HTTP/Icecast live streams *and* podcast MP3,
seeking, accurate `time-pos`/`duration` reporting, gapless transitions, and ICY
`metadata` events. Driving it over IPC (`loadfile`, `set_property pause`,
`seek`, `observe_property time-pos`) gives us all of that for the cost of a
subprocess and a socket — versus owning codec/streaming/buffering logic ourselves.

## Considered Options

- **mpv via JSON IPC (chosen).** Robust, ubiquitous (`brew install mpv`),
  language-agnostic, exposes exactly the properties the UI needs.
- **ffplay / mpg123 subprocess.** Weaker/limited runtime control (seeking,
  position, metadata).
- **Native Go audio (oto/beep + a decoder).** Would require us to own streaming,
  Icecast handling, and seek — large surface, little benefit.

## Consequences

- mpv is a **hard runtime dependency**. The binary probes for it on startup and
  prints an install hint if absent.
- The `Player` interface wraps mpv so the engine and tests never touch mpv
  directly; a fake `Player` is used in unit tests and a real mpv + local file in
  one integration test.
- "Live stream vs seekable" detection comes from mpv's `duration` /
  `seekable` properties, replacing the menubar's `AVPlayerItem.duration`
  inspection.
