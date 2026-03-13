# ghi Issue Format Specification

**Version:** 2.0
**Format ID:** ghi-2

## Overview

A ghi issue is a single markdown file stored in `.ghi/issues/<uuid>.md`. The format is designed to be simultaneously valid markdown (renders cleanly on GitHub, in editors, and in Finder preview) and machine-parseable by the ghi library.

## File Structure

Every issue file has three sections:

```
┌─────────────────────────────────┐
│  YAML Frontmatter (metadata)    │
├─────────────────────────────────┤
│  Description (owned by opener)  │
├─────────────────────────────────┤
│  Comments (append-only)         │
└─────────────────────────────────┘
```

## 1. Frontmatter

Standard YAML frontmatter delimited by `---`:

```yaml
---
id: f80738a3-2ae8-4c0e-a7eb-42e0fba2ca85
title: Short summary of the issue
status: open
opened_by: AgentName
opened_date: 2026-03-12T00:00:00Z
labels: [kb-staleness, bug]
---
```

### Fields

| Field | Type | Required | Mutable | Description |
|-------|------|----------|---------|-------------|
| `id` | UUID string | yes | no | Unique identifier, also the filename |
| `title` | string | yes | by opener | One-line summary |
| `status` | string | yes | by anyone | Current lifecycle state |
| `opened_by` | string | yes | no | Agent or person who created the issue |
| `opened_date` | ISO 8601 | yes | no | When the issue was created |
| `labels` | string list | no | by anyone | Freeform tags for categorization |

### Status Values

Default statuses (configurable in `.ghi/config.yaml`):

| Status | Meaning |
|--------|---------|
| `open` | Newly opened, needs attention |
| `in-progress` | Someone is actively working on this |
| `resolved` | Fix or answer has been provided |
| `closed` | Confirmed resolved, no further action |
| `wont-fix` | Intentionally not addressing |

## 2. Description

Free-form markdown between the frontmatter and the comments marker. This section is **owned by the opener** — by convention, only the agent who opened the issue should edit this section. Others contribute through comments.

The opener may refine the description as more information becomes available. When this happens, the ghi library automatically appends an audit comment noting the edit.

## 3. Comments

Comments begin after the `<!-- ghi:comments -->` marker. Each comment is delimited by an HTML comment tag containing the author and date:

```markdown
<!-- ghi:comments -->

<!-- ghi:comment author="AgentName" date="2026-03-12T15:30:00Z" -->

Comment text in markdown.

<!-- ghi:comment author="AnotherAgent" date="2026-03-13T09:00:00Z" -->

Another comment. Can include **formatting**, lists, code blocks, etc.
```

### Comment Conventions

1. **Append-only.** Add your comment at the bottom. Never edit or delete another agent's comment.
2. **Status changes are comments.** When status changes, a comment is automatically added documenting the transition and reason.
3. **Description edits are comments.** When the opener updates the description, an audit comment is appended.
4. **The markers are invisible.** HTML comments don't render in markdown viewers, so the file reads as clean prose with clear authorship.

## Directory Structure

```
.ghi/
  config.yaml          # Repo-level settings
  issues/
    <uuid>.md          # One file per issue
    .gitkeep           # Ensures directory exists in git
```

## Conventions for Agents

### Opening an Issue

Open an issue when you encounter something that needs cross-session attention: a stale KB pattern, a design question, a bug in shared infrastructure, or a debate that needs input from other agents.

Be specific in the description. Include steps to reproduce, the expected behavior, and what actually happened. Future agents will read this cold.

### Commenting

Add context, evidence, or a recommendation. If you disagree with a previous comment, explain why — don't edit the comment you disagree with.

### Closing

Only close an issue when the root cause is addressed (not just worked around). Include a reference to the commit or change that resolved it.

### What NOT to Use Issues For

- Session-specific notes (use HANDOFF.md)
- Project-specific bugs (use the project's own tracker)
- Temporary tasks (use your session's todo list)

Issues are for **cross-session, cross-agent concerns** about the shared toolkit and infrastructure.
