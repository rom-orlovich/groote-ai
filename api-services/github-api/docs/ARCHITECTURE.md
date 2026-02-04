# GitHub API Service Architecture

## Overview

The GitHub API service provides REST endpoints for GitHub operations. It supports both single-tenant (Personal Access Token) and multi-tenant (OAuth per organization) authentication, acting as an abstraction layer between internal services and the GitHub API.

## Design Principles

1. **Token Abstraction** - Internal services don't handle GitHub tokens
2. **Multi-Tenant Ready** - OAuth tokens per organization
3. **Standardized Responses** - Unified error format across operations
4. **Rate Limit Aware** - Automatic retry with exponential backoff

## Component Architecture

```mermaid
graph TB
    subgraph Clients["Internal Clients"]
        AE[Agent Engine]
        MCP[GitHub MCP Server]
    end

    subgraph Service["GitHub API :3001"]
        MW[Auth Middleware]
        RT[Route Handlers]
        TC[Token Client]
        GC[GitHub Client]
    end

    subgraph External["External Services"]
        OS[OAuth Service]
        GH[GitHub REST API]
    end

    AE --> MW
    MCP --> MW

    MW --> RT
    RT --> TC
    TC -->|Multi-Tenant| OS
    TC -->|Single-Tenant| ENV[GITHUB_TOKEN]

    RT --> GC
    GC --> GH
```

## Directory Structure

```
github-api/
├── main.py                    # FastAPI application
├── api/
│   ├── routes.py              # API route definitions
│   └── server.py              # FastAPI app creation
├── client/
│   ├── github_client.py       # GitHub API client
│   └── multi_tenant_client.py # OAuth token management
├── middleware/
│   ├── auth.py                # Authentication middleware
│   └── error_handler.py       # Error handling
└── config/
    └── settings.py            # Configuration
```

## Token Resolution Flow

```mermaid
flowchart TB
    A[Request Received] --> B{Has org_id?}
    B -->|Yes| C[Query OAuth Service]
    B -->|No| D[Use GITHUB_TOKEN]

    C --> E{Token Found?}
    E -->|Yes| F[Use OAuth Token]
    E -->|No| D

    D --> G[Make GitHub API Call]
    F --> G
```

## API Endpoints

### Issues API

```mermaid
graph LR
    subgraph Issues["/issues/{owner}/{repo}/{number}"]
        I1["GET - Get Issue"]
        I2["GET /comments - List Comments"]
        I3["POST /comments - Add Comment"]
    end
```

### Pull Requests API

```mermaid
graph LR
    subgraph PRs["/pulls/{owner}/{repo}/{number}"]
        P1["GET - Get PR"]
        P2["GET /comments - List Comments"]
        P3["POST /comments - Add Comment"]
        P4["POST /reviews - Create Review"]
    end
```

### Repository API

```mermaid
graph LR
    subgraph Repos["/repos"]
        R1["GET /{owner}/{repo} - Get Repo"]
        R2["GET /{owner}/{repo}/contents/{path} - Read File"]
        R3["POST /{owner}/{repo}/contents/{path} - Write File"]
    end
```

## GitHub Client Protocol

```mermaid
classDiagram
    class GitHubClientProtocol {
        <<interface>>
        +get_issue(owner, repo, number) Issue
        +post_comment(owner, repo, number, body) Comment
        +get_pr(owner, repo, number) PullRequest
        +create_review(owner, repo, number, body, event) Review
        +read_file(owner, repo, path) FileContent
        +write_file(owner, repo, path, content, message) FileCommit
    }

    class GitHubClient {
        -token: str
        -base_url: str
        +get_issue(owner, repo, number)
        +post_comment(owner, repo, number, body)
    }

    class MultiTenantClient {
        -oauth_service_url: str
        -default_token: str
        +get_token(org_id) str
        +get_client(org_id) GitHubClient
    }

    GitHubClientProtocol <|.. GitHubClient
    MultiTenantClient --> GitHubClient
```

## Data Flow

### Post Comment Flow

```mermaid
sequenceDiagram
    participant AE as Agent Engine
    participant API as GitHub API Service
    participant OS as OAuth Service
    participant GH as GitHub

    AE->>API: POST /issues/{owner}/{repo}/123/comments
    API->>OS: GET /oauth/token/github?org_id={org}
    OS-->>API: {access_token: "..."}
    API->>GH: POST /repos/{owner}/{repo}/issues/123/comments
    GH-->>API: 201 Created
    API-->>AE: {id: 456, body: "..."}
```

## Rate Limiting

```mermaid
graph TB
    A[API Request] --> B[Make GitHub Call]
    B --> C{Rate Limited?}
    C -->|No| D[Return Response]
    C -->|Yes| E[Wait + Retry]
    E --> F{Retry Count < 3?}
    F -->|Yes| B
    F -->|No| G[Return 429 Error]
```

| Limit Type | Value | Reset |
|------------|-------|-------|
| Core | 5,000/hour | Hourly |
| Search | 30/minute | Per minute |
| GraphQL | 5,000 points/hour | Hourly |

## Error Handling

### Error Response Format

```json
{
    "error": "not_found",
    "message": "Issue #999 not found",
    "status_code": 404,
    "details": {
        "owner": "acme",
        "repo": "project",
        "issue_number": 999
    }
}
```

### Error Mapping

| GitHub Status | Service Error | Message |
|--------------|---------------|---------|
| 404 | not_found | Resource not found |
| 401 | unauthorized | Invalid token |
| 403 | forbidden | Rate limited or no access |
| 422 | validation_error | Invalid request |

## Testing Strategy

Tests focus on **behavior**, not implementation:

- ✅ "Post comment returns comment ID"
- ✅ "Multi-tenant falls back to default token"
- ✅ "Rate limit triggers retry"
- ❌ "httpx.AsyncClient called with correct headers"

## Integration Points

### With OAuth Service
```
GitHub API → GET /oauth/token/github?org_id={org} → OAuth Service
```

### With Agent Engine
```
Agent Engine → POST /issues/{owner}/{repo}/{num}/comments → GitHub API → GitHub
```

### With MCP Server
```
GitHub MCP → GET /repos/{owner}/{repo}/contents/{path} → GitHub API → GitHub
```
