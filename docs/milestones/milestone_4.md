# M4: Browse Tab

**Status**: NOT STARTED

## Goal

Search 90k+ stations via radio-browser.info. Play any result.

## Done when

- Browse tab shows top-100 stations by default
- Search returns results within 500ms (debounced 300ms)
- Tap result → Station Detail (play, favorite)
- Favorite a browse station → appears in Favorites tab

## What to build

- `RadioBrowserAPI.swift` — radio-browser.info client
- `BrowseViewController` — search UI + results list
- Favicon loading + disk cache

## Notes

- See `docs/designs/browse.md` for API endpoints, response fields, UX
- Always use `url_resolved` not `url` from radio-browser.info
- `hidebroken=true` on all queries
