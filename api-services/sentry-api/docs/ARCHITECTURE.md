# Sentry API Service Architecture

## Overview

The Sentry API service provides REST endpoints for Sentry operations, including issue retrieval, event analysis, release management, and alert handling. It abstracts the Sentry API for internal services to enable error tracking integration.

## Design Principles

1. **Token Abstraction** - Internal services don't handle Sentry tokens
2. **Event Aggregation** - Group related errors and events
3. **Release Tracking** - Associate errors with deployments
4. **Alert Integration** - Process Sentry alerts for automation

## Component Architecture

```mermaid
graph TB
    subgraph Clients["Internal Clients"]
        AE[Agent Engine]
        MCP[Sentry MCP Server]
    end

    subgraph Service["Sentry API :3004"]
        MW[Auth Middleware]
        RT[Route Handlers]
        SC[Sentry Client]
    end

    subgraph External["External"]
        SE[Sentry API]
    end

    AE --> MW
    MCP --> MW

    MW --> RT
    RT --> SC
    SC -->|Bearer Token| SE
```

## Directory Structure

```
sentry-api/
├── main.py                    # FastAPI application
├── api/
│   ├── routes.py              # API route definitions
│   └── server.py              # FastAPI app creation
├── client/
│   └── sentry_client.py       # Sentry API client
├── middleware/
│   ├── auth.py                # Authentication middleware
│   └── error_handler.py       # Error handling
└── config/
    └── settings.py            # Configuration
```

## Authentication Flow

```mermaid
flowchart TB
    A[Request Received] --> B[Load SENTRY_AUTH_TOKEN]
    B --> C[Authorization: Bearer {token}]
    C --> D[Make Sentry API Call]
```

## API Endpoints

### Issues API

```mermaid
graph LR
    subgraph Issues["/issues"]
        I1["GET / - List Issues"]
        I2["GET /{id} - Get Issue"]
        I3["GET /{id}/events - Get Events"]
        I4["PUT /{id} - Update Issue"]
    end
```

### Projects API

```mermaid
graph LR
    subgraph Projects["/projects"]
        P1["GET / - List Projects"]
        P2["GET /{org}/{proj} - Get Project"]
        P3["GET /{org}/{proj}/issues - Project Issues"]
    end
```

### Events API

```mermaid
graph LR
    subgraph Events["/events"]
        E1["GET /{id} - Get Event"]
        E2["GET /{id}/stacktrace - Get Stacktrace"]
    end
```

## Sentry Client Protocol

```mermaid
classDiagram
    class SentryClientProtocol {
        <<interface>>
        +list_issues(project) List~Issue~
        +get_issue(issue_id) Issue
        +get_events(issue_id) List~Event~
        +get_stacktrace(event_id) Stacktrace
        +update_issue(issue_id, status) Issue
        +list_projects() List~Project~
    }

    class SentryClient {
        -token: str
        -base_url: str
        +list_issues(project)
        +get_issue(issue_id)
        +get_events(issue_id)
        +update_issue(issue_id, status)
    }

    SentryClientProtocol <|.. SentryClient
```

## Data Flow

### Issue Analysis Flow

```mermaid
sequenceDiagram
    participant AE as Agent Engine
    participant API as Sentry API Service
    participant SE as Sentry

    AE->>API: GET /issues/{id}
    API->>SE: GET /api/0/issues/{id}/
    SE-->>API: Issue details

    AE->>API: GET /issues/{id}/events
    API->>SE: GET /api/0/issues/{id}/events/
    SE-->>API: Event list

    API->>SE: GET /api/0/events/{event_id}/
    SE-->>API: Event with stacktrace

    API-->>AE: Aggregated issue data
```

## Issue Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Unresolved: New Error
    Unresolved --> Ignored: Ignore
    Unresolved --> Resolved: Resolve
    Resolved --> Unresolved: Regression
    Ignored --> Unresolved: Unignore
```

### Issue Status Values

| Status | Description |
|--------|-------------|
| unresolved | Active issue |
| resolved | Marked as fixed |
| ignored | Suppressed |
| resolvedInNextRelease | Auto-resolve on deploy |

## Event Aggregation

```mermaid
graph TB
    subgraph Events["Raw Events"]
        E1[Event 1]
        E2[Event 2]
        E3[Event 3]
    end

    subgraph Grouping["Fingerprint Grouping"]
        FP[Fingerprint Hash]
    end

    subgraph Issue["Aggregated Issue"]
        IS[Issue]
        CT[Event Count]
        LT[Last Seen]
    end

    E1 --> FP
    E2 --> FP
    E3 --> FP
    FP --> IS
    IS --> CT
    IS --> LT
```

## Stacktrace Format

```json
{
    "issue_id": "12345",
    "event_id": "abc123",
    "stacktrace": {
        "frames": [
            {
                "filename": "src/main.py",
                "function": "process_request",
                "lineno": 42,
                "context_line": "    result = await handler(request)",
                "pre_context": ["    try:", "        validate(request)"],
                "post_context": ["    except Exception as e:", "        log_error(e)"]
            }
        ]
    }
}
```

## Error Handling

### Error Response Format

```json
{
    "error": "not_found",
    "message": "Issue 99999 not found",
    "status_code": 404,
    "details": {
        "issue_id": "99999"
    }
}
```

### Error Mapping

| Sentry Status | Service Error | Message |
|---------------|---------------|---------|
| 404 | not_found | Issue not found |
| 401 | unauthorized | Invalid token |
| 403 | forbidden | No access to project |
| 429 | rate_limited | Rate limited |

## Testing Strategy

Tests focus on **behavior**, not implementation:

- ✅ "Get issue returns issue with event count"
- ✅ "Get events returns stacktraces"
- ✅ "Update issue changes status"
- ❌ "httpx.AsyncClient called with correct headers"

## Integration Points

### With Agent Engine
```
Agent Engine → GET /issues/{id}/events → Sentry API → Sentry
```

### With MCP Server
```
Sentry MCP → GET /projects/{org}/{proj}/issues → Sentry API → Sentry
```

### With API Gateway (Alerts)
```
Sentry → POST /webhooks/sentry → API Gateway → Agent Engine
```
