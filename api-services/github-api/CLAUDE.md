# GitHub API Service

REST API wrapper for GitHub operations with multi-tenant OAuth support.

## Development

- Port: 3001
- Language: Python
- Framework: FastAPI
- Max 300 lines per file, no comments, strict types, async/await for I/O
- Tests: `uv run pytest api-services/github-api/tests/ -v`

## Key Features

- Single-tenant (Personal Access Token) and multi-tenant (OAuth) support
- Issue and PR management
- File content reading/writing
- Credential isolation (stored only in this container)

## Environment

```bash
GITHUB_TOKEN=ghp_xxx
OAUTH_SERVICE_URL=http://oauth-service:8010
INTERNAL_SERVICE_KEY=xxx
USE_OAUTH=true
PORT=3001
```
