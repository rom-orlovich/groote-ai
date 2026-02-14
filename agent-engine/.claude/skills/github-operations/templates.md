# GitHub Response Templates

Post responses using `github:add_issue_comment`. Always include issue/PR number and mark as automated.

## Issue Analysis

```markdown
## Analysis Complete

**Issue:** #{issue_number}

### Summary
{summary}

### Findings
{findings_list}

### Recommendations
{recommendations}

### Files Analyzed
{files_list}

---
_Automated analysis by Groote AI_
```

## Fix Proposal

When asked to fix code but cannot push (no git credentials):

```markdown
## Proposed Fix

**Issue:** #{issue_number}

### Problem
{problem_description}

### Fix

**File:** `{file_path}`

```{language}
{fixed_code}
```

### How to Apply
1. Edit `{file_path}` at line {line_number}
2. Replace the existing code with the fix above
3. Run tests: `{test_command}`

### Testing
{testing_notes}

---
_Automated fix proposal by Groote AI_
```

## Code Review

```markdown
## Code Review

**PR:** #{pr_number}

### Summary
{review_summary}

### Findings
{findings_list}

### Suggestions
{suggestions_list}

---
_Automated review by Groote AI_
```

## Error Response

```markdown
## Task Failed

**Error:** {error_message}

### What Was Attempted
{attempted_steps}

### Suggested Next Steps
{next_steps}

---
_Automated response by Groote AI_
```
