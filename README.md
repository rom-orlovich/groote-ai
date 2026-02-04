# Groote AI

A containerized multi-agent system that processes webhooks from GitHub, Jira, Slack, and Sentry to autonomously handle development tasks using AI agents (Claude Code CLI or Cursor CLI) with Test-Driven Development methodology.

## Architecture

```mermaid
%%{init: {'theme':'base', 'themeVariables': {'fontSize':'16px', 'primaryColor':'#2d2d2d', 'primaryTextColor':'#ffffff', 'primaryBorderColor':'#ffffff', 'lineColor':'#ffffff', 'secondaryColor':'#1a1a1a', 'tertiaryColor':'#2d2d2d'}}}%%
graph TB
    subgraph External["External Services"]
        GitHub[GitHub]
        Jira[Jira]
        Slack[Slack]
        Sentry[Sentry]
    end

    subgraph Gateway["API Gateway :8000"]
        Webhooks["Webhook Handlers<br/>GitHub, Jira, Slack, Sentry"]
    end

    subgraph Storage["Storage Layer"]
        Redis[Redis :6379<br/>Task Queue & Cache]
        Postgres[PostgreSQL :5432<br/>Persistent Data]
    end

    subgraph Engine["Agent Engine :8080-8089"]
        Agents["AI Agents<br/>brain, planning, executor<br/>github-issue-handler<br/>github-pr-review<br/>jira-code-plan<br/>slack-inquiry, verifier"]
        MCPConn["MCP Connections<br/>Server-Sent Events"]
    end

    subgraph MCPServers["MCP Servers"]
        GitHubMCP[GitHub MCP :9001]
        JiraMCP[Jira MCP :9002]
        SlackMCP[Slack MCP :9003]
        SentryMCP[Sentry MCP :9004]
        KGMCP[Knowledge Graph MCP :9005]
        LlamaIndexMCP[LlamaIndex MCP :9006<br/>Optional]
        GKGMcp[GKG MCP :9007<br/>Optional]
    end

    subgraph APIServices["API Services<br/>Credentials Here"]
        GitHubAPI[GitHub API :3001]
        JiraAPI[Jira API :3002]
        SlackAPI[Slack API :3003]
        SentryAPI[Sentry API :3004]
    end

    subgraph Monitoring["Monitoring & Management"]
        DashboardAPI[Dashboard API :5000<br/>WebSocket, Analytics]
        ExternalDash[External Dashboard :3005<br/>React UI]
        OAuth[OAuth Service :8010<br/>Multi-provider OAuth]
        TaskLogger[Task Logger :8090<br/>Output Logging]
    end

    subgraph Knowledge["Knowledge Layer - Optional"]
        ChromaDB[ChromaDB :8001<br/>Vector Database]
        LlamaIndex[LlamaIndex Service :8002<br/>Hybrid RAG]
        GKGService[GKG Service :8003<br/>Code Graph]
        IndexerWorker[Indexer Worker :8004<br/>Background Indexing]
    end

    External -->|Webhooks| Gateway
    Gateway -->|HTTP 200 OK| External
    Webhooks --> Redis
    Webhooks --> Postgres
    Redis --> Engine
    Postgres --> Engine
    Engine --> Agents
    Agents --> MCPConn
    MCPConn -->|SSE| MCPServers
    GitHubMCP -->|HTTP| GitHubAPI
    JiraMCP -->|HTTP| JiraAPI
    SlackMCP -->|HTTP| SlackAPI
    SentryMCP -->|HTTP| SentryAPI
    KGMCP -->|HTTP| Knowledge
    LlamaIndexMCP -.->|HTTP| LlamaIndex
    GKGMcp -.->|HTTP| GKGService
    GitHubAPI --> GitHub
    JiraAPI --> Jira
    SlackAPI --> Slack
    SentryAPI --> Sentry
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

## Task Lifecycle

```mermaid
%%{init: {'theme':'base', 'themeVariables': {'fontSize':'16px', 'primaryColor':'#2d2d2d', 'primaryTextColor':'#ffffff', 'primaryBorderColor':'#ffffff', 'lineColor':'#ffffff', 'secondaryColor':'#1a1a1a', 'tertiaryColor':'#2d2d2d'}}}%%
flowchart TD
    A[External Event<br/>GitHub, Jira, Slack, Sentry] --> B[Webhook → API Gateway :8000]
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
    L --> M[Post Response Back<br/>To Source System]
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
    style M fill:#2d2d2d,color:#ffffff,stroke-width:2px
    style N fill:#2d2d2d,color:#ffffff,stroke-width:2px
