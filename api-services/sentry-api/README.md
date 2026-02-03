# Sentry API Service

> REST API wrapper for Sentry operations with issue management and error tracking.

## Purpose

The Sentry API service provides REST endpoints for Sentry operations, including issue retrieval, event analysis, comment posting, and status management.

## Architecture

```
Agent Engine / MCP Server
         │
         │ HTTP Request (no credentials)
         ▼
┌─────────────────────────────────────┐
│      Sentry API :3004               │
│                                     │
│  1. Receive HTTP request           │
│  2. Authenticate (internal token)  │
│  3. Get Sentry Auth Token          │
│  4. Call Sentry Web API            │
│  5. Return standardized response    │
└─────────────────────────────────────┘
         │
         │ HTTPS (Bearer Token)
         ▼
    Sentry Web API
```

## Business Logic

### Core Responsibilities

1. **Issue Retrieval**: Get issue details including stacktrace and metadata
2. **Event Analysis**: Retrieve error events with full context
3. **Comment Posting**: Post investigation notes and resolution updates
4. **Status Management**: Resolve, ignore, or reopen issues
5. **Impact Analysis**: Get affected user count and occurrence frequency
6. **Response Posting**: Post agent analysis back to Sentry issues

## API Endpoints

### Issues

| Endpoint                      | Method | Purpose              |
| ----------------------------- | ------ | -------------------- |
| `/issues/{issue_id}`          | GET    | Get issue details    |
| `/issues/{issue_id}/events`   | GET    | Get issue events     |
| `/issues/{issue_id}/comments` | POST   | Add comment          |
| `/issues/{issue_id}/status`   | PUT    | Update status        |

### Analysis

| Endpoint                           | Method | Purpose              |
| ---------------------------------- | ------ | -------------------- |
| `/issues/{issue_id}/affected-users`| GET    | Get affected users   |

## Environment Variables

```bash
SENTRY_AUTH_TOKEN=xxx
SENTRY_ORG=your-org
PORT=3004
LOG_LEVEL=INFO
```

## Usage Examples

### Get Issue

```bash
curl http://localhost:3004/issues/12345
```

### Get Issue Events

```bash
curl http://localhost:3004/issues/12345/events?limit=10
```

### Add Comment

```bash
curl -X POST http://localhost:3004/issues/12345/comments \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Investigating this issue..."
  }'
```

### Resolve Issue

```bash
curl -X PUT http://localhost:3004/issues/12345/status \
  -H "Content-Type: application/json" \
  -d '{
    "status": "resolved"
  }'
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

## Health Check

```bash
curl http://localhost:3004/health
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md) - Component diagrams, data flows, design principles
- [Features](docs/features.md) - Feature list with test coverage
- [Flows](docs/flows.md) - Process flow documentation

## Related Services

- **agent-engine**: Uses this service for response posting
- **mcp-servers/sentry-mcp**: Calls this service for Sentry operations
