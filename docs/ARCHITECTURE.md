# Groote AI Architecture

## Overview

Groote AI is a containerized system that automatically handles development tasks. When something happens in GitHub, Jira, or Slack, the system receives a webhook, processes it with AI agents, and responds back to the original service.

**What it does:**

- Receives webhooks from external services (GitHub, Jira, Slack)
- Processes tasks using AI agents (Claude or Cursor CLI)
- Executes code changes using Test-Driven Development
- Posts responses back to the originating service
- Scales horizontally to handle multiple tasks at once

**Key design principles:**

- Each service runs in its own Docker container for isolation
- Services communicate via APIs and queues (no direct imports)
- Optional knowledge layer can be enabled or disabled
- API keys are isolated in specific containers for security

---

## Architecture Diagrams

**Mermaid Diagram Standards:**

All diagrams follow the Mermaid diagram standards defined in `.cursor/rules/guidelines/diagrams-mermaid.mdc`:

- Always use Mermaid syntax (no ASCII art)
- Dark theme styling for better readability
- Descriptive labels and clear structure
- Proper diagram types for different use cases

### 2.1 System Overview

This diagram shows how all services connect together:

```mermaid
%%{init: {'theme':'base', 'themeVariables': {'fontSize':'24px', 'primaryColor':'#2d2d2d', 'primaryTextColor':'#ffffff', 'primaryBorderColor':'#ffffff', 'lineColor':'#ffffff', 'secondaryColor':'#1a1a1a', 'tertiaryColor':'#2d2d2d'}}}%%
graph TB
    subgraph External["External Services"]
        GitHub[GitHub]
        Jira[Jira]
        Slack[Slack]
    end

    subgraph Gateway["API Gateway :8000"]
        Webhooks["Webhook Handlers<br/>GitHub, Jira, Slack"]
    end

    subgraph Storage["Storage Layer"]
        Redis[Redis :6379<br/>Task Queue & Cache]
        Postgres[PostgreSQL :5432<br/>Persistent Data]
    end

    subgraph Engine["Agent Engine :8080-8089"]
        Agents["AI Agents<br/>brain, planning, executor<br/>github-issue-handler<br/>github-pr-review<br/>jira-code-plan<br/>slack-inquiry, verifier"]
        MCPConn["MCP Connections<br/>Server-Sent Events"]![alt text](image.png)
    end

    subgraph MCPServers["MCP Servers"]
        GitHubMCP[GitHub MCP :9001]
        JiraMCP[Jira MCP :9002]
        SlackMCP[Slack MCP :9003]
        KGMCP[Knowledge Graph MCP :9005]
        LlamaIndexMCP[LlamaIndex MCP :9006<br/>Optional]
        GKGMcp[GKG MCP :9007<br/>Optional]
    end

    subgraph APIServices["API Services<br/>Credentials Here"]
        GitHubAPI[GitHub API :3001]
        JiraAPI[Jira API :3002]
        SlackAPI[Slack API :3003]
    end

    subgraph Monitoring["Monitoring & Management"]
        DashboardAPI[Dashboard API :5000<br/>WebSocket, Analytics]
        ExternalDash[External Dashboard :3005<br/>React UI]
        OAuth[OAuth Service :8010<br/>Multi-provider OAuth]
        TaskLogger[Task Logger :8090<br/>Output Logging]
    end

    subgraph Knowledge["Knowledge Layer<br/>Optional"]
        ChromaDB[ChromaDB :8001<br/>Vector Database]
        LlamaIndex[LlamaIndex Service :8002<br/>Hybrid RAG]
        GKGService[GKG Service :8003<br/>Code Graph]
        IndexerWorker[Indexer Worker :8004<br/>Background Indexing]
    end

    External -->|Webhooks| Gateway
    Gateway -->|HTTP 200 OK<br/>Immediate Response| External
    Gateway --> Webhooks
    Webhooks --> Redis
    Webhooks --> Postgres
    Redis --> Engine
    Postgres --> Engine
    Engine --> Agents
    Engine --> MCPConn
    MCPConn -->|SSE| MCPServers
    MCPServers --> GitHubMCP
    MCPServers --> JiraMCP
    MCPServers --> SlackMCP
    MCPServers --> KGMCP
    MCPServers -.->|Optional| LlamaIndexMCP
    MCPServers -.->|Optional| GKGMcp
    GitHubMCP -->|HTTP| GitHubAPI
    JiraMCP -->|HTTP| JiraAPI
    SlackMCP -->|HTTP| SlackAPI
    KGMCP -->|HTTP| Knowledge
    LlamaIndexMCP -.->|HTTP| LlamaIndex
    GKGMcp -.->|HTTP| GKGService
    GitHubAPI --> GitHub
    JiraAPI --> Jira
    SlackAPI --> Slack
    LlamaIndex --> ChromaDB
    GKGService --> ChromaDB
    IndexerWorker --> ChromaDB
    IndexerWorker --> GKGService
    Engine --> DashboardAPI
    DashboardAPI -->|WebSocket| ExternalDash
    Engine --> TaskLogger
    Engine --> OAuth

    style External fill:#2d2d2d,color:#ffffff,stroke-width:2px
    style Gateway fill:#2d2d2d,color:#ffffff,stroke-width:2px
    style Storage fill:#2d2d2d,color:#ffffff,stroke-width:2px
    style Engine fill:#2d2d2d,color:#ffffff,stroke-width:2px
    style MCPServers fill:#2d2d2d,color:#ffffff,stroke-width:2px
    style APIServices fill:#2d2d2d,color:#ffffff,stroke-width:2px
    style Monitoring fill:#2d2d2d,color:#ffffff,stroke-width:2px
    style Knowledge fill:#1a1a1a,color:#ffffff,stroke-width:2px
```

