#!/usr/bin/env python3
"""
Generate a static BOARD.md file from ghi issues.

This script reads all issues from ghi and generates a board state file
optimized for agent consumption. Agents read this file instead of running
ghi.summary(), reducing read-side Python execution.

Usage:
    python3 generate_board.py                          # Default grouped format
    python3 generate_board.py --format table           # Table format
    python3 generate_board.py --format grouped         # Explicit grouped format
    python3 generate_board.py --output FILE            # Write to custom path
    python3 generate_board.py --no-done                # Hide resolved/closed issues
    python3 generate_board.py --refs                   # Add DEPENDENCIES section
    python3 generate_board.py --with-comments 2        # Include last 2 comments per issue
    python3 generate_board.py --with-comments 2 --refs # Combine comments + dependencies
"""

import sys
import argparse
from datetime import datetime, timezone
from pathlib import Path
import os

sys.path.insert(0, '.ghi')
import ghi


def get_last_activity_age(issue):
    """Return human-readable age of last activity."""
    opened = datetime.fromisoformat(issue.opened_date.replace('Z', '+00:00'))
    now = datetime.now(timezone.utc)
    delta = now - opened

    if delta.days > 0:
        return f"{delta.days}d"

    hours = delta.seconds // 3600
    if hours > 0:
        return f"{hours}h"

    minutes = (delta.seconds % 3600) // 60
    return f"{minutes}m"


def get_comment_age(date_str):
    """Return human-readable age of a comment."""
    # date_str can be ISO format or other datetime string
    try:
        comment_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    except (ValueError, TypeError):
        # Fallback for other formats
        return "?"

    now = datetime.now(timezone.utc)
    delta = now - comment_date

    if delta.days > 0:
        return f"{delta.days}d"

    hours = delta.seconds // 3600
    if hours > 0:
        return f"{hours}h"

    minutes = (delta.seconds % 3600) // 60
    return f"{minutes}m"


def format_comment_line(comment, max_length=120):
    """
    Format a single comment line.

    Returns: "└── author (age): \"truncated_text...\""
    """
    age = get_comment_age(comment.date)
    text = comment.text.replace('\n', ' ')  # Remove newlines for single-line display

    if len(text) > max_length:
        text = text[:max_length-3] + "..."

    return f"    └── {comment.author} ({age}): \"{text}\""


def check_freshness(output_path, max_age_seconds=7200):
    """Check if BOARD.md file is stale (older than max_age_seconds)."""
    if not output_path.exists():
        return None, None

    file_mtime = os.path.getmtime(str(output_path))
    now_timestamp = datetime.now(timezone.utc).timestamp()
    age_seconds = int(now_timestamp - file_mtime)

    is_stale = age_seconds > max_age_seconds
    hours = age_seconds // 3600

    return is_stale, hours


def format_freshness_indicator(is_stale, hours):
    """Format freshness indicator for board header."""
    if is_stale:
        return f"⚠ STALE ({hours}h old)"
    return None


def build_dependencies_section(issues):
    """
    Build a DEPENDENCIES section showing cross-issue refs.

    Returns formatted string or empty string if no refs exist.
    Format: "  source_id (@assignee) → target_id (@target_assignee)  # rel_type"
    """
    # Build a map of issue_id -> issue for quick lookup
    issue_map = {issue.id: issue for issue in issues}

    # Collect all ref relationships
    refs_lines = []
    for issue in issues:
        if not issue.refs:
            continue

        source_short = issue.id[:8]
        source_assignee = issue.assigned_to or "unassigned"

        for ref_id in issue.refs:
            # Find full issue_id that matches this ref
            target_issue = issue_map.get(ref_id)
            if not target_issue:
                continue

            target_short = target_issue.id[:8]
            target_assignee = target_issue.assigned_to or "unassigned"

            # Format: source → target (issue lists its refs, so this is "blocks" relationship)
            line = f"  {source_short} (@{source_assignee}) → {target_short} (@{target_assignee})  # blocks"
            refs_lines.append(line)

    if not refs_lines:
        return ""

    # Sort for consistent output
    refs_lines.sort()
    return "## Dependencies\n\n" + "\n".join(refs_lines) + "\n"


