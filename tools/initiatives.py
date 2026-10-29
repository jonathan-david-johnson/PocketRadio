#!/usr/bin/env python3
"""
initiatives.py — print the live facts behind docs/INITIATIVES.md.

For every platform under docs/: the current milestone and its Status line, the
open bug docs, and the nested repo's branch, worktrees, uncommitted files and
commits that are on a side branch but not on the base branch. It also counts
the finished milestones that are still on disk.

It reads files and runs read-only git commands. It changes nothing.

Usage:
    python3 tools/initiatives.py            # full report
    python3 tools/initiatives.py --short    # one line per platform
"""
import argparse, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# docs/<platform> -> nested repo directory (the main checkout)
REPOS = {
    "ios": "pocket-radio-ios", "menubar": "pocket-radio-menubar", "web": "pocket-radio-web",
    "console": "pocket-radio-console", "roku": "pocket-radio-roku", "android": "pocket-radio-android",
}


def git(repo, *args):
    try:
        return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True, timeout=20).stdout.strip()
    except Exception:
        return ""


def first_status(path):
    try:
        text = open(path, encoding="utf-8").read()
    except OSError:
        return "(unreadable)"
    m = re.search(r"^\*\*Status:?\*\*:?\s*(.+)$", text, re.M)
    if not m:
        return "(no Status line)"
    s = m.group(1).strip()
    return s if len(s) <= 150 else s[:147] + "..."


def bug_states(platform):
    d = os.path.join(ROOT, "docs", platform, "bugs")
    out = []
    if not os.path.isdir(d):
        return out
    for f in sorted(os.listdir(d)):
        if not f.endswith(".md"):
            continue
        text = open(os.path.join(d, f), encoding="utf-8").read()
        m = re.search(r"^\*\*Status:?\*\*:?\s*(\w+)", text, re.M)
        out.append((f[:-3], m.group(1) if m else "?"))
    return out


def repo_report(platform):
    repo = os.path.join(ROOT, REPOS.get(platform, ""))
    if not os.path.isdir(os.path.join(repo, ".git")) and not os.path.isfile(os.path.join(repo, ".git")):
        return None
    branch = git(repo, "branch", "--show-current")
    dirty = [l for l in git(repo, "status", "--short").splitlines() if l.strip()]
    trees = []
    for blk in git(repo, "worktree", "list", "--porcelain").split("\n\n"):
        p = re.search(r"^worktree (.+)$", blk, re.M); b = re.search(r"^branch refs/heads/(.+)$", blk, re.M)
        if p:
            trees.append((os.path.relpath(p.group(1), ROOT), b.group(1) if b else "(detached)"))
    ahead = []
    for _, b in trees:
        if b != branch and b != "(detached)":
            n = git(repo, "rev-list", "--count", f"{branch}..{b}")
            if n.isdigit() and int(n) > 0:
                ahead.append((b, int(n)))
    return {"branch": branch, "dirty": dirty, "worktrees": trees, "ahead": ahead}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--short", action="store_true")
    args = ap.parse_args()
    docs = os.path.join(ROOT, "docs")
    for platform in sorted(p for p in os.listdir(docs) if os.path.isdir(os.path.join(docs, p)) and p not in ("__pycache__",)):
        link = os.path.join(docs, platform, "current_milestone.md")
        cur = os.readlink(link) if os.path.islink(link) else None
        rep = repo_report(platform)
        bugs = bug_states(platform)
        open_bugs = [b for b, s in bugs if s.lower().startswith("open")]
        if args.short:
            print(f"{platform:9} current={cur or '-':32} branch={(rep or {}).get('branch','-'):14} dirty={len((rep or {}).get('dirty',[])):2} open_bugs={len(open_bugs)}")
            continue
        print(f"== {platform}")
        if cur:
            print(f"   current milestone: {cur}")
            print(f"   status: {first_status(os.path.join(docs, platform, cur))}")
        else:
            print("   current milestone: (none)")
        if rep:
            print(f"   repo branch: {rep['branch']}; uncommitted files: {len(rep['dirty'])}")
            for rel, b in rep["worktrees"]:
                print(f"   worktree: {rel}  [{b}]")
            for b, n in rep["ahead"]:
                print(f"   {n} commit(s) on {b} not on {rep['branch']}")
        if bugs:
            print(f"   bug docs: {len(bugs)}; open: {', '.join(open_bugs) or 'none'}")
    chk = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "docs_check.py")], capture_output=True, text=True)
    m = re.search(r"Finished milestones still on disk[^\n]*\((\d+)\)", chk.stdout + chk.stderr)
    print(f"\nfinished milestones still on disk: {m.group(1) if m else 'unknown'}")


if __name__ == "__main__":
    main()
