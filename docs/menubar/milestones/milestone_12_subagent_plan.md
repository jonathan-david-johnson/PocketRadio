# M12 subagent plan — normal KCRW playback

**Status:** IMPLEMENTED, AWAITING USER CHECK — all-Sol implementation, independent review, and final automated verification completed on 2026-10-04. This replaces the mixed-model plan. See the [verification handoff](milestone_12_handoff.md).
**Scope:** [M12 — KCRW alignment in normal playback](milestone_12.md).
**Route:** `openai-codex/gpt-6.1-sol`, OAuth, Standard speed. No provider or billing-route changes.

## Decision and ownership

Use one Sol implementation writer for all overlapping configuration, playback, capture-control, and lyric code. Work through the six M12 acceptance behaviors sequentially, red-to-green. A second Sol agent reviews the completed diff and adds independent regression fixtures only after the writer hands back ownership. The lead integrates verification and documentation.

The user said subscription impact is not a concern and requested execution. Do not block on subscription-impact estimates or claim quota savings. The skill's 2026-10-04 rate snapshot is fresh against runtime date 2026-10-04. Authentication checks report `openai-codex` OAuth ready; the active Sol session establishes access.

## Where the work happens

| Area | Location |
|---|---|
| Plan and handoff | Shell `main`: M12, this plan, and verification notes |
| Code | Menubar `feature/kcrw-normal-use`, based on `464ca70`, successor of accepted M11-B merge `e6fa855` |
| Worktree | `pocket-radio-menubar/` |
| Agent | Shell `.pi/agents/m12-sol.md`, pins `openai-codex/gpt-6.1-sol:high` |
| Shell changes | Documentation and dedicated role definition only; no contracts or backend changes |

The menubar checkout has no tracked `AGENTS.md` or Makefile. Use shell instructions and the authoritative milestone; do not invent platform instructions. Existing shell targets call Xcode directly. Leave unrelated untracked `Tools/StreamLab/.pi/` untouched.

## Approved behavior

- Ordinary playback aligns only the existing exact eligible KCRW variants: a KCRW-named station, `streams.kcrw.com`, and `/e24_mp3`, `/e24_aac`, or `/e24_aac/playlist.m3u8`, with existing scheme and credential/query/fragment restrictions.
- Resolve playback to `https://streams.kcrw.com/e24_aac/playlist.m3u8`, freeze `+160s` and accepted clock/history policy, and never change station records or saved URLs.
- Debug **Off** means no experiment: approved ordinary alignment still runs. Observe is an explicit comparison override that does not publish the aligned candidate. Apply remains an explicit experiment path. Update labels and tests to reflect this distinction.
- Normal playback must not create a recorder, trace, or sidecar. Only explicit Debug capture arms recording. Keep recorder schema/privacy guarantees unchanged and add no monitoring, audio capture, or upload.
- One valid item/generation owns polling, selection, lyric resource, correction, and publication. Feed receipt alone cannot publish the next occurrence. Reject late player/feed/lyric callbacks at publication.
- Pause tears down; resume joins a new item and valid clock. History browsing and popover/detail lifecycle cannot replace the active poller or clock.
- Titles, selected history, Now Playing, menubar lyrics, and live detail use the same state. Missing clocks/history expose alignment unavailable rather than falsely aligned feed-top output. Missing/fuzzy timing disables highlighting; exact text lookup does not establish recording identity.
- Recording correction is in-memory and separate from `+160s` and legacy offsets. Reset on a different occurrence/resource. Do not read, rewrite, or delete saved offsets on the aligned path.
- Unsupported sources, other stations, podcasts, and remote commands retain existing behavior. No buffered pause, core calibration change, iOS port, URL migration, artwork/catalog refactor, or new long listening protocol.

## Slices, models, and soft budgets

Input forecasts count aggregate uncached input plus cache reads/writes across requests, including repeated history, mandatory instructions, tools, file reads, and test output. Output forecasts include provider-reported reasoning without double-counting. These are advisory estimates, not enforced caps. The user prioritized implementation and waived subscription-impact blocking; record forecast overruns rather than treating context accounting alone as a correctness blocker. The previous preparation used about 698k aggregate input, mostly cached; the actual delegated usage below also exceeded the revised forecasts.

| Slice / owner | Exact provider/model | Files and ownership | Acceptance check | Input budget | Output/reasoning budget | Stop/escalation trigger | Cost status |
|---|---|---|---|---:|---:|---|---|
| Lead: preparation, seams, final verification/docs | `openai-codex/gpt-6.1-sol` | Read-only production code; shell milestone/plan/handoff and agent setup | Scope and ownership verified; final Debug/Release and test evidence recorded | 2,000k | 15k | Provider mismatch or unresolved invariant; report forecast overrun | Included allowance impact unknown; user does not require estimates |
| Single implementation writer: behaviors 1–6 | `openai-codex/gpt-6.1-sol` | `PocketRadio/Services/StreamExperimentConfiguration.swift`, `RadioPlaybackSession.swift`, `LyricsService.swift`, narrow `RadioFeedClient.swift` if needed; `PocketRadio/View Models/PlayerViewModel.swift`, `ContentView.swift`, `StreamExperimentView.swift`, `StreamExperimentRecorder.swift`; app tests and necessary Xcode test wiring | Exact normal endpoint; no Debug dependency/recording; lifecycle isolation; common lyric resource/clock; unavailable state and legacy regressions | 1,500k | 30k | Two unsuccessful fixes to one check, out-of-scope policy/refactor, unresolved invariant; report forecast overrun | Same as lead |
| Independent regression/review agent, after writer handoff | `openai-codex/gpt-6.1-sol` | Production read-only; app/core regression test files only | Review all six behaviors; test stale callbacks, capture isolation, clocks/resources, saved-data isolation, source boundaries | 500k | 10k | Production defect requiring ownership transfer, unresolved expected behavior, two unsuccessful fixes; report forecast overrun | Same as lead |
| **Initial total** | | | | **4,000k** | **55k** | | No quota or cost-savings claim |
| **Optional reserve, not authorized** | `openai-codex/gpt-6.1-sol` | Explicitly reassigned failed slice only | Scoped escalation after user approval | **500k** | **10k** | Stop when exhausted | No estimate requested |

