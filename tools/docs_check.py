#!/usr/bin/env python3
"""Docs lifecycle checks. Conventions: docs/REPO_STRUCTURE.md § Lifecycle and cleanup.

  python3 tools/docs_check.py            advisory report for the whole tree; exits 0
  python3 tools/docs_check.py --strict   same report; exits 1 if it lists anything
  python3 tools/docs_check.py --staged   pre-commit rules; staged changes only

--staged runs from .githooks/pre-commit in the shell and in every nested repo.
It looks only at what the commit changes, so another session's stale files
cannot block your commit.

  Rule A (every repo): added lines in non-markdown files must not cite
    milestones, handoffs, experiments, or bug docs. Cite an ADR instead.
  Rule B (shell only): deleting a file under docs/ must not leave links to it
    in the index. Deleting a milestone also needs its archive tag, and the
    platform README roadmap must name that tag.
"""
import os
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote

SHELL = Path(__file__).resolve().parent.parent

# A citation of a lifecycle doc, meaning something close-out deletes.
CITE = re.compile(
    r"docs/[\w-]+/(?:milestones|experiments|bugs)/"
    r"|\b(?:milestone_[\w.]+|m[\d.]+[a-z]?_handoff|bug_\d+)\.md\b"
    r"|experiments/traces/"
)
CITE_ERE = (
    r"docs/[A-Za-z0-9_-]+/(milestones|experiments|bugs)/"
    r"|(milestone_[A-Za-z0-9_.]+|m[0-9.]+[a-z]?_handoff|bug_[0-9]+)\.md"
    r"|experiments/traces/"
)
# milestone_13.md, milestone_6.2.5.md, milestone_11a.md, milestone_7_lyrics.md;
# not milestone_13.1_handoff.md or milestone_12_subagent_plan.md.
MILESTONE = re.compile(r"^milestone_(\d[\d.]*[a-z]?)(?:_(?!handoff|subagent_plan)\w+)?\.md$")
SIBLING = re.compile(r"^(?:milestone_(.+?)_(?:handoff|subagent_plan)|m(.+?)_handoff)\.md$")
LINK = re.compile(r"\]\(([^)\s]+)\)")
SHELL_EXEMPT = ("docs/", ".githooks/", "tools/docs_check.py")


def git(*args, cwd=None):
    """stdout, or None when git exits non-zero."""
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, errors="replace")
    return r.stdout if r.returncode == 0 else None


def exempt(path, in_shell):
    if path.endswith((".md", ".markdown")):
        return True
    return in_shell and path.startswith(SHELL_EXEMPT)


# --- staged rules ---------------------------------------------------------


def code_citations(in_shell):
    diff = git("diff", "--cached", "-U0", "--no-color", "--no-ext-diff", "--diff-filter=d") or ""
    errors, path, line_no, header = [], None, 0, False
    for line in diff.splitlines():
        if line.startswith("diff --git "):
            header, path = True, None
        elif header and line.startswith("+++ "):
            path = line[6:] if line.startswith("+++ b/") else None
        elif line.startswith("@@"):
            header = False
            line_no = int(re.search(r"\+(\d+)", line).group(1))
        elif not header and line.startswith("+"):
            if path and not exempt(path, in_shell) and CITE.search(line):
                errors.append(f"{path}:{line_no}: cites a lifecycle doc: {line[1:].strip()[:100]}")
            line_no += 1
    if errors:
        errors.append("  Code outlives milestones, experiments, and bug docs. Cite an ADR,")
        errors.append("  architecture doc, or contract instead.")
    return errors


def dangling_refs(deleted):
    base = os.path.basename(deleted)
    out = git("grep", "--cached", "-n", "-F", "-e", base) or ""
    ref_pat = re.compile(r"[\w./-]*" + re.escape(base))
    errors = []
    for hit in out.splitlines():
        f, n, text = hit.split(":", 2)
        for m in ref_pat.finditer(text):
            # `archive/ios-m13:docs/ios/...` is an archive citation, not a link.
            if m.start() > 0 and text[m.start() - 1] == ":":
                continue
            ref = m.group(0)
            candidates = {os.path.normpath(os.path.join(os.path.dirname(f), ref)), os.path.normpath(ref)}
            if deleted in candidates:
                errors.append(f"{f}:{n}: still links to deleted {deleted}")
                break
    return errors


def archive_checks(platform, mid, path):
    tag = f"archive/{platform}-m{mid}"
    errors = []
    if git("rev-parse", "-q", "--verify", f"refs/tags/{tag}") is None:
        errors.append(f"{path}: tag {tag} is missing. Before deleting, run:")
        errors.append(f"  git tag -a {tag} -m '{platform} M{mid} closed' HEAD")
    elif git("cat-file", "-e", f"{tag}:{path}") is None:
        errors.append(f"{path}: tag {tag} must point at a commit that still contains this file.")
    readme = f"docs/{platform}/README.md"
    content = git("show", f":{readme}")
    if content is None:
        errors.append(f"{path}: {readme} does not exist. Its roadmap must record {tag}.")
    elif not re.search(re.escape(tag) + r"(?!\w|\.\d)", content):
        errors.append(f"{path}: the {readme} roadmap must name {tag}.")
    return errors


