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

__version__ = "2.5.0"

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
    assigned_to: Optional[str] = None
    priority: Optional[str] = None
    refs: list[str] = field(default_factory=list)
    closed_date: Optional[str] = None  # Set automatically when status → terminal


# ── Constants ─────────────────────────────────────────────────


GHI_DIR = ".ghi"
ISSUES_DIR = os.path.join(GHI_DIR, "issues")
CONFIG_FILE = os.path.join(GHI_DIR, "config.yaml")

VALID_PRIORITIES = ["critical", "high", "medium", "low"]

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
        if val is None:
            continue  # Skip None fields entirely
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

    # Parse refs — stored as list, default to empty
    refs_raw = metadata.get("refs", [])
    if isinstance(refs_raw, str):
        refs_raw = [refs_raw] if refs_raw else []

    return Issue(
        id=metadata.get("id", ""),
        title=metadata.get("title", ""),
        status=metadata.get("status", "open"),
        opened_by=metadata.get("opened_by", ""),
        opened_date=metadata.get("opened_date", ""),
        labels=metadata.get("labels", []),
        description=description,
        comments=comments,
        assigned_to=metadata.get("assigned_to") or None,
        priority=metadata.get("priority") or None,
        refs=refs_raw,
        closed_date=metadata.get("closed_date") or None,
    )


