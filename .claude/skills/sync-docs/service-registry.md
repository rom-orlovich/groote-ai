# Service Registry

Complete registry of all Groote AI services with documentation expectations.

## Services

### Core Services

| Service | Directory | Port | Type | Source Files to Read |
|---------|-----------|------|------|---------------------|
| API Gateway | `api-gateway/` | 8000 | FastAPI | `main.py`, `routes/webhooks.py`, `webhooks/*/handler.py`, `config/settings.py` |
| Agent Engine | `agent-engine/` | 8080-8089 | FastAPI | `main.py`, `routes/`, `services/`, `config/` |
| Dashboard API | `dashboard-api/` | 5000 | FastAPI | `main.py`, `routes/`, `services/`, `models/`, `config/` |
| OAuth Service | `oauth-service/` | 8010 | FastAPI | `main.py`, `routes/`, `services/`, `config/` |
| Task Logger | `task-logger/` | 8090 | FastAPI | `main.py`, `routes/`, `services/`, `config/` |
| Admin Setup | `admin-setup/` | 8015 | FastAPI+React | `src/main.py`, `src/routes/`, `frontend/src/` |
| External Dashboard | `external-dashboard/` | 3005 | React 19 | `src/App.tsx`, `src/features/`, `package.json` |
| Knowledge Graph | `knowledge-graph/` | 4000 | Rust | `src/main.rs`, `src/api/`, `src/models/`, `src/services/`, `Cargo.toml` |

### MCP Servers

| Service | Directory | Port | Type | Source Files to Read |
|---------|-----------|------|------|---------------------|
| GitHub MCP | `mcp-servers/github-mcp/` | 9001 | MCP | `github_mcp.py` or `index.js`, `config.py` |
| Jira MCP | `mcp-servers/jira-mcp/` | 9002 | MCP | `jira_mcp.py`, `main.py`, `config.py` |
| Slack MCP | `mcp-servers/slack-mcp/` | 9003 | MCP | `slack_mcp.py`, `main.py`, `config.py` |
| Knowledge Graph MCP | `mcp-servers/knowledge-graph-mcp/` | 9005 | MCP | `kg_client.py`, `chroma_client.py`, `main.py`, `config.py` |
| LlamaIndex MCP | `mcp-servers/llamaindex-mcp/` | 9006 | MCP | `llamaindex_mcp.py`, `main.py`, `config.py` |
| GKG MCP | `mcp-servers/gkg-mcp/` | 9007 | MCP | `gkg_mcp.py`, `main.py`, `config.py` |

### API Services

| Service | Directory | Port | Type | Source Files to Read |
|---------|-----------|------|------|---------------------|
| GitHub API | `api-services/github-api/` | 3001 | FastAPI | `main.py`, `routes/`, `services/` |
| Jira API | `api-services/jira-api/` | 3002 | FastAPI | `main.py`, `routes/`, `services/` |
| Slack API | `api-services/slack-api/` | 3003 | FastAPI | `main.py`, `routes/`, `services/` |

### Infrastructure Services

| Service | Directory | Port | Type | Source Files to Read |
|---------|-----------|------|------|---------------------|
| GKG Service | `gkg-service/` | 8003 | FastAPI | `main.py`, `routes/`, `services/` |
| LlamaIndex Service | `llamaindex-service/` | 8002 | FastAPI | `main.py`, `routes/`, `services/` |
| Indexer Worker | `indexer-worker/` | - | Worker | `main.py`, `workers/`, `services/` |

### Aggregate Directories

| Directory | Type | Description |
|-----------|------|-------------|
| `mcp-servers/` | Root | Parent directory for all MCP servers |
| `api-services/` | Root | Parent directory for all API services |
| `scripts/audit/` | Tooling | End-to-end webhook audit framework |

### Root Documentation

| Path | Type | Description |
|------|------|-------------|
| `docs/` | Root docs | System-level architecture, features, flows |
| `README.md` | Root | Project overview and setup guide |
| `.claude/CLAUDE.md` | Root | Development rules for all services |
| `.claude/rules/microservices.md` | Root | Service map, ports, health checks |

## Expected Documentation Per Service

Every service directory must contain:

```
{service}/
├── README.md                  # Overview, setup, endpoints, env vars
├── CLAUDE.md                  # Development guide for Claude Code
└── docs/
    ├── ARCHITECTURE.md        # Component diagrams, data flow
    ├── features.md            # Feature descriptions
    └── flows.md               # Process flow diagrams
```

Aggregate directories (`mcp-servers/`, `api-services/`) also need their own set.

## Root Documentation Expected

```
docs/
├── ARCHITECTURE.md            # System-level architecture (exists)
├── features.md                # System feature index (missing)
├── flows.md                   # End-to-end system flows (missing)
├── KNOWLEDGE-LAYER.md         # Knowledge layer docs (exists)
├── SETUP-KNOWLEDGE.md         # Knowledge setup guide (exists)
├── TUNNEL_SETUP.md            # Tunnel configuration (exists)
└── webhook-integration-guide.md  # Webhook guide (exists)
```

## Service Dependencies

```
GitHub MCP (9001) --> GitHub API (3001)
Jira MCP (9002) --> Jira API (3002)
Slack MCP (9003) --> Slack API (3003)
Knowledge Graph MCP (9005) --> Knowledge Graph (4000) + ChromaDB
LlamaIndex MCP (9006) --> LlamaIndex Service (8002)
GKG MCP (9007) --> GKG Service (8003)

API Gateway (8000) --> Redis --> Agent Engine (8080)
Agent Engine (8080) --> MCP Servers (9001-9007)
Dashboard API (5000) --> PostgreSQL + Redis
External Dashboard (3005) --> Dashboard API (5000)
OAuth Service (8010) --> PostgreSQL
Admin Setup (8015) --> PostgreSQL
Indexer Worker --> GitHub API + LlamaIndex Service + Knowledge Graph
```
