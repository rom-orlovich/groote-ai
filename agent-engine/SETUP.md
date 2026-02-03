# Agent Engine Setup

The Agent Engine (CLI) executes AI agent tasks using Claude or Cursor CLI providers.

## Overview

| Property | Value |
|----------|-------|
| Port | 8080-8089 |
| Container | cli |
| Technology | Python/FastAPI |
| Scalable | Yes (horizontal) |

## Prerequisites

- Redis running on port 6379
- PostgreSQL running on port 5432
- Anthropic API key (for Claude) or Cursor API key (for Cursor)

## Environment Variables

```bash
# CLI Provider Selection
CLI_PROVIDER=claude                    # or 'cursor'

# API Keys (based on provider)
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxx  # For Claude
CURSOR_API_KEY=cur_xxxxxxxxxxxx        # For Cursor

# Task Configuration
MAX_CONCURRENT_TASKS=5
TASK_TIMEOUT_SECONDS=3600
CLAUDE_CODE_ENABLE_TASKS=true

# Infrastructure
REDIS_URL=redis://redis:6379/0
DATABASE_URL=postgresql+asyncpg://agent:agent@postgres:5432/agent_system

# Optional
KNOWLEDGE_GRAPH_URL=http://knowledge-graph:4000
```

## Start the Service

### With Docker Compose (Recommended)

```bash
# Start with Claude CLI
make cli-claude

# Or start with Cursor CLI
make cli-cursor

# Start with scaling (multiple instances)
make cli PROVIDER=claude SCALE=3
```

### Manual Docker Commands

```bash
# Single instance
docker-compose up -d cli

# Multiple instances
docker-compose up -d --scale cli=3 cli
```

### For Local Development

```bash
cd agent-engine

# Install dependencies
uv pip install -r requirements.txt

# Set environment variables
export CLI_PROVIDER=claude
export ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxx
export REDIS_URL=redis://localhost:6379/0
export DATABASE_URL=postgresql+asyncpg://agent:agent@localhost:5432/agent_system

# Run the service
uvicorn main:app --host 0.0.0.0 --port 8080 --reload
```

## Verify Installation

```bash
# Health check
curl http://localhost:8080/health
# Expected: {"status": "healthy"}

# Detailed health (shows component status)
curl http://localhost:8080/health/detailed

# Check CLI status
make cli-status PROVIDER=claude
```

## CLI Providers

### Claude CLI

Uses Anthropic's Claude Code CLI for task execution.

**Requirements:**
- `ANTHROPIC_API_KEY` environment variable
- Claude CLI installed in container (automatic with Docker)

**Model Configuration:**
```bash
# Complex tasks (planning, consultation)
CLAUDE_MODEL_COMPLEX=opus

# Execution tasks (code implementation)
CLAUDE_MODEL_EXECUTION=sonnet
```

### Cursor CLI

Uses Cursor's CLI for task execution.

**Requirements:**
- `CURSOR_API_KEY` environment variable

**Model Configuration:**
```bash
# Complex tasks
CURSOR_MODEL_COMPLEX=claude-sonnet-4.5

# Execution tasks
CURSOR_MODEL_EXECUTION=composer-1
```

## Scaling

The Agent Engine scales horizontally. Each instance independently consumes tasks from the Redis queue.

```bash
# Scale to 3 instances
make cli PROVIDER=claude SCALE=3

# Scale to 5 instances
docker-compose up -d --scale cli=5 cli

# Check running instances
docker-compose ps cli
```

### Port Allocation

When scaled, instances use ports 8080-8089:
- Instance 1: 8080
- Instance 2: 8081
- Instance 3: 8082
- etc.

## Agents and Skills

The Agent Engine uses 13 specialized agents and 9 reusable skills.

### Agents

| Agent | Purpose |
|-------|---------|
| brain | Main orchestrator |
| planning | Discovery and planning |
| executor | TDD implementation |
| verifier | Quality assurance |
| github-issue-handler | GitHub issue processing |
| github-pr-review | Pull request review |
| jira-code-plan | Jira ticket handling |
| slack-inquiry | Slack Q&A |
| service-integrator | External coordination |

### Skills

| Skill | Purpose |
|-------|---------|
| discovery | Repository identification |
| testing | Test generation |
| code-refactoring | Code improvements |
| github-operations | Git/GitHub actions |
| jira-operations | Jira actions |
| slack-operations | Slack messaging |
| human-approval | Approval workflows |
| verification | Quality checks |
| knowledge-graph | Code search |

## MCP Configuration

The Agent Engine connects to MCP servers for tool access. Configuration is in `.claude/mcp.json`:

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
    "sentry": {
      "url": "http://sentry-mcp:9004/sse",
      "transport": "sse"
    },
    "knowledge-graph": {
      "url": "http://knowledge-graph-mcp:9005/sse",
      "transport": "sse"
    }
  }
}
```

## Logs

```bash
# View CLI logs
make cli-logs PROVIDER=claude

# Or with docker-compose
docker-compose logs -f cli

# Filter for task execution
docker-compose logs cli 2>&1 | grep "task"
```

## Troubleshooting

### CLI not processing tasks

1. Check CLI is running:
   ```bash
   docker-compose ps cli
   ```

2. Check Redis connection:
   ```bash
   docker-compose logs cli | grep "Redis"
   ```

3. Check API key is set:
   ```bash
   docker-compose exec cli env | grep API_KEY
   ```

### Task timeout

Increase timeout in `.env`:
```bash
TASK_TIMEOUT_SECONDS=7200  # 2 hours
```

### MCP connection errors

1. Verify MCP servers are running:
   ```bash
   docker-compose ps | grep mcp
   ```

2. Check network connectivity:
   ```bash
   docker-compose exec cli curl http://jira-mcp:9002/health
   ```

## Related Documentation

- [Main Setup Guide](../SETUP.md)
- [Architecture](../docs/ARCHITECTURE.md)
- [Agent Engine README](README.md)
