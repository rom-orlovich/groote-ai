# Jira Templates

Templates for creating issues and posting responses to Jira.

## Issue Creation Templates

### Standard Task

```markdown
Summary: [Component] Action verb - Brief detail (max 80 chars)
```

```markdown
## Overview

One paragraph explaining what this task accomplishes and why it matters.

## Acceptance Criteria

- First measurable criterion
- Second measurable criterion
- Third measurable criterion

## Technical Notes

- **Key files:** `path/to/file.py`, `path/to/other.ts`
- **Dependencies:** List any blocking tickets (e.g., KAN-42)
- **Scope:** S / M / L
```

### Bug Report

```markdown
Summary: [Component] Fix - Brief bug description
```

```markdown
## Bug Description

What is happening vs what should happen.

## Steps to Reproduce

1. First step
2. Second step
3. Observe the bug

## Expected Behavior

What should happen instead.

## Technical Notes

- **Affected files:** `path/to/file.py`
- **Root cause:** Brief description if known
- **Scope:** S / M / L
```

### Epic

```markdown
Summary: [Groote AI] Epic name - High-level goal
```

```markdown
## Goal

What this epic achieves when all child tasks are complete.

## Scope

- Feature area 1
- Feature area 2
- Feature area 3

## Success Criteria

- Measurable outcome 1
- Measurable outcome 2
```

**IMPORTANT:** Always use real newlines in descriptions, never literal `\n`.
Use markdown formatting (headings, bullets, bold, code) for structured readability.

## Comment Templates

### Analysis Complete

```markdown
## ✅ Analysis Complete

**Summary:** {brief_summary}

### Findings

{findings_list}

### Root Cause

{root_cause}

### Recommendations

{recommendations}

### Next Steps

{next_steps}

---

_Automated analysis by Claude Agent_
```

**MCP Tool:**

```json
{
  "tool": "jira:add_jira_comment",
  "arguments": {
    "issue_key": "{issue_key}",
    "body": "{formatted_markdown}"
  }
}
```

### Implementation Complete

```markdown
## ✅ Implementation Complete

**Summary:** {summary}
**PR:** {pr_html_url}
**Branch:** `{branch_name}`

### Changes Made

{changes_list}

### Files Modified

{files_list}

### Testing

- [x] Unit tests added/updated
- [x] All tests passing
- [x] Lint checks passing

### Next Steps

PR is ready for review. Merge to deploy.

---

_Automated implementation by Claude Agent_
```

### Bug Fix Complete

```markdown
## ✅ Bug Fix Complete

**Issue:** {issue_key}

### Summary

Fixed {bug_description}

### Root Cause

{root_cause}

### Solution

{solution_description}

### Changes

- {change_1}
- {change_2}

### Testing

- [x] Unit tests passing
- [x] Integration tests passing
- [x] Manual testing completed

### Related PR

{pr_link}

---

_Automated fix by Claude Agent_
```

### Code Review Complete

```markdown
## ✅ Code Review Complete

**Summary:** {summary}

### Review Findings

{findings_list}

### Suggestions

{suggestions_list}

### Approval Status

{approval_status}

### Next Steps

{next_steps}

---

_Automated review by Claude Agent_
```

## Error Response Template

### Task Failed

```markdown
## ❌ Task Failed

**Error:** {error_message}

### Details

{error_details}

### Troubleshooting

{troubleshooting_steps}

### Next Steps

{next_steps}

---

_Automated response by Claude Agent_
```

## Status Update Template

### Status Change Notification

```markdown
## Status Update

**Previous Status:** {old_status}
**New Status:** {new_status}

### Reason

{reason}

### Next Actions

{next_actions}

---

_Automated update by Claude Agent_
```

## Best Practices

1. **Always include issue key** in response
2. **Use markdown** - MCP automatically converts to ADF
3. **Include structured sections** - Headers, lists, code blocks
4. **Link to related resources** - GitHub PRs, etc.
5. **Mark as automated** - Always include "_Automated by Claude Agent_"
6. **Use appropriate emoji** - ✅ for success, ❌ for errors
7. **Keep comments structured** - Use headers, lists, code blocks
8. **Include actionable next steps** - What should happen next?

## Markdown to ADF Conversion

**Note:** MCP server automatically converts markdown to ADF format. Use standard markdown:

- `# Header` → Heading 1
- `## Subheader` → Heading 2
- `- List item` → Bullet list
- `` `code` `` → Inline code
- `**bold**` → Bold text
- `*italic*` → Italic text

No manual conversion needed - just use markdown in the `body` parameter.
