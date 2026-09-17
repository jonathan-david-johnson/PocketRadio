# Core vs extra destinations, and a derived Overflow tab

## Current decision — Up Next is required (2026-09-12)

The layout is a user-ordered list of slots. **Core** means required in the tab
bar or More: Podcasts, Playlists, Discover, Streams, Profile, **Up Next**.
Core destinations cannot be deleted from tab settings. **Extras** are optional
shortcuts to individual playlists; they can be removed entirely.

Overflow is derived, never persisted. It contains truncated slots followed by
unpromoted core destinations. The rule remains:
`needsOverflow = !(complement.isEmpty && truncated.isEmpty)`.

## Default and compatibility

Capacity remains five on iPhone and iPad. Six required destinations mean More
is always needed at that capacity. The approved default is:

- Bar: Podcasts, Playlists, Discover, Streams, More.
- More: Profile, Up Next.

`TabLayout.default` explicitly stores the four content destinations, rather
than deriving default slots from the core catalog. Its epoch timestamp still
means never configured. Existing persisted/synced layouts and timestamps are
not migrated or rewritten: their unpromoted Up Next now enters the complement.
A legacy five-slot default therefore renders the same approved bar, with
Profile truncated into More ahead of Up Next.

Users can promote Up Next or Profile by dragging above More, displacing another
item when full. Up Next is no longer offered by the Add Tab picker because it
already exists in the settings list. Individual playlists remain optional.

`navigateToUpNext` uses the same host resolver as Discover/Profile: its own tab
when visible, otherwise a screen pushed from More. The existing Playlists
segmented shortcut remains available; another entry point does not make a
required destination optional.

## Why the decision changed

Originally only five destinations were core, and Up Next was extra because it
already had a home in the Playlists segment. This preserved the pre-M12 default
bar without More. The user explicitly replaced that requirement: Up Next must
always appear either as a tab or under More, just like Discover and Profile.
The old "unchanged default bar" constraint no longer applies.

## Alternatives retained from the original decision

- Persisting Overflow introduces redundant state; deriving it keeps one ordered
  slot list as the wire contract.
- UIKit's native More controller only triggers beyond five items and does not
  match the app's custom themed destination list.
- Treating all playlists as required would fill More with shortcuts users never
  chose. Only explicitly stored playlist slots belong in the layout.

## Consequences

- Adding another core destination changes existing users' More contents.
- Adding an extra does not, unless the user adds its slot.
- Core means required navigation, not "the tab bar is the only way in."
- No persisted IDs, Supabase schema, selection migration, or capacity changes.