def format_grouped(issues, metrics, show_done=True, is_stale=None, stale_hours=None, include_deps=False, with_comments=0):
    """
    Format grouped by assignee.

    This format is optimized for agent consumption: each agent scans
    only their section. Compact line format minimizes token consumption.

    Args:
        issues: List of issue objects
        metrics: Metrics dict from ghi.metrics()
        show_done: If False, hide resolved/closed issues
        is_stale: If True, include stale marker in header
        stale_hours: Hours since last update (for stale display)
        include_deps: If True, include DEPENDENCIES section for cross-refs
        with_comments: If > 0, include up to N recent comments per issue
    """
    lines = []

    # Header
    now = datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')
    open_count = metrics['open']
    stale_count = metrics['stale_count']

    header = f"# Board (Last updated: {now} | Open: {open_count} | Stale (3d+): {stale_count})"
    if is_stale and stale_hours is not None:
        header += f" {format_freshness_indicator(is_stale, stale_hours)}"

    lines.append(header + "\n")

    # Group by assignee
    by_assignee = {}
    unassigned = []

    for issue in issues:
        # Skip resolved/closed if show_done is False
        if not show_done and issue.status in ("resolved", "closed"):
            continue

        if issue.assigned_to:
            if issue.assigned_to not in by_assignee:
                by_assignee[issue.assigned_to] = []
            by_assignee[issue.assigned_to].append(issue)
        else:
            unassigned.append(issue)

    # Output each assignee's section
    for assignee in sorted(by_assignee.keys()):
        assignee_issues = by_assignee[assignee]
        lines.append(f"## @{assignee} ({len(assignee_issues)})\n")

        for issue in assignee_issues:
            status_char = "✓" if issue.status == "resolved" else "●"
            priority_char = "!" if issue.priority == "high" else " "
            age = get_last_activity_age(issue)
            short_id = issue.id[:8]
            short_title = issue.title[:50] + ("..." if len(issue.title) > 50 else "")

            line = (f"  {status_char} {short_id} [{issue.status[:3].upper()}] "
                   f"{priority_char} {short_title} ({age})")
            lines.append(line)

            # Add comments if requested
            if with_comments > 0:
                # Read full issue to get comments
                full_issue = ghi.read_issue(issue.id)
                if full_issue.comments:
                    # Get last N comments
                    recent_comments = full_issue.comments[-with_comments:]
                    for comment in recent_comments:
                        lines.append(format_comment_line(comment))

        lines.append("")

    # Unassigned issues
    if unassigned:
        lines.append(f"## Unassigned ({len(unassigned)})\n")
        for issue in unassigned:
            status_char = "✓" if issue.status == "resolved" else "●"
            priority_char = "!" if issue.priority == "high" else " "
            age = get_last_activity_age(issue)
            short_id = issue.id[:8]
            short_title = issue.title[:50] + ("..." if len(issue.title) > 50 else "")

            line = (f"  {status_char} {short_id} [{issue.status[:3].upper()}] "
                   f"{priority_char} {short_title} ({age})")
            lines.append(line)

            # Add comments if requested
            if with_comments > 0:
                # Read full issue to get comments
                full_issue = ghi.read_issue(issue.id)
                if full_issue.comments:
                    # Get last N comments
                    recent_comments = full_issue.comments[-with_comments:]
                    for comment in recent_comments:
                        lines.append(format_comment_line(comment))

        lines.append("")

    # Add dependencies section if requested
    if include_deps:
        deps_section = build_dependencies_section(issues)
        if deps_section:
            lines.append("")
            lines.append(deps_section)

    return "\n".join(lines)


