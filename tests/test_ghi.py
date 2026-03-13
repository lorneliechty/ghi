"""
Tests for ghi — agent-first issue tracking.

Tests the single-file library (ghi.py at project root).
"""

import os
import sys
import tempfile
import shutil

# Import from the single-file library at project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import importlib
# Force reimport in case the package version was cached
if 'ghi' in sys.modules:
    del sys.modules['ghi']

# Make sure we import the single file, not the package dir
ghi_file = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'ghi.py'
)
spec = importlib.util.spec_from_file_location("ghi", ghi_file)
ghi = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ghi)

Issue = ghi.Issue
Comment = ghi.Comment


# ── Helpers ───────────────────────────────────────────────────


def make_temp_repo():
    """Create a temp directory and initialize ghi in it."""
    d = tempfile.mkdtemp(prefix="ghi_test_")
    ghi.init(d)
    return d


def cleanup(d):
    shutil.rmtree(d, ignore_errors=True)


# ── Parser tests ──────────────────────────────────────────────


def test_parse_roundtrip():
    """An issue should survive serialize → parse roundtrip."""
    issue = Issue(
        id="abc-123",
        title="Test issue",
        status="open",
        opened_by="Wiktor",
        opened_date="2026-03-12T00:00:00Z",
        labels=["bug", "kb-staleness"],
        description="This is the description.\n\nWith multiple paragraphs.",
        comments=[
            Comment(author="Lidia", date="2026-03-12T01:00:00Z", text="I agree."),
            Comment(author="Wiktor", date="2026-03-12T02:00:00Z", text="Fixed in abc123."),
        ],
    )

    text = ghi._serialize_issue(issue)
    parsed = ghi._parse_issue(text)

    assert parsed.id == issue.id
    assert parsed.title == issue.title
    assert parsed.status == issue.status
    assert parsed.opened_by == issue.opened_by
    assert parsed.opened_date == issue.opened_date
    assert parsed.labels == issue.labels
    assert parsed.description == issue.description
    assert len(parsed.comments) == 2
    assert parsed.comments[0].author == "Lidia"
    assert parsed.comments[0].text == "I agree."
    assert parsed.comments[1].author == "Wiktor"


def test_parse_no_comments():
    """An issue with no comments should parse cleanly."""
    issue = Issue(
        id="def-456",
        title="No comments yet",
        status="open",
        opened_by="Sora",
        opened_date="2026-03-12T00:00:00Z",
        labels=[],
        description="Lonely issue.",
        comments=[],
    )

    text = ghi._serialize_issue(issue)
    parsed = ghi._parse_issue(text)

    assert parsed.description == "Lonely issue."
    assert parsed.comments == []


def test_parse_multiline_comment():
    """Comments with multiple paragraphs should parse correctly."""
    issue = Issue(
        id="ghi-789",
        title="Multiline test",
        status="open",
        opened_by="Florent",
        opened_date="2026-03-12T00:00:00Z",
        labels=["question"],
        description="Question about X.",
        comments=[
            Comment(
                author="Erika",
                date="2026-03-12T01:00:00Z",
                text="First paragraph.\n\nSecond paragraph.\n\n- bullet one\n- bullet two",
            ),
        ],
    )

    text = ghi._serialize_issue(issue)
    parsed = ghi._parse_issue(text)

    assert "First paragraph." in parsed.comments[0].text
    assert "- bullet two" in parsed.comments[0].text


def test_parse_title_with_special_chars():
    """Titles with colons and quotes should survive roundtrip."""
    issue = Issue(
        id="special-1",
        title='Pattern "mount-and-clone" fails: timeout error',
        status="open",
        opened_by="Mariana",
        opened_date="2026-03-12T00:00:00Z",
        labels=[],
        description="Details.",
        comments=[],
    )

    text = ghi._serialize_issue(issue)
    parsed = ghi._parse_issue(text)

    assert parsed.title == issue.title


def test_parse_roundtrip_with_new_fields():
    """Issues with assigned_to, priority, and refs survive roundtrip."""
    issue = Issue(
        id="new-fields-1",
        title="Test new fields",
        status="in-progress",
        opened_by="Maryam",
        opened_date="2026-03-12T00:00:00Z",
        labels=["bug"],
        description="Testing new fields.",
        comments=[],
        assigned_to="Kwame",
        priority="high",
        refs=["abc-123", "def-456"],
    )

    text = ghi._serialize_issue(issue)
    parsed = ghi._parse_issue(text)

    assert parsed.assigned_to == "Kwame"
    assert parsed.priority == "high"
    assert parsed.refs == ["abc-123", "def-456"]


def test_parse_without_new_fields():
    """v2.0 issues (no assigned_to/priority/refs) parse with defaults."""
    text = """---
id: legacy-1
title: Old-style issue
status: open
opened_by: Wiktor
opened_date: 2026-03-12T00:00:00Z
labels: [bug]
---

Description from v2.0 format.
"""
    parsed = ghi._parse_issue(text)
    assert parsed.assigned_to is None
    assert parsed.priority is None
    assert parsed.refs == []


# ── Core API tests ────────────────────────────────────────────


def test_init_creates_structure():
    d = make_temp_repo()
    try:
        assert os.path.isdir(os.path.join(d, ".ghi"))
        assert os.path.isdir(os.path.join(d, ".ghi", "issues"))
        assert os.path.isfile(os.path.join(d, ".ghi", "config.yaml"))
    finally:
        cleanup(d)


