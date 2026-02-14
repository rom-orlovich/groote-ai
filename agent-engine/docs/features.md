# Agent Engine - Features

## Overview

Scalable task execution engine with multi-CLI provider support (Claude Code CLI and Cursor CLI). Consumes tasks from Redis queue, executes them using CLI providers, orchestrates 13 specialized agents, and posts results back to sources.

## Core Features

### Task Consumption

Polls Redis queue using BRPOP for efficient blocking consumption. Tasks are consumed atomically ensuring no duplicate processing across multiple engine replicas.

**Capabilities:**
- BRPOP-based blocking consumption
- Atomic task pickup
- Multi-replica support
- Configurable batch size

### CLI Execution

Spawns CLI providers (Claude Code CLI or Cursor CLI) with agent-specific prompts. Handles process lifecycle, output streaming, and error capture.

**CLI Providers:**
- Claude Code CLI: `claude -p --output-format stream-json`
- Cursor CLI: `cursor --headless --output-format json-stream`

**Execution Features:**
- Headless execution mode
- JSON streaming output
- Real-time cost/token tracking
- Configurable timeout

### Agent Orchestration

Routes tasks to 13 specialized agents based on source and event type. Each agent has optimized prompts and tool access for its domain.

**Core Agents:**
- `brain` - Central orchestrator, delegates to specialists
- `planning` - Discovery and PLAN.md creation
- `executor` - TDD implementation
- `verifier` - Quality verification

**Workflow Agents:**
- `github-issue-handler` - GitHub issues and comments
- `github-pr-review` - Pull request reviews
- `jira-code-plan` - Jira ticket implementation
- `slack-inquiry` - Slack questions and requests

**Support Agents:**
- `service-integrator` - External service coordination
- `self-improvement` - Memory and learning
- `agent-creator` - Dynamic agent generation
- `skill-creator` - Dynamic skill generation
- `webhook-generator` - Webhook configuration

### Result Processing

Captures execution results including cost, token usage, stdout, and stderr. Results are persisted to PostgreSQL and streamed to Redis Pub/Sub.

**Captured Metrics:**
- Cost in USD (input + output tokens)
- Input token count
- Output token count
- Execution duration
- Exit code and status

### Session Management

Tracks user sessions with cost aggregation and rate limiting. Sessions persist across disconnections.

**Session Features:**
- Per-user session tracking
- Cost aggregation across tasks
- Task count tracking
- Rate limit enforcement
- Disconnect preservation

### Task Lifecycle

State machine governing all task executions with well-defined transitions.

**Task States:**
- `QUEUED` - Waiting in Redis queue
- `RUNNING` - Currently executing
- `WAITING_INPUT` - Awaiting user response
- `COMPLETED` - Successfully finished
- `FAILED` - Execution error
- `CANCELLED` - User cancelled

### Model Selection

Maps agent types to appropriate models based on complexity.

**Claude Provider:**
- Complex agents (brain, planning, verifier) → `opus`
- Execution agents (executor, handlers) → `sonnet`

**Cursor Provider:**
- Complex agents → `claude-sonnet-4.5`
- Execution agents → `composer-1`

### Agent Routing

Complete routing table mapping sources and event types to agents.

**Routing Map:**
| Source | Event Type | Agent |
|--------|------------|-------|
| github | issues | github-issue-handler |
| github | pull_request | github-pr-review |
| jira | issue_created | jira-code-plan |
| slack | app_mention | slack-inquiry |
| internal | discovery | planning |
| internal | implementation | executor |

### Output Streaming

Streams CLI output to Redis Pub/Sub and WebSocket in real-time for dashboard display.

**Streaming Channels:**
- Redis Pub/Sub: `task:{task_id}:output`
- WebSocket: Dashboard API hub

### MCP Integration

Connects to MCP servers for external service access during agent execution.

**MCP Servers:**
- GitHub MCP: Repository and issue operations
- Jira MCP: Ticket and project operations
- Slack MCP: Channel and message operations

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Basic health check |
| `/health/auth` | GET | CLI provider authentication status |
| `/health/detailed` | GET | Detailed component status |
| `/status` | GET | Service status with queue depth |
| `/tasks` | POST | Create task (internal) |
| `/tasks/{task_id}` | GET | Get task status |
| `/knowledge/toggle` | POST | Enable/disable knowledge services |
