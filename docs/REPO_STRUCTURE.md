# Multi-Repo / Multi-Platform Project Structure

This is the preferred shape for a project with one product shipped to
multiple platforms, each platform living in its own nested git repo, with a
shared top-level shell for orchestration and docs.

This file owns the **conventions**: layout, formats, and rules. The
`meta-repo` skill owns the **procedures** (step-by-step tasks) and points
here for every convention. Milestone procedures are project skills in this
shell's `.agents/skills/`: `new-milestone`, `close-milestone`, and
`subagent-plan`.

## Layout

```
project/                           # shell repo, always on `main`
├── Makefile                       # top-level: repo admin + delegation
├── CLAUDE.md / AGENTS.md          # repo map + conventions (for AI agents)
├── .githooks/                     # shared hooks; `make hooks` wires every repo
├── contracts/                     # cross-platform contracts
│   ├── <area>/*.json              #   golden fixtures, e.g. contracts/remote/
│   └── features/<area>/*.feature  #   shared Gherkin specs; steps live per platform
├── .agents/skills/                # milestone skills; .claude/skills links here
├── tools/                         # shell-level scripts, incl. docs_check.py
├── supabase/                      # shared backend
├── docs/
│   ├── REPO_STRUCTURE.md          # this file
│   ├── bugs/                      # GLOBAL bugs — cross-platform or shared-backend
│   │   └── bug_1.md
│   ├── todo.md
│   ├── security_concerns.md
│   ├── <platform_a>/              # one dir per platform implementation
│   │   ├── README.md              # includes the roadmap, one row per milestone
│   │   ├── CONTEXT.md             # optional: persistent architecture notes
│   │   ├── current_milestone.md   # symlink -> active milestones/milestone_N.md
│   │   ├── adr/                   # architecture decision records (optional)
│   │   ├── architecture/          # design docs (optional)
│   │   │   └── reviews/           #   dated review reports
│   │   ├── bugs/                  # PLATFORM-SPECIFIC bugs
│   │   │   └── bug_1.md
│   │   ├── experiments/           # dated experiment reports (optional)
│   │   │   └── traces/            #   raw evidence the reports cite
│   │   └── milestones/            # open milestones only; closing deletes them
│   │       ├── milestone_7.md
│   │       ├── milestone_7_handoff.md
│   │       └── milestone_8.md
│   └── <platform_b>/ ...          # same shape
├── <platform_a_dir>/              # nested git repo (own .git, own Makefile)
├── <platform_a_dir>-<topic>/      # optional: worktree of platform_a for parallel work
└── <platform_b_dir>/              # nested git repo (may not exist yet)
```

Not every platform needs to be implemented — `docs/<platform>/` can exist
with a roadmap/milestone_0 before the nested repo is created (`make checkout`
clones it, skips if absent).

Nested repos and their worktrees are gitignored by the shell
(`pocket-radio-*/` in this project).

## Makefile hierarchy

- **Top-level `Makefile`**: repo-shell concerns only.
  - `checkout` — clone any missing platform repos.
  - `status` — branch/sync/dirty status across all nested repos, plus any
    extra worktrees.
  - `hooks` / `hooks-check` — wire every repo (and worktree) to `.githooks/`.
  - `upstream-remote` — wire upstream remotes for forks.
  - Thin **delegating** targets per platform, e.g. `console-test`, `roku-deploy`,
    `menubar-build` — each is `@$(MAKE) -C $(PLATFORM_DIR) <target>`.
  - `help` lists every target grouped by platform.
- **Per-platform `Makefile`** (inside the nested repo): owns the real build/
  test/run/deploy targets and platform-specific tooling. Top-level never
  duplicates this logic — it only forwards.

## Branches and parallel work

The shell is the coordination record. Platform repos are where code changes.

### The shell stays on `main`

- Plans, milestone status, handoffs, experiment reports, bug docs, and
  contracts are committed straight to shell `main`. Docs may describe work
  that is still in flight on a platform branch; the milestone's status line
  says so.
- Don't create long-lived shell feature branches for platform work.

### Code happens on platform branches

