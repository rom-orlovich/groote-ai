# GitHub MCP Development Guide

## Overview

Thin MCP wrapper around the GitHub API service. Exposes GitHub operations as tools for Claude Code CLI and other MCP clients.

## Key Principles

1. **Thin Wrapper** - No business logic, just protocol translation
2. **Passthrough Design** - All parameters passed directly to backend
3. **Formatted Output** - Results formatted for LLM consumption

## Structure

```
github-mcp/
├── main.py              # FastMCP server + tool registrations (15 tools)
├── github_mcp.py        # GitHubAPI HTTP client class
├── config.py            # Settings (port, github_api_url, timeout)
├── requirements.txt     # Runtime deps
├── requirements-dev.txt # Test deps
├── Dockerfile
└── tests/
    ├── conftest.py
    └── test_github_mcp.py
```

## Tools (15)

| Tool | Description |
|------|-------------|
| `get_repository` | Get repository details |
| `get_issue` | Get issue details |
| `create_issue` | Create a new issue |
| `add_issue_comment` | Comment on an issue |
| `add_reaction` | React to a comment |
| `create_pull_request` | Create a PR |
| `get_pull_request` | Get PR details |
| `create_pr_review_comment` | Review comment on PR |
| `get_file_contents` | Read file from repo |
| `search_code` | Search code across repos |
| `list_branches` | List repository branches |
| `list_repos` | List installation repos |
| `get_branch_sha` | Get branch HEAD SHA |
| `create_branch` | Create branch from SHA |
| `create_or_update_file` | Create/update file via Contents API |

## Adding a New Tool

1. Add HTTP method in `github_mcp.py` (GitHubAPI class)
2. Add tool function in `main.py` with `@mcp.tool()` decorator
3. Ensure corresponding endpoint exists in GitHub API service (port 3001)

## Testing

```bash
PYTHONPATH=mcp-servers/github-mcp:$PYTHONPATH uv run --with pytest --with pytest-asyncio --with respx --with httpx --with fastmcp --with pydantic-settings pytest mcp-servers/github-mcp/tests/ -v
```

## Development

- Port: 9001
- Backend: github-api:3001
- Language: Python
- Framework: FastMCP
- Max 300 lines per file, no comments, strict types, async/await for I/O