def test_init_deploys_library():
    """init() should copy ghi.py into .ghi/ for self-contained use."""
    d = make_temp_repo()
    try:
        deployed = os.path.join(d, ".ghi", "ghi.py")
        assert os.path.isfile(deployed), "ghi.py should be deployed into .ghi/"

        # The deployed file should be importable
        spec = importlib.util.spec_from_file_location("ghi_deployed", deployed)
        deployed_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(deployed_mod)
        assert hasattr(deployed_mod, 'open_issue')
        assert hasattr(deployed_mod, '__version__')
    finally:
        cleanup(d)


def test_init_idempotent():
    d = make_temp_repo()
    try:
        ghi.init(d)  # second call should not fail
        assert os.path.isdir(os.path.join(d, ".ghi"))
    finally:
        cleanup(d)


def test_init_creates_gitignore():
    """init() should create a .gitignore excluding __pycache__ and bytecode."""
    d = make_temp_repo()
    try:
        gitignore = os.path.join(d, ".ghi", ".gitignore")
        assert os.path.isfile(gitignore), ".gitignore should be created in .ghi/"
        content = open(gitignore).read()
        assert "__pycache__/" in content
        assert "*.pyc" in content
    finally:
        cleanup(d)


def test_open_and_read():
    d = make_temp_repo()
    try:
        issue = ghi.open_issue(
            title="Test issue",
            description="Something is broken.",
            author="Wiktor",
            labels=["bug"],
            root=d,
        )

        assert issue.id
        assert issue.status == "open"
        assert issue.opened_by == "Wiktor"
        assert issue.labels == ["bug"]

        read_back = ghi.read_issue(issue.id, root=d)
        assert read_back.title == "Test issue"
        assert read_back.description == "Something is broken."
        assert read_back.comments == []
    finally:
        cleanup(d)


def test_open_with_assignment_and_priority():
    """open_issue should accept assigned_to and priority."""
    d = make_temp_repo()
    try:
        issue = ghi.open_issue(
            title="Assigned issue",
            description="Has an owner and priority.",
            author="Ren",
            assigned_to="Kwame",
            priority="high",
            root=d,
        )

        assert issue.assigned_to == "Kwame"
        assert issue.priority == "high"

        read_back = ghi.read_issue(issue.id, root=d)
        assert read_back.assigned_to == "Kwame"
        assert read_back.priority == "high"
    finally:
        cleanup(d)


def test_open_with_invalid_priority():
    """open_issue should reject invalid priority values."""
    d = make_temp_repo()
    try:
        raised = False
        try:
            ghi.open_issue(
                title="Bad priority",
                description="Should fail.",
                author="Test",
                priority="urgent",  # Not a valid value
                root=d,
            )
        except ValueError as e:
            raised = True
            assert "Invalid priority" in str(e)
        assert raised, "Should have raised ValueError"
    finally:
        cleanup(d)


def test_open_with_refs():
    """open_issue should accept cross-references."""
    d = make_temp_repo()
    try:
        a = ghi.open_issue("Issue A", "First", "Test", root=d)
        b = ghi.open_issue(
            "Issue B", "References A", "Test",
            refs=[a.id],
            root=d,
        )

        read_back = ghi.read_issue(b.id, root=d)
        assert a.id in read_back.refs
    finally:
        cleanup(d)


def test_comment_appends():
    d = make_temp_repo()
    try:
        issue = ghi.open_issue(
            title="Needs discussion",
            description="Should we change X?",
            author="Sora",
            root=d,
        )

        ghi.comment(issue.id, "Lidia", "I think yes.", root=d)
        ghi.comment(issue.id, "Florent", "I think no.", root=d)

        read_back = ghi.read_issue(issue.id, root=d)
        assert len(read_back.comments) == 2
        assert read_back.comments[0].author == "Lidia"
        assert read_back.comments[0].text == "I think yes."
        assert read_back.comments[1].author == "Florent"
        assert read_back.comments[1].text == "I think no."
    finally:
        cleanup(d)


def test_update_status():
    d = make_temp_repo()
    try:
        issue = ghi.open_issue(
            title="Stale pattern",
            description="The X pattern doesn't work.",
            author="Lidia",
            root=d,
        )

        updated = ghi.update_status(
            issue.id, "resolved", "Nightly Maintainer",
            "Updated kb/agents.md in commit abc123.",
            root=d,
        )

        assert updated.status == "resolved"

        read_back = ghi.read_issue(issue.id, root=d)
        assert read_back.status == "resolved"
        assert len(read_back.comments) == 1
        assert "open → resolved" in read_back.comments[0].text
        assert "abc123" in read_back.comments[0].text
    finally:
        cleanup(d)


def test_update_description():
    d = make_temp_repo()
    try:
        issue = ghi.open_issue(
            title="Vague report",
            description="Something is wrong.",
            author="Erika",
            root=d,
        )

        ghi.update_description(
            issue.id, "Erika",
            "The mount-and-clone pattern fails when the bare repo has a stale HEAD.lock.",
            root=d,
        )

        read_back = ghi.read_issue(issue.id, root=d)
        assert "stale HEAD.lock" in read_back.description
        assert len(read_back.comments) == 1
        assert "Description updated" in read_back.comments[0].text
    finally:
        cleanup(d)


def test_assign():
    """assign() should update assigned_to and add audit comment."""
    d = make_temp_repo()
    try:
        issue = ghi.open_issue("Needs owner", "Unassigned.", "Ren", root=d)
        assert issue.assigned_to is None

        updated = ghi.assign(issue.id, "Kwame", "Ren", root=d)
        assert updated.assigned_to == "Kwame"

        read_back = ghi.read_issue(issue.id, root=d)
        assert read_back.assigned_to == "Kwame"
        assert len(read_back.comments) == 1
        assert "unassigned → Kwame" in read_back.comments[0].text
    finally:
        cleanup(d)