def deletions():
    out = git("diff", "--cached", "--name-only", "--no-renames", "--diff-filter=D", "-z") or ""
    deleted = [p for p in out.split("\0") if p.startswith("docs/")]
    errors = []
    # git grep skips symlink targets, so check current_milestone.md and friends here.
    for entry in (git("ls-files", "-s", "--", "docs") or "").splitlines():
        meta, link = entry.split("\t", 1)
        mode, sha = meta.split()[:2]
        if mode != "120000":
            continue
        target = os.path.normpath(os.path.join(os.path.dirname(link), git("cat-file", "-p", sha) or ""))
        if target in deleted:
            errors.append(f"{link}: symlink points at deleted {target}. Repoint it to the next milestone.")
    for path in deleted:
        errors += dangling_refs(path)
        p = Path(path)
        m = MILESTONE.match(p.name)
        if m and len(p.parts) == 4 and p.parts[2] == "milestones":
            errors += archive_checks(p.parts[1], m.group(1), path)
    return errors


def staged():
    top = git("rev-parse", "--show-toplevel")
    if top is None:
        return 0
    in_shell = Path(top.strip()).resolve() == SHELL
    errors = code_citations(in_shell)
    if in_shell:
        errors += deletions()
    if not errors:
        return 0
    print("pre-commit: docs lifecycle check failed.", file=sys.stderr)
    for e in errors:
        print(f"  {e}", file=sys.stderr)
    print("  Conventions: docs/REPO_STRUCTURE.md § Lifecycle and cleanup.", file=sys.stderr)
    return 1


# --- advisory report ------------------------------------------------------


def rel(p):
    return str(p.relative_to(SHELL))


def milestone_findings():
    finished, no_status, orphans = [], [], []
    for d in sorted(SHELL.glob("docs/*/milestones")):
        files = sorted(d.glob("*.md"))
        ids = {MILESTONE.match(f.name).group(1) for f in files if MILESTONE.match(f.name)}
        for f in files:
            sib = SIBLING.match(f.name)
            if sib:
                if (sib.group(1) or sib.group(2)) not in ids:
                    orphans.append(rel(f))
                continue
            if not MILESTONE.match(f.name):
                continue
            head = f.read_text(errors="replace").splitlines()[:20]
            status = next((l for l in head if re.match(r"^\**status\**\s*:", l, re.I)), None)
            if (head and "✓" in head[0]) or (
                status and re.search(r"\b(done|complete|completed|shipped)\b", status, re.I)
            ):
                finished.append(rel(f))
            elif status is None:
                no_status.append(rel(f))
    return finished, no_status, orphans


def broken_links():
    out = git("ls-files", "-z", "*.md", cwd=SHELL) or ""
    broken = []
    for name in filter(None, out.split("\0")):
        f = SHELL / name
        # Links in a symlinked file resolve against its target; check the target.
        if f.is_symlink() or not f.is_file():
            continue
        fenced = False
        for n, line in enumerate(f.read_text(errors="replace").splitlines(), 1):
            if line.lstrip().startswith("```"):
                fenced = not fenced
            if fenced:
                continue
            for target in LINK.findall(line):
                if re.match(r"^[a-z][a-z0-9+.-]*:", target, re.I) or target.startswith(("#", "/")):
                    continue
                target = unquote(target.split("#", 1)[0])
                if target and not (f.parent / target).exists():
                    broken.append(f"{name}:{n}: {target}")
    for link in sorted(SHELL.glob("docs/*/current_milestone.md")):
        if link.is_symlink() and not link.exists():
            broken.append(f"{rel(link)}: symlink target {os.readlink(link)} is missing")
    return broken


def code_citation_findings():
    found = []
    repos = [(SHELL, True)] + [
        (d, False) for d in sorted(SHELL.glob("pocket-radio-*")) if (d / ".git").exists()
    ]
    for repo, in_shell in repos:
        out = git("grep", "-n", "-I", "-E", CITE_ERE, "--", ".", ":(exclude)*.md", cwd=repo) or ""
        for hit in out.splitlines():
            path, n, text = hit.split(":", 2)
            if exempt(path, in_shell) or not CITE.search(text):
                continue
            prefix = "" if in_shell else f"{repo.name}/"
            found.append(f"{prefix}{path}:{n}: {text.strip()[:90]}")
    return found


def report(strict):
    finished, no_status, orphans = milestone_findings()
    sections = [
        ("Finished milestones still on disk. Close them with close-milestone", finished),
        ("Milestones with no Status line", no_status),
        ("Handoffs or subagent plans whose milestone is gone", orphans),
        ("Broken relative links in shell markdown", broken_links()),
        ("Code citing lifecycle docs. Repoint to an ADR", code_citation_findings()),
    ]
    total = 0
    for title, items in sections:
        if not items:
            continue
        total += len(items)
        print(f"\n{title} ({len(items)}):")
        for item in items:
            print(f"  {item}")
    print(f"\ndocs-check: {total} finding(s)." if total else "docs-check: clean.")
    return 1 if strict and total else 0


if __name__ == "__main__":
    if "--staged" in sys.argv:
        sys.exit(staged())
    sys.exit(report("--strict" in sys.argv))