The writer forecast allowed repeated context from the roughly 2,025-line view model, async lifecycle/lyrics reasoning, and sequential fixture-driven tests, but still underestimated many-turn repetition. The reviewer received a concise interface/diff handoff, not the parent conversation. All roles used the current model, so there is no mixed-model saving to calculate. Actual subscription consumption remains unknown and is not evaluated at the user's request.

### Reported delegated usage

| Completed role | Uncached input | Cache read | Output/reasoning | Turns |
|---|---:|---:|---:|---:|
| Implementation writer | 123,778 | 5,485,824 | 35,361 | 87 |
| Independent review/regressions | 81,083 | 1,581,824 | 13,644 | 32 |
| **Delegated total** | **204,861** | **7,067,648** | **49,005** | **119** |

Cache writes were reported as zero. Aggregate delegated input was 7,272,509 tokens. These figures exclude lead preparation, review fix, builds, documentation, and final verification; they are not a milestone-wide usage total or a dollar/credit charge. Both delegates exceeded their soft forecasts without requesting a budget pause; the harness did not enforce those forecasts. No publisher/provider/model escalation occurred. The lead fixed the reviewer's verified equal-timestamp mismatch after the reviewer relinquished production ownership.

## Execution order

1. **Lead:** activate M12 documentation, verify the branch/auth route, inspect existing test/build commands, and pass the focused scope/invariants to the writer. Reuse the established discovery map: endpoint resolution and session creation in `startPlayback`; Apply-only publication guards throughout the view model; capture arming via `pendingExperimentRoute`; same-item publication in `RadioPlaybackSession`; live detail currently fetches lyrics separately and needs resource/clock agreement.
2. **Implementation writer:** read shell `AGENTS.md`, M12, this plan, and focused source/test files. Confirm the effective model/provider and OAuth route before editing. Implement one acceptance behavior at a time. Use synthetic player items and injected feed/clock/lyrics/recorder dependencies; do not open live radio. Return a concise diff summary, red/green evidence, test results, remaining uncertainty, and usage if available.
3. **Lead:** approve implemented seams and review recording/lifecycle boundaries. Transfer test ownership only after the writer stops.
4. **Independent reviewer/test agent:** inspect the diff and observable behavior; add bounded regression fixtures. Report production defects to the lead, without independently editing production code.
5. **Lead/writer:** resolve any reported defects under explicit ownership transfer within the approved implementation allocation. Stop after two unsuccessful fixes to the same acceptance check. Do not consume reserve silently.
6. **Lead:** run final verification, record tested commits/dirty state and unavailable checks, and prepare the ordinary-use demonstration checkpoint. Do not require extra long captures or claim measured ±5s/±2s accuracy.

No parallel writers touch the view model, session, shared test file, or project wiring. Existing role agents using another provider must not be reused. The subagent tool reads the dedicated pinned role; verify its effective provider/model from runtime metadata. Stop rather than silently falling back if pinning fails. Fetch current Context7 docs before coding against a third-party package API; Apple frameworks and repo-local packages are not third-party libraries.

## Verification

Baseline preparation passed 23 core tests and the endpoint app test. The first development-certificate test invocation timed out at host launch; the subsequent ad-hoc signed, serial invocation passed. Use the working signing/test route below. Baseline lab output must be counted from both package test suites, not a single trailing summary.

From the menubar root:

```sh
swift test --package-path Packages/StreamSession
swift test --package-path Tools/StreamLab
xcodebuild test -project PocketRadio.xcodeproj -scheme PocketRadio \
  -destination 'platform=macOS' -parallel-testing-enabled NO \
  -derivedDataPath /tmp/pocketradio-m12-signed \
  -only-testing:PocketRadioTests \
  CODE_SIGNING_ALLOWED=YES CODE_SIGN_IDENTITY=- DEVELOPMENT_TEAM=
```

Build both Debug and Release with isolated DerivedData. App unit tests may launch their test host but must not start radio playback. UI tests may launch a test app; they are not attended playback evidence. Preserve the listener's existing running app; do not kill it or launch an M12 replacement for normal use without a separate checkpoint.

Use injected boundaries and isolated directories to verify absence of trace/sidecar creation; absence of a capture button is insufficient. Verify source/mode/capture behavior in Release rather than relying on Debug guards. Record commands, exact results, source/shell revisions, and limitations in `milestone_12_handoff.md`.

## Approval and closeout

Implementation, the exact normal-use scope, Debug Off semantics, and all-Sol assignment were authorized by the user's execution requests. Token forecasts replaced the earlier cost-optimized plan; subscription impact is not a blocking gate. A provider/model change, scope expansion, or unresolved correctness invariant still requires approval. No remaining verified review defect is open; ordinary-use acceptance is pending.

The user separately authorized the macOS installation and replacement-app launch on 2026-10-04; `/Applications/PocketRadio.app` is now running. Acceptance and commit/merge/push remain separate user checkpoints. No automatic playback, commits, uploads, or live captures.