def format_table(issues, metrics, show_done=True, is_stale=None, stale_hours=None, include_deps=False, with_comments=0):
    """
    Format as a compact table sorted by priority then status.

    Single-line-per-issue format, easy to scan for specific issues.
    Sorted: high priority first, then open before resolved.

    Args:
        issues: List of issue objects
        metrics: Metrics dict from ghi.metrics()
        show_done: If False, hide resolved/closed issues
        is_stale: If True, include stale marker in header
        stale_hours: Hours since last update (for stale display)
        include_deps: If True, include DEPENDENCIES section for cross-refs
        with_comments: If > 0, include up to N recent comments per issue
    """
    lines = []

    # Header
    now = datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')
    open_count = metrics['open']
    stale_count = metrics['stale_count']

    header = f"# Board (Last updated: {now} | Open: {open_count} | Stale (3d+): {stale_count})"
    if is_stale and stale_hours is not None:
        header += f" {format_freshness_indicator(is_stale, stale_hours)}"

    lines.append(header + "\n")

    # Filter: skip resolved/closed if show_done is False
    filtered_issues = issues
    if not show_done:
        filtered_issues = [i for i in issues if i.status not in ("resolved", "closed")]

    # Sort: high priority first, open first, then by date
    def sort_key(issue):
        priority_order = {"high": 0, "medium": 1, "low": 2}
        status_order = {"open": 0, "resolved": 1}
        return (
            priority_order.get(issue.priority, 999),
            status_order.get(issue.status, 999),
            issue.opened_date
        )

    sorted_issues = sorted(filtered_issues, key=sort_key)

    # Column headers
    lines.append("| ID | Title | Status | Assigned | Priority | Age |")
    lines.append("|---|---|---|---|---|---|")

    # Issue rows
    for issue in sorted_issues:
        short_id = issue.id[:8]
        short_title = issue.title[:40] + ("..." if len(issue.title) > 40 else "")
        assigned = issue.assigned_to or "—"
        priority = "HIGH" if issue.priority == "high" else issue.priority.upper()
        status = issue.status.upper()
        age = get_last_activity_age(issue)

        line = f"| {short_id} | {short_title} | {status} | {assigned} | {priority} | {age} |"
        lines.append(line)

        # Add comments if requested (below the table row)
        if with_comments > 0:
            # Read full issue to get comments
            full_issue = ghi.read_issue(issue.id)
            if full_issue.comments:
                # Get last N comments
                recent_comments = full_issue.comments[-with_comments:]
                for comment in recent_comments:
                    lines.append(format_comment_line(comment))

    lines.append("")

    # Add dependencies section if requested
    if include_deps:
        deps_section = build_dependencies_section(issues)
        if deps_section:
            lines.append("")
            lines.append(deps_section)

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Generate a static BOARD.md file from ghi issues"
    )
    parser.add_argument(
        "--format",
        choices=["grouped", "table"],
        default="grouped",
        help="Output format (default: grouped)"
    )
    parser.add_argument(
        "--output",
        default="BOARD.md",
        help="Output file path (default: BOARD.md in repo root)"
    )
    parser.add_argument(
        "--no-done",
        action="store_true",
        help="Hide resolved/closed issues from board"
    )
    parser.add_argument(
        "--check-freshness",
        action="store_true",
        help="Check if existing board is stale (>2h old) and warn"
    )
    parser.add_argument(
        "--refs",
        action="store_true",
        help="Include DEPENDENCIES section showing cross-issue refs"
    )
    parser.add_argument(
        "--with-comments",
        type=int,
        default=0,
        metavar="N",
        help="Include up to N recent comments per issue (default: 0, disabled)"
    )

    args = parser.parse_args()

    # Read all issues and metrics
    all_issues = ghi.list_issues()
    metrics = ghi.metrics()

    output_path = Path(args.output)

    # Check freshness of existing board if requested
    is_stale = None
    stale_hours = None
    if args.check_freshness:
        is_stale, stale_hours = check_freshness(output_path, max_age_seconds=7200)

    # Generate board
    if args.format == "table":
        board_content = format_table(
            all_issues, metrics,
            show_done=not args.no_done,
            is_stale=is_stale,
            stale_hours=stale_hours,
            include_deps=args.refs,
            with_comments=args.with_comments
        )
    else:  # grouped
        board_content = format_grouped(
            all_issues, metrics,
            show_done=not args.no_done,
            is_stale=is_stale,
            stale_hours=stale_hours,
            include_deps=args.refs,
            with_comments=args.with_comments
        )

    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(board_content)

    print(f"✓ BOARD.md generated ({args.format} format)")
    print(f"  Location: {output_path.resolve()}")
    print(f"  Issues: {len(all_issues)} total ({metrics['open']} open)")
    if args.no_done:
        active_count = len([i for i in all_issues if i.status not in ("resolved", "closed")])
        print(f"  Showing: {active_count} active (resolved/closed hidden)")
    if args.with_comments > 0:
        print(f"  Comments: up to {args.with_comments} per issue")


if __name__ == "__main__":
    main()
