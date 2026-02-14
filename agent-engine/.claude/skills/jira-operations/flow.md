# Jira Operations Workflow

Complete workflow for handling Jira operations using MCP tools.

## Workflow Overview

```
Task Received → Analyze → Execute → Post Response → Update Status
```

## Step-by-Step Workflow

### 1. Receive Task from Jira

**Task Metadata Required:**

```json
{
  "source": "jira",
  "source_metadata": {
    "ticket_key": "PROJ-123",
    "project": "PROJ"
  }
}
```

### 2. Get Issue Details

**Use MCP tool:**

```
jira:get_issue
```

**Example:**

```json
{
  "tool": "jira:get_issue",
  "arguments": {
    "issue_key": "PROJ-123"
  }
}
```

### 3. Analyze Task

Based on issue description and requirements, determine:

- What needs to be done
- Which repositories/files are affected
- Complexity level

### 4. Execute Task

Execute the requested work (code analysis, bug fix, feature implementation, etc.)

### 5. Post Response

**Always post comment to originating ticket** using `issue_key` from task metadata.

**Use MCP tool:**

```
jira:add_jira_comment
```

**Required Parameters:**

- `issue_key`: Jira issue key from `source_metadata.ticket_key`
- `body`: Comment body (markdown, automatically converted to ADF)

**See [templates.md](templates.md) for complete templates.**

**Example:**

```json
{
  "tool": "jira:add_jira_comment",
  "arguments": {
    "issue_key": "PROJ-123",
    "body": "## ✅ Analysis Complete\n\nFound authentication bug in login.py line 45.\n\n### Recommendations\n- Add rate limiting\n- Fix validation logic"
  }
}
```

### 6. Update Issue Status (Optional)

**Use MCP tool:**

```
jira:transition_issue
```

**Common Transitions:**

- "In Progress" → Transition ID: `21`
- "In Review" → Transition ID: `31`
- "Done" → Transition ID: `41`

**Example:**

```json
{
  "tool": "jira:transition_issue",
  "arguments": {
    "issue_key": "PROJ-123",
    "transition_id": "21"
  }
}
```

## Common Workflows

### Workflow 1: Issue Analysis

1. Receive Jira issue with "AI-Fix" label
2. Get issue details: `jira:get_issue`
3. Analyze codebase (use GitHub MCP tools)
4. Post analysis comment: `jira:add_jira_comment`
5. Update status to "In Review": `jira:transition_issue`

### Workflow 2: Bug Fix Implementation

1. Receive Jira issue
2. Get issue details: `jira:get_issue`
3. Create fix (use GitHub operations)
4. Post implementation comment: `jira:add_jira_comment`
5. Update status to "Done": `jira:transition_issue`

### Workflow 3: Code Review Request

1. Receive Jira issue requesting code review
2. Review code (use GitHub MCP tools)
3. Post review comments: `jira:add_jira_comment`
4. Update status based on review outcome

## Markdown to ADF Conversion

**Important:** MCP server automatically converts markdown to ADF format.

**Use standard markdown:**

- `# Header` → Heading 1
- `## Subheader` → Heading 2
- `- List item` → Bullet list
- `` `code` `` → Inline code
- `**bold**` → Bold text
- `*italic*` → Italic text

**No manual conversion needed** - just use markdown in the `body` parameter.

## Templates

**See [templates.md](templates.md) for complete templates** including:

- Analysis complete templates
- Implementation complete templates
- Bug fix templates
- Error response templates
- MCP tool call examples

### Workflow 4: Project & Board Setup

1. Create project: `jira:create_jira_project`
2. Create board: `jira:create_jira_board`
3. Create initial epics and tasks: `jira:create_jira_issue`
4. Post confirmation to Slack thread

**Example: Create project + board**

```json
{
  "tool": "jira:create_jira_project",
  "arguments": {
    "key": "GROOTE",
    "name": "Groote AI",
    "project_type_key": "software",
    "description": "AI-powered development assistant for GitHub, Jira, and Slack"
  }
}
```

```json
{
  "tool": "jira:create_jira_board",
  "arguments": {
    "name": "Groote AI Kanban",
    "project_key": "GROOTE",
    "board_type": "kanban"
  }
}
```

### Workflow 5: Self-Directed Task Creation

When the agent analyzes a repo and creates tickets:

1. List existing projects: `jira:search_jira_issues` (JQL: `project = KEY`)
2. Create structured issues using templates from [templates.md](templates.md)
3. Use proper markdown with real newlines (never literal `\n`)
4. Link related issues via description references

**Issue format rules:**
- Summary: `[Component] Action - Detail` (max 80 chars)
- Description: Use markdown with `## Headings`, `- Bullets`, `` `code` ``
- Always include: Overview, Acceptance Criteria, Technical Notes sections

## Error Handling

**If task fails:**

1. Post error comment using `jira:add_jira_comment`
2. See [templates.md](templates.md) for error templates
3. Include error details and troubleshooting steps
4. Update status if needed

## Best Practices

1. **Always use MCP tools** for Jira API operations
2. **Use markdown** - MCP automatically converts to ADF
3. **Post responses** after every task completion
4. **Include issue key** in all comments
5. **Update status** when appropriate (In Progress, Done, etc.)
6. **Link to related resources** - GitHub PRs, etc.
7. **Keep comments structured** - Use headers, lists, code blocks
8. **Mark as automated** - Include "_Automated by Claude Agent_"
9. **Use templates** from [templates.md](templates.md) for consistent formatting