def test_set_priority():
    """set_priority() should update priority and add audit comment."""
    d = make_temp_repo()
    try:
        issue = ghi.open_issue("Low bug", "Minor.", "Test", root=d)
        assert issue.priority is None

        updated = ghi.set_priority(issue.id, "critical", "Test", root=d)
        assert updated.priority == "critical"

        read_back = ghi.read_issue(issue.id, root=d)
        assert read_back.priority == "critical"
        assert "unset → critical" in read_back.comments[0].text
    finally:
        cleanup(d)


def test_set_invalid_priority():
    """set_priority() should reject invalid values."""
    d = make_temp_repo()
    try:
        issue = ghi.open_issue("Test", "Test", "Test", root=d)
        raised = False
        try:
            ghi.set_priority(issue.id, "blocker", "Test", root=d)
        except ValueError:
            raised = True
        assert raised, "Should have raised ValueError"
    finally:
        cleanup(d)


def test_add_ref():
    """add_ref() should add cross-reference and audit comment."""
    d = make_temp_repo()
    try:
        a = ghi.open_issue("Issue A", "First", "Test", root=d)
        b = ghi.open_issue("Issue B", "Second", "Test", root=d)

        ghi.add_ref(a.id, b.id, "Test", root=d)

        read_back = ghi.read_issue(a.id, root=d)
        assert b.id in read_back.refs
        assert len(read_back.comments) == 1
        assert "Linked" in read_back.comments[0].text
    finally:
        cleanup(d)


def test_add_ref_idempotent():
    """Adding the same ref twice should not duplicate."""
    d = make_temp_repo()
    try:
        a = ghi.open_issue("Issue A", "First", "Test", root=d)
        b = ghi.open_issue("Issue B", "Second", "Test", root=d)

        ghi.add_ref(a.id, b.id, "Test", root=d)
        ghi.add_ref(a.id, b.id, "Test", root=d)

        read_back = ghi.read_issue(a.id, root=d)
        assert read_back.refs.count(b.id) == 1
        assert len(read_back.comments) == 1  # Only one audit comment
    finally:
        cleanup(d)


def test_list_all():
    d = make_temp_repo()
    try:
        ghi.open_issue("Issue A", "A desc", "Sora", root=d)
        ghi.open_issue("Issue B", "B desc", "Lidia", root=d)
        ghi.open_issue("Issue C", "C desc", "Florent", root=d)

        all_issues = ghi.list_issues(root=d)
        assert len(all_issues) == 3
    finally:
        cleanup(d)


def test_list_filter_status():
    d = make_temp_repo()
    try:
        ghi.open_issue("Open issue", "Open", "Sora", root=d)
        b = ghi.open_issue("Will close", "Close me", "Lidia", root=d)
        ghi.update_status(b.id, "closed", "Lidia", "Done.", root=d)

        open_issues = ghi.list_issues(status="open", root=d)
        closed_issues = ghi.list_issues(status="closed", root=d)

        assert len(open_issues) == 1
        assert open_issues[0].title == "Open issue"
        assert len(closed_issues) == 1
        assert closed_issues[0].title == "Will close"
    finally:
        cleanup(d)


def test_list_filter_label():
    d = make_temp_repo()
    try:
        ghi.open_issue("Bug", "A bug", "Sora", labels=["bug"], root=d)
        ghi.open_issue("Feature", "A feature", "Lidia", labels=["enhancement"], root=d)
        ghi.open_issue("Stale KB", "Stale", "Florent", labels=["kb-staleness"], root=d)

        bugs = ghi.list_issues(label="bug", root=d)
        assert len(bugs) == 1
        assert bugs[0].title == "Bug"
    finally:
        cleanup(d)


def test_list_filter_assigned():
    """list_issues should filter by assigned_to."""
    d = make_temp_repo()
    try:
        a = ghi.open_issue("A", "A", "Test", assigned_to="Kwame", root=d)
        b = ghi.open_issue("B", "B", "Test", assigned_to="Ren", root=d)
        c = ghi.open_issue("C", "C", "Test", root=d)  # Unassigned

        kwame_issues = ghi.list_issues(assigned_to="Kwame", root=d)
        assert len(kwame_issues) == 1
        assert kwame_issues[0].title == "A"
    finally:
        cleanup(d)


def test_list_filter_priority():
    """list_issues should filter by priority."""
    d = make_temp_repo()
    try:
        ghi.open_issue("Crit", "Critical", "Test", priority="critical", root=d)
        ghi.open_issue("Low", "Low", "Test", priority="low", root=d)
        ghi.open_issue("None", "No priority", "Test", root=d)

        crits = ghi.list_issues(priority="critical", root=d)
        assert len(crits) == 1
        assert crits[0].title == "Crit"
    finally:
        cleanup(d)


def test_list_multi_filter():
    """Multiple filters should AND together."""
    d = make_temp_repo()
    try:
        ghi.open_issue("A", "A", "Test", labels=["bug"], priority="high", root=d)
        ghi.open_issue("B", "B", "Test", labels=["bug"], priority="low", root=d)
        ghi.open_issue("C", "C", "Test", labels=["enhancement"], priority="high", root=d)

        results = ghi.list_issues(label="bug", priority="high", root=d)
        assert len(results) == 1
        assert results[0].title == "A"
    finally:
        cleanup(d)


