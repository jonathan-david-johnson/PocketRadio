---
name: close-milestone
description: Close a finished PocketRadio milestone. Moves its durable knowledge into ADRs, README/CONTEXT, tests, and contracts; tags the archive; then deletes the milestone with its handoffs, subagent plans, experiments, and fixed bugs in one reviewed commit. Use for "close M13", "milestone done", "/close-milestone menubar 11b", or the backlog sweep.
---

# Close milestone

Run this from the shell checkout. The conventions are in
`docs/REPO_STRUCTURE.md` § Lifecycle and cleanup.

The pre-commit hook (`tools/docs_check.py --staged`) enforces the mechanical
parts: dangling links, the archive tag, and the roadmap row. This skill covers
the judgment: what is worth keeping, and where it goes.

## Arguments

`<platform> <id>`. Default: the target of
`docs/<platform>/current_milestone.md`. The archive tag is
`archive/<platform>-m<id>`.

## 1. Gates

Stop at the first gate that fails, and tell the user why.

- **The code is merged.** Read **Where the work happens** for the repo,
  branch, and base. Check:

  ```bash
  git -C <repo> merge-base --is-ancestor <branch> <base> && echo merged
  ```

  If the branch is gone, ask for the merge commit. Unmerged work means the
  milestone is still the spec, so deleting it now would break the branch's
  references.
- **Sub-milestones are closed.** To close M13, no `milestone_13.*.md` may
  remain. Close the children first.
- **Hand-performed interactions are ticked**, if the milestone has that list.
  The human ticks them, not the agent. Tests can't prove gestures: iOS M12.2
  shipped a dead drag-to-reorder with twelve passing tests.
- **No in-flight branch cites the bundle.** Search every
  `pocket-radio-*/` checkout and worktree for the bundle's file names. A hit on
  an unmerged branch means you wait, or ask the user.

## 2. Gather the bundle

List these files for the user:

- `milestone_<id>.md`
- `milestone_<id>_handoff.md`, `milestone_<id>_subagent_plan.md`, and
  `m<id>_handoff.md`
- experiment reports named for or cited by the milestone, and the traces they
  cite
- bug docs that this milestone fixed. Leave open bugs in place.

## 3. Extract

Walk the milestone's **Docs impact** first. Then read the rest of the bundle
for anything else that would be lost. Give each item exactly one destination.

| Found in the bundle | Destination |
|---|---|
| A decision, or a question it settled | An ADR: context, decision, consequences, rejected alternatives. Cite evidence as `archive/<platform>-m<id>:<path>`. |
| A negative experiment result | The same ADR, under **Rejected alternatives**. This is the easiest thing to lose. |
| How the system works now | The platform README, `CONTEXT.md`, or an `architecture/` doc, edited in place. Describe the current state; don't append history. |
| A new domain term | The `CONTEXT.md` glossary |
| An item from Behaviors to test | The name of the test that covers it. If it can't be tested (CarPlay, Roku, stream timing), record how it was verified. Put that in `CONTEXT.md` only if a later change could break it silently. |
| Traces a tool or test replays | The platform repo, in a separate commit there. Update the tool README that cites them. |
| A fixed bug | A regression test or a verification note. General lessons go to an ADR or `CONTEXT.md`. |
| A lesson about how agents should work | The right repo's `AGENTS.md`, or a skill |
| Progress notes, phase plans, status chatter, "first we tried X, then Y" | Nothing. Git has it. |

If a decision changes an existing ADR, write a new ADR and mark the old one
`Superseded by NNNN`.

**Review gate.** Show the user a table of item, destination, and status. Wait
for approval before deleting anything.

## 4. Repoint references

- **The README roadmap row:** replace the link with the tag. The hook requires
  this.

  ```markdown
  | M13 (`archive/ios-m13`) | <title> | <user checkpoint> |
  ```

- **Other shell docs** that link to the bundle: rewrite each link as an
  archive citation, or drop it.
- **`current_milestone.md`**, if it points here: run `ln -sfn` to the next
  planned milestone. If none is planned, ask the user whether to run
  `new-milestone`.
- **Code in nested repos** that cites the bundle: point it at the ADR. Make
  that change in the nested repo, on its branch, as a separate commit.
  `python3 tools/docs_check.py` lists these citations.

## 5. Tag the archive

The tag must point at a commit that contains every bundle file in its final
form. If a bundle file has uncommitted edits, commit them first. Then tag right
before deleting, because other sessions can move `HEAD`:

```bash
git tag -a archive/<platform>-m<id> -m "<platform> M<id> — <title>" HEAD
git cat-file -e archive/<platform>-m<id>:<path>   # once per bundle file
```

## 6. Delete and commit

```bash
git rm <each bundle file>
git add <each extraction file>                    # explicit paths only
git diff --cached --name-only                     # only your files
git commit -m "docs(<platform>): close M<id> — <title>"
```

- In the commit body, list each extraction with its destination.
- If the hook fails, fix what it reports. Don't use `--no-verify`.
- Don't push. Tell the user that tags aren't pushed by default:
  `git push origin main archive/<platform>-m<id>`.

## Backlog mode

For milestones written before this convention, triage by inbound references:

```bash
git grep -n milestone_<id>.md       # shell docs that link to it
python3 tools/docs_check.py         # code that cites it
```

- If nothing but the roadmap cites it and its code has shipped, the
  extraction can be "nothing". Tag it, repoint the roadmap row, and delete it.
- If something cites it, run the full extraction for whatever that citation
  depends on.

Several milestones can share one commit, with one tag each.

## Retrieving an archive

```bash
git show archive/ios-m13:docs/ios/milestones/milestone_13.md
git ls-tree -r --name-only archive/ios-m13 -- docs/ios
git tag -l 'archive/*'
```

## Don't

- Mark a milestone COMPLETE and leave the file. Closing means deleting.
- Delete before the user approves the extraction table.
- Tag after deleting. The archive would miss the files, and the hook catches
  it.
- Extract narrative. Keep the decision and the rejected alternatives; leave
  the story to git.
