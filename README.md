# ghi: Git Has Issues

An agent-first issue tracker that stores issues as markdown files inside your git repository. No external services, no network, no databases. Issues are committed alongside code and travel with the repo.

Originally created by [Lorne Liechty](https://github.com/lorneliechty/ghi) in 2012 as a CLI tool for developers. Rewritten in 2026 for AI agent collaboration — where the "interface" is the file format itself, and the "CLI" is a thin Python library that agents import directly.

## Why

Multi-agent systems need a way to debate. When Agent A discovers that a documented pattern no longer works, it needs to say so in a place where Agent B (running days later) can see the report, add evidence, and help resolve it. KB files aren't the right place for that — they're reference material, not discussions. Issues are discussions.

ghi stores those discussions in `.ghi/issues/` as readable markdown files, committed to git. No infrastructure required. Issues branch with the code, merge with the code, and provide a complete audit trail through git history.

## What's in This Repo

| File | Version | Purpose |
|------|---------|---------|
| `ghi.py` | 2.4.0 | Python library — full API, analytics (`stale()`, `metrics()`), self-deploys via `ghi.init()` |
| `ghi.sh` | 2.5.0 | Bash CLI wrapper — zero-Python writes and reads for agents. 85.7% boilerplate reduction. |
| `generate_board.py` | 2.5.0 | BOARD.md generator — manager runs once per cycle; agents `cat BOARD.md` instead of calling `summary()`. 75% read boilerplate reduction. |

See [CHANGELOG.md](CHANGELOG.md) for full version history.

## Architecture

ghi is a **single Python file** (`ghi.py`) that self-deploys. When you run `ghi.init()`, it copies itself (and the shell tools) into the repo's `.ghi/` directory:

```
.ghi/
  ghi.py           ← the Python library (self-deployed)
  FORMAT.md        ← format specification
  config.yaml      ← repo-level settings
  issues/
    <uuid>.md      ← one file per issue

ghi.sh             ← bash CLI (in repo root after init)
generate_board.py  ← board generator (in repo root after init)
BOARD.md           ← regenerated each cycle by manager
```

The library travels with the repo. An agent on any branch gets the version of ghi that was current when that branch was created. Improvements merge forward through normal git operations.

## Quick Start

### Setup

```bash
# Seed a new project repo (run from a clone of your project)
python3 -c "import sys; sys.path.insert(0, '/path/to/ghi'); import ghi; ghi.init()"
# This creates .ghi/, copies ghi.py, and adds ghi.sh + generate_board.py to the repo root
```

### v2.5.0 Hybrid Usage (recommended)

```bash
# Manager: regenerate board at cycle start
python3 generate_board.py --no-done --with-comments 2

# All agents: orient
cat BOARD.md
./ghi.sh read <id8>              # read full issue thread

# All agents: write
./ghi.sh open "Title" --priority high --assigned Name
./ghi.sh comment <id8> --author Name "text"
./ghi.sh close <id8> --author Name --comment "Done."

# Manager: analytics (Python, once per cycle)
python3 -c "import sys; sys.path.insert(0, '.ghi'); import ghi; print(ghi.stale(days=3)); print(ghi.metrics())"
```

### Python API (v2.4.0)

```python
# Import from the deployed copy
import sys; sys.path.insert(0, '.ghi')
import ghi

# Open an issue
issue = ghi.open_issue(
    title="kb/agents.md mount pattern outdated",
    description="The documented mount-and-clone pattern fails when...",
    author="Lidia",
    labels=["kb-staleness"],
)

# Add a comment
ghi.comment(issue.id, "Wiktor", "Investigated. The pattern is valid but...")

# Change status
ghi.update_status(issue.id, "resolved", "Wiktor",
    "Added troubleshooting note in commit 26ded11.")

# List open issues
for issue in ghi.list_issues(status="open"):
    print(f"[{issue.id[:8]}] {issue.title}")

# Search
results = ghi.find_issues("mount")
```

## The File Format

Issues are markdown with YAML frontmatter and HTML-comment delimiters for comments. The format is designed to be readable as plain markdown while being machine-parseable:

```markdown
---
id: f80738a3-2ae8-4c0e-a7eb-42e0fba2ca85
title: kb/agents.md mount pattern outdated
status: resolved
opened_by: Lidia
opened_date: 2026-03-12T00:00:00Z
labels: [kb-staleness]
---

The documented mount-and-clone pattern fails when the bare repo
has stale lock files from the nightly maintainer.

<!-- ghi:comments -->

<!-- ghi:comment author="Wiktor" date="2026-03-12T15:30:00Z" -->

Investigated. The pattern is valid but the KB needs a
troubleshooting note about lock files.

<!-- ghi:comment author="Wiktor" date="2026-03-13T09:00:00Z" -->

**Status changed:** open → resolved

Added troubleshooting note in commit 26ded11.
```

The HTML comment markers (`<!-- ghi:comment ... -->`) are invisible in rendered markdown, so the file reads as clean prose with clear authorship.

See [FORMAT.md](FORMAT.md) for the full specification.

## Conventions

**Management between mutually consenting adults.** There's no access control. The conventions are:

1. **Only the opener edits the Description.** Others contribute through comments.
2. **Comments are append-only.** Add yours at the bottom. Never edit or delete someone else's.
3. **Status changes are documented.** Every status transition gets an automatic comment explaining why.
4. **Issues are for cross-session concerns.** Not for session-specific notes or project-specific bugs.

These aren't enforced by code. They're enforced by the format making the right thing obvious and the wrong thing feel weird — the same way `branch-per-agent` works in the toolkit without any enforcement mechanism.

## API Reference

| Function | Purpose |
|----------|---------|
| `ghi.init(path=".")` | Initialize `.ghi/` directory |
| `ghi.open_issue(title, description, author, labels=[], root=None)` | Create a new issue |
| `ghi.comment(issue_id, author, text, root=None)` | Append a comment |
| `ghi.update_status(issue_id, new_status, author, reason, root=None)` | Change status (adds audit comment) |
| `ghi.update_description(issue_id, author, new_description, root=None)` | Update description (adds audit comment) |
| `ghi.read_issue(issue_id, root=None)` | Read a single issue |
| `ghi.list_issues(status=None, label=None, root=None)` | List issues with optional filters |
| `ghi.find_issues(query, root=None)` | Search by text match |

All `issue_id` parameters accept full UUIDs or unambiguous prefixes.

## Dependencies

Python 3.10+. No external packages.

## License

Apache License 2.0 — same as the original ghi.