### 2.2 Layer Architecture

The system is organized into four layers:

```mermaid
%%{init: {'theme':'base', 'themeVariables': {'fontSize':'24px', 'primaryColor':'#2d2d2d', 'primaryTextColor':'#ffffff', 'primaryBorderColor':'#ffffff', 'lineColor':'#ffffff', 'secondaryColor':'#1a1a1a', 'tertiaryColor':'#2d2d2d'}}}%%
graph TB
    subgraph Layer1["Layer 1: Presentation"]
        Dashboard[External Dashboard :3005<br/>React UI]
        DashboardAPI[Dashboard API :5000<br/>FastAPI Backend]
    end

    subgraph Layer2["Layer 2: Core Services"]
        AgentEngine[Agent Engine :8080<br/>Task Execution]
        OAuthService[OAuth Service :8010<br/>Token Management]
        WebhookServer[API Gateway :8000<br/>Webhook Reception]
        TaskLogger[Task Logger :8090<br/>Output Logging]
    end

    subgraph Layer3["Layer 3: Knowledge Optional"]
        LlamaIndex[LlamaIndex :8002<br/>Semantic Search]
        GKGService[GKG Service :8003<br/>Code Graph]
        IndexerWorker[Indexer Worker :8004<br/>Background Indexing]
        ChromaDB[ChromaDB :8001<br/>Vector Database]
    end

    subgraph Layer4["Layer 4: Data Storage"]
        PostgreSQL[PostgreSQL :5432<br/>Relational Data]
        Redis[Redis :6379<br/>Queues & Cache]
    end

    Layer1 --> Layer2
    Layer2 --> Layer3
    Layer2 --> Layer4
    Layer3 --> Layer4

    style Layer1 fill:#2d2d2d,color:#ffffff,stroke-width:2px
    style Layer2 fill:#2d2d2d,color:#ffffff,stroke-width:2px
    style Layer3 fill:#1a1a1a,color:#ffffff,stroke-width:2px
    style Layer4 fill:#2d2d2d,color:#ffffff,stroke-width:2px
```

### 2.3 Task Lifecycle Flow

How a task moves through the system:

```mermaid
%%{init: {'theme':'base', 'themeVariables': {'fontSize':'24px', 'primaryColor':'#2d2d2d', 'primaryTextColor':'#ffffff', 'primaryBorderColor':'#ffffff', 'lineColor':'#ffffff', 'secondaryColor':'#1a1a1a', 'tertiaryColor':'#2d2d2d'}}}%%
flowchart TD
    A[External Event<br/>GitHub, Jira, Slack] --> B[Webhook → API Gateway :8000]
    B -->|HTTP 200 OK<br/>Immediate Response| A2[External Service<br/>Receives Confirmation]
    B --> C[Validate Signature<br/>Extract Metadata]
    C --> D[Create Task in PostgreSQL]
    D --> E[Enqueue to Redis<br/>agent:tasks queue]
    E --> F[Agent Engine :8080<br/>Picks Up Task]
    F --> G[Update Status:<br/>QUEUED → RUNNING]
    G --> H[Execute CLI Provider<br/>Claude or Cursor]
    H --> I[Stream Output to<br/>Redis Pub/Sub]
    I --> J[Task Logger :8090<br/>Captures to Files]
    I --> K[Dashboard API :5000<br/>Broadcasts via WebSocket]
    H --> L[Agent Calls MCP Tools<br/>Via MCP Servers]
    L --> L1[Knowledge MCP Tools<br/>Knowledge Graph MCP :9005<br/>LlamaIndex MCP :9006<br/>GKG MCP :9007]
    L1 --> M[Post Response Back<br/>To Source System]
    M --> N[Update Status:<br/>RUNNING → COMPLETED/FAILED]

    style A fill:#2d2d2d,color:#ffffff,stroke-width:2px
    style A2 fill:#2d2d2d,color:#ffffff,stroke-width:2px
    style B fill:#2d2d2d,color:#ffffff,stroke-width:2px
    style C fill:#2d2d2d,color:#ffffff,stroke-width:2px
    style D fill:#2d2d2d,color:#ffffff,stroke-width:2px
    style E fill:#2d2d2d,color:#ffffff,stroke-width:2px
    style F fill:#2d2d2d,color:#ffffff,stroke-width:2px
    style G fill:#2d2d2d,color:#ffffff,stroke-width:2px
    style H fill:#2d2d2d,color:#ffffff,stroke-width:2px
    style I fill:#2d2d2d,color:#ffffff,stroke-width:2px
    style J fill:#2d2d2d,color:#ffffff,stroke-width:2px
    style K fill:#2d2d2d,color:#ffffff,stroke-width:2px
    style L fill:#2d2d2d,color:#ffffff,stroke-width:2px
    style L1 fill:#1a1a1a,color:#ffffff,stroke-width:2px
    style M fill:#2d2d2d,color:#ffffff,stroke-width:2px
    style N fill:#2d2d2d,color:#ffffff,stroke-width:2px
```

