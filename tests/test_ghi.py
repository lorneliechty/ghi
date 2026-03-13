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


# ── Run all tests ─────────────────────────────────────────────


def run_all():
    tests = [
        test_parse_roundtrip,
        test_parse_no_comments,
        test_parse_multiline_comment,
        test_parse_title_with_special_chars,
        test_init_creates_structure,
        test_init_deploys_library,
        test_init_idempotent,
        test_open_and_read,
        test_comment_appends,
        test_update_status,
        test_update_description,
        test_list_all,
        test_list_filter_status,
        test_list_filter_label,
        test_find_issues,
        test_prefix_id_resolution,
        test_file_is_readable_markdown,
        test_deployed_library_works,
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
