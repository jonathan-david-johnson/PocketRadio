---
name: new-milestone
description: Open a new milestone for any PocketRadio platform. Creates docs/<platform>/milestones/milestone_<id>.md from the shell template, drafts its Docs impact, repoints current_milestone.md without writing through it, and adds a README roadmap row. Use for "new milestone", "start M14", "/new-milestone ios 14".
---

# New milestone

Run this from the shell checkout. The conventions are in
`docs/REPO_STRUCTURE.md` § Milestones and § Lifecycle and cleanup. That file
also holds the template.

## Arguments

`<platform> <id>`, for example `ios 14`, `menubar 12a`, or `global 3.1`.

If either is missing, ask. Suggest the next id from
`docs/<platform>/milestones/` and the README roadmap. Follow the platform's
existing numbering style (`N.M` for sequenced sub-milestones, `Na` for sibling
slices).

## Steps

1. **Check the active milestone.** Run
   `readlink docs/<platform>/current_milestone.md`.
   - If that milestone's work is finished, stop. Close it with
     `close-milestone` first.
   - If it is still in progress and the new milestone runs in parallel, ask
     which one `current_milestone.md` should point at.
   - Never mark a milestone COMPLETE here. Closing deletes it.

2. **Create the file.** Write `docs/<platform>/milestones/milestone_<id>.md`
   from `docs/REPO_STRUCTURE.md` § Milestone doc shape.
   - Fill in only the title, `**Status**: PLANNED`, **Depends on**, and
     **Where the work happens**. Ask the user for the repo, branch, and
     worktree.
   - Leave `<bracketed>` placeholders for the goal, scope, and behaviors
     unless the user asks you to draft them.

3. **Draft Docs impact with the user.** This is when the question is cheapest
   to answer. Record only what is knowable now:
   - **Docs this changes or makes stale**: paths in `docs/`, ADRs, contracts,
     or a platform README.
   - **Questions this must settle**: open decisions whose answers may become
     ADRs.

   `none — <reason>` is a valid answer. Don't pick destinations yet;
   `close-milestone` does that.

4. **Repoint the symlink** if this milestone becomes current. Never write
   through the symlink.

   ```bash
   ln -sfn milestones/milestone_<id>.md docs/<platform>/current_milestone.md
   readlink docs/<platform>/current_milestone.md
   ```

5. **Add a roadmap row** to `docs/<platform>/README.md`:

   ```markdown
   | [M<id>](./milestones/milestone_<id>.md) | <title> *(planned)* | <user checkpoint> |
   ```

   If the README has no roadmap table, add one. If the README doesn't exist
   (`ios` and `global` today), create a minimal one: a title, one sentence,
   and the roadmap table. `close-milestone` needs that table.

6. **Commit.** Several sessions share this checkout.

   ```bash
   git add docs/<platform>/milestones/milestone_<id>.md \
           docs/<platform>/current_milestone.md docs/<platform>/README.md
   git diff --cached --name-only   # must list only your files
   git commit -m "docs(<platform>): open M<id> — <title>"
   ```

   Don't push.

## Don't

- Write through `current_milestone.md`.
- Mark the previous milestone COMPLETE and leave it on disk.
- Stage with `git add -A`, `git add .`, or `git add docs/`.
