"""
ghi: Git Has Issues — agent-first issue tracking in git.

Issues are markdown files stored in .ghi/issues/ and committed
alongside code. No external services, no network, no CLI required.
Agents read and write issues through this library or by editing
the files directly (the format is the spec).

This single file IS the library. When you run ghi.init(), it copies
itself into .ghi/ghi.py so the library travels with the repo. Agents
on any branch get the version of ghi that was current when that
branch was created.

Original ghi by Lorne Liechty (2012). Rewritten for agents (2026).
Licensed under Apache 2.0.

Usage:
    import sys; sys.path.insert(0, '.ghi')
    import ghi

    ghi.open_issue("Title", "Description", "AgentName")
"""

__version__ = "2.0.0"

import os
import re
import uuid
import shutil
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Optional


# ── Data structures ───────────────────────────────────────────


@dataclass
class Comment:
    author: str
    date: str
    text: str


@dataclass
class Issue:
    id: str
    title: str
    status: str
    opened_by: str
    opened_date: str
    labels: list[str]
    description: str
    comments: list[Comment] = field(default_factory=list)


# ── Constants ─────────────────────────────────────────────────


GHI_DIR = ".ghi"
ISSUES_DIR = os.path.join(GHI_DIR, "issues")
CONFIG_FILE = os.path.join(GHI_DIR, "config.yaml")

DEFAULT_CONFIG = """\
# ghi configuration
# Statuses: the lifecycle of an issue (order matters for display)
statuses:
  - open
  - in-progress
  - resolved
  - closed
  - wont-fix

# Labels: freeform tags for categorization
# (agents can use any label; these are suggestions)
labels:
  - kb-staleness
  - bug
  - enhancement
  - question
  - design-debate
"""


# ── Frontmatter parser (no PyYAML dependency) ────────────────


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """Parse YAML frontmatter. Returns (metadata, body)."""
    if not text.startswith("---"):
        raise ValueError("Issue file must start with YAML frontmatter (---)")

    end = text.find("\n---", 3)
    if end == -1:
        raise ValueError("Unterminated frontmatter (missing closing ---)")

    fm_text = text[4:end].strip()
    body = text[end + 4:].strip()

    metadata = {}
    for line in fm_text.split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        colon_pos = line.find(":")
        if colon_pos == -1:
            continue

        key = line[:colon_pos].strip()
        val = line[colon_pos + 1:].strip()

        # Inline list: [item1, item2]
        if val.startswith("[") and val.endswith("]"):
            items = val[1:-1]
            if items.strip():
                metadata[key] = [
                    item.strip().strip('"').strip("'")
                    for item in items.split(",")
                ]
            else:
                metadata[key] = []
        # Quoted string (unescape \" inside)
        elif (val.startswith('"') and val.endswith('"')) or \
             (val.startswith("'") and val.endswith("'")):
            metadata[key] = val[1:-1].replace('\\"', '"').replace("\\'", "'")
        else:
            metadata[key] = val

    return metadata, body


def _serialize_frontmatter(metadata: dict) -> str:
    """Serialize metadata dict to YAML frontmatter."""
    lines = ["---"]
    for key, val in metadata.items():
        if isinstance(val, list):
            items = ", ".join(val)
            lines.append(f"{key}: [{items}]")
        elif '"' in str(val) or (":" in str(val) and not re.match(r'^\d{4}-\d{2}-\d{2}T', str(val))):
            escaped = str(val).replace('"', '\\"')
            lines.append(f'{key}: "{escaped}"')
        else:
            lines.append(f"{key}: {val}")
    lines.append("---")
    return "\n".join(lines)


# ── Comment parser ────────────────────────────────────────────


_COMMENT_MARKER = re.compile(
    r'<!--\s*ghi:comment\s+'
    r'author="([^"]+)"\s+'
    r'date="([^"]+)"\s*'
    r'-->'
)

_COMMENTS_SECTION = re.compile(r'<!--\s*ghi:comments\s*-->')


def _parse_comments(body: str) -> tuple[str, list[Comment]]:
    """Split body into description and comments."""
    match = _COMMENTS_SECTION.search(body)
    if not match:
        return body.strip(), []

    description = body[:match.start()].strip()
    comments_text = body[match.end():]

    comments = []
    parts = _COMMENT_MARKER.split(comments_text)
    # parts: [preamble, author1, date1, text1, author2, date2, text2, ...]
    i = 1
    while i + 2 < len(parts):
        comments.append(Comment(
            author=parts[i],
            date=parts[i + 1],
            text=parts[i + 2].strip(),
        ))
        i += 3

    return description, comments


