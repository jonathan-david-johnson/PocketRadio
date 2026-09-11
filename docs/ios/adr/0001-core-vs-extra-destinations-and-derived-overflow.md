# Core vs extra destinations, and a derived Overflow tab

The tab bar layout is a user-ordered list of **Slots**. Destinations are split
into **core** (Podcasts, Playlists, Discover, Streams, Profile) and **extra**
(Up Next, and any specific playlist). The **Overflow** tab is never stored — it
is derived at render time, and exists only when it would be non-empty: it holds
unpromoted *core* destinations plus any slots truncated past device capacity.

## Why

Two properties had to hold at once, and a single flat catalog cannot deliver
both.

1. **A user who never opens the setting sees no change.** The default layout is
   today's five destinations. If the catalog were flat and Overflow held the
   strict complement, adding Up Next as a promotable destination would leave it
   unpromoted by default, so Overflow would appear on a default install and the
   bar would no longer match today's.
2. **Nothing becomes unreachable.** Hiding Discover must not orphan
   `navigateToDiscover(category:)`, which is reached from Siri, widgets, and
   notification deep links.

The split resolves it. A core destination is precisely one where the tab bar is
the *only* way in, so that is exactly the set Overflow must cover. Up Next
already has a home as a segment of `PlaylistsHostViewController`, and a playlist
already has a home as a row in the Playlists list, so neither needs an Overflow
row when unpromoted.

Deriving Overflow rather than storing it keeps the Layout minimal and makes the
"looks like today" property structural rather than a special case — an empty
complement with no truncation simply produces no Overflow tab.

## Considered Options

- **Core/extra split with derived Overflow (chosen).** Both properties hold.
  Costs one concept.
- **Flat catalog, Overflow always present.** Simple, but a default install shows
  a "More" tab containing one row, and the bar no longer matches today's.
- **Flat catalog, drop Up Next as a destination.** Also preserves the default,
  but you can never pin Up Next to the bar. Rejected as a real capability loss
  for no structural gain.
- **UIKit's native `moreNavigationController`.** Free, but only triggers above
  five items, is un-themeable, and looks nothing like the rest of the app.

## Consequences

- The Layout stores slots only. Overflow is computed by
  `needsOverflow = !(complement.isEmpty && truncated.isEmpty)`.
- Truncation is the one case where an *extra* reaches Overflow, because a
  truncated slot has no visible home in that render.
- `navigateToUpNext` needs a resolution chain rather than plain lookup: the Up
  Next tab if promoted, otherwise the Playlists host segment as today.
- The split generalises. Pinning a specific podcast or radio station later is an
  extra by the same rule, with no change to Overflow's logic.
- Adding a new *core* destination is a behavioural change for existing users,
  since it enters the complement. Adding an extra is not.