def test_find_issues():
    d = make_temp_repo()
    try:
        ghi.open_issue("Mount-and-clone failure", "Fails on lock file", "Sora", root=d)
        ghi.open_issue("KB agents.md outdated", "The mount pattern...", "Lidia", root=d)
        ghi.open_issue("Unrelated issue", "Nothing to see here", "Florent", root=d)

        results = ghi.find_issues("mount", root=d)
        assert len(results) == 2
        # Title match should rank higher
        assert results[0].title == "Mount-and-clone failure"
    finally:
        cleanup(d)


def test_prefix_id_resolution():
    d = make_temp_repo()
    try:
        issue = ghi.open_issue("Test", "Test", "Wiktor", root=d)
        prefix = issue.id[:8]

        read_back = ghi.read_issue(prefix, root=d)
        assert read_back.id == issue.id
    finally:
        cleanup(d)


def test_file_is_readable_markdown():
    """The generated file should be valid, readable markdown."""
    d = make_temp_repo()
    try:
        issue = ghi.open_issue(
            title="Human-readable test",
            description="This should look good in any markdown viewer.",
            author="Wiktor",
            labels=["question", "design-debate"],
            root=d,
        )
        ghi.comment(issue.id, "Lidia", "Agreed, very readable.", root=d)
        ghi.comment(issue.id, "Florent", "The markers are invisible in rendered markdown.", root=d)

        filepath = os.path.join(d, ".ghi", "issues", f"{issue.id}.md")
        with open(filepath, "r") as f:
            raw = f.read()

        assert raw.startswith("---")
        assert "<!-- ghi:comments -->" in raw
        assert '<!-- ghi:comment author="Lidia"' in raw
        assert '<!-- ghi:comment author="Florent"' in raw
        assert "very readable" in raw
        assert "invisible in rendered markdown" in raw
    finally:
        cleanup(d)


def test_deployed_library_works():
    """The deployed .ghi/ghi.py should work independently."""
    d = make_temp_repo()
    try:
        # Import the deployed copy
        deployed_path = os.path.join(d, ".ghi", "ghi.py")
        spec = importlib.util.spec_from_file_location("ghi_test_deployed", deployed_path)
        deployed = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(deployed)

        # Use it to create an issue
        issue = deployed.open_issue(
            title="Created by deployed copy",
            description="This proves the deployed library works.",
            author="TestAgent",
            root=d,
        )

        # Read it back with the deployed copy
        read_back = deployed.read_issue(issue.id, root=d)
        assert read_back.title == "Created by deployed copy"
    finally:
        cleanup(d)


def test_summary_output():
    """summary() should return a compact dashboard."""
    d = make_temp_repo()
    try:
        ghi.open_issue("Bug A", "A", "Test", labels=["bug"], priority="critical", root=d)
        ghi.open_issue("Feature B", "B", "Test", labels=["enhancement"], assigned_to="Kwame", root=d)
        c = ghi.open_issue("Done C", "C", "Test", root=d)
        ghi.update_status(c.id, "closed", "Test", "Done", root=d)

        output = ghi.summary(root=d)

        assert "3 issues" in output
        assert "2 active" in output
        assert "[OPEN]" in output
        assert "[CLOSED]" in output
        assert "!critical" in output
        assert "@Kwame" in output
    finally:
        cleanup(d)


def test_summary_empty():
    """summary() on empty repo returns sensible message."""
    d = make_temp_repo()
    try:
        output = ghi.summary(root=d)
        assert "No issues found" in output
    finally:
        cleanup(d)


def test_none_fields_not_serialized():
    """None-valued fields should not appear in frontmatter."""
    d = make_temp_repo()
    try:
        issue = ghi.open_issue("No extras", "Plain issue.", "Test", root=d)

        filepath = os.path.join(d, ".ghi", "issues", f"{issue.id}.md")
        with open(filepath, "r") as f:
            raw = f.read()

        assert "assigned_to" not in raw
        assert "priority" not in raw
        assert "refs" not in raw
    finally:
        cleanup(d)


# ── v2.2.0 feature tests ─────────────────────────────────────


def test_list_filter_opened_by():
    """list_issues should filter by opened_by."""
    d = make_temp_repo()
    try:
        ghi.open_issue("By Alice", "A", "Alice", root=d)
        ghi.open_issue("By Bob", "B", "Bob", root=d)
        ghi.open_issue("Also Alice", "C", "Alice", root=d)

        alice_issues = ghi.list_issues(opened_by="Alice", root=d)
        assert len(alice_issues) == 2
        titles = {i.title for i in alice_issues}
        assert "By Alice" in titles
        assert "Also Alice" in titles

        bob_issues = ghi.list_issues(opened_by="Bob", root=d)
        assert len(bob_issues) == 1
        assert bob_issues[0].title == "By Bob"
    finally:
        cleanup(d)


def test_list_filter_opened_by_with_other_filters():
    """opened_by should AND with other filters."""
    d = make_temp_repo()
    try:
        ghi.open_issue("A", "A", "Alice", labels=["bug"], root=d)
        ghi.open_issue("B", "B", "Alice", labels=["enhancement"], root=d)
        ghi.open_issue("C", "C", "Bob", labels=["bug"], root=d)

        results = ghi.list_issues(opened_by="Alice", label="bug", root=d)
        assert len(results) == 1
        assert results[0].title == "A"
    finally:
        cleanup(d)


