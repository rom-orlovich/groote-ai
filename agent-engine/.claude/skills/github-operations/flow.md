# GitHub Operations Workflow

All GitHub operations use MCP tools (`github:*`). No local git commands.

## Decision Flow

```
Task Received → Classify Intent → Execute with MCP Tools → Post Response
```

### Intent Classification

| Keywords | Intent | Approach |
|----------|--------|----------|
| search, find, where, check, show | **Read** | `github:search_code` or `github:get_file_contents` |
| review, analyze, look at | **Analyze** | `github:get_pull_request` + `github:get_file_contents` |
| fix, implement, change, update | **Fix Request** | Analyze → post fix as issue comment with code blocks |
| create issue, report bug | **Create** | `github:create_issue` |

## Workflows

### 1. Code Search / File Reading

```
github:search_code(query="auth middleware", per_page=10)
  → Review results
  → github:get_file_contents(owner, repo, path, ref="main")
  → Analyze and respond
```

### 2. Issue Analysis

```
github:get_issue(owner, repo, issue_number)
  → Read referenced files with github:get_file_contents
  → Use knowledge tools if available (llamaindex:knowledge_query, gkg:find_usages)
  → github:add_issue_comment(owner, repo, issue_number, body=analysis)
```

### 3. Fix Request (Code Changes)

You CANNOT push code. Instead:

1. Analyze the problem using `github:get_file_contents` and `github:search_code`
2. Write the fix in your response as code blocks
3. Post via `github:add_issue_comment` with:
   - Problem summary
   - Exact file paths and line numbers
   - Complete code fix in fenced code blocks
   - Testing suggestions

```
github:get_file_contents(owner, repo, "path/to/file.py")
  → Analyze and write fix
  → github:add_issue_comment(owner, repo, issue_number, body=fix_with_code_blocks)
```

### 4. PR Review

```
github:get_pull_request(owner, repo, pr_number)
  → For each changed file: github:get_file_contents(owner, repo, path, ref=head_sha)
  → Analyze changes
  → github:add_issue_comment(owner, repo, pr_number, body=review)
```

For line-specific comments:
```
github:create_pr_review_comment(owner, repo, pr_number, body, commit_id, path, line)
```

### 5. PR Improvement (Requested Changes)

When a PR comment asks for code changes:

1. Read the PR and comment to understand the request
2. Read relevant files via `github:get_file_contents`
3. Write the improved code
4. Post the fix as an issue comment with code blocks and instructions

You CANNOT push commits to the PR branch. Always post code as comments.

## Response Posting

**Always post a response** after completing any task:

- Issues: `github:add_issue_comment`
- PRs: `github:add_issue_comment` (same tool, PRs are issues)
- Line comments: `github:create_pr_review_comment`

See [templates.md](templates.md) for response formatting.

## Error Handling

If a task fails or is beyond your capabilities:

1. Post an error response via `github:add_issue_comment`
2. Explain what was attempted and what failed
3. Suggest manual steps the user can take

## Anti-Patterns (NEVER DO)

- `git clone` — no git credentials, will fail
- `git push` — no git credentials, will fail
- `curl` to GitHub API — use MCP tools instead
- `list_repos` without owner — returns all repos, wastes tokens
- Spending more than 3 tool calls trying to push code — it's not possible
