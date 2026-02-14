# Microservices Architecture

## Service Map

| Service | Directory | Ports | Description |
|---------|-----------|-------|-------------|
| API Gateway | `api-gateway/` | 8000 | Webhook reception, signature validation, task queuing |
| Agent Engine | `agent-engine/` | 8080-8089 | AI task execution via CLI providers (Claude/Cursor) |
| Admin Setup | `admin-setup/` | 8015 | System OAuth app configuration (admin-only) |
| MCP Servers | `mcp-servers/` | 9001-9007 | Model Context Protocol servers (GitHub, Jira, Slack, Knowledge Graph, LlamaIndex, GKG) |
| API Services | `api-services/` | 3001-3003 | REST wrappers for external APIs (GitHub, Jira, Slack) |
| Dashboard API | `dashboard-api/` | 5000 | Backend REST + WebSocket for dashboard |
| External Dashboard | `external-dashboard/` | 3005 | Frontend dashboard (React 19) |
| OAuth Service | `oauth-service/` | 8010 | Centralized OAuth flows and token management |
| Task Logger | `task-logger/` | 8090 | Structured task event logging from Redis stream |
| GKG Service | `gkg-service/` | 8003 | HTTP wrapper for GitLab Knowledge Graph binary |
| LlamaIndex Service | `llamaindex-service/` | 8002 | Hybrid RAG orchestration (vector + graph search) |
| Indexer Worker | `indexer-worker/` | - | Background worker indexing GitHub/Jira/Confluence into vector/graph stores |
| Knowledge Graph | `knowledge-graph/` | 4000 | Rust-based code entity graph database |

## Communication Rules

- Services communicate via **API/Queue ONLY**
- **NO direct imports** between services
- Each service has its own dependencies and runs independently

## Health Check Endpoints

```
GET http://localhost:8000/health      # API Gateway
GET http://localhost:8015/health      # Admin Setup
GET http://localhost:8080/health      # Agent Engine
GET http://localhost:5000/api/health  # Dashboard API
GET http://localhost:8010/health      # OAuth Service
GET http://localhost:8090/health      # Task Logger
GET http://localhost:4000/health      # Knowledge Graph
```

Or use `make health` to check all services at once.

## Public URL Gateway

All services are accessible through a single URL via the nginx reverse proxy on port 3005:

```
PUBLIC_URL (ngrok/production) -> port 3005 -> nginx
  /              -> External Dashboard (React SPA)
  /api/*         -> Dashboard API (port 5000)
  /oauth/*       -> OAuth Service (port 8010)
  /webhooks/*    -> API Gateway (port 8000)
  /ws            -> Dashboard API WebSocket (port 5000)
```

Set `PUBLIC_URL` in `.env`:
```bash
PUBLIC_URL=https://your-domain.example.com
```

OAuth callbacks, webhook URLs, and frontend all use this single URL automatically.

## Environment Variables

All secrets configured via `.env` file (created by `make init`):
- `PUBLIC_URL` - Single public gateway URL (ngrok/production domain)
- `CLI_PROVIDER` - `claude` or `cursor`
- `POSTGRES_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `GITHUB_TOKEN`, `JIRA_API_TOKEN`, `SLACK_BOT_TOKEN` - Service tokens
- `*_WEBHOOK_SECRET` - Webhook verification secrets

## Webhook Integration Flow

Webhooks from Jira, GitHub, and Slack create conversations in the dashboard with full context tracking.

```
Webhook -> API Gateway (8000) -> Redis queue -> Agent Engine -> Conversation Bridge -> Dashboard API
                                                     |
                                                     v
                                              CLI execution (Claude/Cursor)
                                                     |
                                                     v
                                              MCP tool response (Jira/GitHub/Slack)
```

**Flow ID Format** (deterministic, used for conversation reuse):
- Jira: `jira:KAN-6`
- GitHub: `github:owner/repo#42`
- Slack: `slack:C12345:1234567890.123456`

**Conversation API Endpoints:**
- `GET /api/conversations` - List conversations
- `GET /api/conversations/by-flow/{flow_id}` - Find by flow_id
- `POST /api/conversations` - Create conversation (with optional flow_id, source)
- `POST /api/conversations/{id}/messages` - Add message
- `GET /api/conversations/{id}/context` - Get last N messages for agent context
- `GET /api/conversations/{id}/messages` - Get all messages
- `POST /api/tasks` - Register external task from webhook

**Real-time Updates:** Dashboard API broadcasts task status changes via WebSocket (`/ws`) using Redis pub/sub.