def test_find_issues_title_only():
    """find_issues with title_only=True should not match description/comments."""
    d = make_temp_repo()
    try:
        ghi.open_issue("Mount failure", "Unrelated desc", "Test", root=d)
        ghi.open_issue("Other issue", "Mount is mentioned here", "Test", root=d)

        # Full search finds both
        all_results = ghi.find_issues("mount", root=d)
        assert len(all_results) == 2

        # Title-only finds just the first
        title_results = ghi.find_issues("mount", title_only=True, root=d)
        assert len(title_results) == 1
        assert title_results[0].title == "Mount failure"
    finally:
        cleanup(d)


def test_find_issues_with_status_filter():
    """find_issues should combine text search with status filter."""
    d = make_temp_repo()
    try:
        a = ghi.open_issue("Fix mount bug", "Details", "Test", root=d)
        ghi.open_issue("Mount improvement", "Ideas", "Test", root=d)
        ghi.update_status(a.id, "closed", "Test", "Fixed.", root=d)

        # Search "mount" but only open issues
        results = ghi.find_issues("mount", status="open", root=d)
        assert len(results) == 1
        assert results[0].title == "Mount improvement"
    finally:
        cleanup(d)


def test_find_issues_compound_query():
    """find_issues should support text + opened_by + status compound queries."""
    d = make_temp_repo()
    try:
        ghi.open_issue("Deploy fix", "Deploy issue", "Alice", root=d)
        ghi.open_issue("Deploy review", "Deploy review", "Bob", root=d)
        ghi.open_issue("Other thing", "Unrelated", "Alice", root=d)

        results = ghi.find_issues("deploy", opened_by="Alice", root=d)
        assert len(results) == 1
        assert results[0].title == "Deploy fix"
    finally:
        cleanup(d)


def test_count_issues():
    """count_issues should return counts grouped by status."""
    d = make_temp_repo()
    try:
        ghi.open_issue("A", "A", "Test", root=d)
        ghi.open_issue("B", "B", "Test", root=d)
        c = ghi.open_issue("C", "C", "Test", root=d)
        ghi.update_status(c.id, "closed", "Test", "Done.", root=d)

        counts = ghi.count_issues(root=d)
        assert counts["open"] == 2
        assert counts["closed"] == 1
        assert counts["_total"] == 3
    finally:
        cleanup(d)


def test_count_issues_empty():
    """count_issues on empty repo."""
    d = make_temp_repo()
    try:
        counts = ghi.count_issues(root=d)
        assert counts["_total"] == 0
    finally:
        cleanup(d)


def test_bulk_update_status():
    """bulk_update_status should close multiple issues at once."""
    d = make_temp_repo()
    try:
        a = ghi.open_issue("A", "A", "Test", root=d)
        b = ghi.open_issue("B", "B", "Test", root=d)
        c = ghi.open_issue("C", "C", "Test", root=d)

        results = ghi.bulk_update_status(
            [a.id, b.id, c.id], "closed", "Test",
            "Batch closing all.", root=d,
        )
        assert len(results) == 3
        for issue in results:
            assert issue.status == "closed"

        # Verify by reading back
        for issue_id in [a.id, b.id, c.id]:
            read_back = ghi.read_issue(issue_id, root=d)
            assert read_back.status == "closed"
    finally:
        cleanup(d)


def test_bulk_update_status_with_objects():
    """bulk_update_status should accept Issue objects."""
    d = make_temp_repo()
    try:
        a = ghi.open_issue("A", "A", "Test", root=d)
        b = ghi.open_issue("B", "B", "Test", root=d)

        # Pass Issue objects directly
        results = ghi.bulk_update_status(
            [a, b], "resolved", "Test",
            "Both resolved.", root=d,
        )
        assert len(results) == 2
        assert results[0].status == "resolved"
        assert results[1].status == "resolved"
    finally:
        cleanup(d)


def test_comment_accepts_issue_object():
    """comment() should accept an Issue object instead of a string ID."""
    d = make_temp_repo()
    try:
        issue = ghi.open_issue("Test", "Test", "Test", root=d)

        # Pass the Issue object directly
        ghi.comment(issue, "Author", "Works with object!", root=d)

        read_back = ghi.read_issue(issue.id, root=d)
        assert len(read_back.comments) == 1
        assert read_back.comments[0].text == "Works with object!"
    finally:
        cleanup(d)


# ── v2.3.0 feature tests ─────────────────────────────────────


def test_closed_date_set_on_terminal_status():
    """update_status to a terminal status should set closed_date."""
    d = make_temp_repo()
    try:
        issue = ghi.open_issue("Close me", "Will be closed.", "Test", root=d)
        assert issue.closed_date is None

        updated = ghi.update_status(issue.id, "closed", "Test", "Done.", root=d)
        assert updated.closed_date is not None

        read_back = ghi.read_issue(issue.id, root=d)
        assert read_back.closed_date is not None
        # Should be an ISO timestamp
        assert "T" in read_back.closed_date
    finally:
        cleanup(d)


def test_closed_date_set_on_resolved():
    """resolved is also a terminal status — should record closed_date."""
    d = make_temp_repo()
    try:
        issue = ghi.open_issue("Resolve me", "Will be resolved.", "Test", root=d)
        updated = ghi.update_status(issue.id, "resolved", "Test", "Fixed.", root=d)
        assert updated.closed_date is not None
    finally:
        cleanup(d)


