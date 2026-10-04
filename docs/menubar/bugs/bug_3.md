# Bug 3 — bottom-left information button does not open Remote Debug

**Status:** Open — reported by the user on 2026-10-04 in the installed M12 menubar build. Filed only; not fixed.
**Related milestone:** [M12](../milestones/milestone_12.md).

## Symptom: clicking the footer information icon does nothing

The user reports no visible action from the bottom-left circled **i** button.

Expected: open the **Remote Debug** log window. This button is not station information or the KCRW alignment experiment. The window contains remote-control log entries, a filter field, and a Clear button. Repeated clicks should bring the existing visible window forward.

### Evidence

- User report: the footer icon currently does nothing. No separate click reproduction or runtime delegate inspection was performed while filing.
- Installed app: `/Applications/PocketRadio.app`, M12 Debug build on `feature/kcrw-normal-use`, based on `464ca70` plus uncommitted changes; executable SHA-256 `46af5c4d31a817d24258d0b7eec45cb8b9e98e62ec59682126ef024901855618`.
- `ContentView.swift:237–247` wires the footer action to `(NSApplication.shared.delegate as? AppDelegate)?.openDebugWindow()` and labels its help text “Remote debug log”.
- `PocketRadioApp.swift:15` uses `@NSApplicationDelegateAdaptor(AppDelegate.self)`.
- `PocketRadioApp.swift:244–262` implements `openDebugWindow()`: create a titled 640×400 window containing `RemoteDebugView`, or bring an existing visible window forward, then activate the app.
- `RemoteDebugView.swift` renders `RemoteDebugLogger.shared` entries with filtering and clearing.
- The footer action was not changed by M12. The report is on M12, but regression origin is not established.

### Root cause (hypothesis, not confirmed)

The action relies on an optional cast from the application's runtime delegate to `AppDelegate`. If SwiftUI supplies a delegate adapter/proxy rather than that concrete instance, the cast fails and optional chaining silently skips the action. Source inspection establishes this silent failure path, not the installed app's actual runtime delegate type. Click delivery or window presentation could also require investigation.

### Proposed fix

Inspect the actual delegate/action path before declaring the hypothesis proven. Prefer passing an explicit window-opening callback from the owning `AppDelegate` to `ContentView`, rather than recovering it through the optional global delegate cast. Preserve existing window reuse and bring-to-front behavior. Avoid an apparently active control that silently does nothing.

Add a focused action-routing check and an attended/UI check that clicking the footer icon opens **Remote Debug**, repeated clicks focus the same visible window, and closing then reopening works. Do not confuse this icon with row-level “Show details” buttons or the separate Debug alignment waveform button.

## Files involved

Paths are relative to `pocket-radio-menubar/`:

- `PocketRadio/ContentView.swift` — footer button/action and help text.
- `PocketRadio/PocketRadioApp.swift` — SwiftUI delegate adaptor, root view construction, and debug-window owner.
- `PocketRadio/RemoteDebugView.swift` — log-window content.
- `PocketRadioUITests/` — existing suite does not test the footer action or debug-window appearance.