```

## How It Works

### System Flow

1. **Webhook Reception**: External services (GitHub, Jira, Slack, Sentry) send webhooks to the API Gateway
2. **Validation & Queuing**: API Gateway validates signatures, creates task in PostgreSQL, and enqueues to Redis
3. **Task Pickup**: Agent Engine picks up task from Redis queue (`agent:tasks`)
4. **CLI Execution**: Agent Engine executes task using Claude or Cursor CLI with specialized agents
5. **MCP Tool Calls**: Agents use MCP tools (via SSE) to interact with external services
6. **Response Posting**: Results are posted back to the originating service
7. **Real-time Updates**: Output streams to Dashboard via WebSocket

### Layer Architecture

```mermaid
%%{init: {'theme':'base', 'themeVariables': {'fontSize':'16px', 'primaryColor':'#2d2d2d', 'primaryTextColor':'#ffffff', 'primaryBorderColor':'#ffffff', 'lineColor':'#ffffff'}}}%%
graph TB
    subgraph Layer1["Layer 1: Presentation"]
        Dashboard[External Dashboard :3005]
        DashboardAPI[Dashboard API :5000]
    end

    subgraph Layer2["Layer 2: Core Services"]
        AgentEngine[Agent Engine :8080]
        APIGateway[API Gateway :8000]
        OAuth[OAuth Service :8010]
        TaskLogger[Task Logger :8090]
    end

    subgraph Layer3["Layer 3: Integration"]
        MCPServers[MCP Servers :9001-9007]
        APIServices[API Services :3001-3004]
    end

    subgraph Layer4["Layer 4: Storage"]
        PostgreSQL[PostgreSQL :5432]
        Redis[Redis :6379]
    end

    subgraph Layer5["Layer 5: Knowledge - Optional"]
        LlamaIndex[LlamaIndex :8002]
        GKG[GKG Service :8003]
        ChromaDB[ChromaDB :8001]
    end

    Layer1 --> Layer2
    Layer2 --> Layer3
    Layer2 --> Layer4
    Layer3 --> Layer4
    Layer3 -.-> Layer5

    style Layer1 fill:#2d2d2d,color:#ffffff,stroke-width:2px
    style Layer2 fill:#2d2d2d,color:#ffffff,stroke-width:2px
    style Layer3 fill:#2d2d2d,color:#ffffff,stroke-width:2px
    style Layer4 fill:#2d2d2d,color:#ffffff,stroke-width:2px
    style Layer5 fill:#1a1a1a,color:#ffffff,stroke-width:2px
```

### Key Design Principles

- **Service Isolation**: Each service runs in its own Docker container
- **Credential Security**: API keys only stored in API service containers
- **Async Processing**: Webhooks respond immediately (HTTP 200), tasks processed asynchronously
- **Horizontal Scaling**: Agent Engine can scale to multiple instances
- **No Direct Imports**: Services communicate via API/Queue only

## Quick Start

```bash
# 1. Clone and initialize
git clone <repository-url>
cd groote-ai
make init

# 2. Set bootstrap secrets (only 2-3 vars needed)
#    Edit .env and set: POSTGRES_PASSWORD, TOKEN_ENCRYPTION_KEY
nano .env

# 3. Build and start all services
make up

# 4. Open the Setup Wizard — configures everything else via UI
#    (Dashboard auto-redirects here on first launch)
open http://localhost:3005/setup

# 5. Start the AI agent CLI
make cli-claude    # or: make cli-cursor