def test_closed_date_not_set_on_open():
    """Moving to a non-terminal status should not set closed_date."""
    d = make_temp_repo()
    try:
        issue = ghi.open_issue("In progress", "Working on it.", "Test", root=d)
        updated = ghi.update_status(issue.id, "in-progress", "Test", "Started.", root=d)
        assert updated.closed_date is None
    finally:
        cleanup(d)


def test_closed_date_cleared_on_reopen():
    """Reopening a closed issue should clear closed_date."""
    d = make_temp_repo()
    try:
        issue = ghi.open_issue("Flappy issue", "Opens and closes.", "Test", root=d)
        closed = ghi.update_status(issue.id, "closed", "Test", "Done.", root=d)
        assert closed.closed_date is not None

        reopened = ghi.update_status(issue.id, "open", "Test", "Regression found.", root=d)
        assert reopened.closed_date is None

        read_back = ghi.read_issue(issue.id, root=d)
        assert read_back.closed_date is None
    finally:
        cleanup(d)


def test_closed_date_not_overwritten():
    """A second terminal transition should not change the original closed_date."""
    d = make_temp_repo()
    try:
        issue = ghi.open_issue("Terminal twice", "Hmm.", "Test", root=d)
        first_close = ghi.update_status(issue.id, "resolved", "Test", "Fixed.", root=d)
        original_date = first_close.closed_date

        second = ghi.update_status(issue.id, "closed", "Test", "Double close.", root=d)
        assert second.closed_date == original_date
    finally:
        cleanup(d)


def test_closed_date_roundtrip():
    """closed_date should survive serialize/parse roundtrip."""
    d = make_temp_repo()
    try:
        issue = ghi.open_issue("Roundtrip", "Desc.", "Test", root=d)
        ghi.update_status(issue.id, "closed", "Test", "Done.", root=d)

        read_back = ghi.read_issue(issue.id, root=d)
        assert read_back.closed_date is not None
        # Parse the date to ensure it's valid ISO format
        from datetime import datetime, timezone
        dt = datetime.fromisoformat(read_back.closed_date.replace("Z", "+00:00"))
        assert dt.year >= 2026
    finally:
        cleanup(d)


def test_metrics_empty():
    """metrics() on empty repo returns zeros."""
    d = make_temp_repo()
    try:
        m = ghi.metrics(root=d)
        assert m["total"] == 0
        assert m["open"] == 0
        assert m["done"] == 0
        assert m["cycle_time_avg"] is None
        assert m["cycle_time_p50"] is None
        assert m["closed_last_7d"] == 0
        assert m["closed_last_30d"] == 0
    finally:
        cleanup(d)


def test_metrics_basic():
    """metrics() should count open and done issues."""
    d = make_temp_repo()
    try:
        ghi.open_issue("A", "A", "Test", priority="high", root=d)
        ghi.open_issue("B", "B", "Test", priority="low", root=d)
        c = ghi.open_issue("C", "C", "Test", root=d)
        ghi.update_status(c.id, "closed", "Test", "Done.", root=d)

        m = ghi.metrics(root=d)
        assert m["total"] == 3
        assert m["open"] == 2
        assert m["done"] == 1
        assert m["closed_last_7d"] == 1
        assert m["closed_last_30d"] == 1
        assert m["cycle_time_avg"] is not None
        assert m["cycle_time_p50"] is not None
        assert m["cycle_time_avg"] >= 0
    finally:
        cleanup(d)


def test_metrics_open_by_priority():
    """metrics() should break open issues down by priority."""
    d = make_temp_repo()
    try:
        ghi.open_issue("A", "A", "Test", priority="critical", root=d)
        ghi.open_issue("B", "B", "Test", priority="high", root=d)
        ghi.open_issue("C", "C", "Test", root=d)  # No priority

        m = ghi.metrics(root=d)
        assert m["open_by_priority"].get("critical") == 1
        assert m["open_by_priority"].get("high") == 1
        assert m["open_by_priority"].get("unset") == 1
    finally:
        cleanup(d)


def test_metrics_by_status():
    """metrics()['by_status'] should reflect all status values."""
    d = make_temp_repo()
    try:
        a = ghi.open_issue("A", "A", "Test", root=d)
        b = ghi.open_issue("B", "B", "Test", root=d)
        ghi.update_status(a.id, "closed", "Test", "Done.", root=d)
        ghi.update_status(b.id, "resolved", "Test", "Fixed.", root=d)

        m = ghi.metrics(root=d)
        assert m["by_status"].get("closed") == 1
        assert m["by_status"].get("resolved") == 1
    finally:
        cleanup(d)


def test_summary_shows_comment_age():
    """summary() should show time since last comment, not just count."""
    d = make_temp_repo()
    try:
        issue = ghi.open_issue("Has comments", "Desc.", "Test", root=d)
        ghi.comment(issue.id, "Reviewer", "Looks good.", root=d)

        output = ghi.summary(root=d)
        # Should show count AND age indicator
        assert "(1c," in output  # comma indicates age follows
    finally:
        cleanup(d)


# ── v2.4.0 feature tests ─────────────────────────────────────


def test_init_creates_root_gitignore():
    """init() should create a root-level .gitignore with bytecode patterns."""
    d = make_temp_repo()
    try:
        root_gitignore = os.path.join(d, ".gitignore")
        assert os.path.isfile(root_gitignore), "root .gitignore should be created"
        content = open(root_gitignore).read()
        assert "__pycache__/" in content
        assert "*.pyc" in content
    finally:
        cleanup(d)


