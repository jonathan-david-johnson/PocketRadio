# Open Questions

## iOS ↔ macOS menubar install flow

How does a user who has the iOS app discover and install the menubar app?
Need an in-app link or prompt — where does it live, what does it point to (App Store listing? direct download? TestFlight?).
Needs an answer before M6 ships.

## Podcast listen time in PC

Does Pocket Casts already track per-podcast listen time internally?
The Usage & Donations screen plans to show podcast listen-time alongside radio.
If PC tracks it (likely — it has "listening history"), we should read that data rather than re-implement.
Needs a PC source dive before M5.

## Menubar auth (MVP)

Menubar app needs `user_uuid` to sync favorites with Supabase.
Current MVP plan: manual paste of UUID in menubar Settings popover.
How does user find their UUID? PC doesn't surface it in the UI.
Options: (a) add a "Copy User ID" button to PocketRadio iOS settings, (b) derive from email hash, (c) defer sync to post-MVP.

## Contextual nav revisit

Design doc specifies a "Home" layer with contextual tab bars (Podcasts world / Streams world).
MVP simplified this to a 6th Streams tab in PC's existing tab bar.
Revisit: is the simplified nav good enough for launch, or does it feel wrong in practice?
Decide after M2 is in hands.

## radio-browser.info rate limits + redundancy

No documented rate limit. Single DNS endpoint (`de1.api.radio-browser.info`) used for MVP.
Mirror IPs available (`nl1`, `at1`). Add rotation if failures observed in testing.

## Upstream merge cadence

How often to pull from `Automattic/pocket-casts-ios`?
Options: monthly, on major PC releases only, or as-needed when a specific fix is needed.
No answer needed pre-launch — just needs a decision before M7+ maintenance phase.

## Shared code: iOS ↔ menubar

MVP duplicates ~3 files (station model, Supabase client, tracklist APIs).
Post-MVP: extract into a shared Swift package inside the pocket-casts-ios fork.
Not urgent until both apps are stable.

## Local favorites fallback

Favorites tab currently shows "Sign in to Pocket Casts" if user is logged out.
No local-only fallback. Is that acceptable? Most users will be signed in, but worth confirming.