### 2.4 Task Status State Machine

Tasks move through these states:

```mermaid
%%{init: {'theme':'base', 'themeVariables': {'fontSize':'24px', 'primaryColor':'#2d2d2d', 'primaryTextColor':'#ffffff', 'primaryBorderColor':'#ffffff', 'lineColor':'#ffffff', 'secondaryColor':'#1a1a1a', 'tertiaryColor':'#2d2d2d'}}}%%
stateDiagram-v2
    [*] --> QUEUED
    QUEUED --> RUNNING
    QUEUED --> CANCELLED
    RUNNING --> WAITING_INPUT
    RUNNING --> COMPLETED
    RUNNING --> FAILED
    RUNNING --> CANCELLED
    WAITING_INPUT --> RUNNING
    WAITING_INPUT --> CANCELLED
    COMPLETED --> [*]
    FAILED --> [*]
    CANCELLED --> [*]
```

**Valid transitions:**

- `QUEUED` → `RUNNING`, `CANCELLED`
- `RUNNING` → `WAITING_INPUT`, `COMPLETED`, `FAILED`, `CANCELLED`
- `WAITING_INPUT` → `RUNNING`, `CANCELLED`
- Terminal states (`COMPLETED`, `FAILED`, `CANCELLED`) cannot transition

### 2.5 Knowledge System Flow (Optional)

How the optional knowledge system works:

```mermaid
%%{init: {'theme':'base', 'themeVariables': {'fontSize':'24px', 'primaryColor':'#2d2d2d', 'primaryTextColor':'#ffffff', 'primaryBorderColor':'#ffffff', 'lineColor':'#ffffff', 'secondaryColor':'#1a1a1a', 'tertiaryColor':'#2d2d2d'}}}%%
flowchart TD
    subgraph Sources["Data Sources"]
        GitHub[GitHub Repos]
        Jira[Jira Tickets]
        Confluence[Confluence Docs]
    end

    subgraph Indexing["Indexing Process"]
        Indexer[Indexer Worker :8004<br/>Fetches & Processes]
    end

    subgraph Storage["Knowledge Storage"]
        ChromaDB[ChromaDB :8001<br/>Vector Embeddings]
        GKG[GKG Service :8003<br/>Code Graph]
    end

    subgraph MCPServers["MCP Servers"]
        KGMCP[Knowledge Graph MCP :9005]
        LlamaIndexMCP[LlamaIndex MCP :9006]
        GKGMcp[GKG MCP :9007]
    end

    subgraph Query["Query Process"]
        LlamaIndex[LlamaIndex Service :8002<br/>Hybrid Search]
        AgentEngine[Agent Engine<br/>Calls MCP Tools]
    end

    Sources --> Indexing
    Indexing --> ChromaDB
    Indexing --> GKG
    ChromaDB --> LlamaIndex
    GKG --> GKGService[GKG Service]
    AgentEngine -->|Via MCP| MCPServers
    MCPServers --> KGMCP
    MCPServers --> LlamaIndexMCP
    MCPServers --> GKGMcp
    KGMCP -->|HTTP| ChromaDB
    LlamaIndexMCP -->|HTTP| LlamaIndex
    GKGMcp -->|HTTP| GKGService

    style Sources fill:#2d2d2d,color:#ffffff,stroke-width:2px
    style Indexing fill:#1a1a1a,color:#ffffff,stroke-width:2px
    style Storage fill:#1a1a1a,color:#ffffff,stroke-width:2px
    style MCPServers fill:#1a1a1a,color:#ffffff,stroke-width:2px
    style Query fill:#1a1a1a,color:#ffffff,stroke-width:2px
    style AgentEngine fill:#2d2d2d,color:#ffffff,stroke-width:2px
    style KGMCP fill:#1a1a1a,color:#ffffff,stroke-width:2px
    style LlamaIndexMCP fill:#1a1a1a,color:#ffffff,stroke-width:2px
    style GKGMcp fill:#1a1a1a,color:#ffffff,stroke-width:2px
    style LlamaIndex fill:#1a1a1a,color:#ffffff,stroke-width:2px
    style GKGService fill:#1a1a1a,color:#ffffff,stroke-width:2px
```

### 2.6 File Structure

Project organization:

