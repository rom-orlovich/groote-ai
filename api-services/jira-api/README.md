# Jira API Service

> REST API wrapper for Jira operations with issue and project management.

## Purpose

The Jira API service provides REST endpoints for Jira operations, including issue management, comment posting, JQL search, and project operations.

## Architecture

```
Agent Engine / MCP Server
         │
         │ HTTP Request (no credentials)
         ▼
┌─────────────────────────────────────┐
│      Jira API :3002                │
│                                     │
│  1. Receive HTTP request           │
│  2. Authenticate (internal token)  │
│  3. Get Jira credentials            │
│     - Email + API Token            │
│  4. Call Jira REST API             │
│  5. Return standardized response    │
└─────────────────────────────────────┘
         │
         │ HTTPS (Basic Auth)
         ▼
    Jira REST API v3
```

## Folder Structure

```
jira-api/
├── main.py                    # FastAPI application
├── api/
│   ├── routes.py              # API route definitions
│   └── server.py              # FastAPI app creation
├── client/
│   └── jira_client.py         # Jira API client
├── middleware/
│   └── auth.py                # Authentication middleware
└── config/
    └── settings.py            # Configuration
```

## Business Logic

### Core Responsibilities

1. **Issue Management**: Create, read, update Jira issues
2. **Comment Posting**: Post agent responses to Jira tickets
3. **JQL Search**: Execute JQL queries to find issues
4. **Transition Management**: Move issues through workflow states
5. **Project Operations**: List projects and project metadata
6. **Response Posting**: Post agent responses back to Jira tickets

## API Endpoints

All endpoints use the `/api/v1` prefix.

### Issues

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/issues/{issue_key}` | GET | Get issue details |
| `/api/v1/issues` | POST | Create issue |
| `/api/v1/issues/{issue_key}` | PUT | Update issue |
| `/api/v1/issues/{issue_key}/comments` | POST | Post comment |
| `/api/v1/issues/{issue_key}/transitions` | GET | Get transitions |
| `/api/v1/issues/{issue_key}/transitions` | POST | Execute transition |

### Search

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/search` | POST | Execute JQL query |

### Projects & Boards

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/projects` | GET | List all projects |
| `/api/v1/projects` | POST | Create project |
| `/api/v1/boards` | GET | List boards |
| `/api/v1/boards` | POST | Create board |

### Confluence

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/confluence/pages` | GET | List Confluence pages |
| `/api/v1/confluence/spaces` | GET | List Confluence spaces |

## Environment Variables

```bash
JIRA_URL=https://company.atlassian.net
JIRA_EMAIL=agent@company.com
JIRA_API_TOKEN=xxx
PORT=3002
LOG_LEVEL=INFO
```

## Authentication

Jira uses email + API token authentication:

1. **API Token**: Generated in Jira account settings
2. **Basic Auth**: Base64(email:api_token)
3. **Headers**: `Authorization: Basic <base64>`

## Usage Examples

### Get Issue

```bash
curl http://localhost:3002/issues/PROJ-123
```

### Post Comment

```bash
curl -X POST http://localhost:3002/issues/PROJ-123/comments \
  -H "Content-Type: application/json" \
  -d '{
    "body": "✅ Task completed successfully!"
  }'
```

### Search Issues

```bash
curl "http://localhost:3002/search?jql=project=PROJ%20AND%20status=Open"
```

### Transition Issue

```bash
curl -X POST http://localhost:3002/issues/PROJ-123/transitions \
  -H "Content-Type: application/json" \
  -d '{
    "transition": {"id": "21"}
  }'
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

## Health Check

```bash
curl http://localhost:3002/health
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md) - Component diagrams, data flows, design principles
- [Features](docs/features.md) - Feature list with test coverage status
- [Flows](docs/flows.md) - Process flow documentation

## Related Services

- **agent-engine**: Uses this service for response posting
- **mcp-servers/jira-mcp**: Calls this service for Jira operations
