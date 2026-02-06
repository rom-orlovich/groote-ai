# Microservices Architecture

## Service Map

| Service | Directory | Ports | Description |
|---------|-----------|-------|-------------|
| API Gateway | `api-gateway/` | 8000 | Webhook reception, signature validation, task queuing |
| Agent Engine | `agent-engine/` | 8080-8089 | AI task execution via CLI providers (Claude/Cursor) |
| MCP Servers | `mcp-servers/` | 9001-9004 | Model Context Protocol servers (GitHub, Jira, Slack, Sentry) |
| API Services | `api-services/` | 3001-3004 | REST wrappers for external APIs (GitHub, Jira, Slack, Sentry) |
| Dashboard API | `dashboard-api/` | 5000 | Backend REST + WebSocket for dashboard |
| External Dashboard | `external-dashboard/` | 3005 | Frontend dashboard (React 19) |
| OAuth Service | `oauth-service/` | 8010 | Centralized OAuth flows and token management |
| Task Logger | `task-logger/` | 8090 | Structured task event logging from Redis stream |
| GKG Service | `gkg-service/` | - | HTTP wrapper for GitLab Knowledge Graph binary |
| LlamaIndex Service | `llamaindex-service/` | 8100 | Hybrid RAG orchestration (vector + graph search) |
| Indexer Worker | `indexer-worker/` | - | Background worker indexing GitHub/Jira/Confluence into vector/graph stores |
| Knowledge Graph | `knowledge-graph/` | 4000 | Rust-based code entity graph database |

## Communication Rules

- Services communicate via **API/Queue ONLY**
- **NO direct imports** between services
- Each service has its own dependencies and runs independently

## Health Check Endpoints

```
GET http://localhost:8000/health      # API Gateway
GET http://localhost:8080/health      # Agent Engine
GET http://localhost:5000/api/health  # Dashboard API
GET http://localhost:8010/health      # OAuth Service
GET http://localhost:8090/health      # Task Logger
```

Or use `make health` to check all services at once.

## Environment Variables

All secrets configured via `.env` file (created by `make init`):
- `CLI_PROVIDER` - `claude` or `cursor`
- `POSTGRES_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `GITHUB_TOKEN`, `JIRA_API_TOKEN`, `SLACK_BOT_TOKEN` - Service tokens
- `*_WEBHOOK_SECRET` - Webhook verification secrets
