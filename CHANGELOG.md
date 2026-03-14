# ghi Changelog

---

## v2.5.0 — 2026-03-13

**Shell toolkit for multi-agent use.** Adds `ghi.sh` and `generate_board.py` — a bash CLI wrapper and a static board generator that together reduce context cost by ~85% in multi-agent Cowork sessions. The Python library (`ghi.py`) is unchanged at v2.4.0 and remains the analytics fallback.

### New: `ghi.sh` — Bash CLI wrapper

Zero-Python issue operations for agents. Eliminates the `import sys; sys.path.insert(0, '.ghi'); import ghi` boilerplate from every ghi call.

**Supported operations:**
```bash
./ghi.sh open "Title" [--author Name] [--assigned Name] [--priority critical|high|medium|low] [--label l1,l2]
./ghi.sh comment <id8> --author Name "Comment text"
./ghi.sh close <id8> --author Name [--comment "Done."]
./ghi.sh status <id8> --status open|in-progress|resolved|closed|wont-fix --author Name [--reason "Why"]
./ghi.sh assign <id8> --to Name --author Name
./ghi.sh priority <id8> --level critical|high|medium|low --author Name
./ghi.sh read <id8>
./ghi.sh summary [--assigned Name] [--no-done]
./ghi.sh list [--status open] [--assigned Name]
./ghi.sh find <keyword>
```

**Not yet in ghi.sh** (Python fallback): `stale()`, `metrics()`, `reopen()`, `add_ref()`, `bulk_update()`, `export()`. Targeted for v2.6.0: `stale` and `metrics`.

**Measured impact** (ghi-dev experiment, 5 cycles):
- 85.7% boilerplate reduction per write operation (0.86 lines vs 6.0)
- 100% round-trip correctness: shell-created issues parse cleanly in ghi.py

### New: `generate_board.py` — Static BOARD.md generator

Manager runs once per cycle; all other agents `cat BOARD.md` instead of calling `ghi.summary()` and N `read_issue()` calls.

```bash
# Basic (open issues, no comments)
python3 generate_board.py --no-done

# Recommended for PM triage: last 2 comments per issue
python3 generate_board.py --no-done --with-comments 2

# Full board including closed issues
python3 generate_board.py --with-comments 3
```

**Measured impact** (ghi-dev experiment):
- 75% boilerplate reduction on reads (1 line vs 4)
- 18% reduction on full PM triage workflow (9 lines vs 11)
- Eliminates O(N) thread-reading cost: `--with-comments 2` gives comment context for all issues in one read

### Background

Developed in the `ghi-dev` experiment (March 2026): 5 agents, 5 cycles, three approaches tested (shell CLI, static board, markdown-native). The A+B hybrid was selected based on empirical measurement. Approach C (markdown-native writes) was explored and deprecated — ghi.sh covers the same operations with lower cognitive load.

The experiment also identified a force-push hazard in multi-agent repos: agents should never use `git push --force`; always `git pull --rebase && git push`.

---

## v2.4.0 — 2026-03-13

- `stale(days=7)` — returns non-terminal issues with no activity for N days, oldest-first
- `list_issues(status=[...])` / `status="active"` — multi-status filter; backward compatible
- `summary(show_done, limit_done, assigned_to)` — view control at scale
- `summary()` shows `opened_age` for issues with no comments
- `metrics()` adds `velocity`, `by_assignee`, `stale_count`
- `init()` now creates/updates root-level `.gitignore`
- 73 tests, all passing

## v2.3.0 — 2026-03-13

- `closed_date` auto-tracking on terminal status transitions
- `metrics()` function (open/closed counts, cycle time, priority breakdowns)
- Comment age in `summary()` output
- 56 tests

## v2.2.1 — 2026-03-13

- `init()` creates `.ghi/.gitignore` (was missing)

## v2.2.0 — 2026-03-13

- `opened_by` filter on `list_issues()`
- `title_only` search mode in `find_issues()`
- Compound query support
- Bulk status operations

## v2.1.0 — 2026-03-13

- `assigned_to`, `priority`, `refs` fields
- `summary()` function
- Defensive APIs (graceful handling of malformed issues)

## v2.0.0 — 2026-03-10

Complete rewrite as an agent-first library. No CLI dependency; pure Python import. Issues as markdown + YAML frontmatter in `.ghi/issues/`.

## v0.x — 2012–2026

Original CLI tool for human use. See git history.