def _serialize_issue(issue: Issue) -> str:
    """Serialize an Issue object to a complete issue file."""
    metadata = {
        "id": issue.id,
        "title": issue.title,
        "status": issue.status,
        "opened_by": issue.opened_by,
        "opened_date": issue.opened_date,
        "closed_date": issue.closed_date,
        "labels": issue.labels,
        "assigned_to": issue.assigned_to,
        "priority": issue.priority,
        "refs": issue.refs if issue.refs else None,
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


def _time_ago(iso_date: str) -> str:
    """Return a human-readable relative time: '5m ago', '3h ago', 'Mar 10'."""
    try:
        then = datetime.fromisoformat(iso_date.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        seconds = int((now - then).total_seconds())
        if seconds < 60:
            return "just now"
        elif seconds < 3600:
            return f"{seconds // 60}m ago"
        elif seconds < 86400:
            return f"{seconds // 3600}h ago"
        elif seconds < 7 * 86400:
            return f"{seconds // 86400}d ago"
        else:
            return then.strftime("%b %d")
    except Exception:
        return ""


# Statuses that mean an issue is resolved; used to set closed_date
_TERMINAL_STATUSES = frozenset([
    "closed", "resolved", "wont-fix", "done", "complete", "shipped",
])


def _ensure_root_gitignore(path: str) -> None:
    """Create or update root-level .gitignore with Python bytecode patterns.

    Safe to call on repos that already have a .gitignore — only adds
    missing lines, never removes anything.
    """
    gitignore_path = os.path.join(path, ".gitignore")
    patterns = ["__pycache__/", "*.pyc", "*.pyo"]

    existing = ""
    if os.path.exists(gitignore_path):
        with open(gitignore_path, "r") as f:
            existing = f.read()

    missing = [p for p in patterns if p not in existing]
    if missing:
        with open(gitignore_path, "a") as f:
            if existing and not existing.endswith("\n"):
                f.write("\n")
            f.write("# Python bytecode (managed by ghi.init)\n")
            f.write("\n".join(missing) + "\n")


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

    # Copy v2.5.0 shell tools to the repo root so agents can use them directly.
    # ghi.sh and generate_board.py live alongside ghi.py in the source repo.
    # They are copied to the project root (not .ghi/) since they're meant to be
    # called as ./ghi.sh and python3 generate_board.py from the working directory.
    src_dir = os.path.dirname(this_file)
    repo_root = os.path.abspath(path)
    for shell_tool in ("ghi.sh", "generate_board.py"):
        src = os.path.join(src_dir, shell_tool)
        dest = os.path.join(repo_root, shell_tool)
        if os.path.exists(src) and not os.path.exists(dest):
            shutil.copy2(src, dest)
            if shell_tool.endswith(".sh"):
                os.chmod(dest, 0o755)

    # Ensure issues dir exists in git
    gitkeep = os.path.join(issues_path, ".gitkeep")
    if not os.path.exists(gitkeep):
        with open(gitkeep, "w") as f:
            pass

    # Exclude Python bytecode from .ghi/ itself
    gitignore = os.path.join(ghi_path, ".gitignore")
    if not os.path.exists(gitignore):
        with open(gitignore, "w") as f:
            f.write("__pycache__/\n*.pyc\n*.pyo\n")

    # Also protect the repo root — agents run Python there too, and
    # .ghi/.gitignore only covers the .ghi/ subdirectory
    _ensure_root_gitignore(os.path.abspath(path))

    return ghi_path


def open_issue(
    title: str,
    description: str,
    author: str,
    labels: Optional[list[str]] = None,
    assigned_to: Optional[str] = None,
    priority: Optional[str] = None,
    refs: Optional[list[str]] = None,
    root: Optional[str] = None,
) -> Issue:
    """Create a new issue. Returns the Issue object.

    Args:
        title: Short summary (one line).
        description: Full description (markdown). The author
            owns this section and may refine it later.
        author: Name of the agent or person opening the issue.
        labels: Optional list of labels/tags.
        assigned_to: Optional agent name who should work on this.
        priority: Optional priority level (critical/high/medium/low).
        refs: Optional list of related issue IDs (cross-references).
        root: Repo root (auto-detected if None).
    """
    if root is None:
        root = _find_ghi_root()

    if priority and priority not in VALID_PRIORITIES:
        raise ValueError(
            f"Invalid priority '{priority}'. "
            f"Must be one of: {', '.join(VALID_PRIORITIES)}"
        )

    issue = Issue(
        id=str(uuid.uuid4()),
        title=title.strip(),
        status="open",
        opened_by=author,
        opened_date=_now_iso(),
        labels=labels or [],
        description=description.strip(),
        comments=[],
        assigned_to=assigned_to,
        priority=priority,
        refs=refs or [],
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
    if hasattr(issue_id, 'id'):
        issue_id = issue_id.id
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

    # Record when the issue first reaches a terminal status
    if new_status in _TERMINAL_STATUSES and issue.closed_date is None:
        issue.closed_date = _now_iso()
    # Clear closed_date if explicitly reopened
    elif new_status not in _TERMINAL_STATUSES:
        issue.closed_date = None

    issue.comments.append(Comment(
        author=author,
        date=_now_iso(),
        text=f"**Status changed:** {old_status} → {new_status}\n\n{reason.strip()}",
    ))

    with open(filepath, "w") as f:
        f.write(_serialize_issue(issue))

    return issue


def assign(
    issue_id: str,
    assignee: str,
    author: str,
    root: Optional[str] = None,
) -> Issue:
    """Assign an issue to an agent. Adds an audit comment."""
    if root is None:
        root = _find_ghi_root()

    filepath = _resolve_issue_path(issue_id, root)
    issue = _read_from_path(filepath)

    old_assignee = issue.assigned_to or "unassigned"
    issue.assigned_to = assignee

    issue.comments.append(Comment(
        author=author,
        date=_now_iso(),
        text=f"**Assigned:** {old_assignee} → {assignee}",
    ))

    with open(filepath, "w") as f:
        f.write(_serialize_issue(issue))

    return issue


def set_priority(
    issue_id: str,
    priority: str,
    author: str,
    root: Optional[str] = None,
) -> Issue:
    """Set or change an issue's priority. Adds an audit comment."""
    if root is None:
        root = _find_ghi_root()

    if priority not in VALID_PRIORITIES:
        raise ValueError(
            f"Invalid priority '{priority}'. "
            f"Must be one of: {', '.join(VALID_PRIORITIES)}"
        )

    filepath = _resolve_issue_path(issue_id, root)
    issue = _read_from_path(filepath)

    old_priority = issue.priority or "unset"
    issue.priority = priority

    issue.comments.append(Comment(
        author=author,
        date=_now_iso(),
        text=f"**Priority changed:** {old_priority} → {priority}",
    ))

    with open(filepath, "w") as f:
        f.write(_serialize_issue(issue))

    return issue


def add_ref(
    issue_id: str,
    ref_issue_id: str,
    author: str,
    root: Optional[str] = None,
) -> Issue:
    """Add a cross-reference to another issue. Adds audit comment.

    Both issue_id and ref_issue_id should be strings (full UUID or
    prefix). If you have an Issue object, pass issue.id instead.
    """
    if root is None:
        root = _find_ghi_root()

    # Handle common mistake: passing Issue object instead of string
    if hasattr(issue_id, 'id'):
        issue_id = issue_id.id
    if hasattr(ref_issue_id, 'id'):
        ref_issue_id = ref_issue_id.id

    filepath = _resolve_issue_path(issue_id, root)
    issue = _read_from_path(filepath)

    # Resolve the ref to its full ID
    ref_path = _resolve_issue_path(ref_issue_id, root)
    ref_full_id = os.path.basename(ref_path).replace(".md", "")

    if ref_full_id not in issue.refs:
        issue.refs.append(ref_full_id)
        issue.comments.append(Comment(
            author=author,
            date=_now_iso(),
            text=f"**Linked:** → {ref_full_id[:8]}",
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
    status=None,
    label: Optional[str] = None,
    assigned_to: Optional[str] = None,
    priority: Optional[str] = None,
    opened_by: Optional[str] = None,
    root: Optional[str] = None,
) -> list[Issue]:
    """List all issues, optionally filtered. Newest first.

    All filters are ANDed — an issue must match every specified
    filter to be included.

    Args:
        status: Filter by status. Accepts a single string ("open") or
            a list of strings (["open", "in-progress"]) to match any.
            The special value "active" expands to ["open", "in-progress"].
        label: Filter by label (issue must have this label).
        assigned_to: Filter by assignee name.
        priority: Filter by priority level.
        opened_by: Filter by who opened the issue.
        root: Repo root (auto-detected if None).
    """
    if root is None:
        root = _find_ghi_root()

    # Normalize status to a set (or None for no filter)
    if status is None:
        status_filter = None
    elif status == "active":
        status_filter = {"open", "in-progress"}
    elif isinstance(status, list):
        status_filter = set(status)
    else:
        status_filter = {status}

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

        if status_filter is not None and issue.status not in status_filter:
            continue
        if label and label not in issue.labels:
            continue
        if assigned_to and issue.assigned_to != assigned_to:
            continue
        if priority and issue.priority != priority:
            continue
        if opened_by and issue.opened_by != opened_by:
            continue

        results.append(issue)

    results.sort(key=lambda i: i.opened_date, reverse=True)
    return results


def find_issues(
    query: str,
    title_only: bool = False,
    status: Optional[str] = None,
    assigned_to: Optional[str] = None,
    opened_by: Optional[str] = None,
    root: Optional[str] = None,
) -> list[Issue]:
    """Search issues by text match. Case-insensitive. Title matches
    rank highest.

    Args:
        query: Text to search for.
        title_only: If True, only search in issue titles.
        status: Optional filter — only search issues with this status.
        assigned_to: Optional filter — only search issues assigned to this name.
        opened_by: Optional filter — only search issues opened by this name.
        root: Repo root (auto-detected if None).
    """
    if root is None:
        root = _find_ghi_root()

    query_lower = query.lower()
    scored = []

    base_issues = list_issues(
        status=status,
        assigned_to=assigned_to,
        opened_by=opened_by,
        root=root,
    )

    for issue in base_issues:
        score = 0
        if query_lower in issue.title.lower():
            score += 3
        if not title_only:
            if query_lower in issue.description.lower():
                score += 2
            for c in issue.comments:
                if query_lower in c.text.lower():
                    score += 1
        if score > 0:
            scored.append((score, issue))

    scored.sort(key=lambda x: (-x[0], x[1].opened_date))
    return [issue for _, issue in scored]


def count_issues(root: Optional[str] = None) -> dict:
    """Return a dict of issue counts grouped by status.

    Example return: {"open": 3, "closed": 5, "in-progress": 1, "_total": 9}
    """
    if root is None:
        root = _find_ghi_root()

    counts: dict[str, int] = {}
    for issue in list_issues(root=root):
        counts[issue.status] = counts.get(issue.status, 0) + 1
    counts["_total"] = sum(counts.values())
    return counts


def stale(days: int = 7, root: Optional[str] = None) -> list[Issue]:
    """Return non-terminal issues with no activity for more than `days` days.

    'Activity' means any comment. Issues with no comments are judged
    by their opened_date. Terminal issues (closed, resolved, etc.) are
    always excluded — only open/in-progress/custom-active issues are
    considered.

    Results are sorted oldest-activity-first so the most neglected
    issues surface at the top.

    Args:
        days: Minimum days of inactivity to be considered stale.
        root: Repo root (auto-detected if None).

    Example:
        for issue in ghi.stale(days=3):
            print(issue.title, '— last activity:', issue.comments[-1].date
                  if issue.comments else issue.opened_date)
    """
    if root is None:
        root = _find_ghi_root()

    now = datetime.now(timezone.utc)
    cutoff_ts = now.timestamp() - days * 86400

    results = []
    for issue in list_issues(root=root):
        # Skip terminal issues
        if issue.status in _TERMINAL_STATUSES:
            continue

        # Activity date = last comment date, or opened_date if no comments
        if issue.comments:
            activity_date = issue.comments[-1].date
        else:
            activity_date = issue.opened_date

        try:
            activity_ts = datetime.fromisoformat(
                activity_date.replace("Z", "+00:00")
            ).timestamp()
        except Exception:
            continue

        if activity_ts < cutoff_ts:
            results.append(issue)

    # Oldest activity first — most neglected at the top
    results.sort(key=lambda i: (
        i.comments[-1].date if i.comments else i.opened_date
    ))
    return results


def metrics(root: Optional[str] = None) -> dict:
    """Return tracker-level metrics for the issue set.

    Returns a dict with:
        total            — total issue count
        open             — count with an active status (open or in-progress)
        done             — count with a terminal status
        by_status        — {status: count} for every distinct status
        open_by_priority — {priority: count} for open/in-progress issues
                           (priority None → "unset")
        by_assignee      — {assignee: count} for open/in-progress issues
                           (unassigned → "unassigned")
        stale_count      — open issues with no activity for 7+ days
        velocity         — issues closed per day over the last 7 days
                           (closed_last_7d / 7, rounded to 2 decimal places)
        cycle_time_avg   — mean days from opened_date → closed_date
                           (None when no closed issues have closed_date)
        cycle_time_p50   — median days (None when no data)
        closed_last_7d   — issues with closed_date in the last 7 days
        closed_last_30d  — issues with closed_date in the last 30 days

    Cycle time is only computed for issues where closed_date was recorded
    automatically by update_status() (v2.3.0+). Older issues show None.
    Velocity is always computable and is the more useful signal in
    short-burst projects where cycle_time_avg approaches zero.
    """
    if root is None:
        root = _find_ghi_root()

    all_issues = list_issues(root=root)

    active_statuses = {"open", "in-progress"}
    by_status: dict[str, int] = {}
    open_count = 0
    done_count = 0
    open_by_priority: dict[str, int] = {}
    by_assignee: dict[str, int] = {}
    cycle_times: list[float] = []
    closed_7d = 0
    closed_30d = 0

    now = datetime.now(timezone.utc)
    cutoff_7d  = now.timestamp() - 7  * 86400
    cutoff_30d = now.timestamp() - 30 * 86400
    stale_cutoff = now.timestamp() - 7 * 86400
    stale_count = 0

    for issue in all_issues:
        by_status[issue.status] = by_status.get(issue.status, 0) + 1

        is_active = issue.status in active_statuses
        if is_active:
            open_count += 1
            pri_key = issue.priority or "unset"
            open_by_priority[pri_key] = open_by_priority.get(pri_key, 0) + 1

            assignee_key = issue.assigned_to or "unassigned"
            by_assignee[assignee_key] = by_assignee.get(assignee_key, 0) + 1

            # Stale check: last activity older than 7 days
            activity_date = (
                issue.comments[-1].date if issue.comments else issue.opened_date
            )
            try:
                activity_ts = datetime.fromisoformat(
                    activity_date.replace("Z", "+00:00")
                ).timestamp()
                if activity_ts < stale_cutoff:
                    stale_count += 1
            except Exception:
                pass
        else:
            done_count += 1

        if issue.closed_date:
            try:
                closed_ts = datetime.fromisoformat(
                    issue.closed_date.replace("Z", "+00:00")
                ).timestamp()
                if closed_ts >= cutoff_7d:
                    closed_7d += 1
                if closed_ts >= cutoff_30d:
                    closed_30d += 1

                opened_ts = datetime.fromisoformat(
                    issue.opened_date.replace("Z", "+00:00")
                ).timestamp()
                cycle_days = (closed_ts - opened_ts) / 86400
                if cycle_days >= 0:
                    cycle_times.append(cycle_days)
            except Exception:
                pass

    if cycle_times:
        cycle_times.sort()
        avg = sum(cycle_times) / len(cycle_times)
        mid = len(cycle_times) // 2
        if len(cycle_times) % 2 == 0:
            p50 = (cycle_times[mid - 1] + cycle_times[mid]) / 2
        else:
            p50 = cycle_times[mid]
        cycle_time_avg = round(avg, 2)
        cycle_time_p50 = round(p50, 2)
    else:
        cycle_time_avg = None
        cycle_time_p50 = None

    velocity = round(closed_7d / 7.0, 2)

    return {
        "total": len(all_issues),
        "open": open_count,
        "done": done_count,
        "by_status": by_status,
        "open_by_priority": open_by_priority,
        "by_assignee": by_assignee,
        "stale_count": stale_count,
        "velocity": velocity,
        "cycle_time_avg": cycle_time_avg,
        "cycle_time_p50": cycle_time_p50,
        "closed_last_7d": closed_7d,
        "closed_last_30d": closed_30d,
    }


def bulk_update_status(
    issue_ids: list[str],
    new_status: str,
    author: str,
    reason: str,
    root: Optional[str] = None,
) -> list[Issue]:
    """Change the status of multiple issues at once.

    Convenience wrapper around update_status() for closing/resolving
    batches of issues without N separate calls.

    Args:
        issue_ids: List of issue IDs (full UUIDs or prefixes).
            Also accepts Issue objects.
        new_status: The new status to set on all issues.
        author: Name of the agent making the change.
        reason: Reason for the status change (shared across all).
        root: Repo root (auto-detected if None).

    Returns:
        List of updated Issue objects.
    """
    if root is None:
        root = _find_ghi_root()

    results = []
    for issue_id in issue_ids:
        if hasattr(issue_id, 'id'):
            issue_id = issue_id.id
        results.append(update_status(issue_id, new_status, author, reason, root=root))

    return results


def summary(
    root: Optional[str] = None,
    show_done: bool = True,
    limit_done: Optional[int] = None,
    assigned_to: Optional[str] = None,
) -> str:
    """Return a compact text dashboard of all issues.

    Groups by status, shows priority and assignment, sorted by
    priority within each group. Designed for agents to quickly
    get the lay of the land.

    Args:
        show_done: If False, skip terminal (done/closed/resolved) issues
            entirely. Useful when you only care about active work.
        limit_done: If set, show at most this many terminal issues per
            status group. A "... N more" line is appended when truncated.
            Ignored when show_done=False.
        assigned_to: If set, only show issues assigned to this agent name.
            Active issues without this assignee are hidden; done issues
            are always filtered when this is set.
        root: Repo root (auto-detected if None).
    """
    if root is None:
        root = _find_ghi_root()

    all_issues = list_issues(root=root)

    if not all_issues:
        return "No issues found."

    # Group by status
    active_statuses = ["open", "in-progress"]
    terminal_statuses = ["resolved", "closed", "wont-fix", "done", "complete", "shipped"]
    grouped: dict[str, list[Issue]] = {}
    for issue in all_issues:
        grouped.setdefault(issue.status, []).append(issue)

    # Priority sort order (critical first, unset last)
    priority_rank = {"critical": 0, "high": 1, "medium": 2, "low": 3}

    # Count active vs terminal across the full (unfiltered) set
    active_count = sum(
        len(grouped.get(s, []))
        for s in grouped
        if s not in _TERMINAL_STATUSES
    )
    terminal_count = len(all_issues) - active_count

    lines = []
    total = len(all_issues)
    header = f"ghi: {total} issues ({active_count} active, {terminal_count} done)"
    if assigned_to:
        header += f" — showing @{assigned_to}"
    lines.append(header)
    lines.append("=" * 60)

    def _fmt_issue(issue: Issue) -> str:
        pri = f" !{issue.priority}" if issue.priority else ""
        assign = f" @{issue.assigned_to}" if issue.assigned_to else ""
        refs_str = f" refs:{len(issue.refs)}" if issue.refs else ""
        if issue.comments:
            age = _time_ago(issue.comments[-1].date)
            comments_str = f" ({len(issue.comments)}c, {age})" if age else f" ({len(issue.comments)}c)"
        else:
            # For issues with no comments, show how long they've been open
            age = _time_ago(issue.opened_date)
            comments_str = f" (opened {age})" if age else ""
        labels_str = f" [{', '.join(issue.labels)}]" if issue.labels else ""
        return (
            f"  {issue.id[:8]} {issue.title[:50]}{pri}{assign}"
            f"{comments_str}{refs_str}{labels_str}"
        )

    def _render_group(status: str, issues: list[Issue], is_terminal: bool) -> None:
        # Apply assigned_to filter
        if assigned_to:
            issues = [i for i in issues if i.assigned_to == assigned_to]

        if not issues:
            return

        if is_terminal and not show_done:
            return

        issues = sorted(issues, key=lambda i: priority_rank.get(i.priority or "", 4))

        if is_terminal and limit_done is not None:
            display = issues[:limit_done]
            hidden = len(issues) - len(display)
        else:
            display = issues
            hidden = 0

        lines.append(f"\n[{status.upper()}] ({len(issues)})")
        for issue in display:
            lines.append(_fmt_issue(issue))
        if hidden > 0:
            lines.append(f"  ... and {hidden} more (use limit_done=None to see all)")

    # Show active statuses first, then terminal, then any custom
    seen = set()
    standard_order = active_statuses + ["resolved", "closed", "wont-fix", "done", "complete", "shipped"]
    for status in standard_order:
        seen.add(status)
        issues = grouped.get(status, [])
        if not issues:
            continue
        is_terminal = status in _TERMINAL_STATUSES
        _render_group(status, issues, is_terminal)

    # Any custom statuses not in the standard list
    for status, issues in grouped.items():
        if status not in seen:
            is_terminal = status in _TERMINAL_STATUSES
            _render_group(status, issues, is_terminal)

    return "\n".join(lines)