def test_init_root_gitignore_idempotent():
    """Calling init() twice should not duplicate .gitignore entries."""
    d = make_temp_repo()
    try:
        ghi.init(d)  # Second call
        root_gitignore = os.path.join(d, ".gitignore")
        content = open(root_gitignore).read()
        # Should appear exactly once
        assert content.count("__pycache__/") == 1
    finally:
        cleanup(d)


def test_init_root_gitignore_appends_to_existing():
    """init() should append to an existing .gitignore without overwriting."""
    import tempfile
    d = tempfile.mkdtemp(prefix="ghi_test_")
    try:
        # Write a .gitignore before init
        with open(os.path.join(d, ".gitignore"), "w") as f:
            f.write("node_modules/\n.env\n")
        ghi.init(d)
        content = open(os.path.join(d, ".gitignore")).read()
        # Original entries preserved
        assert "node_modules/" in content
        assert ".env" in content
        # Bytecode patterns added
        assert "__pycache__/" in content
    finally:
        cleanup(d)


def test_list_issues_multi_status():
    """list_issues should accept a list of statuses."""
    d = make_temp_repo()
    try:
        a = ghi.open_issue("Open", "A", "Test", root=d)
        b = ghi.open_issue("In Progress", "B", "Test", root=d)
        ghi.update_status(b.id, "in-progress", "Test", "Started.", root=d)
        c = ghi.open_issue("Closed", "C", "Test", root=d)
        ghi.update_status(c.id, "closed", "Test", "Done.", root=d)

        active = ghi.list_issues(status=["open", "in-progress"], root=d)
        assert len(active) == 2
        titles = {i.title for i in active}
        assert "Open" in titles
        assert "In Progress" in titles
        assert "Closed" not in titles
    finally:
        cleanup(d)


def test_list_issues_active_shorthand():
    """list_issues(status='active') should return open + in-progress."""
    d = make_temp_repo()
    try:
        ghi.open_issue("Open", "A", "Test", root=d)
        b = ghi.open_issue("In Progress", "B", "Test", root=d)
        ghi.update_status(b.id, "in-progress", "Test", "Started.", root=d)
        c = ghi.open_issue("Closed", "C", "Test", root=d)
        ghi.update_status(c.id, "closed", "Test", "Done.", root=d)

        active = ghi.list_issues(status="active", root=d)
        assert len(active) == 2
    finally:
        cleanup(d)


def test_list_issues_single_string_still_works():
    """list_issues(status='open') should still work as before."""
    d = make_temp_repo()
    try:
        ghi.open_issue("Open", "A", "Test", root=d)
        b = ghi.open_issue("Closed", "B", "Test", root=d)
        ghi.update_status(b.id, "closed", "Test", "Done.", root=d)

        results = ghi.list_issues(status="open", root=d)
        assert len(results) == 1
        assert results[0].title == "Open"
    finally:
        cleanup(d)


def test_stale_empty():
    """stale() on empty repo returns empty list."""
    d = make_temp_repo()
    try:
        results = ghi.stale(days=7, root=d)
        assert results == []
    finally:
        cleanup(d)


def test_stale_fresh_issue_not_stale():
    """A just-opened issue should not be stale."""
    d = make_temp_repo()
    try:
        ghi.open_issue("Fresh", "Just opened.", "Test", root=d)
        results = ghi.stale(days=1, root=d)
        assert len(results) == 0
    finally:
        cleanup(d)


def test_stale_terminal_excluded():
    """Closed issues should not appear in stale()."""
    d = make_temp_repo()
    try:
        issue = ghi.open_issue("Old closed", "Done.", "Test", root=d)
        ghi.update_status(issue.id, "closed", "Test", "Done.", root=d)
        # Even with days=0, closed issues are excluded
        results = ghi.stale(days=0, root=d)
        assert all(i.status not in ghi._TERMINAL_STATUSES for i in results)
    finally:
        cleanup(d)


def test_stale_with_days_zero():
    """stale(days=0) returns all non-terminal issues (everything is stale)."""
    d = make_temp_repo()
    try:
        ghi.open_issue("A", "A", "Test", root=d)
        ghi.open_issue("B", "B", "Test", root=d)
        c = ghi.open_issue("C (closed)", "C", "Test", root=d)
        ghi.update_status(c.id, "closed", "Test", "Done.", root=d)

        results = ghi.stale(days=0, root=d)
        assert len(results) == 2  # C excluded because it's terminal
    finally:
        cleanup(d)


def test_summary_show_done_false():
    """summary(show_done=False) should hide terminal issues."""
    d = make_temp_repo()
    try:
        ghi.open_issue("Open bug", "A", "Test", root=d)
        c = ghi.open_issue("Closed feature", "B", "Test", root=d)
        ghi.update_status(c.id, "closed", "Test", "Done.", root=d)

        output = ghi.summary(show_done=False, root=d)
        assert "Open bug" in output
        assert "Closed feature" not in output
        assert "[CLOSED]" not in output
    finally:
        cleanup(d)


def test_summary_limit_done():
    """summary(limit_done=1) should truncate done issues."""
    d = make_temp_repo()
    try:
        for i in range(3):
            issue = ghi.open_issue(f"Done issue {i}", "A", "Test", root=d)
            ghi.update_status(issue.id, "closed", "Test", "Done.", root=d)

        output = ghi.summary(limit_done=1, root=d)
        assert "and 2 more" in output
    finally:
        cleanup(d)


