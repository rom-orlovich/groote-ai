# Slack MCP Server

> FastMCP-based MCP server for Slack operations.

## Purpose

The Slack MCP server provides a Model Context Protocol interface for Slack operations. It translates MCP tool calls into HTTP requests to the Slack API service, keeping credentials isolated.

## Architecture

```
Agent Engine (via mcp.json)
         |
         | SSE Connection
         v
+-----------------------------------------+
|      Slack MCP :9003                     |
|                                          |
|  1. Receive MCP tool call               |
|  2. Translate to HTTP request            |
|  3. Call slack-api service              |
|     (no credentials)                     |
|  4. Return standardized response         |
+-----------------------------------------+
         |
         | HTTP (no credentials)
         v
+-----------------------------------------+
|      Slack API Service :3003             |
|  (Has credentials, makes API call)       |
+-----------------------------------------+
```

## Folder Structure

```
slack-mcp/
├── main.py            # FastMCP server + 8 tool registrations
├── slack_mcp.py       # SlackAPI HTTP client class
├── config.py          # Settings
├── requirements.txt   # Dependencies
└── Dockerfile
```

## MCP Tools (8)

### Messaging

| Tool | Description |
|------|-------------|
| `send_slack_message` | Send message to channel or thread (via thread_ts) |
| `update_slack_message` | Update an existing message |

### History

| Tool | Description |
|------|-------------|
| `get_slack_channel_history` | Get channel messages with time-range filtering |
| `get_slack_thread` | Get replies in a thread |

### Reactions

| Tool | Description |
|------|-------------|
| `add_slack_reaction` | Add emoji reaction to a message |

### Channel & User Info

| Tool | Description |
|------|-------------|
| `get_slack_channel_info` | Get channel details (name, topic, members) |
| `list_slack_channels` | List workspace channels with cursor pagination |
| `get_slack_user_info` | Get user details (name, email, status) |

## Environment Variables

```bash
SLACK_API_URL=http://slack-api:3003
PORT=9003
REQUEST_TIMEOUT=30
```

## SSE Endpoint

MCP clients connect via Server-Sent Events:

```
GET /sse HTTP/1.1
Host: slack-mcp:9003
Accept: text/event-stream
```

## Health Check

```bash
curl http://localhost:9003/health
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md) - Component diagrams and data flows
- [Features](docs/features.md) - Feature list and capabilities
- [Flows](docs/flows.md) - Process flow documentation

## Related Services

- **slack-api**: Provides actual Slack API operations (port 3003)
- **agent-engine**: Connects to this MCP server via SSE
