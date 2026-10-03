# M11-A handoff — offline KCRW selection proof

**Updated:** 2026-10-03
**Branch:** menubar `feature/stream-session-model`, committed as `186aa6d` on top of base commit `0d6653e`; not merged
**Status:** Implementation, synthetic tests, retained-trace replay, sensitivity analysis, and report are complete. The user reviewed the result and authorized this commit. M11-B implementation remains gated on explicit approval of the frozen candidate configuration.

## Result

The fixed `+160s` media-clock rule selected the intended occurrence for all nine included KCRW markers across the two retained AAC/HLS sessions.

- Combined median absolute sampled error: **0.571s**.
- Worst absolute sampled error: **3.193s**.
- Missed “What Was I Made For?” transition: selected and reported, excluded from metrics because no marker exists.
- Station-ID commercial: remained excluded; “Fools in Love” was selected 58.213s after the commercial marker and 0.457s after its song marker.
- 10.999s and 31.367s pause intervals: media and reconstructed program clocks each changed only +0.027s between the first samples after the pause/resume markers.
- Initial missing player clock pairs: seven in s1 and six in s2; no later backward, correlation, or media-progression discontinuities.

Full evidence and interpretation: [M11-A experiment report](../experiments/2026-10-02_kcrw_m11a_offline.md). Deterministic raw report: [`2026-10-02_kcrw_m11a_compare.txt`](../experiments/2026-10-02_kcrw_m11a_compare.txt), SHA-256 `9cc9b349982a5a9fb806de0924ff9601678ed1e00380205d26bb53d85bcca7e1`.

## Tests

Last complete results:

- `swift test --package-path pocket-radio-menubar/Packages/StreamSession`: **23 passed, 0 failures**.
- `swift test --package-path pocket-radio-menubar/Tools/StreamLab`: **63 passed, 0 failures** — 41 StreamLab and 22 StreamDiagnostics.
- Total: **86 passed, 0 failures**.
- Two consecutive retained-trace comparisons were byte-identical.
- `git diff --check` passed in both the menubar and shell repositories.

Synthetic coverage includes occurrence identity/revisions/repeats/breaks, unambiguous and ambiguous timestamp correction, failure/empty/out-of-order feed results, eviction/expiry, threshold boundaries, initial mid-song join, stale/uncovered history, paired-clock pause and discontinuity behavior, new generations, causal replay, annotation validation, commercial exclusion, deterministic comparison, non-finite input, and CLI dispatch.

## Sensitivity and leave-one-session-out

| Offset | Median absolute error | Worst absolute error |
|---:|---:|---:|
| +158s | 1.622s | 5.260s |
| +159s | 0.712s | 4.247s |
| **+160s** | **0.571s** | **3.193s** |
| +161s | 1.488s | 2.157s |
| +162s | 2.469s | 3.223s |
| +163s | 3.488s | 4.291s |

Training on s1's median `+160.805s` and evaluating s2 produced 2.006s median / 2.157s worst. Training on s2's median `+159.818s` and evaluating s1 produced 0.571s median / 1.813s worst. These sessions remain related development evidence, not an independent holdout.

## Implementation shape

- `Packages/StreamSession`: Foundation-only occurrence history, selector, paired media clock, and session reducer.
- `Tools/StreamLab`: local-package dependency plus `select` and multi-session `compare` commands. Existing observation-only `replay` remains separate.
- `docs/menubar/experiments/*.annotations.json`: trace/session-bound marker and pause sidecars.
- No AVPlayer app adapter, endpoint override, UI, account access, preference write, Supabase write, or live request was added.

The `.gitignore` now excludes SwiftPM `.build/` directories. Existing untracked `Tools/StreamLab/.pi/` remains untouched.

## Review decision

Recommendation: freeze `+160s` for an M11-B **Observe only** implementation and fresh fixed-policy attended sessions. Do not treat it as a production constant or infer lyric accuracy.

The user approved the M11-A result and authorized this scoped commit on 2026-10-03. Approval covers the committed offline analysis only; it is not an approval of the frozen candidate configuration that M11-B's entry criteria require.

M11-B implementation, Apply candidate mode, production defaults, endpoint persistence, merge, and iOS work remain separately gated.