- Each milestone names its repo, branch, and worktree in a
  **Where the work happens** table (see [Milestone doc shape](#milestone-doc-shape)).
- One platform branch at a time can use the main checkout,
  `<platform_dir>/`.
- For a second, parallel branch in the same platform, create a **sibling
  worktree** at `<platform_dir>-<topic>/`, e.g. `pocket-radio-ios-carplay/`.
  It must sit at the same depth as `<platform_dir>/`, because nested repos
  find the shell by relative path:
  - tests load `../contracts/...` via `#filePath` or the equivalent;
  - hooks use `core.hooksPath=../.githooks`, which worktrees share with
    their repo.
- Never place a worktree anywhere else, or fixtures and hooks silently break.

### Untracked files a new worktree needs

A worktree contains only tracked files. Copy these from the main checkout:

| Platform | Files |
|---|---|
| iOS | `podcasts/Credentials/LocalApiCredentials.swift` (secrets); `podcasts/Strings+Generated.swift`, `podcasts/ThemeColor.swift`, `podcasts/ThemeStyle.swift` (generated by `make generate_code` / `make generate_colors`, not by a build phase) |

Add a row when another platform needs one. Each worktree also gets its own
Xcode DerivedData, so expect a full first build.

### Shell changes during platform work

- **Additive changes go straight to `main`:** new docs, new contract
  fixtures, new `.feature` files, new delegating Make targets. Nothing reads
  them until a platform does, so they can't break another branch.
- **Breaking changes need a shell branch:** editing an existing contract,
  rewording a Gherkin step another platform already implements, a Supabase
  migration that must ship with an app release, or restructuring the
  top-level Makefile. Create a shell worktree on that branch, with the
  platform worktree nested inside it at the usual relative position.
- Nested repos aren't submodules, so nothing pins which shell commit a
  platform branch was tested against. Record the shell commit hash in the
  milestone's verification notes.

### Committing in the shared shell checkout

Several sessions share one shell checkout, and so one staging area.

- Stage explicit file paths only.
- Never use `git add -A`, `git add .`, `git add docs/`, or `git commit -a`.
- Before committing, check `git diff --cached --name-only` and make sure it
  lists only your files.

### Finishing parallel work

1. Merge the platform branch in its repo.
2. `git -C <platform_dir> worktree remove ../<platform_dir>-<topic>`
3. Delete the branch.
4. Update the milestone's status on shell `main`.

## Bugs

- `docs/bugs/bug_N.md` — bugs spanning platforms, or in shared backend
  (Supabase, sync API). Anything one platform team can't fix alone.
- `docs/<platform>/bugs/bug_N.md` — platform-local bugs.
- Bug doc format (see `docs/console/bugs/bug_1.md` for a worked fixed bug,
  `docs/ios/bugs/bug_1.md` for a worked open one):
  - Title + **Status:** (Open / Fixed YYYY-MM-DD / Suggestion)
  - One `## Symptom <X>` section per distinct observed issue
  - `### Root cause`, then either `### Fix applied (date)` + `### Files
    changed` once fixed, or `### Proposed fix` + `## Files involved` while
    still open. An open bug keeps the same skeleton; only those two headings
    change, so a fix is a rename rather than a rewrite.
  - An open bug should carry its **evidence** — the commands or queries that
    establish the diagnosis — so the next reader does not repeat them. Say
    plainly what was predicted but not yet confirmed.
  - **Status: Suggestion** is for a latent design weakness worth exploring
    rather than an observed failure. Same skeleton, with `## Suggestion` in
    place of `## Symptom` and an explicit "what would have to be true for this
    to be worth doing" section.
  - Multi-symptom bugs get lettered symptoms (A, B, ...) under one doc if
    they were diagnosed/fixed together.
- While a bug is open, its doc is append-only: change the status and add
  sections, but don't delete past symptoms. Once the bug is fixed, the doc is
  closed out and deleted. See [Lifecycle and cleanup](#lifecycle-and-cleanup).

## Milestones

`docs/<platform>/milestones/milestone_N.md`, with `current_milestone.md` as a
symlink to the active one. Open milestones with the `new-milestone` skill and
close them with `close-milestone`. **Never write through the symlink**, because
that overwrites the milestone it points at. Repoint it with `ln -sfn`.

Numbering:

- `milestone_N.M.md` — a sequenced sub-milestone of N (iOS uses this).
- `milestone_Na.md`, `milestone_Nb.md` — sibling slices of N (menubar uses
  this). Either is fine; stay consistent within a platform.
- Handoff notes: `milestone_<id>_handoff.md` next to the milestone they
  belong to. They are deleted when that milestone closes.

### Milestone doc shape

```markdown
# <Platform> M<N> — <short title>

**Status**: PLANNED | IN PROGRESS | COMPLETE — <commit or date>
**Depends on**: <milestones / decisions>
**Required by**: <milestones / branches>
**Model**: optional — which work suits which model

## Where the work happens

| | |
|---|---|
| Plan | Shell `main`: this file (+ reports, bug docs) |
| Code | `<platform_dir>`, branch `<branch>` from `<base>` |
| Worktree | `<platform_dir>/` or `<platform_dir>-<topic>/` |
| Shell changes | None, or the additive list |

**Goal:** one paragraph, plain language, what this milestone achieves.

**User checkpoint:** what the user can *do* / observe when this milestone is
done — a concrete, demoable scenario, not an implementation detail.

## Scope

- File/module-level breakdown of what gets built or changed, grouped by
  area (data layer, UI, API client, etc.) — concrete enough that a sub-agent
  can pick up one bullet and go.

## Behaviors to test (red -> green, one at a time)

1. Numbered, independently-testable behaviors. Each one should map to a
   test (or a small group of tests) that can be written first (red) then
   made to pass (green). This list doubles as a work-splitting plan: each
   numbered item is a candidate unit of work for a sub-agent.

## Out of scope

- What's explicitly deferred, and to which milestone.

## Docs impact

- **Docs this changes or makes stale:** <paths, or "none — <reason>">
- **Questions this must settle:** <open decisions whose answers may become
  ADRs, or "none — <reason>">

## Hand-performed interactions

- [ ] <gesture> — <what should happen>
```

Fill in **Docs impact** when the milestone opens, with only what is knowable
then. `close-milestone` decides where each answer goes.

Keep **Hand-performed interactions** only for UI driven by gestures. The human
ticks each line, and the milestone can't close while a line is unticked.
Gesture handling is often unreachable from tests: iOS M12.2 shipped a dead
drag-to-reorder with twelve passing tests.

At close, each **Behaviors to test** item names the test that covers it.

### Experiment milestones

When a milestone exists to prove feasibility or gather evidence before
building, replace **Behaviors to test** with:

- **Hypotheses** — predictions, labeled as not yet observed.
- **Experiments** — each with question, method, pass criterion, and the
  decision it feeds. These are the fan-out units.
- **Decision gate** — the decisions the user makes from the results, and
  which experiment supplies the evidence for each.

Record each result in `docs/<platform>/experiments/YYYY-MM-DD_<topic>.md`,
with raw evidence under `experiments/traces/`. Worked examples: iOS M13 and
menubar M10. While they're open they live in `docs/<platform>/milestones/`.
Once closed, they're under the tags `archive/ios-m13` and
`archive/menubar-m10`.
Reports and traces are deleted at close-out. Their conclusions, negative ones
included, go to an ADR that cites the report by archive tag.

### Sub-agent fan-out

The **Behaviors to test** (or **Experiments**) list is the fan-out unit.
Each numbered item should be:

- **Independently verifiable** — has its own test(s), doesn't require another
  behavior's code to exist first (or clearly states the dependency).
- **Scoped to specific files** — a sub-agent reading just that line + the
  `## Scope` file list should know exactly what to touch.
- **Small enough for one PR** — if a behavior needs its own sub-breakdown,
  split it into `N.a`, `N.b`, etc., or split into a separate milestone
  (`milestone_N.1.md`) rather than growing the list item.

When a milestone needs cross-cutting handoff notes (partial progress, open
questions for the next session/agent), add a handoff file alongside the
milestone file rather than editing the milestone doc's scope after work
has started. Handoffs and subagent plans are deleted when the milestone
closes.

## Lifecycle and cleanup

Milestones, handoffs, subagent plans, experiment reports, and fixed bug docs
are working state. When a milestone closes, its durable knowledge moves to a
permanent home and the working files are deleted. Git keeps them under an
archive tag.

| Artifact | Lives until | Durable part goes to |
|---|---|---|
| Milestone | Its code is merged on the platform base branch | Tests, contracts, ADRs, README/CONTEXT |
| Handoff, subagent plan | Its milestone closes | Nothing |
| Experiment report | Its milestone closes | An ADR, including rejected alternatives |
| Traces | Its milestone closes | The platform repo, if a tool or test replays them |
| Bug doc | The bug is fixed | A regression test or verification note; ADR or CONTEXT for general lessons |
| ADR, README, CONTEXT, architecture, contracts | Permanent | — |

Permanent docs describe the current state. Edit them in place rather than
appending history. To change a decision, write a new ADR and mark the old one
`Superseded by NNNN`.

### Opening and closing

- `new-milestone` opens a milestone. It creates the file, drafts Docs impact,
  repoints the symlink, and adds a roadmap row.
- `close-milestone` closes one. It checks that the code is merged, extracts the
  durable knowledge, tags, and deletes, all in one commit that you review.
- No COMPLETE state stays on disk. A finished milestone is either being closed
  or already gone.

### Archive tags and citations

- Tag: `archive/<platform>-m<id>`, on the last commit that contains the
  milestone and its bundle.
- Cite an archived file as `archive/<platform>-m<id>:<path>`. Read it with
  `git show archive/ios-m13:docs/ios/milestones/milestone_13.md`.
- The platform README roadmap keeps one row per milestone, and a closed row
  names its tag. That table is the history.
- A bug closed outside a milestone is cited as `<commit>:<path>`, using the
  commit before the deletion.
- Tags aren't pushed by default. Push them with `git push origin <tag>`.

### What code may cite

Code, meaning any non-markdown file in any repo, may cite ADRs, architecture
docs, and contracts. It never cites milestones, handoffs, experiments, or bug
docs, because those get deleted.

### Enforcement

`.githooks/pre-commit` runs `tools/docs_check.py --staged`. It checks only the
commit's own changes, so another session's files can't block yours.

- **Rule A, every repo:** added lines in non-markdown files may not cite
  lifecycle docs.
- **Rule B, shell only:** deleting a file under `docs/` fails while a tracked
  file or a `current_milestone.md` symlink still links to it. Deleting a
  milestone also requires an archive tag that contains the file, and a README
  roadmap row that names the tag.

`python3 tools/docs_check.py` prints an advisory report for the whole tree:
finished milestones still on disk, milestones without a status line, orphaned
handoffs, broken links, and code citations. Add `--strict` to exit non-zero.

### Where the skills live

Milestone skills live only in this shell's `.agents/skills/`, never in a
platform repo. Pi discovers project skills from the working directory up to
the nearest repository root. A session started inside a nested repo therefore
doesn't see them. Run milestone work from the shell checkout.

### Backlog

Milestones written before this convention close the same way, with lighter
extraction. Triage them by inbound references. If nothing but the roadmap cites
a milestone and its code has shipped, extract nothing: tag it, repoint the
roadmap row, and delete it.

## Contracts and shared specs

- `contracts/<area>/` holds golden fixtures that every platform's tests load.
  The fixtures are the contract; typed structs on each platform are
  conveniences that must conform.
- `contracts/features/<area>/*.feature` holds Gherkin specs worded
  platform-neutrally (e.g. "the system now-playing display shows") and tagged
  by platform (`@ios`, `@carplay`, …). Each platform implements its own step
  definitions. Platform-specific known-bug markers live with that platform's
  steps, never as tags in the shared spec.
- Contracts change additively. See
  [Shell changes during platform work](#shell-changes-during-platform-work).

## Cross-platform consistency

When a behavior must match across platforms (e.g. "auto-archive episode on
completion"), don't assume parity — each platform's milestone history may
have implemented it independently with different constants/thresholds.
Check all platform implementations before treating one as the reference, and
record the agreed-upon shared value (and which platforms implement it) in
`docs/bugs/` or a shared ADR if it's not yet consistent.