```
groote-ai/
├── CLAUDE.md                           # Project-level rules
├── docker-compose.yml                  # Main orchestration
├── Makefile                            # Development commands
├── .env.example                        # Environment template
│
├── agent-engine/                       # CLI Task Execution (Scalable)
│   ├── Dockerfile
│   ├── main.py                         # FastAPI + Redis worker
│   ├── .claude/
│   │   ├── agents/                     # 10 specialized agents
│   │   │   ├── brain.md                # Main orchestrator
│   │   │   ├── planning.md             # Discovery & planning
│   │   │   ├── executor.md             # TDD implementation
│   │   │   ├── verifier.md             # Quality assurance
│   │   │   ├── github-issue-handler.md # Issue processing
│   │   │   ├── github-pr-review.md     # PR review
│   │   │   ├── jira-code-plan.md       # Jira ticket handling
│   │   │   ├── slack-inquiry.md        # Slack Q&A
│   │   │   ├── knowledge-researcher.md # Knowledge search
│   │   │   └── service-integrator.md   # External coordination
│   │   └── skills/                     # 9 reusable skills
│   │       ├── discovery/              # Repo identification
│   │       ├── testing/                # Test generation
│   │       ├── code-refactoring/       # Code improvements
│   │       ├── github-operations/      # Git/GitHub actions
│   │       ├── jira-operations/        # Jira actions
│   │       ├── slack-operations/       # Slack messaging
│   │       ├── human-approval/         # Approval workflows
│   │       ├── verification/           # Quality checks
│   │       └── knowledge-graph/        # Code search
│   ├── cli/                            # CLI provider implementations
│   │   ├── base.py                     # Provider interface
│   │   ├── factory.py                  # Provider factory
│   │   └── providers/
│   │       ├── claude.py               # Claude Code CLI
│   │       └── cursor.py               # Cursor CLI
│   └── config/
│       └── settings.py
│
├── api-gateway/                        # Webhook Reception :8000
│   ├── Dockerfile
│   ├── main.py
│   ├── routes/
│   │   └── webhooks.py
│   └── webhooks/
│       ├── github/
│       ├── jira/
│       └── slack/
│
├── dashboard-api/                      # Analytics & WebSocket :5000
│   ├── Dockerfile
│   ├── main.py
│   └── api/
│       ├── analytics.py
│       ├── conversations.py
│       ├── dashboard.py
│       ├── webhook_status.py
│       └── websocket.py
│
├── external-dashboard/                 # React UI :3005
│   ├── Dockerfile
│   ├── package.json
│   └── src/
│       ├── features/
│       └── hooks/
│
├── oauth-service/                      # OAuth Flows :8010
│   ├── Dockerfile
│   ├── main.py
│   ├── providers/
│   │   ├── github.py
│   │   ├── jira.py
│   │   └── slack.py
│   └── services/
│       ├── installation_service.py
│       └── token_service.py
│
├── task-logger/                        # Task Output Logging :8090
│   ├── Dockerfile
│   ├── main.py
│   └── core/
│       └── log_writer.py
│
├── mcp-servers/                        # MCP Protocol Servers
│   ├── github-mcp/       :9001         # Official GitHub MCP
│   ├── jira-mcp/         :9002         # FastMCP - Jira
│   ├── slack-mcp/        :9003         # FastMCP - Slack
│   ├── knowledge-graph-mcp/ :9005      # FastMCP - Code Search
│   ├── llamaindex-mcp/   :9006         # Optional - Hybrid Search
│   └── gkg-mcp/          :9007         # Optional - Code Graph
│
├── api-services/                       # API Wrappers (Credentials Here)
│   ├── github-api/       :3001
│   ├── jira-api/         :3002
│   └── slack-api/        :3003
│
├── knowledge-graph/                    # Code Graph Database :4000
│   ├── Dockerfile                      # Rust-based
│   ├── Cargo.toml
│   └── src/
│
├── llamaindex-service/                 # Optional - Semantic Search :8002
│   ├── Dockerfile
│   ├── main.py
│   └── core/
│
├── gkg-service/                        # Optional - Code Graph :8003
│   ├── Dockerfile
│   ├── main.py
│   └── core/
│
├── indexer-worker/                     # Optional - Background Indexing :8004
│   ├── Dockerfile
│   ├── main.py
│   └── core/
│
└── docs/
    ├── ARCHITECTURE.md                 # This file
    └── SETUP-KNOWLEDGE.md              # Knowledge layer setup guide
```

---

## Core Services

The system has 16 core services that always run. Each service runs in its own Docker container.

### Service List

| #   | Service                 | Port      | Purpose                     |
| --- | ----------------------- | --------- | --------------------------- |
| 1   | **CLI (Agent Engine)**  | 8080-8089 | Task execution (scalable)   |
| 2   | **API Gateway**         | 8000      | Webhook reception           |
| 3   | **Dashboard API**       | 5000      | Analytics & WebSocket hub   |
| 4   | **External Dashboard**  | 3005      | React monitoring UI         |
| 5   | **OAuth Service**       | 8010      | Multi-provider OAuth flows  |
| 6   | **Task Logger**         | 8090      | Task output logging         |
| 7   | **Knowledge Graph**     | 4000      | Code entity indexing (Rust) |
| 8   | **GitHub MCP**          | 9001      | GitHub tool interface       |
| 9   | **Jira MCP**            | 9002      | Jira tool interface         |
| 10  | **Slack MCP**           | 9003      | Slack tool interface        |
| 11  | **Knowledge Graph MCP** | 9005      | Code search tool interface  |
| 12  | **GitHub API**          | 3001      | GitHub API wrapper          |
| 13  | **Jira API**            | 3002      | Jira API wrapper            |
| 14  | **Slack API**           | 3003      | Slack API wrapper           |
| 15  | **Redis**               | 6379      | Task queue & cache          |
| 16  | **PostgreSQL**          | 5432      | Persistent storage          |

