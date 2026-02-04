# Groote AI Development Rules

**STRICT ENFORCEMENT** - Must be followed for all groote-ai code:

## Package Managers

- **Python**: Use `uv` (NOT pip) - `uv pip install -r requirements.txt`
- **JavaScript/TypeScript**: Use `pnpm` (NOT npm/yarn) - `pnpm install`, `pnpm add <pkg>`

## Code Standards

- **Maximum 300 lines per file** - Split into: `constants.py`, `models.py`, `exceptions.py`, `core.py`
- **NO `any` types EVER** - Use `ConfigDict(strict=True)` in Pydantic models
- **NO comments in code** - Self-explanatory code only
- **Tests MUST run fast** (< 5 seconds per file), NO real network calls
- **ALWAYS use async/await** for I/O - Use `httpx.AsyncClient`, NOT `requests`
- **Structured logging**: `logger.info("task_started", task_id=task_id, user_id=user_id)`

## Key Commands

```bash
make init                    # Initialize project (creates .env)
make up                      # Build and start all services
make down                    # Stop all services
make health                  # Check service health
make cli-claude              # Start Claude CLI
make cli-cursor              # Start Cursor CLI
make cli PROVIDER=claude SCALE=3  # Scale CLI instances
make test                    # Run all tests
make lint                    # Lint code
make format                  # Format code
make db-migrate MSG="..."    # Create migration
make db-upgrade              # Apply migrations
```

## Architecture

Microservices: `api-gateway/` (8000), `agent-engine/` (8080-8089), `mcp-servers/` (9001-9004), `api-services/` (3001-3004), `dashboard-api/` (5000). Services communicate via API/Queue only (NO direct imports).

## Environment Variables

```bash
CLI_PROVIDER=claude                    # or 'cursor'
POSTGRES_URL=postgresql://agent:agent@postgres:5432/agent_system
REDIS_URL=redis://redis:6379/0
GITHUB_TOKEN=ghp_xxx
JIRA_API_TOKEN=xxx
SLACK_BOT_TOKEN=xoxb-xxx
SENTRY_DSN=https://xxx@sentry.io/xxx
GITHUB_WEBHOOK_SECRET=xxx
JIRA_WEBHOOK_SECRET=xxx
SLACK_WEBHOOK_SECRET=xxx
```

## Health Checks

```bash
make health                            # All services
curl http://localhost:8000/health      # API Gateway
curl http://localhost:8080/health      # Agent Engine
curl http://localhost:5000/api/health  # Dashboard API
```
