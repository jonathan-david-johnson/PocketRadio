# KCRW AAC/HLS M11-A offline selection — 2026-10-02

**Status:** Offline implementation and retained-trace validation complete; awaiting user review. This is development evidence from the same two captures that motivated the rule, not an independent holdout and not approval for M11-B.

## Inputs and reproducibility

- Menubar work branch: `feature/stream-session-model`, based on M10 feature head `0d6653e`. M10 is merged on `main` at `a3787ff`. The M11-A worktree is dirty and uncommitted.
- Exact endpoint represented by both traces: `https://streams.kcrw.com/e24_aac/playlist.m3u8`.
- Primary fixed parameter: `feedToProgramOffset = +160.000s`.
- History policy: 100 occurrences, six-hour source-time window, 120s unambiguous timestamp-correction window.
- Selection availability: maximum 1200s selected-occurrence age and 120s since the last successful feed response.
- Media clock: paired media/program-date anchor with 2s correlation and progression tolerances. Wall time never advances song position.
- Tests: **23 StreamSession + 63 Stream Lab = 86 passed, 0 failures**. Stream Lab consists of 41 `StreamLabTests` and the unchanged 22 `StreamDiagnosticsTests`.

Retained inputs:

| Session | Trace SHA-256 | Annotation sidecar |
|---|---|---|
| s1 | `8c72bd4b694e55892cb36b9cc96063e85dbc4e271f4c1c503e996b7688924057` | `2026-09-26_kcrw_hls_attended_s1.annotations.json` |
| s2 | `92d5a557fa0633cd1eb3561b0f92fdd3645153583173ce9ae773d8c482b3805c` | `2026-09-26_kcrw_hls_attended_s2.annotations.json` |

The generated deterministic report is [`2026-10-02_kcrw_m11a_compare.txt`](2026-10-02_kcrw_m11a_compare.txt), 147 lines, SHA-256 `9cc9b349982a5a9fb806de0924ff9601678ed1e00380205d26bb53d85bcca7e1`. Two consecutive runs compared byte-identically.

Commands, from the shell repository:

```bash
swift test --package-path pocket-radio-menubar/Packages/StreamSession
swift test --package-path pocket-radio-menubar/Tools/StreamLab

pocket-radio-menubar/Tools/StreamLab/.build/debug/stream-lab compare \
  docs/menubar/experiments/traces/2026-09-26_kcrw_hls_attended_s1.jsonl \
  docs/menubar/experiments/2026-09-26_kcrw_hls_attended_s1.annotations.json \
  docs/menubar/experiments/traces/2026-09-26_kcrw_hls_attended_s2.jsonl \
  docs/menubar/experiments/2026-09-26_kcrw_hls_attended_s2.annotations.json \
  --offset 160
```

`select` and `compare` read only the supplied local files. They do not contact a stream, feed, account, or Supabase. The sidecars contain only public station metadata, marker classifications already recorded in the attended report, trace identity, and timing.

## Primary `+160s` result

The selector chose the annotated occurrence at every one of the **nine included song markers**. Signed error is the first sampled candidate decision elapsed time minus the listener marker; negative means the candidate changed first.

| Session | Occurrence | Candidate elapsed | Marker elapsed | Signed error |
|---|---|---:|---:|---:|
| s1 | I Go Up, You Go Down | 70.087s | 70.169s | −0.082s |
| s1 | Hardy (feat. Clairo) | 280.879s | 280.526s | +0.353s |
| s1 | I Feel Electric (Max Essa remix) | 513.414s | 512.842s | +0.571s |
| s1 | Things Take Time | 1248.814s | 1250.627s | −1.813s |
| s1 | Wanderlust (Original Mix) | 1454.077s | 1454.514s | −0.438s |
| s2 | Barthelona | 85.667s | 88.860s | −3.193s |
| s2 | Fools in Love | 305.092s | 304.635s | +0.457s |
| s2 | Friend of Mine | 585.765s | 584.657s | +1.108s |
| s2 | Colosse (feat. Laurence-Anne) | 834.014s | 833.198s | +0.816s |

Combined median absolute error was **0.571s** and worst absolute error was **3.193s**, within the proposed ±5s coarse-marker signal. These are sampled transition errors, not sample-accurate audio boundaries.

### Excluded observations remained visible

- The missed “What Was I Made For?” transition was selected at 1035.498s but has no marker, so it was excluded from error metrics.
- The s2 station-ID commercial marker was at 246.879s. The selector did not choose “Fools in Love” until 305.092s, **58.213s after the commercial marker** and 0.457s after the identified song marker. The feed omitted the commercial; the selector neither recognized nor invented it.
- All three order-inferred s1 identities remain labeled as inferred in the sidecar and report.

### Pauses

| Session | Recorded marker interval | Media-clock change | Reconstructed program-date change | Result |
|---|---:|---:|---:|---|
| s1 | 10.999s | +0.027s | +0.027s | frozen |
| s2 | 31.367s | +0.027s | +0.027s | frozen |

Feed observations during the pauses did not advance the media-derived clock or candidate. The 0.027s change reflects samples just after the pause/resume markers, not wall-clock accumulation.

The replayer reported seven initial missing clock pairs in s1 and six in s2 before AVPlayer supplied usable program dates. It reported no backward, correlation, or media-progression discontinuity in either retained trace.

## Predeclared sensitivity

| Fixed offset | Markers measured | Median absolute error | Worst absolute error |
|---:|---:|---:|---:|
| +158s | 9/9 | 1.622s | 5.260s |
| +159s | 9/9 | 0.712s | 4.247s |
| **+160s** | **9/9** | **0.571s** | **3.193s** |
| +161s | 9/9 | 1.488s | 2.157s |
| +162s | 9/9 | 2.469s | 3.223s |
| +163s | 9/9 | 3.488s | 4.291s |

`+160s` has the lowest in-sample median; `+161s` has the lowest worst case. The experiment does not retune to either statistic. `+160s` was fixed before this replay, marker sampling quantizes transitions to roughly one second, and these captures are not a holdout.

## Leave-one-session-out check

- Median mapping from s1: `+160.805s`; applied to s2, median absolute error **2.006s**, worst **2.157s** across 4/4 markers.
- Median mapping from s2: `+159.818s`; applied to s1, median absolute error **0.571s**, worst **1.813s** across 5/5 markers.

This reduces direct reuse of each evaluated session but is still related development evidence: both sessions used the same endpoint, machine, day, capture implementation, and unrecorded output route.

## Decision for review

M11-A's mechanical and proposed quality signals pass:

- causal replay uses no future feed rows;
- output is byte-deterministic;
- all nine included markers select the intended occurrence;
- worst fixed-`160s` sampled error is 3.193s, inside ±5s;
- both pauses freeze the media clock;
- the missed marker and commercial are excluded without disappearing;
- ordinary schema-v1 observation replay remains separate and tested.

**Recommendation:** freeze `+160s` as the candidate for a fresh M11-B observe-only experiment, not as a production constant. Fresh fixed-policy sessions on a recorded output route remain necessary. M11-A cannot validate lyric-line timing because the retained traces contain no lyric landmarks, and it cannot validate route-specific behavior because the route was not recorded.

No M11-B implementation, production endpoint change, commit, or merge is authorized by this result.
