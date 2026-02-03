# OAuth Service Architecture

## Overview

The OAuth Service manages OAuth tokens for multi-tenant, organization-level installations. Organizations install the OAuth app once, and all services use organization-level tokens. It handles OAuth flows for GitHub, Jira, and Slack integrations.

## Design Principles

1. **Organization-Level Tokens** - One token per org, not per user
2. **Automatic Refresh** - Handle token expiration transparently
3. **Centralized Management** - Single source of truth for all tokens
4. **Secure Storage** - Encrypted token storage

## Component Architecture

```mermaid
graph TB
    subgraph Users["Organization Admins"]
        UA[User Authorization]
    end

    subgraph Service["OAuth Service :8010"]
        FL[OAuth Flow Handler]
        CB[Callback Handler]
        TS[Token Service]
        IS[Installation Service]
    end

    subgraph Providers["OAuth Providers"]
        GH[GitHub OAuth]
        JR[Jira OAuth]
        SL[Slack OAuth]
    end

    subgraph Storage["Data Layer"]
        PG[(PostgreSQL)]
    end

    subgraph Consumers["Token Consumers"]
        GA[GitHub API]
        JA[Jira API]
        SA[Slack API]
    end

    UA --> FL
    FL --> GH
    FL --> JR
    FL --> SL

    GH --> CB
    JR --> CB
    SL --> CB

    CB --> TS
    TS --> PG

    GA --> TS
    JA --> TS
    SA --> TS

    IS --> PG
```

## Directory Structure

```
oauth-service/
├── main.py                    # FastAPI application
├── api/
│   ├── routes.py              # OAuth routes
│   └── server.py              # FastAPI app creation
├── providers/
│   ├── base.py                # Base OAuth provider
│   ├── github.py              # GitHub OAuth provider
│   ├── jira.py                # Jira OAuth provider
│   └── slack.py               # Slack OAuth provider
├── services/
│   ├── token_service.py       # Token storage and refresh
│   └── installation_service.py # Installation management
└── config/
    └── settings.py            # Configuration
```

## OAuth Provider Protocol

```mermaid
classDiagram
    class OAuthProviderProtocol {
        <<interface>>
        +get_authorization_url(state) str
        +exchange_code(code) TokenData
        +refresh_token(refresh_token) TokenData
        +revoke_token(token) void
    }

    class GitHubOAuthProvider {
        -client_id: str
        -client_secret: str
        +get_authorization_url(state)
        +exchange_code(code)
    }

    class JiraOAuthProvider {
        -client_id: str
        -client_secret: str
        +get_authorization_url(state)
        +exchange_code(code)
        +refresh_token(refresh_token)
    }

    class SlackOAuthProvider {
        -client_id: str
        -client_secret: str
        +get_authorization_url(state)
        +exchange_code(code)
    }

    OAuthProviderProtocol <|.. GitHubOAuthProvider
    OAuthProviderProtocol <|.. JiraOAuthProvider
    OAuthProviderProtocol <|.. SlackOAuthProvider
```

## OAuth Flow

### GitHub OAuth Flow

```mermaid
sequenceDiagram
    participant U as User
    participant OS as OAuth Service
    participant GH as GitHub

    U->>OS: GET /oauth/install/github
    OS->>OS: Generate state token
    OS-->>U: Redirect to GitHub

    U->>GH: Authorize App
    GH-->>U: Redirect to callback

    U->>OS: GET /oauth/callback/github?code=xxx
    OS->>GH: POST /access_token
    GH-->>OS: {access_token, refresh_token}

    OS->>OS: Store in PostgreSQL
    OS-->>U: Installation complete
```

### Token Refresh Flow

```mermaid
sequenceDiagram
    participant API as API Service
    participant OS as OAuth Service
    participant DB as PostgreSQL
    participant PR as Provider

    API->>OS: GET /oauth/token/github?org_id=xxx
    OS->>DB: Get token

    alt Token Valid
        DB-->>OS: Token
        OS-->>API: {access_token}
    else Token Expired
        DB-->>OS: Expired token + refresh_token
        OS->>PR: Refresh token
        PR-->>OS: New tokens
        OS->>DB: Update tokens
        OS-->>API: {access_token}
    end
```

## Token Service Protocol

```mermaid
classDiagram
    class TokenServiceProtocol {
        <<interface>>
        +store_token(platform, org_id, tokens) Installation
        +get_token(platform, org_id) TokenData
        +refresh_token(platform, org_id) TokenData
        +revoke_token(platform, org_id) void
        +list_installations(platform) List~Installation~
    }

    class TokenService {
        -db: AsyncSession
        -encryption_key: str
        +store_token(platform, org_id, tokens)
        +get_token(platform, org_id)
        +refresh_token(platform, org_id)
    }

    TokenServiceProtocol <|.. TokenService
```

## Data Model

```mermaid
erDiagram
    INSTALLATION {
        uuid id PK
        string platform
        string external_org_id
        string external_org_name
        string access_token
        string refresh_token
        datetime token_expires_at
        json scopes
        string status
        json metadata_json
        datetime created_at
        datetime updated_at
    }
```

### Installation Status Values

| Status | Description |
|--------|-------------|
| ACTIVE | Token valid and usable |
| EXPIRED | Token expired, needs refresh |
| REVOKED | User revoked access |
| ERROR | Refresh failed |

## API Endpoints

### OAuth Flows

```mermaid
graph LR
    subgraph OAuth["/oauth"]
        O1["GET /install/{platform}"]
        O2["GET /callback/{platform}"]
    end
```

### Token Management

```mermaid
graph LR
    subgraph Tokens["/oauth"]
        T1["GET /token/{platform}?org_id=xxx"]
        T2["GET /installations?platform=xxx"]
        T3["DELETE /installations/{id}"]
    end
```

## Security

### Token Encryption

```mermaid
flowchart TB
    A[Access Token] --> B[Fernet Encryption]
    B --> C[Encrypted Token]
    C --> D[(PostgreSQL)]

    D --> E[Encrypted Token]
    E --> F[Fernet Decryption]
    F --> G[Access Token]
```

### Webhook Secret vs OAuth Token

| Type | Scope | Purpose |
|------|-------|---------|
| Webhook Secret | App-level | Verify webhook signatures |
| OAuth Token | Org-level | API access per organization |

## Testing Strategy

Tests focus on **behavior**, not implementation:

- ✅ "Store token creates installation record"
- ✅ "Get token returns valid token"
- ✅ "Expired token triggers refresh"
- ❌ "Fernet.encrypt called with correct key"

## Integration Points

### With API Services
```
GitHub API → GET /oauth/token/github?org_id=xxx → OAuth Service
Jira API → GET /oauth/token/jira?org_id=xxx → OAuth Service
Slack API → GET /oauth/token/slack?workspace_id=xxx → OAuth Service
```

### With Dashboard
```
Dashboard → GET /oauth/installations?platform=github → OAuth Service
```
