# API Services

> REST API wrappers for external services (GitHub, Jira, Slack) with isolated credential management.

## Purpose

API Services provide REST endpoints that wrap external service APIs. They serve as a security boundary where API keys are isolated in dedicated containers. MCP servers and agent engines call these services via HTTP.

## Architecture

```
Agent Engine / MCP Server
         │
         │ HTTP Request (no credentials)
         ▼
┌─────────────────────────────────────┐
│      API Service Container         │
│                                     │
│  1. Receive HTTP request           │
│  2. Authenticate (internal token)  │
│  3. Add API credentials             │
│  4. Call external API               │
│  5. Return standardized response    │
└─────────────────────────────────────┘
         │
         │ HTTPS (with credentials)
         ▼
External API (GitHub/Jira/Slack)
```

## Folder Structure

```
api-services/
├── README.md                 # This file
├── docker-compose.services.yml
├── github-api/
│   ├── main.py              # FastAPI app
│   ├── api/
│   │   └── routes.py        # API endpoints
│   ├── client/
│   │   ├── github_client.py # GitHub API client
│   │   └── multi_tenant_client.py # OAuth support
│   └── middleware/
│       └── auth.py          # Authentication
├── jira-api/                # Similar structure
└── slack-api/                # Similar structure
```

## Services

| Service    | Port | External API    | Credential Type               |
| ---------- | ---- | --------------- | ----------------------------- |
| GitHub API | 3001 | GitHub REST API | Personal Access Token / OAuth |
| Jira API   | 3002 | Jira REST API   | API Token + Email             |
| Slack API  | 3003 | Slack Web API   | Bot Token (OAuth)             |

## Security Model

**Key Principle**: API keys are ONLY stored in API service containers.

- GitHub token → `github-api` container only
- Jira credentials → `jira-api` container only
- Slack bot token → `slack-api` container only

MCP servers and agent engines have NO access to API keys.

## GitHub API Service

**Purpose**: Wrapper for GitHub REST API operations.

**Key Operations**:

- Issue and PR management
- Comment posting and reactions
- File content reading/writing
- Branch management and code search
- Multi-tenant OAuth support

**Endpoints** (prefix: `/api/v1`):

- `GET /repos/{owner}/{repo}/issues/{number}` - Get issue
- `POST /repos/{owner}/{repo}/issues/{number}/comments` - Post comment
- `GET /repos/{owner}/{repo}/pulls/{number}` - Get PR
- `POST /repos/{owner}/{repo}/pulls/{number}/comments` - Post PR review comment
- `GET /repos/{owner}/{repo}/contents/{path}` - Read file
- `PUT /repos/{owner}/{repo}/contents/{path}` - Create/update file

**Environment**:

```bash
GITHUB_TOKEN=ghp_xxx
GITHUB_OAUTH_CLIENT_ID=xxx      # Multi-tenant
GITHUB_OAUTH_CLIENT_SECRET=xxx  # Multi-tenant
```

## Jira API Service

**Purpose**: Wrapper for Jira REST API operations.

**Key Operations**:

- Issue management (create, get, update)
- Comment posting
- JQL search (POST-based)
- Transition management
- Project and board management
- Confluence pages and spaces

**Endpoints** (prefix: `/api/v1`):

- `GET /issues/{issue_key}` - Get issue
- `POST /issues` - Create issue
- `POST /issues/{issue_key}/comments` - Post comment
- `POST /search` - JQL search
- `GET /projects` - List projects
- `GET /boards` - List boards
- `GET /confluence/pages` - List Confluence pages

**Environment**:

```bash
JIRA_URL=https://company.atlassian.net
JIRA_EMAIL=agent@company.com
JIRA_API_TOKEN=xxx
```

## Slack API Service

**Purpose**: Wrapper for Slack Web API operations.

**Key Operations**:

- Message posting with Block Kit support
- Thread replies and message updates
- Channel operations (list, info, history)
- User information lookup
- Reaction management

**Endpoints** (prefix: `/api/v1`):

- `POST /messages` - Send message
- `PUT /messages` - Update message
- `POST /reactions` - Add reaction
- `GET /channels` - List channels
- `GET /channels/{channel}/history` - Get message history
- `GET /users/{user_id}` - Get user info

**Environment**:

```bash
SLACK_BOT_TOKEN=xoxb-xxx
```

## Error Handling

Standardized error responses:

```json
{
  "error": "not_found",
  "message": "Issue PROJ-999 not found",
  "status_code": 404
}
```

## Health Checks

```bash
curl http://localhost:3001/health  # GitHub
curl http://localhost:3002/health  # Jira
curl http://localhost:3003/health  # Slack
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md) - Component diagrams and data flows
- [Features](docs/features.md) - Feature list and capabilities
- [Flows](docs/flows.md) - Process flow documentation

## Related Services

- **mcp-servers**: Call API services for external operations
- **agent-engine**: Uses API services for response posting
- **oauth-service**: Manages OAuth tokens for multi-tenant support
