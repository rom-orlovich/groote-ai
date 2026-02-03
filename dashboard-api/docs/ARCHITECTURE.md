# Dashboard API Architecture

## Overview

The Dashboard API provides REST endpoints and WebSocket connections for the groote-ai dashboard. It handles task management, analytics, conversations, webhook status monitoring, and real-time updates.

## Design Principles

1. **Real-Time First** - WebSocket hub for live task streaming
2. **Analytics Ready** - Pre-computed metrics and histograms
3. **Multi-Source** - Unified view across PostgreSQL and Redis
4. **Conversation Context** - Chat interface for agent interactions

## Component Architecture

```mermaid
graph TB
    subgraph Frontend["Dashboard Frontend"]
        RC[React Components]
        WC[WebSocket Client]
    end

    subgraph API["Dashboard API :5000"]
        REST[REST Endpoints]
        WSH[WebSocket Hub]
        AN[Analytics Service]
        CV[Conversation Service]
    end

    subgraph Storage["Data Layer"]
        PG[(PostgreSQL)]
        RD[(Redis)]
    end

    RC -->|HTTP| REST
    WC -->|WS| WSH

    REST --> PG
    REST --> RD
    AN --> PG
    CV --> PG

    WSH --> RD

    subgraph External["External Services"]
        AE[Agent Engine]
    end

    AE -->|Pub/Sub| RD
    RD -->|Subscribe| WSH
```

## Directory Structure

```
dashboard-api/
├── main.py                    # FastAPI application
├── api/
│   ├── dashboard.py           # Dashboard endpoints
│   ├── analytics.py           # Analytics endpoints
│   ├── conversations.py       # Conversation endpoints
│   ├── sources.py             # Data source management
│   ├── oauth_status.py        # OAuth status endpoints
│   ├── webhook_status.py      # Webhook monitoring
│   └── websocket.py           # WebSocket handler
├── core/
│   ├── config.py              # Configuration
│   ├── database/
│   │   ├── models.py          # SQLAlchemy models
│   │   ├── knowledge_models.py # Knowledge graph models
│   │   └── redis_client.py    # Redis client
│   ├── websocket_hub.py       # WebSocket connection manager
│   └── webhook_configs.py     # Webhook configuration loader
├── shared/
│   └── machine_models.py      # Shared Pydantic models
└── tests/
    ├── factories/             # Test data factories
    ├── conftest.py            # Shared fixtures
    └── test_*.py              # Test files
```

## API Structure

### REST Endpoints

```mermaid
graph LR
    subgraph Dashboard["/api"]
        D1["/status"]
        D2["/tasks"]
        D3["/tasks/{id}"]
        D4["/agents"]
    end

    subgraph Analytics["/api/analytics"]
        A1["/summary"]
        A2["/costs/histogram"]
        A3["/performance"]
    end

    subgraph Conversations["/api/conversations"]
        C1["GET /"]
        C2["POST /"]
        C3["GET /{id}/messages"]
    end

    subgraph Webhooks["/api/webhooks"]
        W1["/"]
        W2["/events"]
        W3["/stats"]
    end
```

## Data Flow

### Real-Time Task Streaming

```mermaid
sequenceDiagram
    participant FE as Frontend
    participant WS as WebSocket Hub
    participant RD as Redis Pub/Sub
    participant AE as Agent Engine

    FE->>WS: Connect to /ws
    FE->>WS: Subscribe to task:{task_id}

    AE->>RD: Publish task output
    RD->>WS: Receive message
    WS->>FE: Send to subscribed clients

    AE->>RD: Publish task completion
    RD->>WS: Receive message
    WS->>FE: Send final result
```

### WebSocket Protocol

```mermaid
sequenceDiagram
    participant C as Client
    participant S as Server

    C->>S: {"type": "subscribe", "channel": "task:123"}
    S-->>C: {"type": "subscribed", "channel": "task:123"}

    loop Task Execution
        S-->>C: {"type": "task_output", "output": "..."}
    end

    S-->>C: {"type": "task_status", "status": "completed"}
```

## Analytics Pipeline

```mermaid
graph TB
    subgraph Sources["Data Sources"]
        T[Tasks Table]
        S[Sessions Table]
    end

    subgraph Aggregation["Analytics Processing"]
        CS[Cost Summary]
        PM[Performance Metrics]
        HG[Histograms]
    end

    subgraph Output["API Response"]
        J1[JSON Summary]
        J2[Cost Breakdown]
        J3[Performance Report]
    end

    T --> CS
    T --> PM
    T --> HG
    S --> PM

    CS --> J1
    HG --> J2
    PM --> J3
```

### Metrics Computed

| Metric | Source | Aggregation |
|--------|--------|-------------|
| Total Cost | tasks.cost_usd | SUM |
| Avg Tokens | tasks.input_tokens + output_tokens | AVG |
| Success Rate | tasks.status | COUNT(completed) / COUNT(*) |
| Avg Duration | tasks.completed_at - created_at | AVG |
| Cost/Hour | tasks | GROUP BY hour |
| Tasks/Day | tasks | GROUP BY day |

## WebSocket Hub

```mermaid
classDiagram
    class WebSocketHub {
        -connections: Dict[str, WebSocket]
        -subscriptions: Dict[str, Set[str]]
        +connect(websocket, client_id)
        +disconnect(client_id)
        +subscribe(client_id, channel)
        +unsubscribe(client_id, channel)
        +broadcast(channel, message)
    }

    class RedisSubscriber {
        -hub: WebSocketHub
        +start()
        +on_message(channel, message)
    }

    WebSocketHub <-- RedisSubscriber
```

## Conversation Model

```mermaid
erDiagram
    CONVERSATION {
        uuid id PK
        string title
        string agent_type
        datetime created_at
    }

    MESSAGE {
        uuid id PK
        uuid conversation_id FK
        string role
        text content
        datetime created_at
    }

    TASK {
        uuid id PK
        uuid conversation_id FK
        string status
    }

    CONVERSATION ||--o{ MESSAGE : has
    CONVERSATION ||--o{ TASK : triggers
```

## Testing Strategy

Tests focus on **behavior**, not implementation:

- ✅ "GET /api/tasks returns paginated results"
- ✅ "WebSocket receives task updates"
- ✅ "Analytics summary includes cost breakdown"
- ❌ "SQLAlchemy query uses correct joins"

## Integration Points

### With Agent Engine
```
Agent Engine → Redis Pub/Sub → Dashboard API WebSocket → Frontend
```

### With External Dashboard
```
React Frontend → HTTP/WS → Dashboard API → PostgreSQL/Redis
```
