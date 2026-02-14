# Webhook Integration Guide

## Overview

Groote AI processes webhooks from Jira, GitHub, and Slack through a conversation-based pipeline. Each webhook source maps to a conversation via a deterministic `flow_id`, enabling context reuse across multiple events from the same source entity.

## Architecture

```
Platform (Jira/GitHub/Slack)
    |
    v
API Gateway (port 8000)
    |  - Signature validation
    |  - Task queuing to Redis
    v
Agent Engine
    |  - Conversation Bridge: get_or_create conversation by flow_id
    |  - Fetch last 5 messages for context
    |  - Build enriched prompt with platform instructions
    |  - Execute via CLI provider (Claude/Cursor)
    v
MCP Tool Response
    |  - Jira: jira:add_jira_comment
    |  - GitHub: github:add_issue_comment
    |  - Slack: slack:send_slack_message
    v
Dashboard (real-time via WebSocket)
```

## How It Works

### 1. Conversation Reuse via flow_id

Each webhook source generates a deterministic flow_id:

| Platform | Format | Example |
|----------|--------|---------|
| Jira | `jira:{ticket_key}` | `jira:KAN-6` |
| GitHub | `github:{owner/repo}#{number}` | `github:acme/app#42` |
| Slack | `slack:{channel}:{thread_ts}` | `slack:C12345:1234567890.123456` |

When a webhook fires, the agent engine calls `GET /api/conversations/by-flow/{flow_id}`. If a conversation exists, it reuses it. Otherwise, it creates a new one via `POST /api/conversations`.

### 2. Context Awareness

Before executing a task, the agent fetches the last 5 messages from the conversation via `GET /api/conversations/{id}/context`. This gives the AI model awareness of prior interactions on the same ticket, PR, or thread.

### 3. Platform Instructions

The enriched prompt includes platform-specific instructions telling the agent which MCP tool to use for posting its response back to the source platform:

- **Jira**: Post comment via `jira:add_jira_comment`
- **GitHub**: Post comment via `github:add_issue_comment`
- **Slack**: Post message via `slack:send_slack_message`

### 4. Real-time Dashboard Updates

Task events (`task:created`, `task:completed`) are broadcast via WebSocket to the dashboard frontend. The `useTaskStream` hook invalidates React Query caches so the UI updates automatically.

## API Reference

### Conversation Endpoints (Dashboard API, port 5000)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/conversations` | List all conversations |
| GET | `/api/conversations/by-flow/{flow_id}` | Find conversation by flow_id |
| POST | `/api/conversations` | Create conversation |
| GET | `/api/conversations/{id}` | Get conversation detail |
| GET | `/api/conversations/{id}/messages` | Get all messages |
| POST | `/api/conversations/{id}/messages` | Add message |
| GET | `/api/conversations/{id}/context` | Get last N messages |
| GET | `/api/conversations/{id}/metrics` | Get aggregated metrics |

### Task Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/tasks` | Register external task |
| GET | `/api/tasks/{id}/logs` | Get task logs |

## Key Files

| File | Purpose |
|------|---------|
| `agent-engine/services/conversation_bridge.py` | flow_id builders, conversation CRUD, system messages |
| `agent-engine/services/task_routing.py` | Prompt enrichment with context and platform instructions |
| `dashboard-api/api/conversations.py` | Conversation REST API endpoints |
| `external-dashboard/src/hooks/useTaskStream.ts` | WebSocket hook for real-time task events |
| `external-dashboard/src/hooks/useConversations.ts` | React Query hooks for conversation data |

## Troubleshooting

### Conversation not created

Check agent-engine logs for conversation bridge errors:
```bash
docker compose logs agent-engine | grep conversation
```

Verify the dashboard-api is reachable from agent-engine:
```bash
docker compose exec cli curl http://dashboard-api:5000/api/health
```

### Context not fetched

Verify the conversation has messages:
```bash
curl http://localhost:5001/api/conversations/{id}/context?max_messages=5
```

### Agent not posting back to platform

Verify MCP servers are configured in `agent-engine/.claude/mcp.json` and running:
```bash
docker compose ps | grep mcp
```

Check agent-engine logs for MCP tool invocation errors:
```bash
docker compose logs cli | grep "mcp\|tool"
```

### WebSocket not updating dashboard

Verify Redis pub/sub is working:
```bash
docker compose exec redis redis-cli SUBSCRIBE "task:*:status"
```

Check dashboard-api logs for WebSocket listener status:
```bash
docker compose logs dashboard-api | grep "task_status_listener"
```