# 6. Verify everything is running
make health
```

### Setup Wizard

On first launch the Dashboard redirects to a guided **Setup Wizard** at `/setup`.
The wizard walks through each integration step-by-step:

1. **Infrastructure Check** — verifies PostgreSQL and Redis are healthy
2. **AI Provider** — configure Claude or Cursor API key
3. **GitHub / Jira / Slack / Sentry** — optional, each can be skipped
4. **Review & Export** — download config as `.env`, Kubernetes Secret, Docker Swarm secrets, or GitHub Actions format

All credentials are Fernet-encrypted at rest in PostgreSQL. You can reconfigure
anytime from **Settings** in the sidebar.

**Access points:**
- API Gateway: http://localhost:8000
- Dashboard UI: http://localhost:3005
- Dashboard API: http://localhost:5000

For detailed setup instructions, see **[SETUP.md](SETUP.md)**.

## Services

### Core Services

| Service | Port | Purpose |
|---------|------|---------|
| **Agent Engine (CLI)** | 8080-8089 | Task execution using Claude/Cursor CLI (scalable) |
| **API Gateway** | 8000 | Webhook reception and validation |
| **Dashboard API** | 5000 | Analytics, WebSocket hub for real-time updates |
| **External Dashboard** | 3005 | React monitoring UI |
| **OAuth Service** | 8010 | Multi-provider OAuth flows (GitHub, Jira, Slack) |
| **Task Logger** | 8090 | Task output logging to files |
| **Knowledge Graph** | 4000 | Code entity indexing (Rust) |

### MCP Servers (Tool Interfaces)

| Service | Port | Purpose |
|---------|------|---------|
| **GitHub MCP** | 9001 | GitHub operations (PRs, issues, comments) |
| **Jira MCP** | 9002 | Jira operations (tickets, transitions) |
| **Slack MCP** | 9003 | Slack messaging and channels |
| **Sentry MCP** | 9004 | Sentry error tracking |
| **Knowledge Graph MCP** | 9005 | Code search and references |
| **LlamaIndex MCP** | 9006 | Hybrid search (optional) |
| **GKG MCP** | 9007 | Code graph queries (optional) |

### API Services (Credentials Here)

| Service | Port | Purpose |
|---------|------|---------|
| **GitHub API** | 3001 | GitHub REST API wrapper |
| **Jira API** | 3002 | Jira REST API wrapper |
| **Slack API** | 3003 | Slack REST API wrapper |
| **Sentry API** | 3004 | Sentry REST API wrapper |

### Storage

| Service | Port | Purpose |
|---------|------|---------|
| **Redis** | 6379 | Task queue (`agent:tasks`) and cache |
| **PostgreSQL** | 5432 | Persistent storage (tasks, OAuth tokens, analytics) |

### Knowledge Layer (Optional)

| Service | Port | Purpose |
|---------|------|---------|
| **ChromaDB** | 8001 | Vector database for embeddings |
| **LlamaIndex Service** | 8002 | Hybrid RAG orchestration |
| **GKG Service** | 8003 | Code relationship graph |
| **Indexer Worker** | 8004 | Background data source indexing |

## Key Commands

### CLI Management

```bash
make cli-claude                      # Start Claude CLI
make cli-cursor                      # Start Cursor CLI
make cli PROVIDER=claude SCALE=3     # Scale CLI instances
make cli-down PROVIDER=claude        # Stop CLI
make cli-logs PROVIDER=claude        # View CLI logs
```

### Service Management

```bash
make up                              # Start all services
make down                            # Stop all services
make health                          # Check service health
make logs                            # View all logs
```

### Development

```bash
make init                            # Initialize project
make test                            # Run all tests
make lint                            # Lint code
make format                          # Format code
make db-migrate MSG="..."            # Create migration
make db-upgrade                      # Apply migrations
```

### Knowledge Services (Optional)

```bash
docker-compose --profile knowledge up -d  # Enable knowledge layer
make knowledge-up                         # Alternative command
```

## Environment Variables

Minimum required configuration in `.env`:

```bash
# CLI Provider (choose one)
CLI_PROVIDER=claude
ANTHROPIC_API_KEY=sk-ant-xxx         # For Claude
# CURSOR_API_KEY=xxx                 # For Cursor

# Database (defaults work for local dev)
POSTGRES_PASSWORD=agent
REDIS_URL=redis://redis:6379/0

