# M6.1: <one-line title>

**Status**: NOT STARTED
**Builds on**: M6 (committed at `02d1a00`).

## Goal

<1-3 sentences. What is the user-visible outcome of this milestone?>

## Done when

- <Specific, observable success criteria.>

## Architecture

<Pattern to follow. Reference existing in-repo patterns from AGENTS.md "In-repo patterns" table when possible.>

## Files

### NEW
- <path> — <purpose>

### EDIT
- <path> — <purpose>

### NO CHANGE
- <path> — <why it might look relevant but stays>

## Risks / Edge cases

- <Each risk with mitigation.>

## Reference sweep

```bash
<grep commands to run before declaring file list complete>
```

## Automated tests

<New tests + edits to existing tests. Use repo test pattern: XCTest + @testable import podcasts.>

## Manual smoke

1. `make run_sim`
2. <Numbered steps the human walks through.>

## Agentic plan

Sequential phases. Each agent reads this file as ground truth.

### Phase 1 — <name>
- Agent: `general-purpose`, model: Sonnet 4.6
- Files allowed: <list>
- Verify: <make commands>

### Phase 2 — Review
- Agent: `caveman:cavecrew-reviewer`, model: Sonnet 4.6
- Focus: <areas to review>

### Phase 3 — Manual smoke
- Human runs Manual smoke list. Sign off before commit.
