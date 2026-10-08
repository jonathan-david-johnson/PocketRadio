# Intermittent initial artwork setup fails in the CarPlay suite

**Status:** Open; investigation deferred by the user when approving M13 closure on 2026-10-08. One full-suite occurrence, followed by an isolated pass and a full pass without code changes. Cause unresolved; not established as a production bug.
**Evidence:** `archive/ios-m13.2:docs/ios/experiments/2026-10-08_m13_2_verification.md`, integration verification section. Local logs: `/tmp/m13-integration-test.log`, `/tmp/m13-integration-focused.log`, `/tmp/m13-integration-test-2.log`.

## Observed failure

After integration into `trunk`, a full `make test_carplay` run executed 128 tests with one ordinary failure. The scenario “A song without artwork anywhere shows the logo” failed at its initial Song A/red-artwork setup assertion, before the Song B/no-artwork transition.

The image request to `http://127.0.0.1:57621/art/red-large.png?song=…` failed with URLSession error −1005, connection lost, at 12:01:38.518 EDT. The display retained the station logo, and the red-artwork assertion timed out after 10.01 seconds. Normal scenario teardown began at 12:01:55.996, so it does not explain the earlier loss. No host sleep was found during the run.

The same scenario passed alone: one test, 17.464 seconds, with initial red artwork and the subsequent logo transition observed. A second full run passed all 128 tests in 440.734 seconds. No source, fixture, timeout or expected-failure changes intervened. These passes do not establish the first failure's cause or prove every suite ordering is safe.

## What remains unknown

The timeout output did not identify the current artwork server's port, expected URL and request-event timeline. A stale-world URL or late work remains unexcluded. The artwork server's cancel-after-send pattern is another transport hypothesis, not a confirmed cause. Its send completion does not establish receipt by the client.

Loopback artwork bypasses the URLProtocol guard. A clean reset snapshot cannot prove all background callbacks finished. The failed initial-artwork assertion correctly prevents a vacuous logo pass; do not mark or suppress it as an expected app-output defect.

## Next step

Add harness-only failure diagnostics for the active artwork server, expected request URL and existing server events before teardown. Reproduce under full-suite ordering; add send-error/state timestamps only if needed. Preserve the failed run alongside reruns, and establish the cause before claiming this setup failure is fixed. No production bug fix is implied.