# External Services (configure as needed)
GITHUB_TOKEN=ghp_xxx
GITHUB_WEBHOOK_SECRET=xxx
JIRA_URL=https://yourcompany.atlassian.net
JIRA_EMAIL=your-email@company.com
JIRA_API_TOKEN=xxx
SLACK_BOT_TOKEN=xoxb-xxx
SLACK_SIGNING_SECRET=xxx
SENTRY_DSN=https://xxx@sentry.io/xxx
SENTRY_AUTH_TOKEN=xxx
```

See `.env.example` for complete configuration.

## Health Checks

```bash
curl http://localhost:8000/health    # API Gateway
curl http://localhost:8080/health    # Agent Engine
curl http://localhost:5000/health    # Dashboard API
curl http://localhost:8010/health    # OAuth Service
curl http://localhost:8090/health    # Task Logger
curl http://localhost:4000/health    # Knowledge Graph
```

## Project Structure

```
groote-ai/
├── agent-engine/           # CLI task execution engine
│   └── .claude/agents/     # 13 specialized agents
│   └── .claude/skills/     # 9 reusable skills
├── api-gateway/            # Webhook reception
├── api-services/           # REST API wrappers (credentials here)
│   ├── github-api/
│   ├── jira-api/
│   ├── slack-api/
│   └── sentry-api/
├── mcp-servers/            # MCP protocol servers
│   ├── github-mcp/
│   ├── jira-mcp/
│   ├── slack-mcp/
│   ├── sentry-mcp/
│   ├── knowledge-graph-mcp/
│   ├── llamaindex-mcp/     # Optional
│   └── gkg-mcp/            # Optional
├── dashboard-api/          # Analytics & WebSocket hub
├── external-dashboard/     # React monitoring UI
├── oauth-service/          # OAuth flows
├── task-logger/            # Task output logging
├── knowledge-graph/        # Code entity indexing (Rust)
├── llamaindex-service/     # Hybrid RAG (optional)
├── gkg-service/            # Code graph (optional)
├── indexer-worker/         # Background indexing (optional)
├── docs/                   # Documentation
│   └── ARCHITECTURE.md     # Detailed architecture
├── docker-compose.yml      # Service orchestration
├── Makefile                # Development commands
├── SETUP.md                # Setup guide
└── .env.example            # Environment template
```

## Documentation

### Getting Started

| Document | Description |
|----------|-------------|
| **[SETUP.md](SETUP.md)** | Complete setup guide - start here |
| **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** | Detailed architecture, data flows, service interactions |
| **[.claude/CLAUDE.md](.claude/CLAUDE.md)** | Development rules and coding standards |

### Service Documentation

Each service has its own setup guide and README:

| Service | Setup | README |
|---------|-------|--------|
| Agent Engine | [SETUP.md](agent-engine/SETUP.md) | [README.md](agent-engine/README.md) |
| API Gateway | [SETUP.md](api-gateway/SETUP.md) | [README.md](api-gateway/README.md) |
| Dashboard API | [SETUP.md](dashboard-api/SETUP.md) | [README.md](dashboard-api/README.md) |
| External Dashboard | [SETUP.md](external-dashboard/SETUP.md) | [README.md](external-dashboard/README.md) |
| MCP Servers | [SETUP.md](mcp-servers/SETUP.md) | [README.md](mcp-servers/README.md) |
| API Services | [SETUP.md](api-services/SETUP.md) | [README.md](api-services/README.md) |
| OAuth Service | [SETUP.md](oauth-service/SETUP.md) | [README.md](oauth-service/README.md) |
| Knowledge Layer | [SETUP-KNOWLEDGE.md](docs/SETUP-KNOWLEDGE.md) | - |

## Key Components

### Agents

The system includes **13 specialized agents**:
- `brain` - Main orchestrator
- `planning` - Discovery and planning
- `executor` - TDD implementation
- `verifier` - Quality assurance
- `github-issue-handler` - GitHub issue processing
- `github-pr-review` - PR review handling
- `jira-code-plan` - Jira ticket handling
- `slack-inquiry` - Slack Q&A
- And more...

### Skills

**9 reusable skills** for agents:
- Discovery, Testing, Code Refactoring
- GitHub/Jira/Slack Operations
- Human Approval, Verification, Knowledge Graph

### Security Model

- **Credential Isolation**: API keys only in API service containers
- **Webhook Validation**: HMAC-SHA256 signature validation
- **Loop Prevention**: Agent-posted content tracked in Redis
- **No Direct Imports**: Services communicate via API/Queue only

## License

[Add your license information here]

## Contributing

[Add contributing guidelines here]
