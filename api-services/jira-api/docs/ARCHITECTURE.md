# Jira API Service Architecture

## Overview

The Jira API service provides REST endpoints for Jira operations, including issue management, comment posting, JQL search, and project operations. It abstracts the Jira REST API for internal services.

## Design Principles

1. **Authentication Abstraction** - Internal services don't handle Jira credentials
2. **JQL Support** - Full JQL query capabilities for complex searches
3. **Transition Management** - Handle workflow state changes
4. **Standardized Responses** - Unified error format

## Component Architecture

```mermaid
graph TB
    subgraph Clients["Internal Clients"]
        AE[Agent Engine]
        MCP[Jira MCP Server]
    end

    subgraph Service["Jira API :3002"]
        MW[Auth Middleware]
        RT[Route Handlers]
        JC[Jira Client]
    end

    subgraph External["External"]
        JR[Jira REST API v3]
    end

    AE --> MW
    MCP --> MW

    MW --> RT
    RT --> JC
    JC -->|Basic Auth| JR
```

## Directory Structure

```
jira-api/
├── main.py                    # FastAPI application
├── api/
│   ├── routes.py              # API route definitions
│   └── server.py              # FastAPI app creation
├── client/
│   └── jira_client.py         # Jira API client
├── middleware/
│   ├── auth.py                # Authentication middleware
│   └── error_handler.py       # Error handling
└── config/
    └── settings.py            # Configuration
```

## Authentication Flow

```mermaid
flowchart TB
    A[Request Received] --> B[Load Credentials]
    B --> C[JIRA_EMAIL + JIRA_API_TOKEN]
    C --> D[Base64 Encode]
    D --> E[Authorization: Basic {encoded}]
    E --> F[Make Jira API Call]
```

## API Endpoints

### Issues API

```mermaid
graph LR
    subgraph Issues["/issues/{issue_key}"]
        I1["GET - Get Issue"]
        I2["GET /comments - List Comments"]
        I3["POST /comments - Add Comment"]
        I4["POST /transitions - Transition Issue"]
    end
```

### Search API

```mermaid
graph LR
    subgraph Search["/search"]
        S1["GET ?jql={query} - JQL Search"]
    end
```

### Projects API

```mermaid
graph LR
    subgraph Projects["/projects"]
        P1["GET / - List Projects"]
        P2["GET /{key} - Get Project"]
    end
```

## Jira Client Protocol

```mermaid
classDiagram
    class JiraClientProtocol {
        <<interface>>
        +get_issue(issue_key) Issue
        +get_comments(issue_key) List~Comment~
        +add_comment(issue_key, body) Comment
        +transition_issue(issue_key, transition_id) void
        +search(jql, max_results) SearchResult
        +get_projects() List~Project~
    }

    class JiraClient {
        -base_url: str
        -email: str
        -api_token: str
        +get_issue(issue_key)
        +add_comment(issue_key, body)
        +transition_issue(issue_key, transition_id)
        +search(jql, max_results)
    }

    JiraClientProtocol <|.. JiraClient
```

## Data Flow

### Issue Transition Flow

```mermaid
sequenceDiagram
    participant AE as Agent Engine
    participant API as Jira API Service
    participant JR as Jira

    AE->>API: POST /issues/PROJ-123/transitions
    Note right of API: {transition: {id: "21"}}

    API->>JR: GET /issue/PROJ-123/transitions
    JR-->>API: Available transitions

    API->>JR: POST /issue/PROJ-123/transitions
    JR-->>API: 204 No Content

    API-->>AE: {status: "transitioned"}
```

### JQL Search Flow

```mermaid
sequenceDiagram
    participant Client as Internal Client
    participant API as Jira API Service
    participant JR as Jira

    Client->>API: GET /search?jql=project=PROJ AND status=Open
    API->>JR: POST /search with JQL
    JR-->>API: {issues: [...], total: 42}
    API-->>Client: {issues: [...], total: 42}
```

## Issue Workflow

```mermaid
stateDiagram-v2
    [*] --> Open: Create
    Open --> InProgress: Start Work
    InProgress --> Review: Submit
    Review --> Done: Approve
    Review --> InProgress: Request Changes
    Done --> [*]
```

### Transition IDs (Example)

| Transition | ID | From | To |
|------------|-----|------|-----|
| Start Progress | 11 | Open | In Progress |
| Submit | 21 | In Progress | Review |
| Approve | 31 | Review | Done |
| Reject | 41 | Review | In Progress |

## Error Handling

### Error Response Format

```json
{
    "error": "not_found",
    "message": "Issue PROJ-999 not found",
    "status_code": 404,
    "details": {
        "issue_key": "PROJ-999"
    }
}
```

### Error Mapping

| Jira Status | Service Error | Message |
|-------------|---------------|---------|
| 404 | not_found | Issue not found |
| 401 | unauthorized | Invalid credentials |
| 403 | forbidden | No access |
| 400 | bad_request | Invalid JQL |

## Testing Strategy

Tests focus on **behavior**, not implementation:

- ✅ "Get issue returns issue details"
- ✅ "JQL search returns matching issues"
- ✅ "Invalid transition returns error"
- ❌ "httpx.AsyncClient called with Basic auth header"

## Integration Points

### With Agent Engine
```
Agent Engine → POST /issues/PROJ-123/comments → Jira API → Jira
```

### With MCP Server
```
Jira MCP → GET /search?jql=... → Jira API → Jira
```
