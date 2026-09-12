# Bug 2 — `TabLayoutStore` takes its `UserDefaults` implicitly

**Status:** Suggestion (raised 2026-09-12)

Not an observed user-facing failure. A latent weakness noticed while diagnosing
`bug_1.md`, recorded so the decision is deliberate rather than accidental.

---

## Suggestion

Give `TabLayoutStore` an injected `UserDefaults` instead of reaching for
`UserDefaults.standard`, and point the tab layout test suites at their own
domain.

### What prompted it

The test host for `PocketCastsTests` is the app itself, so
`UserDefaults.standard` inside a test *is* the app's preferences on whichever
simulator runs the suite. Three suites —
`TabLayoutSyncServiceTests`, `TabLayoutSyncApplyTests` and
`TabLayoutReconciliationTests` — remove `Constants.UserDefaults.tabLayout` from
the real domain in `setUp` and `tearDown` and write through
`TabLayoutStore.shared`. Two of them also set `lastTabOpenedMigratedM12` to
`true` and leave it set.

Running the suite therefore deletes the saved tab bar layout of anyone using
that simulator. That is what left the pinned simulator with no stored layout on
2026-09-12, which briefly looked like a sync failure and sent the `bug_1`
diagnosis down a wrong path before the table query ruled push out.

`TabLayoutStoreTests` does not have the problem. It builds its own
`UserDefaults(suiteName:)` and clears only that. The seam it assumes is exactly
the one `TabLayoutStore` does not currently offer, which is why the other three
suites did not follow it.

### Shape it would take

`TabLayoutStore` gains a `UserDefaults` in its initializer, defaulting to
`.standard`, so `shared` is unchanged and no production call site moves. The
three suites construct their own store over a private suite name. Roughly the
same change `TabLayoutSyncService.currentUserID` already received for the same
underlying reason — the ambient environment leaking into tests.

### What would have to be true for this to be worth doing

- **The simulator's app state has to matter.** It does in this project, because
  manual verification happens on the pinned simulator immediately after test
  runs, and the two now interfere. If testing moved entirely to the device this
  would be close to harmless.
- **More suites have to be coming.** One isolated suite is a small cost; the
  feature already has four and the pattern is spreading in the wrong direction.
- **The cheaper fix has to be insufficient.** Simply switching the three suites
  to their own `UserDefaults(suiteName:)` and constructing a local store fixes
  the damage without touching production code — but only if `TabLayoutStore`
  can be pointed at that domain, which is the injection itself. There is no
  cheaper fix that does not also weaken the tests.

### Argument against

`TabLayoutStore.shared` is a singleton by design and the rest of the codebase
reaches for `UserDefaults.standard` freely. Injecting here makes this one type
inconsistent with its neighbours for the benefit of three test files, and the
same argument applies to a dozen other stores that have never caused trouble.
A narrower reading is that the tests are simply wrong to touch the real domain
and should be fixed where they are wrong.

### Scope note

Whatever is decided, the behaviour should be written down rather than left to be
rediscovered. The warning now lives in `pocket-radio-ios/AGENTS.md` under
*Test file layout*.

---

## Files involved

- `podcasts/Main/TabLayout/TabLayoutStore.swift` — reads and writes
  `UserDefaults.standard` via `Constants.UserDefaults.tabLayout`
- `PocketCastsTests/Tests/Main/TabLayoutStoreTests.swift` — the isolated model
- `PocketCastsTests/Tests/Main/TabLayoutSyncServiceTests.swift`,
  `TabLayoutSyncApplyTests.swift`, `TabLayoutReconciliationTests.swift` — the
  three that touch the real domain
- `podcasts/Constants.swift:141` — `tabLayout` key (`SJTabLayout`)
