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

## Planning & Documentation

- **Implementation plans** - Always write plans to `docs/plans/` directory
- **Plan naming format** - Use `docs/plans/YYYY-MM-DD-<feature-name>.md`
- **Plan structure** - Include context, phases, file changes, verification steps

## Documentation Conventions

Every service directory must have:

- **`CLAUDE.md`** - Service guide for Claude Code (purpose, structure, commands, env vars)
- **`README.md`** - Human-readable service documentation with Documentation section
- **`docs/ARCHITECTURE.md`** - Component diagrams (mermaid) and data flows
- **`docs/features.md`** - Feature list and capabilities
- **`docs/flows.md`** - Process flow diagrams (ASCII art) with processing steps

Templates: `.claude/skills/sync-docs/templates.md`
Gold standard: `api-gateway/docs/`

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
make tunnel-zrok             # Start zrok tunnel (permanent public URL)
make tunnel                  # Start ngrok tunnel (alternative)
make tunnel-setup            # First-time zrok setup
```

## Docker Workflow

- **Rebuild after code changes**: After modifying code in any service, rebuild its container to apply the changes:
  ```bash
  docker-compose up -d --build <service-name>
  ```
- Use `make up` only for full rebuilds of all services

## Architecture

See `.claude/rules/microservices.md` for full service map, ports, health checks, and environment variables.

## Agent Teams

This project supports Claude Code agent teams (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` is enabled).

### When to Use Team-Based Parallel Execution

Use the `brain` agent as team lead with specialist teammates when:

- **Complex multi-phase implementation plans** (5+ independent tasks)
- **Cross-service features** requiring changes to 3+ microservices
- **Parallel workstreams** with no blocking dependencies
- **Large refactoring** affecting multiple services simultaneously
- **Implementation plans with clear task boundaries** from `docs/plans/`

**Required Skills:**
- `superpowers:dispatching-parallel-agents` - For tasks in current session
- `superpowers:subagent-driven-development` - For executing plans with independent tasks
- `superpowers:executing-plans` - For separate session with review checkpoints

### Team Structure

- **Brain** (team lead) - Decomposes tasks, coordinates teammates, reviews deliverables
- **Service specialists** - Own specific services (api-gateway, agent-engine, dashboard-api, etc.)
- **Concern specialists** - Focus on security, performance, testing, documentation

### Team Workflow Rules

1. **Task Decomposition**: Brain creates micro-tasks in shared task list (max 300 lines per task)
2. **Ownership**: Each teammate claims tasks via TaskUpdate (prefer lowest ID first)
3. **Scope Boundaries**: Teammates MUST NOT edit files outside assigned scope
4. **Code Standards**: All teammates follow same rules (no comments, strict types, 300 lines max)
5. **Communication**: Use SendMessage tool (NOT text output) to communicate with team
6. **Completion**: Teammates mark tasks completed, then check TaskList for next work
7. **Review**: Brain reviews all deliverables before final integration

### Parallel Execution Guidelines

- Split tasks by service boundaries (api-gateway, dashboard-api, agent-engine, etc.)
- Identify truly independent tasks (no shared state, no sequential dependencies)
- Avoid premature parallelization (sequential is fine if tasks are small)
- Use structured findings format when reporting to team lead

### Service Ownership for Teams

When assigning teammates to services, each teammate should work within their service directory and read its CLAUDE.md:

| Service | Directory | Typical Teammate Role |
|---------|-----------|----------------------|
| API Gateway | `api-gateway/` | Webhook & routing changes |
| Agent Engine | `agent-engine/` | Task processing & CLI integration |
| Dashboard API | `dashboard-api/` | Backend API & WebSocket changes |
| External Dashboard | `external-dashboard/` | Frontend React 19 changes |
| OAuth Service | `oauth-service/` | Auth flow changes |
| Admin Setup | `admin-setup/` | Admin configuration changes |
| MCP Servers | `mcp-servers/` | Tool integration changes |
| API Services | `api-services/` | REST API wrapper changes |
| Task Logger | `task-logger/` | Event logging changes |
| Knowledge Graph | `knowledge-graph/` | Rust graph DB changes |
| LlamaIndex Service | `llamaindex-service/` | RAG pipeline changes |
| Audit Framework | `scripts/audit/` | System audit changes |
