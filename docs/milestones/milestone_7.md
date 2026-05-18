# M7: Clean up Favorites ↔ Browse interaction for saved streams

**Status**: NOT STARTED
**Builds on**: M6.1 (committed at `8d557f3`).

## Goal

Clean up the interaction between saved streams — KCRW, KEXP (curated favorites) and any other stations the user has favorited from Browse. Today these two populations are handled by different code paths and surface inconsistently: curated stations get bundled logos, tracklist feeds, and bitrate from JSON; Browse-favorited stations get a radio-browser UUID, a favicon URL, and rely on whatever radio-browser metadata happens to be populated. The detail screen, the Favorites list, and the play behavior should be uniform regardless of origin. (Specifics below to be filled in as we scope.)

## Done when

- <Specific, observable success criteria — fill in once scope is settled.>

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
