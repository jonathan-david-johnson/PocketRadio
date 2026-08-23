# ADR-0002 — One shared `:core:*` stack, two thin app modules

**Status:** Accepted (2026-08-23)
**Applies to:** `pocket-radio-android`

## Context

"PocketStreams" is the 10-foot brand (Roku). But Android is the one platform
where TV and phone are the *same* SDK, language, player stack, and toolchain —
only the UI layer and launcher metadata genuinely differ.

The options were: TV-only (mirror Roku), phone-only (mirror iOS), or both.

## Decision

**Both, from one repo.** A shared, form-factor-agnostic `:core:*` stack plus
two thin app modules:

- `:core:model` — pure Kotlin domain types
- `:core:pocketcasts` — protobuf + API client (pure Kotlin/JVM)
- `:core:radio` — Supabase favorites, radio-browser, tracklists (pure Kotlin/JVM)
- `:core:auth` — token storage (Android)
- `:core:player` — Media3 `MediaSessionService`, the playback Engine (Android)
- `:core:designsystem` — shared Compose theme + tokens
- `:tv` — Compose for TV, D-pad, `LEANBACK_LAUNCHER`
- `:mobile` — Compose Material3, touch, media notification

**App modules own UI and manifest only.** No API call, no protobuf, no player
control logic may live in `:tv` or `:mobile`. If both app modules need a
behavior, it belongs in `:core:*`.

## Rationale

- **The genuinely-different surface is small.** Navigation, focus handling,
  and density differ. Auth, protobuf, favorites, resume, position sync,
  tracklists, and playback are byte-identical. Splitting into two repos would
  duplicate ~80% of the work and immediately begin drifting — exactly the
  cross-platform parity failure `docs/REPO_STRUCTURE.md` warns about.
- **Media3 is already form-factor agnostic.** `MediaSessionService` is the
  correct architecture for both TV and phone. Building it once is not a
  compromise for either.
- **Parity becomes structural, not aspirational.** On other platforms parity is
  maintained by discipline and re-reading the menubar source. Here the compiler
  enforces it: there is only one implementation to diverge from.

## Consequences

- **M0 is larger than a single-app skeleton** — Gradle multi-module wiring,
  version catalog, and two app modules before anything is demoable. Accepted;
  it is one-time cost and M1 immediately exercises both.
- **Every milestone M1–M6 must land its checkpoint on both surfaces.** A
  behavior is not done when only the TV app shows it. Milestone checkpoints
  are written to say "either app" or "both apps" explicitly.
- **Two app modules are kept deliberately dumb until M7.** Until the shared
  core is proven, `:tv` and `:mobile` stay near-identical shells. Real 10-foot
  and touch-native UX is M7 work, not something to sneak in early.
- **Risk: `:core:designsystem` becomes a lowest-common-denominator UI.** It is
  scoped to tokens (color, type scale, spacing) and genuinely shared
  components only — not layouts. Layout lives in the app modules.

## Related

- [ADR-0001](./0001-native-protobuf-not-relay.md)
- `docs/REPO_STRUCTURE.md` § Cross-platform consistency
