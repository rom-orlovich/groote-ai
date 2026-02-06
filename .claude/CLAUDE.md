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
```

## Architecture

See `.claude/rules/microservices.md` for full service map, ports, health checks, and environment variables.

## Agent Teams

This project supports Claude Code agent teams (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` is enabled). When working as a team:

- **Brain** is the team lead — it decomposes tasks and coordinates teammates
- Each teammate owns a specific service or concern (security, performance, etc.)
- Teammates MUST NOT edit files outside their assigned scope
- All teammates follow the same code standards above
- Use structured findings when reporting to the team lead

### Service Ownership for Teams

When assigning teammates to services, each teammate should work within their service directory and read its CLAUDE.md:

| Service | Directory | Typical Teammate Role |
|---------|-----------|----------------------|
| API Gateway | `api-gateway/` | Webhook & routing changes |
| Agent Engine | `agent-engine/` | Task processing & CLI integration |
| Dashboard API | `dashboard-api/` | Backend API & WebSocket changes |
| External Dashboard | `external-dashboard/` | Frontend React 19 changes |
| OAuth Service | `oauth-service/` | Auth flow changes |
| MCP Servers | `mcp-servers/` | Tool integration changes |
| Task Logger | `task-logger/` | Event logging changes |
| Knowledge Graph | `knowledge-graph/` | Rust graph DB changes |
| LlamaIndex Service | `llamaindex-service/` | RAG pipeline changes |
