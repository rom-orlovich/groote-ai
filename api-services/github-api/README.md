# GitHub API Service

> REST API wrapper for GitHub operations with multi-tenant OAuth support.

## Purpose

The GitHub API service provides REST endpoints for GitHub operations. It supports both single-tenant (Personal Access Token) and multi-tenant (OAuth per organization) authentication.

## Architecture

```
Agent Engine / MCP Server
         │
         │ HTTP Request (no credentials)
         ▼
┌─────────────────────────────────────┐
│      GitHub API :3001              │
│                                     │
│  1. Receive HTTP request           │
│  2. Authenticate (internal token)  │
│  3. Get GitHub token               │
│     - Single-tenant: GITHUB_TOKEN  │
│     - Multi-tenant: OAuth lookup   │
│  4. Call GitHub REST API           │
│  5. Return standardized response    │
└─────────────────────────────────────┘
         │
         │ HTTPS (with GitHub token)
         ▼
    GitHub REST API v3
```

## Folder Structure

```
github-api/
├── main.py                    # FastAPI application
├── api/
│   ├── routes.py              # API route definitions
│   └── server.py             # FastAPI app creation
├── client/
│   ├── github_client.py       # GitHub API client
│   └── multi_tenant_client.py # OAuth token management
├── middleware/
│   └── auth.py                # Authentication middleware
└── config/
    └── settings.py            # Configuration
```

## Business Logic

### Core Responsibilities

1. **Issue Management**: Create, read, update issues and comments
2. **PR Operations**: Review PRs, post comments, manage reviews
3. **File Operations**: Read and write repository files
4. **Repository Operations**: List repos, get repository metadata
5. **Multi-Tenant Support**: Handle OAuth tokens per organization
6. **Response Posting**: Post agent responses back to GitHub

## API Endpoints

All endpoints use the `/api/v1` prefix.

### Issues

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/repos/{owner}/{repo}/issues/{number}` | GET | Get issue details |
| `/api/v1/repos/{owner}/{repo}/issues` | POST | Create issue |
| `/api/v1/repos/{owner}/{repo}/issues/{number}/comments` | POST | Post issue comment |
| `/api/v1/repos/{owner}/{repo}/issues/comments/{id}/reactions` | POST | Add reaction |

### Pull Requests

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/repos/{owner}/{repo}/pulls/{number}` | GET | Get PR details |
| `/api/v1/repos/{owner}/{repo}/pulls/{number}/comments` | POST | Post PR review comment |
| `/api/v1/repos/{owner}/{repo}/pulls` | POST | Create pull request |

### Repository Files

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/repos/{owner}/{repo}/contents/{path}` | GET | Read file contents |
| `/api/v1/repos/{owner}/{repo}/contents/{path}` | PUT | Create/update file |

### Repositories & Search

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/repos/{owner}/{repo}` | GET | Get repository details |
| `/api/v1/repos/{owner}/{repo}/branches` | GET | List branches |
| `/api/v1/repos/{owner}/{repo}/git/ref/heads/{branch}` | GET | Get branch SHA |
| `/api/v1/repos/{owner}/{repo}/git/refs` | POST | Create branch |
| `/api/v1/search/code` | GET | Search code |
| `/api/v1/search/repositories` | GET | Search repositories |
| `/api/v1/installation/repos` | GET | List installation repos |
| `/api/v1/users/{username}/repos` | GET | List user repos |

## Environment Variables

```bash
GITHUB_TOKEN=ghp_xxx                    # Personal Access Token (single-tenant)
GITHUB_OAUTH_CLIENT_ID=xxx              # OAuth Client ID (multi-tenant)
GITHUB_OAUTH_CLIENT_SECRET=xxx          # OAuth Client Secret (multi-tenant)
OAUTH_SERVICE_URL=http://oauth-service:8010
PORT=3001
LOG_LEVEL=INFO
```

## OAuth Support

**Multi-Tenant Flow**:

1. Service receives request with `organization_id`
2. Calls `oauth-service` to lookup token for organization
3. Uses OAuth token for GitHub API calls
4. Falls back to `GITHUB_TOKEN` if no OAuth token found

**Single-Tenant Flow**:

1. Service receives request without `organization_id`
2. Uses `GITHUB_TOKEN` environment variable
3. Makes GitHub API call with token

## Usage Examples

### Post Issue Comment

```bash
curl -X POST http://localhost:3001/issues/owner/repo/123/comments \
  -H "Content-Type: application/json" \
  -d '{
    "body": "✅ Task completed successfully!"
  }'
```

### Get Issue

```bash
curl http://localhost:3001/issues/owner/repo/123
```

### Read File

```bash
curl http://localhost:3001/repos/owner/repo/contents/src/main.py
```

## Error Handling

Standardized error responses:

```json
{
  "error": "not_found",
  "message": "Issue not found",
  "status_code": 404
}
```

## Rate Limiting

Respects GitHub API rate limits:

- 5,000 requests/hour (authenticated)
- Automatic retry with exponential backoff

## Health Check

```bash
curl http://localhost:3001/health
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md) - Component diagrams, data flows, design principles
- [Features](docs/features.md) - Feature list with test coverage status
- [Flows](docs/flows.md) - Process flow documentation

## Related Services

- **oauth-service**: Provides OAuth tokens for multi-tenant support
- **agent-engine**: Uses this service for response posting
- **mcp-servers/github-mcp**: Calls this service for GitHub operations