### Service Details

#### 1. Agent Engine (CLI)

**What it does:** Executes AI agent tasks using Claude or Cursor CLI.

**Location:** `agent-engine/`

**Key features:**

- Supports Claude and Cursor CLI providers
- Horizontal scaling via Redis queue
- 13 specialized agents (brain, planning, executor, verifier, etc.)
- 9 reusable skills (discovery, testing, code-refactoring, etc.)
- Connects to MCP servers for tool access

**API endpoints:**

- `POST /tasks` - Create new task
- `GET /tasks/{id}` - Get task status
- `GET /health` - Health check
- `GET /health/detailed` - Detailed component status

#### 2. API Gateway

**What it does:** Receives and validates webhooks from external services.

**Location:** `api-gateway/`

**Key features:**

- **Immediate response** - Responds with HTTP 200 OK immediately upon receiving webhook (before processing)
- Validates webhook signatures (HMAC-SHA256)
- Extracts metadata from webhooks
- Creates tasks in PostgreSQL
- Enqueues tasks to Redis

**How it works:**

1. Webhook arrives from external service
2. API Gateway validates signature
3. **Immediately responds with HTTP 200 OK** (prevents webhook timeouts)
4. Asynchronously processes webhook (creates task, enqueues to Redis)

**Supported webhooks:**

- GitHub (issues, pull requests)
- Jira (ticket updates)
- Slack (mentions, messages)

#### 3. Dashboard API

**What it does:** Backend API for the dashboard UI.

**Location:** `dashboard-api/`

**Key features:**

- Real-time task status via WebSocket
- Analytics aggregation
- OAuth connection validation
- Data source management

#### 4. External Dashboard

**What it does:** React UI for monitoring and configuration.

**Location:** `external-dashboard/`

**Key features:**

- Real-time task monitoring
- OAuth integration management
- Analytics and metrics
- Data source configuration

#### 5. OAuth Service

**What it does:** Manages OAuth tokens for external service authentication.

**Location:** `oauth-service/`

**Key features:**

- Multi-provider OAuth (GitHub, Jira, Slack)
- Token storage and encryption
- Automatic token refresh
- Installation management

**Supported platforms:**

- GitHub (App Installation, auto-refresh)
- Jira (PKCE OAuth 2.0, refresh token)
- Slack (OAuth 2.0)

#### 6. Task Logger

**What it does:** Logs task output and status to files.

**Location:** `task-logger/`

**Key features:**

- Captures task output from Redis pub/sub
- Writes logs to files
- Tracks task status changes

#### 7. Knowledge Graph

**What it does:** Code entity indexing using Rust-based graph database.

**Location:** `knowledge-graph/`

**Key features:**

- Indexes code repositories
- Tracks code relationships
- Provides code search capabilities

**How agents access it:** Agents access the Knowledge Graph service via the **Knowledge Graph MCP** server (port 9005), not directly. The MCP server translates MCP tool calls into HTTP requests to the Knowledge Graph service.

#### 8-12. MCP Servers

**What they do:** Provide tool interfaces for AI agents via Model Context Protocol.

**Servers:**

- GitHub MCP (9001) - GitHub operations
- Jira MCP (9002) - Jira operations
- Slack MCP (9003) - Slack messaging
- Knowledge Graph MCP (9005) - Code search (core)
- LlamaIndex MCP (9006) - Hybrid search (optional)
- GKG MCP (9007) - Code graph queries (optional)

**Key features:**

- No API keys stored (credentials in API services)
- Server-Sent Events (SSE) transport
- Tool-based interface for agents
- Agents connect via MCP Connections (SSE)

**How agents interact with knowledge layer:**

Agents **always** access the knowledge layer through MCP servers, never directly:

- **Knowledge Graph MCP (9005)** → Calls Knowledge Graph service (4000) → Accesses ChromaDB
- **LlamaIndex MCP (9006)** → Calls LlamaIndex service (8002) → Accesses ChromaDB and GKG
- **GKG MCP (9007)** → Calls GKG service (8003) → Accesses code graph

This MCP-based approach provides:

- Standardized interface for all knowledge operations
- Decoupling between agents and knowledge services
- Easy to add new knowledge tools without changing agent code
- Consistent error handling and retry logic

#### 13-16. API Services

**What they do:** REST API wrappers that hold credentials for external services.

**Services:**

- GitHub API (3001) - GitHub API wrapper
- Jira API (3002) - Jira API wrapper
- Slack API (3003) - Slack API wrapper

**Key features:**

- Credentials isolated in these containers
- Simple REST API interface
- MCP servers call these services (no direct API access)

#### 17-18. Storage Services

**Redis (6379):**

- Task queue (`agent:tasks`)
- Pub/sub for real-time updates
- Caching

**PostgreSQL (5432):**

- Task metadata
- OAuth tokens (encrypted)
- User data
- Analytics data

---

## Optional Knowledge Services

Three optional services provide advanced knowledge capabilities. These are enabled using Docker profiles (`--profile knowledge`).

### Service List

