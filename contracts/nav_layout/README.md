# nav_layout render contract

Golden fixtures for how a stored tab Layout renders. iOS renders it as the tab bar and its More tab; the web player renders the same Layout as a Sidebar with the Bar line where the phone's tab bar ends ([web ADR 0005](../../docs/web/adr/0005-sidebar-mirrors-the-ios-tab-settings-list.md)). Every port of the render rules must produce each fixture's `expected` from its inputs.

The reference implementation is iOS `TabLayout.renderPlan(capacity:isAvailable:)` and `TabRenderPlan.overflowDestinations` in `pocket-radio-ios/podcasts/Main/TabLayout/TabLayout.swift`, with `isAvailable` true for every core destination and for a playlist whose UUID is in `available_playlists`. The fixtures were generated from those rules and checked against the iOS tests named in `ios_test`.

## Fixture shape

```json
{
  "description": "what the case is about",
  "ios_test": "optional: the iOS XCTest that asserts the same thing",
  "slots": ["podcasts", "playlist:<uuid>", "..."],
  "capacity": 5,
  "available_playlists": ["<uuid>"],
  "expected": {
    "bar": ["..."],
    "more": ["..."],
    "sidebar": ["..."],
    "bar_line_after": 4
  }
}
```

- `slots`: the `nav_layout.slots` column, exactly as stored: an ordered array of destination ids (`supabase/migrations/20260911000007_nav_layout.sql`).
- `capacity`: tab items the device renders, counting More. 5 on every iOS device today (`TabLayout.capacity(for:)`).
- `available_playlists`: playlist UUIDs that exist for the user. A `playlist:<uuid>` slot not listed here is unavailable.
- `expected.bar`: the tabs, in order, not counting More.
- `expected.more`: the More tab's rows, in order: slots that did not fit, then unplaced core destinations in core order. Empty when there is no More tab.
- `expected.sidebar`: `bar` then `more`.
- `expected.bar_line_after`: how many Sidebar rows sit above the Bar line (`bar.length`), or `null` when there is no More tab and so no line.

## The rules, in brief

1. Drop slots this build can't resolve (an unknown id, `playlist:` with no UUID) and unavailable playlists. Keep the rest in order.
2. The complement is the core destinations (`podcasts, playlists, discover, streams, profile, upNext`, in that order) that have no slot.
3. A More tab exists unless the complement is empty and every slot fits.
4. With a More tab, the bar holds `capacity - 1` slots; without one, `capacity`.
5. More lists the slots that didn't fit, then the complement.

## Cases

| File | What it pins |
|---|---|
| `ios_default.json` | iOS default Layout |
| `primary_user.json` | Playlists in the bar; all unplaced core below the line (web M2 checkpoint) |
| `all_core_placed.json` | Empty complement, still overflowing |
| `more_than_five_slots.json` | Truncated slots come before the complement in More |
| `unknown_future_id.json` | Unknown and malformed ids are dropped without reordering |
| `deleted_playlist.json` | An unavailable playlist is dropped |
| `duplicate_slots.json` | A repeated destination renders as stored (decided below) |
| `empty_slots.json` | An empty Layout (open question below) |
| `fits_without_more.json` | No More tab, no Bar line |

## Decided: duplicates render as stored

A repeated slot renders as stored: `["podcasts","podcasts","streams"]` shows Podcasts twice, in the iOS tab bar and in the web Sidebar alike. The render rules do not remove duplicates. The user cleans them up by saving from the Layout editor, which removes duplicates when it opens (iOS `TabLayoutEditor`, and the web editor that ports it). Decided by the user on 2026-10-18.

The iOS editor never writes a duplicate, so one only appears when something else wrote the `nav_layout` row: a hand edit, a script, or a bug in another writer. The web player's Layout write must not create one either.

## Open question

- **Empty Layout.** `[]` gives an empty bar and a More tab holding everything. iOS's settings screen would instead put Podcasts in the bar. Neither app writes an empty Layout today; the question is what to show if one is ever stored.

## Who uses these

- Web: `pocket-radio-web` loads `../contracts/nav_layout/*.json` in its Vitest suite.
- iOS: not yet. Adopting these in `TabLayoutTests` is tracked in `docs/todo.md`.

Changing an `expected` value changes the contract. Change the iOS rules (and their tests) and every port in the same change.
