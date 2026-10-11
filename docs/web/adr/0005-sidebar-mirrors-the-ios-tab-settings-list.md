# The web sidebar mirrors the iOS tab settings list

Status: accepted (2026-10-11)

On a wide window the web player's sidebar shows every Destination in one list:
the Layout's slots in order, then unplaced core Destinations in their fixed
derived order. A divider sits exactly where the iOS settings screen puts its
**More** row, at the iPhone's capacity of 5 including More. Above the divider
is the phone's tab bar; below it is the phone's More tab. Narrow windows use
the iOS rule directly: up to five tabs, the last being More.

The sidebar's edit mode is a port of iOS `TabLayoutEditor`: drag to reorder,
drag across the divider to promote or demote, drag the divider itself. Items
below the divider are not reorderable, because the Layout stores an unplaced
core Destination as an absence, not as a position. The web player writes
`nav_layout` through its Worker and follows the same rules, so a web
save and an iOS save produce the same Layout.

## Considered Options

- **Mirror the iOS list (chosen).** One mental model across devices. The
  divider tells the user what the phone will show.
- **Flat list with no divider.** Uses the space, but hides how the phone will
  render the same Layout.
- **Collapsible More group.** Keeps the main list short, but the user chose to
  see every Destination.
- **Reorderable below the divider.** Would need iOS to store and preserve an
  order for unplaced core Destinations. iOS currently discards that order
  whenever it saves.

## Consequences

- The divider's position comes from the iPhone's capacity, not the browser's
  width. If iOS capacity ever varies by device, the web player must decide
  which device's line to draw.
- The rules now live in Swift and TypeScript. The shared `nav_layout` fixtures
  in `contracts/` are the contract both ports must pass.
- iOS ADR 0002's statement that other surfaces can't read the layout no
  longer holds. Update that ADR.
