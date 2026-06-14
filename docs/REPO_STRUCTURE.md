# Multi-Repo / Multi-Platform Project Structure

This is the preferred shape for a project with one product shipped to
multiple platforms, each platform living in its own nested git repo, with a
shared top-level shell for orchestration and docs.

## Layout

```
project/
├── Makefile                     # top-level: branch admin + delegation
├── CLAUDE.md / AGENTS.md         # repo map + conventions (for AI agents)
├── docs/
│   ├── bugs/                     # GLOBAL bugs — cross-platform or shared-backend
│   │   └── bug_1.md
│   ├── todo.md
│   ├── security_concerns.md
│   ├── <platform_a>/             # one dir per platform implementation
│   │   ├── README.md
│   │   ├── CONTEXT.md            # optional: persistent architecture notes
│   │   ├── current_milestone.md  # symlink -> active milestones/milestone_N.md
│   │   ├── adr/                  # architecture decision records (optional)
│   │   ├── bugs/                 # PLATFORM-SPECIFIC bugs
│   │   │   └── bug_1.md
│   │   └── milestones/
│   │       ├── milestone_0.md
│   │       ├── milestone_1.md
│   │       └── ...
│   ├── <platform_b>/
│   │   └── ... (same shape)
│   └── <platform_c>/
│       └── ... (same shape)
├── <platform_a_dir>/             # nested git repo (own .git, own Makefile)
├── <platform_b_dir>/             # nested git repo
└── <platform_c_dir>/             # nested git repo (may not exist yet)
```

Not every platform needs to be implemented — `docs/<platform>/` can exist
with a roadmap/milestone_0 before the nested repo is created (`make checkout`
clones it, skips if absent).

## Makefile hierarchy

- **Top-level `Makefile`**: repo-shell concerns only.
  - `checkout` — clone any missing platform repos.
  - `status` — branch/sync/dirty status across all nested repos.
  - `upstream-remote` — wire upstream remotes for forks.
  - Thin **delegating** targets per platform, e.g. `console-test`, `roku-deploy`,
    `menubar-build` — each is `@$(MAKE) -C $(PLATFORM_DIR) <target>`.
  - `help` lists every target grouped by platform.
- **Per-platform `Makefile`** (inside the nested repo): owns the real build/
  test/run/deploy targets and platform-specific tooling. Top-level never
  duplicates this logic — it only forwards.

## Bugs

- `docs/bugs/bug_N.md` — bugs spanning platforms, or in shared backend
  (Supabase, sync API). Anything one platform team can't fix alone.
- `docs/<platform>/bugs/bug_N.md` — platform-local bugs.
- Bug doc format (see `docs/console/bugs/bug_1.md` for a worked example):
  - Title + **Status:** (Open / Fixed YYYY-MM-DD)
  - One `## Symptom <X>` section per distinct observed issue
  - `### Root cause`, `### Fix applied (date)`, `### Files changed`
  - Multi-symptom bugs get lettered symptoms (A, B, ...) under one doc if
    they were diagnosed/fixed together.

## Milestones

`docs/<platform>/milestones/milestone_N.md`, with `current_milestone.md` as a
symlink to the active one. **Never edit through the symlink** — when a
milestone completes, create `milestone_N+1.md` and repoint the symlink.

### Milestone doc shape

```markdown
# M<N> — <short title>

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
```

### Sub-agent fan-out

The **Behaviors to test** list is the fan-out unit. Each numbered behavior
should be:

- **Independently verifiable** — has its own test(s), doesn't require another
  behavior's code to exist first (or clearly states the dependency).
- **Scoped to specific files** — a sub-agent reading just that line + the
  `## Scope` file list should know exactly what to touch.
- **Small enough for one PR** — if a behavior needs its own sub-breakdown,
  split it into `N.a`, `N.b`, etc., or split into a separate milestone
  (`milestone_N.1.md`) rather than growing the list item.

When a milestone needs cross-cutting handoff notes (partial progress, open
questions for the next session/agent), add `milestone_N_handoff.md` alongside
the milestone file rather than editing the milestone doc's scope after work
has started.

## Cross-platform consistency

When a behavior must match across platforms (e.g. "auto-archive episode on
completion"), don't assume parity — each platform's milestone history may
have implemented it independently with different constants/thresholds.
Check all platform implementations before treating one as the reference, and
record the agreed-upon shared value (and which platforms implement it) in
`docs/bugs/` or a shared ADR if it's not yet consistent.