def test_summary_assigned_to_filter():
    """summary(assigned_to=...) should show only that agent's issues."""
    d = make_temp_repo()
    try:
        ghi.open_issue("Zara issue", "A", "Test", assigned_to="Zara", root=d)
        ghi.open_issue("Orion issue", "B", "Test", assigned_to="Orion", root=d)
        ghi.open_issue("Unassigned", "C", "Test", root=d)

        output = ghi.summary(assigned_to="Zara", root=d)
        assert "Zara issue" in output
        assert "Orion issue" not in output
        assert "Unassigned" not in output
    finally:
        cleanup(d)


def test_metrics_velocity():
    """metrics() should include velocity (issues/day over last 7 days)."""
    d = make_temp_repo()
    try:
        a = ghi.open_issue("A", "A", "Test", root=d)
        b = ghi.open_issue("B", "B", "Test", root=d)
        ghi.update_status(a.id, "closed", "Test", "Done.", root=d)
        ghi.update_status(b.id, "closed", "Test", "Done.", root=d)

        m = ghi.metrics(root=d)
        assert "velocity" in m
        # 2 closed in the last 7 days → velocity = 2/7 ≈ 0.29
        assert m["velocity"] == round(2 / 7, 2)
    finally:
        cleanup(d)


def test_metrics_by_assignee():
    """metrics() should break open issues down by assignee."""
    d = make_temp_repo()
    try:
        ghi.open_issue("A", "A", "Test", assigned_to="Zara", root=d)
        ghi.open_issue("B", "B", "Test", assigned_to="Zara", root=d)
        ghi.open_issue("C", "C", "Test", assigned_to="Orion", root=d)
        ghi.open_issue("D unassigned", "D", "Test", root=d)

        m = ghi.metrics(root=d)
        assert m["by_assignee"].get("Zara") == 2
        assert m["by_assignee"].get("Orion") == 1
        assert m["by_assignee"].get("unassigned") == 1
    finally:
        cleanup(d)


def test_metrics_stale_count():
    """metrics() stale_count should be 0 for a fresh repo."""
    d = make_temp_repo()
    try:
        ghi.open_issue("Fresh A", "A", "Test", root=d)
        ghi.open_issue("Fresh B", "B", "Test", root=d)

        m = ghi.metrics(root=d)
        assert "stale_count" in m
        # Just-created issues are not stale
        assert m["stale_count"] == 0
    finally:
        cleanup(d)


def test_summary_no_comments_shows_opened_age():
    """Issues with no comments should show 'opened Xh ago' in summary."""
    d = make_temp_repo()
    try:
        ghi.open_issue("Silent issue", "No comments ever.", "Test", root=d)
        output = ghi.summary(root=d)
        assert "opened" in output
    finally:
        cleanup(d)


# ── Run all tests ─────────────────────────────────────────────


def run_all():
    tests = [
        test_parse_roundtrip,
        test_parse_no_comments,
        test_parse_multiline_comment,
        test_parse_title_with_special_chars,
        test_parse_roundtrip_with_new_fields,
        test_parse_without_new_fields,
        test_init_creates_structure,
        test_init_deploys_library,
        test_init_idempotent,
        test_init_creates_gitignore,
        test_open_and_read,
        test_open_with_assignment_and_priority,
        test_open_with_invalid_priority,
        test_open_with_refs,
        test_comment_appends,
        test_update_status,
        test_update_description,
        test_assign,
        test_set_priority,
        test_set_invalid_priority,
        test_add_ref,
        test_add_ref_idempotent,
        test_list_all,
        test_list_filter_status,
        test_list_filter_label,
        test_list_filter_assigned,
        test_list_filter_priority,
        test_list_multi_filter,
        test_find_issues,
        test_prefix_id_resolution,
        test_file_is_readable_markdown,
        test_deployed_library_works,
        test_summary_output,
        test_summary_empty,
        test_none_fields_not_serialized,
        # v2.2.0 tests
        test_list_filter_opened_by,
        test_list_filter_opened_by_with_other_filters,
        test_find_issues_title_only,
        test_find_issues_with_status_filter,
        test_find_issues_compound_query,
        test_count_issues,
        test_count_issues_empty,
        test_bulk_update_status,
        test_bulk_update_status_with_objects,
        test_comment_accepts_issue_object,
        # v2.3.0 tests
        test_closed_date_set_on_terminal_status,
        test_closed_date_set_on_resolved,
        test_closed_date_not_set_on_open,
        test_closed_date_cleared_on_reopen,
        test_closed_date_not_overwritten,
        test_closed_date_roundtrip,
        test_metrics_empty,
        test_metrics_basic,
        test_metrics_open_by_priority,
        test_metrics_by_status,
        test_summary_shows_comment_age,
        # v2.4.0 tests
        test_init_creates_root_gitignore,
        test_init_root_gitignore_idempotent,
        test_init_root_gitignore_appends_to_existing,
        test_list_issues_multi_status,
        test_list_issues_active_shorthand,
        test_list_issues_single_string_still_works,
        test_stale_empty,
        test_stale_fresh_issue_not_stale,
        test_stale_terminal_excluded,
        test_stale_with_days_zero,
        test_summary_show_done_false,
        test_summary_limit_done,
        test_summary_assigned_to_filter,
        test_metrics_velocity,
        test_metrics_by_assignee,
        test_metrics_stale_count,
        test_summary_no_comments_shows_opened_age,
    ]

    passed = 0
    failed = 0
    for test in tests:
        name = test.__name__
        try:
            test()
            print(f"  PASS  {name}")
            passed += 1
        except Exception as e:
            print(f"  FAIL  {name}: {e}")
            failed += 1

    print(f"\n{'=' * 40}")
    print(f"  {passed} passed, {failed} failed, {len(tests)} total")
    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    run_all()