def _serialize_comments(comments: list[Comment]) -> str:
    """Serialize comments to markdown with markers."""
    if not comments:
        return ""

    lines = ["\n<!-- ghi:comments -->"]
    for c in comments:
        lines.append(f'\n<!-- ghi:comment author="{c.author}" date="{c.date}" -->')
        lines.append(f"\n{c.text}")

    return "\n".join(lines)


# ── Issue serialization ───────────────────────────────────────


def _parse_issue(text: str) -> Issue:
    """Parse a complete issue file into an Issue object."""
    metadata, body = _parse_frontmatter(text)
    description, comments = _parse_comments(body)

    return Issue(
        id=metadata.get("id", ""),
        title=metadata.get("title", ""),
        status=metadata.get("status", "open"),
        opened_by=metadata.get("opened_by", ""),
        opened_date=metadata.get("opened_date", ""),
        labels=metadata.get("labels", []),
        description=description,
        comments=comments,
    )


def _serialize_issue(issue: Issue) -> str:
    """Serialize an Issue object to a complete issue file."""
    metadata = {
        "id": issue.id,
        "title": issue.title,
        "status": issue.status,
        "opened_by": issue.opened_by,
        "opened_date": issue.opened_date,
        "labels": issue.labels,
    }

    parts = [
        _serialize_frontmatter(metadata),
        "",
        issue.description,
        "",
        _serialize_comments(issue.comments),
        "",
    ]

    return "\n".join(parts)


# ── Internal helpers ──────────────────────────────────────────


def _find_ghi_root(start: str = ".") -> str:
    """Walk up from start to find the nearest .ghi directory."""
    current = os.path.abspath(start)
    while True:
        if os.path.isdir(os.path.join(current, GHI_DIR)):
            return current
        parent = os.path.dirname(current)
        if parent == current:
            raise FileNotFoundError(
                "No .ghi directory found. Run ghi.init() first."
            )
        current = parent


def _issues_dir(root: Optional[str] = None) -> str:
    if root is None:
        root = _find_ghi_root()
    return os.path.join(root, ISSUES_DIR)


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _resolve_issue_path(issue_id: str, root: str) -> str:
    """Resolve an issue ID (full or prefix) to a filepath."""
    issues_path = _issues_dir(root)

    exact = os.path.join(issues_path, f"{issue_id}.md")
    if os.path.exists(exact):
        return exact

    matches = [
        f for f in os.listdir(issues_path)
        if f.startswith(issue_id) and f.endswith(".md")
    ]

    if len(matches) == 0:
        raise FileNotFoundError(f"No issue found matching '{issue_id}'")
    if len(matches) > 1:
        raise ValueError(
            f"Ambiguous issue ID '{issue_id}' matches {len(matches)} issues. "
            f"Use a longer prefix."
        )

    return os.path.join(issues_path, matches[0])


def _read_from_path(filepath: str) -> Issue:
    with open(filepath, "r") as f:
        return _parse_issue(f.read())


# ── Public API ────────────────────────────────────────────────


def init(path: str = ".") -> str:
    """Initialize a .ghi directory in the given path.

    Creates the directory structure and copies this library file
    and the format spec into .ghi/ so the tracker is self-contained.

    Returns the path to the created .ghi directory.
    Idempotent — safe to call if .ghi already exists.
    """
    ghi_path = os.path.join(os.path.abspath(path), GHI_DIR)
    issues_path = os.path.join(ghi_path, "issues")

    os.makedirs(issues_path, exist_ok=True)

    # Write default config if absent
    config_path = os.path.join(ghi_path, "config.yaml")
    if not os.path.exists(config_path):
        with open(config_path, "w") as f:
            f.write(DEFAULT_CONFIG)

    # Copy this library file into .ghi/ so it travels with the repo
    this_file = os.path.abspath(__file__)
    dest_lib = os.path.join(ghi_path, "ghi.py")
    if os.path.abspath(dest_lib) != this_file:
        shutil.copy2(this_file, dest_lib)

    # Copy FORMAT.md if it exists alongside this file
    format_src = os.path.join(os.path.dirname(this_file), "FORMAT.md")
    format_dest = os.path.join(ghi_path, "FORMAT.md")
    if os.path.exists(format_src) and not os.path.exists(format_dest):
        shutil.copy2(format_src, format_dest)

    # Ensure issues dir exists in git
    gitkeep = os.path.join(issues_path, ".gitkeep")
    if not os.path.exists(gitkeep):
        with open(gitkeep, "w") as f:
            pass

    return ghi_path


