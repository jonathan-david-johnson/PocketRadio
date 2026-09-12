# Bug 1 — Tab bar layout does not sync until the app is relaunched

**Status:** Open (diagnosed 2026-09-12)

Found during M12.3 manual verification, on an iPhone 15 running iOS 26.6.1 and
an iPhone 17 Pro simulator running iOS 26.4, both signed into the same account.

Diagnosed but **not fixed** — the fix carries an open design question, recorded
below, that should be settled first.

---

## Symptom: signing in does not pull the synced layout

The tab bar was customized on the iPhone. The simulator, signed into the same
account, kept rendering the stock five tabs — Podcasts, Playlists, Discover,
Streams, Profile.

### Root cause

The layout pulls at launch and nowhere else, and signing in is not a launch.

`TabLayoutSyncService.pullAtLaunch()` has exactly one caller,
`AppDelegate.swift:148`. On that launch the simulator was signed out, so
`signedInUserID()` threw `RadioError.notLoggedIn` and the pull returned
silently — correct, and deliberately silent, since it runs on every launch. The
user then signed in. Nothing re-pulls, so the service never ran again for the
rest of the process's life.

This is the design as M12.3 specified it. The milestone named one trigger and
the code implements that trigger. It is a gap in the design rather than a
mistake in the implementation, which is why no test catches it: every test of
this path drives the service directly.

### Evidence

| Check | Result |
|-------|--------|
| `nav_layout` row for the account | Present, four slots, `updated_at` 2026-09-12T15:12:12Z |
| Row contents | `["podcasts","playlist:2797DCF8…","playlist:98c49e0e…","playlist:95b6d548…"]` — the iPhone's layout |
| Simulator's stored layout | `SJTabLayout` key absent from the app's preferences, so `TabLayout.default` renders |
| Pull call sites | One, `AppDelegate.swift:148` |
| Simulator app launched | 11:02 local; sign-in happened after, no relaunch since |

Push works, and the safe-apply gate is not involved. `PlayerOpenState.closed`
tracks only the full screen player, so a visible mini player still satisfies
`MainTabBarController.isSafeToRebuild`.

Predicted, not yet confirmed: relaunching the app should pull the row and apply
it, which would make the symptom reachable only in the window between signing in
and the next launch — for a new device, the entire first session. Worth doing,
because if a relaunch does *not* fix it there is a second fault underneath this
one.

### Proposed fix

Observe `.userSignedIn` and call the same pull. The notification already exists
(`podcasts/Notifications.swift:8`), is posted from all four sign-in paths, and
`MainTabBarController` already observes it for End of Year stats
(`MainTabBarController.swift:1163`), so the pattern is established.

`pullAtLaunch` should be renamed once it has two callers. Its `inFlightPull`
guard already makes a second concurrent call safe.

### Open design question — decide before fixing

Last-write-wins is wrong at the moment of signing in.

Customizing the layout while signed out stamps `updatedAt` to now, which is
newer than the remote row. `decision(local:remote:)` would then return
`.pushLocal`, and signing in on a fresh device would overwrite the layout on
every other device with whatever the user had arranged locally before they had
an account.

Signing in is arguably the one moment the remote copy should win outright,
regardless of timestamps — the user is asking to adopt an existing account, not
to publish a local draft. The alternative is to keep last-write-wins and accept
that a signed-out customization is a real preference that should propagate. Both
are defensible; the current code picks the second by accident rather than by
decision.

---

## Related, and now fixed: a test that reached the network

Before `TabLayoutSyncService.currentUserID` was made injectable,
`testPullAtLaunchSignedOutMakesNoNetworkCallAndLeavesLocalLayoutUnchanged`
asserted `ServerSettings.userId == nil` as a precondition. That held only while
nobody was signed in on the simulator running the suite. Once someone signed in,
the test made a real request and wrote the account's remote layout over the
local one. Fixed 2026-09-12 by injecting the user lookup; see
`milestone_12.3.md` § What manual verification found.

The same class of problem — the ambient environment leaking into tests — also
means the suite deletes the saved layout on whichever simulator runs it. That is
why the pinned simulator had no stored layout when this bug was diagnosed, and
it sent the diagnosis down a wrong path until the table query ruled push out.
Raised separately as `bug_2.md`, because the remedy is a design choice rather
than a defect to fix.

---

## Files involved

- `podcasts/AppDelegate.swift:148` — the only pull call site
- `podcasts/Main/TabLayout/TabLayoutSyncService.swift` — `pullAtLaunch`,
  `signedInUserID`, `decision(local:remote:)`
- `podcasts/Notifications.swift:8` — `userSignedIn`, unobserved by this feature
- `podcasts/Main/MainTabBarController.swift:1163` — existing observer precedent
- `PocketCastsTests/Tests/Main/TabLayoutSyncServiceTests.swift` — the test that
  reached the network, now injecting signed-out