| #   | Service                | Port | Purpose                          |
| --- | ---------------------- | ---- | -------------------------------- |
| 1   | **LlamaIndex Service** | 8002 | Hybrid RAG orchestration         |
| 2   | **GKG Service**        | 8003 | Code relationship graph analysis |
| 3   | **Indexer Worker**     | 8004 | Background indexing worker       |

**Note:** ChromaDB (8001) is included in core services but is primarily used by the knowledge layer.

### Service Details

#### 1. LlamaIndex Service

**What it does:** Provides hybrid search combining vector similarity with graph relationships.

**Location:** `llamaindex-service/`

**Key features:**

- Hybrid query engine (vectors + graphs)
- Query routing to appropriate indexes
- Context assembly from multiple sources
- Reranking for relevance
- Redis-backed query cache

**How agents access it:** Agents access LlamaIndex via the **LlamaIndex MCP** server (port 9006), not directly. The MCP server translates MCP tool calls (like `knowledge_query`, `code_search`) into HTTP requests to the LlamaIndex service.

**API endpoints:**

- `POST /query` - Hybrid query across all sources
- `POST /query/code` - Code-specific queries
- `POST /query/docs` - Documentation queries
- `POST /query/tickets` - Jira ticket queries
- `GET /health` - Health check

#### 2. GKG Service

**What it does:** Code relationship graph for understanding dependencies and call hierarchies.

**Location:** `gkg-service/`

**Key features:**

- Tracks function calls, imports, inheritance
- Dependency analysis
- Call graph visualization
- Class hierarchy analysis

**How agents access it:** Agents access GKG via the **GKG MCP** server (port 9007), not directly. The MCP server translates MCP tool calls (like `analyze_dependencies`, `get_call_graph`) into HTTP requests to the GKG service.

**API endpoints:**

- `POST /graph/analyze` - Analyze repository
- `POST /graph/related` - Find related entities
- `GET /graph/entities` - List entities
- `GET /health` - Health check

#### 3. Indexer Worker

**What it does:** Background worker that indexes data from external sources.

**Location:** `indexer-worker/`

**Key features:**

- Clones/pulls repositories
- Fetches Jira tickets
- Fetches Confluence pages
- Generates embeddings
- Stores in ChromaDB and GKG

**Process:**

1. Get job from Redis queue (`indexer:jobs`)
2. Fetch OAuth token from OAuth Service
3. Pull data from external API
4. Generate embeddings
5. Store in ChromaDB (vectors) and GKG (relationships)
6. Update job status in PostgreSQL

### Enabling Knowledge Services

**Via Docker Compose Profile:**

```bash
docker-compose --profile knowledge up
```

**Via Environment Variable:**

```bash
KNOWLEDGE_SERVICES_ENABLED=true docker-compose up
```

**Via API (runtime):**

```bash
curl -X POST "http://localhost:8080/knowledge/toggle?enabled=true"
```

---

## Data Flows

### Task Execution Flow

How a task moves through the system:

1. **Webhook arrives** → API Gateway receives webhook from external service
2. **Immediate response** → API Gateway responds with HTTP 200 OK immediately (before processing)
3. **Validation** → Signature validated, metadata extracted
4. **Task creation** → Task created in PostgreSQL
5. **Queue** → Task enqueued to Redis (`agent:tasks`)
6. **Pickup** → Agent Engine picks up task from queue
7. **Execution** → CLI provider (Claude/Cursor) executes task
8. **Tool calls** → Agent calls MCP tools as needed (including knowledge MCP tools)
9. **Knowledge queries** → If knowledge layer enabled, agent calls Knowledge Graph MCP, LlamaIndex MCP, or GKG MCP
10. **Output streaming** → Output streamed to Redis pub/sub
11. **Logging** → Task Logger captures output to files
12. **Dashboard** → Dashboard API broadcasts via WebSocket
13. **Response** → Agent posts response back to source system
14. **Completion** → Task status updated to COMPLETED/FAILED

**Important:** The API Gateway responds immediately (HTTP 200 OK) to the webhook sender before processing begins. This prevents webhook timeouts and allows asynchronous processing.

### OAuth Token Flow

How services get OAuth tokens:

1. **Service needs token** → Service requests token from OAuth Service
2. **Check expiration** → OAuth Service checks if token is valid
3. **If expired** → Refresh token from provider
4. **Return token** → Return valid token to requesting service

### Knowledge Indexing Flow

How data gets indexed (optional):

1. **Configuration** → User configures data sources in Dashboard UI
2. **Validation** → Dashboard API validates OAuth connection
3. **Source creation** → Source created in PostgreSQL
4. **Job creation** → Indexing job enqueued to Redis (`indexer:jobs`)
5. **Worker pickup** → Indexer Worker picks up job
6. **Data fetching** → Worker fetches data from external API
7. **Processing** → Data processed, embeddings generated
8. **Storage** → Vectors stored in ChromaDB, graph in GKG
9. **Status update** → Job status updated in PostgreSQL

### How Agents Access Knowledge Layer

**Important:** Agents **always** access the knowledge layer through MCP servers, never through direct HTTP calls.

**Flow:**

