# IOS
## Todo

- [ ] Register WordPress.com OAuth app for `dotcomSecret` (PC sign-in requirement)
- [x] On first account sync: load user's existing favorites/listen history from Supabase and show a loading state until ready
- [x] Streams shouldn't go in the Up Next list.
- [ ] Clean up stranded M6 radio favorites in Supabase. After M7 migrates seeding to radio-browser UUIDs, the old string-id rows (`"kcrw"`, `"kexp"`, `"npr_hourly"`) seeded under M6's `radioFavoritesSeededM6` flag remain in the Supabase `radio_favorites` table as orphaned data. Either delete by hand from another client, or write a one-shot cleanup that the app runs on launch to issue `removeFavorite(stationId:)` for the three legacy ids and set a `radioFavoritesM6CleanupRan` flag.

---

## Open Questions


### Upstream merge cadence

How often to pull from `Automattic/pocket-casts-ios`?
Options: monthly, on major PC releases only, or as-needed when a specific fix is needed.
No answer needed pre-launch — just needs a decision before M7+ maintenance phase.

### Local favorites fallback

Favorites tab currently shows "Sign in to Pocket Casts" if user is logged out.
No local-only fallback. Is that acceptable? Most users will be signed in, but worth confirming.

### Year-end wrapped summary

PC already ships a year-end wrapped feature (JSON data files in `podcasts/2025_*.json`).
PocketRadio should extend this with radio data: top stations, total listen hours, estimated cost vs. donated.
Design needed before it's relevant (post-M5). Decide whether to extend PC's existing wrapped UI or build a separate radio-only summary screen.

### Telemetry / crash reporting

Sentry.io is the candidate. MPL 2.0 has no restriction on adding crash reporting; Sentry SDK is MIT.
PC already has analytics hooks (`AnalyticsHelper`). Sentry would be additive — init in SceneDelegate, no conflict.
Questions to settle:
- Self-hosted Sentry (free, more control) or Sentry.io cloud (easier, paid at scale)?
- What data to capture: crashes only, or also stream-start failures, API errors?
- Privacy policy implications — need a policy page before App Store submission.
Decide before App Store submission, not before MVP testing.

### Pocket Casts account requirement + signup flow

PocketRadio requires a PC account for sync (`ServerSettings.userId`). Users without one must sign up.
PC's existing signup flow is intact and untouched — this is fine under MPL 2.0 (no relicensing, source available).
UX friction: new users hitting PocketRadio for radio streaming must create a PC account first.
Options: (a) keep as-is (acceptable for early adopters), (b) add a guest/offline mode with local-only favorites (post-MVP), (c) surface a "create account" prompt with clear explanation of why it's needed.
Decide before public launch.

### New Web UI

Need to build a web UI that replaces the existing web UI. Can we fork a repo for this like we are for other things?


# Menubar
- [ ] When we get to the menu bar app, we need a selection for whether it's going to scroll the title like our current KCWR app or just do something else. 

### Menubar auth (MVP)

Menubar app needs `user_uuid` to sync favorites with Supabase.
Current MVP plan: manual paste of UUID in menubar Settings popover.
How does user find their UUID? PC doesn't surface it in the UI.
Options: (a) add a "Copy User ID" button to PocketRadio iOS settings, (b) derive from email hash, (c) defer sync to post-MVP.

### Shared code: iOS ↔ menubar

MVP duplicates ~3 files (station model, Supabase client, tracklist APIs).
Post-MVP: extract into a shared Swift package inside the pocket-casts-ios fork.
Not urgent until both apps are stable.


### PocketCastsOSX — fork, inspire, or ignore?

Local copy: `/Users/jdj/Documents/code/PocketRadio/other_apps/PocketCastsOSX`

Prior conclusion (from plan): discard — uses deprecated `WebView` API and brittle JS injection into the Angular web player. Wrong architecture for a native audio player.

Still worth a quick scan before M6 to check:
- Any useful `NSStatusItem` / menubar plumbing patterns to borrow
- Any audio session or media key handling worth adapting
- Anything else that saves reinventing the wheel

Decision: fork (unlikely), use for inspiration (maybe), or confirm ignore.
Do before starting M6 menubar work.