def open_issue(
    title: str,
    description: str,
    author: str,
    labels: Optional[list[str]] = None,
    root: Optional[str] = None,
) -> Issue:
    """Create a new issue. Returns the Issue object.

    Args:
        title: Short summary (one line).
        description: Full description (markdown). The author
            owns this section and may refine it later.
        author: Name of the agent or person opening the issue.
        labels: Optional list of labels/tags.
        root: Repo root (auto-detected if None).
    """
    if root is None:
        root = _find_ghi_root()

    issue = Issue(
        id=str(uuid.uuid4()),
        title=title.strip(),
        status="open",
        opened_by=author,
        opened_date=_now_iso(),
        labels=labels or [],
        description=description.strip(),
        comments=[],
    )

    filepath = os.path.join(_issues_dir(root), f"{issue.id}.md")
    with open(filepath, "w") as f:
        f.write(_serialize_issue(issue))

    return issue


def comment(
    issue_id: str,
    author: str,
    text: str,
    root: Optional[str] = None,
) -> Comment:
    """Append a comment to an existing issue.

    Comments are append-only. You cannot edit or delete another
    agent's comments. This is convention, not enforcement —
    management between mutually consenting adults.
    """
    if root is None:
        root = _find_ghi_root()

    filepath = _resolve_issue_path(issue_id, root)
    issue = _read_from_path(filepath)

    new_comment = Comment(author=author, date=_now_iso(), text=text.strip())
    issue.comments.append(new_comment)

    with open(filepath, "w") as f:
        f.write(_serialize_issue(issue))

    return new_comment


def update_status(
    issue_id: str,
    new_status: str,
    author: str,
    reason: str,
    root: Optional[str] = None,
) -> Issue:
    """Change an issue's status. Adds an audit comment."""
    if root is None:
        root = _find_ghi_root()

    filepath = _resolve_issue_path(issue_id, root)
    issue = _read_from_path(filepath)

    old_status = issue.status
    issue.status = new_status

    issue.comments.append(Comment(
        author=author,
        date=_now_iso(),
        text=f"**Status changed:** {old_status} → {new_status}\n\n{reason.strip()}",
    ))

    with open(filepath, "w") as f:
        f.write(_serialize_issue(issue))

    return issue


def update_description(
    issue_id: str,
    author: str,
    new_description: str,
    root: Optional[str] = None,
) -> Issue:
    """Update an issue's description. By convention, only the
    original opener should do this — but this is not enforced."""
    if root is None:
        root = _find_ghi_root()

    filepath = _resolve_issue_path(issue_id, root)
    issue = _read_from_path(filepath)

    issue.description = new_description.strip()
    issue.comments.append(Comment(
        author=author,
        date=_now_iso(),
        text="*Description updated by author.*",
    ))

    with open(filepath, "w") as f:
        f.write(_serialize_issue(issue))

    return issue


def read_issue(
    issue_id: str,
    root: Optional[str] = None,
) -> Issue:
    """Read a single issue by ID (full UUID or unambiguous prefix)."""
    if root is None:
        root = _find_ghi_root()
    return _read_from_path(_resolve_issue_path(issue_id, root))


def list_issues(
    status: Optional[str] = None,
    label: Optional[str] = None,
    root: Optional[str] = None,
) -> list[Issue]:
    """List all issues, optionally filtered. Newest first."""
    if root is None:
        root = _find_ghi_root()

    issues_path = _issues_dir(root)
    results = []

    if not os.path.isdir(issues_path):
        return results

    for filename in os.listdir(issues_path):
        if not filename.endswith(".md"):
            continue
        try:
            issue = _read_from_path(os.path.join(issues_path, filename))
        except Exception:
            continue

        if status and issue.status != status:
            continue
        if label and label not in issue.labels:
            continue

        results.append(issue)

    results.sort(key=lambda i: i.opened_date, reverse=True)
    return results


def find_issues(
    query: str,
    root: Optional[str] = None,
) -> list[Issue]:
    """Search issues by text match in title, description, comments.

    Case-insensitive. Title matches rank highest.
    """
    if root is None:
        root = _find_ghi_root()

    query_lower = query.lower()
    scored = []

    for issue in list_issues(root=root):
        score = 0
        if query_lower in issue.title.lower():
            score += 3
        if query_lower in issue.description.lower():
            score += 2
        for c in issue.comments:
            if query_lower in c.text.lower():
                score += 1
        if score > 0:
            scored.append((score, issue))

    scored.sort(key=lambda x: (-x[0], x[1].opened_date))
    return [issue for _, issue in scored]
