---
name: github-operations
description: GitHub API operations using MCP tools. Use for reading files, searching code, managing issues/PRs, and posting comments. All operations go through the GitHub MCP server.
---

GitHub operations using MCP tools (`github:*`) for ALL interactions.

> **CRITICAL:** NEVER use local git commands (`git clone`, `git push`, `git checkout`, etc.). You have NO git credentials in the container. ALL GitHub operations MUST go through MCP tools.

## MCP Tools Available

| Tool | Purpose |
|------|---------|
| `github:get_file_contents` | Read file contents (specify `ref` for branch/SHA) |
| `github:search_code` | Search code across repositories |
| `github:get_repository` | Get repository metadata (do NOT use `list_repos` without filters) |
| `github:get_issue` | Get issue details |
| `github:create_issue` | Create new issues |
| `github:add_issue_comment` | Post comments on issues/PRs |
| `github:add_reaction` | React to comments (+1, -1, laugh, heart, rocket, eyes) |
| `github:get_pull_request` | Get PR details and diff |
| `github:create_pull_request` | Create PR (branch must already exist) |
| `github:create_pr_review_comment` | Comment on specific PR line |
| `github:list_branches` | List repository branches |

### NOT Available

- `create_or_update_file` — cannot commit files via API
- `git clone` / `git push` — no git credentials in container
- `list_repos` without owner — returns ALL repos, wastes tokens. Use `get_repository` with specific owner/repo instead

## Workflows

See [flow.md](flow.md) for complete workflow guide and [templates.md](templates.md) for response templates.

## Key Rules

1. **MCP tools only** — never use bash for git or GitHub API calls
2. **Post responses** after every task using `github:add_issue_comment`
3. **Use `get_repository`** with specific owner/repo, never `list_repos` unfiltered
4. **Code changes are read-only** — you can analyze code but cannot push changes. For fix requests, post the fix as an issue comment with code blocks