1. Agent needs knowledge → Calls MCP tool (e.g., `knowledge_query`)
2. MCP Connection → Forwards tool call via Server-Sent Events (SSE) to appropriate MCP server
3. MCP Server → Translates MCP tool call to HTTP request
4. Knowledge Service → Processes request and returns results
5. MCP Server → Translates HTTP response back to MCP format
6. Agent → Receives results via MCP

**MCP Servers for Knowledge:**

- **Knowledge Graph MCP (9005)** - Basic knowledge operations (core)
- **LlamaIndex MCP (9006)** - Hybrid search, code search, Jira/Confluence search (optional)
- **GKG MCP (9007)** - Dependency analysis, call graphs, class hierarchies (optional)

**Benefits of MCP approach:**

- Standardized interface - All knowledge operations use same MCP protocol
- Decoupling - Agents don't need to know HTTP endpoints or API details
- Easy to extend - Add new knowledge tools by adding MCP tools, not changing agent code
- Consistent error handling - MCP servers handle retries and errors uniformly

### How It Actually Works

**Complete flow example - Agent queries knowledge:**

1. **Agent needs information** → Agent decides to call `knowledge_query` tool
2. **MCP tool call** → Agent sends tool call via MCP protocol through MCP Connections
3. **SSE transport** → MCP Connections forwards call via Server-Sent Events to LlamaIndex MCP (9006)
4. **MCP server receives** → LlamaIndex MCP receives the tool call
5. **HTTP translation** → MCP server translates MCP call to HTTP POST request to LlamaIndex service (8002)
6. **Service processes** → LlamaIndex service queries ChromaDB and GKG service
7. **Results returned** → LlamaIndex service returns results via HTTP
8. **MCP translation** → LlamaIndex MCP translates HTTP response back to MCP format
9. **Agent receives** → Agent receives results via MCP protocol
10. **Agent uses results** → Agent uses knowledge in its response

**Key point:** Agents never make direct HTTP calls to knowledge services. All access goes through MCP servers, which provides a clean abstraction layer.

---

## Configuration

### Environment Variables

#### Infrastructure

```bash
POSTGRES_PASSWORD=agent
REDIS_URL=redis://redis:6379/0
DATABASE_URL=postgresql+asyncpg://agent:agent@postgres:5432/agent_system
```

#### CLI Provider

```bash
CLI_PROVIDER=claude                    # or 'cursor'
MAX_CONCURRENT_TASKS=5
TASK_TIMEOUT_SECONDS=3600
ANTHROPIC_API_KEY=sk-ant-xxx          # For Claude
CURSOR_API_KEY=xxx                    # For Cursor
```

#### External Services

```bash
GITHUB_TOKEN=ghp_xxx
JIRA_URL=https://yourcompany.atlassian.net
JIRA_EMAIL=your-email@company.com
JIRA_API_TOKEN=xxx
SLACK_BOT_TOKEN=xoxb-xxx
```

#### Webhook Secrets

```bash
GITHUB_WEBHOOK_SECRET=xxx
JIRA_WEBHOOK_SECRET=xxx
SLACK_WEBHOOK_SECRET=xxx
```

#### OAuth (Optional)

```bash
OAUTH_BASE_URL=http://localhost:8010
GITHUB_APP_ID=xxx
GITHUB_CLIENT_ID=xxx
GITHUB_CLIENT_SECRET=xxx
SLACK_CLIENT_ID=xxx
SLACK_CLIENT_SECRET=xxx
JIRA_CLIENT_ID=xxx
JIRA_CLIENT_SECRET=xxx
TOKEN_ENCRYPTION_KEY=xxx
```

#### Knowledge Services (Optional)

```bash
KNOWLEDGE_SERVICES_ENABLED=false       # Enable knowledge layer
LLAMAINDEX_URL=http://llamaindex-service:8002
GKG_URL=http://gkg-service:8003
CHROMADB_URL=http://chromadb:8000
```

### MCP Configuration

**agent-engine/.claude/mcp.json:**

```json
{
    "mcpServers": {
        "github": {
            "url": "http://github-mcp:9001/sse",
            "transport": "sse"
        },
        "jira": {
            "url": "http://jira-mcp:9002/sse",
            "transport": "sse"
        },
        "slack": {
            "url": "http://slack-mcp:9003/sse",
            "transport": "sse"
        },
        "knowledge-graph": {
            "url": "http://knowledge-graph-mcp:9005/sse",
            "transport": "sse"
        }
    }
}
```

---

## Security Model

### Credential Isolation

API keys are only stored in API service containers. MCP servers, webhooks, and agents never have direct access to credentials.

**Credential-free zone:**

- API Gateway (no API keys)
- MCP Servers (no API keys)
- Agent Engine (no API keys)

**API Services (credentials here):**

- GitHub API (GITHUB_TOKEN)
- Jira API (JIRA_API_KEY)
- Slack API (SLACK_BOT_TOKEN)

### Webhook Signature Validation

All webhooks are validated using HMAC-SHA256:

- GitHub: `X-Hub-Signature-256`
- Jira: `X-Atlassian-Webhook-Signature`
- Slack: `X-Slack-Signature`

### Loop Prevention

Agent-posted comments are tracked in Redis to prevent infinite webhook loops:

- Key: `posted_comments:{comment_id}`
- TTL: 1 hour
- Check: Before processing webhook, verify comment_id not in Redis

