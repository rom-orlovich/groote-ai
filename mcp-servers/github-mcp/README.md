# GitHub MCP Server

> FastMCP-based MCP server for GitHub operations.

## Purpose

The GitHub MCP server provides a Model Context Protocol interface for GitHub operations. It translates MCP tool calls into HTTP requests to the GitHub API service, keeping credentials isolated.

## Architecture

```
Agent Engine (via mcp.json)
         |
         | SSE Connection
         v
+-----------------------------------------+
|      GitHub MCP :9001                    |
|                                          |
|  1. Receive MCP tool call               |
|  2. Translate to HTTP request            |
|  3. Call github-api service              |
|     (no credentials)                     |
|  4. Return standardized response         |
+-----------------------------------------+
         |
         | HTTP (no credentials)
         v
+-----------------------------------------+
|      GitHub API Service :3001            |
|  (Has credentials, makes API call)       |
+-----------------------------------------+
```

## Folder Structure

```
github-mcp/
├── main.py              # FastMCP server + tool registrations
├── github_mcp.py        # GitHubAPI HTTP client class
├── config.py            # Settings
├── requirements.txt     # Runtime deps
├── requirements-dev.txt # Test deps
├── Dockerfile
└── tests/
    ├── conftest.py
    └── test_github_mcp.py
```

## MCP Tools (15)

### Repository Operations

| Tool | Description |
|------|-------------|
| `get_repository` | Get repository details (name, description, metadata) |
| `list_repos` | List repositories accessible to the installation |
| `get_file_contents` | Get file contents from a repository |
| `search_code` | Search for code across repositories |

### Issue Operations

| Tool | Description |
|------|-------------|
| `get_issue` | Get issue details (title, body, state, labels) |
| `create_issue` | Create a new issue with title, body, and labels |
| `add_issue_comment` | Add a comment to an issue |
| `add_reaction` | Add emoji reaction to a comment |

### Pull Request Operations

| Tool | Description |
|------|-------------|
| `get_pull_request` | Get PR details (title, body, state, diff) |
| `create_pull_request` | Create a PR (title, head, base, draft) |
| `create_pr_review_comment` | Add review comment on specific file/line |

### Branch & File Operations

| Tool | Description |
|------|-------------|
| `list_branches` | List repository branches |
| `get_branch_sha` | Get SHA of a branch HEAD |
| `create_branch` | Create a new branch from SHA |
| `create_or_update_file` | Create or update file via Contents API |

## Environment Variables

```bash
GITHUB_API_URL=http://github-api:3001
PORT=9001
REQUEST_TIMEOUT=30
```

## SSE Endpoint

MCP clients connect via Server-Sent Events:

```
GET /sse HTTP/1.1
Host: github-mcp:9001
Accept: text/event-stream
```

## Health Check

```bash
curl http://localhost:9001/health
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md) - Component diagrams and data flows
- [Features](docs/features.md) - Feature list and capabilities
- [Flows](docs/flows.md) - Process flow documentation

## Related Services

- **github-api**: Provides actual GitHub API operations (port 3001)
- **agent-engine**: Connects to this MCP server via SSE