---

## Deployment

### Quick Start

```bash
# 1. Configure environment
cp .env.example .env
# Edit .env with your credentials

# 2. Start all services
make init
make cli-up PROVIDER=claude SCALE=1

# 3. Verify health
make cli-status PROVIDER=claude
curl http://localhost:8000/health
```

### Scaling

```bash
# Scale CLI workers
make cli-up PROVIDER=claude SCALE=3

# Scale specific service
docker-compose up -d --scale cli=5 cli
```

### Viewing Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f cli
docker-compose logs -f api-gateway
docker-compose logs -f dashboard-api

# Task execution logs
docker-compose logs -f task-logger
```

### Health Checks

```bash
curl http://localhost:8000/health      # API Gateway
curl http://localhost:8080/health      # CLI (Agent Engine)
curl http://localhost:5000/health      # Dashboard API
curl http://localhost:8010/health      # OAuth Service
curl http://localhost:8090/health      # Task Logger
curl http://localhost:4000/health      # Knowledge Graph
```

### Starting with Knowledge Services

```bash
# Start with knowledge profile
docker-compose --profile knowledge up -d

# Or set environment variable
KNOWLEDGE_SERVICES_ENABLED=true docker-compose up -d
```

---

## Reference

### Port Reference

| Service             | Port(s)   | Container Name      | Purpose                        |
| ------------------- | --------- | ------------------- | ------------------------------ |
| CLI (Agent Engine)  | 8080-8089 | cli                 | Task execution (scalable)      |
| API Gateway         | 8000      | api-gateway         | Webhook reception              |
| Dashboard API       | 5000      | dashboard-api       | Analytics & WebSocket          |
| External Dashboard  | 3005      | external-dashboard  | React monitoring UI            |
| OAuth Service       | 8010      | oauth-service       | Multi-provider OAuth           |
| Task Logger         | 8090      | task-logger         | Output logging                 |
| Knowledge Graph     | 4000      | knowledge-graph     | Code entity indexing           |
| ChromaDB            | 8001      | chromadb            | Vector database                |
| GitHub MCP          | 9001      | github-mcp          | GitHub tool interface          |
| Jira MCP            | 9002      | jira-mcp            | Jira tool interface            |
| Slack MCP           | 9003      | slack-mcp           | Slack tool interface           |
| Knowledge Graph MCP | 9005      | knowledge-graph-mcp | Code search interface          |
| LlamaIndex Service  | 8002      | llamaindex-service  | Hybrid RAG (optional)          |
| LlamaIndex MCP      | 9006      | llamaindex-mcp      | Advanced search (optional)     |
| GKG Service         | 8003      | gkg-service         | Code graph (optional)          |
| GKG MCP             | 9007      | gkg-mcp             | Graph tools (optional)         |
| Indexer Worker      | 8004      | indexer-worker      | Background indexing (optional) |
| GitHub API          | 3001      | github-api          | GitHub API wrapper             |
| Jira API            | 3002      | jira-api            | Jira API wrapper               |
| Slack API           | 3003      | slack-api           | Slack API wrapper              |
| Redis               | 6379      | redis               | Task queue & cache             |
| PostgreSQL          | 5432      | postgres            | Persistent storage             |

### Agent Routing

| Source    | Event Type              | Target Agent         |
| --------- | ----------------------- | -------------------- |
| GitHub    | Issue opened/commented  | github-issue-handler |
| GitHub    | PR opened/reviewed      | github-pr-review     |
| Jira      | Issue with `ai-agent` label | jira-code-plan       |
| Slack     | @agent mention          | slack-inquiry        |
| Dashboard | Discovery request       | planning             |
| Dashboard | Implementation          | executor             |

### MCP Tools by Server

| Server              | Tools                                                                               |
| ------------------- | ----------------------------------------------------------------------------------- |
| github-mcp          | create_pull_request, get_file_contents, create_branch, add_comment, search_code     |
| jira-mcp            | get_issue, create_issue, update_issue, add_comment, search_issues, transition_issue |
| slack-mcp           | post_message, get_conversations, list_channels, reply_in_thread                     |
| knowledge-graph-mcp | search_code, find_references, get_call_graph, get_dependencies                      |

### Key Benefits

1. **Maximum Isolation** - Each service in own container, failure in one doesn't affect others
2. **Independent Scaling** - Scale CLI workers horizontally, scale each service independently
3. **Security** - API keys only in API service containers, webhook validation, loop prevention
4. **Maintainability** - Update one service without affecting others, clear boundaries
5. **Observability** - Real-time WebSocket updates, task logging, analytics dashboard

---

## Related Documentation

- [TUNNEL_SETUP.md](./TUNNEL_SETUP.md) - Configure public URLs for webhooks & OAuth
- [KNOWLEDGE-LAYER.md](./KNOWLEDGE-LAYER.md) - Knowledge layer architecture and data flow
- [SETUP-KNOWLEDGE.md](./SETUP-KNOWLEDGE.md) - Knowledge layer setup guide
- [CLAUDE.md](../.claude/CLAUDE.md) - Development rules and conventions
- [README.md](../README.md) - Project overview and quick start
- [SETUP.md](../SETUP.md) - Complete setup guide
