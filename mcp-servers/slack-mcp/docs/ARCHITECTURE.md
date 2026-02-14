# Slack MCP Architecture

## Overview

The Slack MCP server is a thin protocol translation layer that exposes 8 Slack operations as MCP tools. It delegates all API calls to the Slack API service (port 3003), maintaining credential isolation.

## Design Principles

1. **Thin Wrapper** - No business logic, pure protocol translation
2. **Credential Isolation** - Never stores Slack tokens, delegates to slack-api
3. **Lazy Connection** - HTTP client created on first use, reused across requests
4. **Thread Awareness** - Tools support Slack threading via thread_ts parameter

## Component Architecture

```mermaid
graph TB
    subgraph Clients["MCP Clients"]
        AE[Agent Engine]
        CLI[Claude Code CLI]
    end

    subgraph Server["Slack MCP :9003"]
        MCP[FastMCP Server]
        TOOLS[Tool Definitions - main.py]
        CLIENT[SlackAPI Client - slack_mcp.py]
        CFG[Settings - config.py]
    end

    subgraph Backend["Slack API :3003"]
        API[Slack API Service]
        CREDS[Bot Token Store]
    end

    subgraph External["Slack"]
        SLACK[Slack Web API]
    end

    AE -->|SSE| MCP
    CLI -->|SSE| MCP
    MCP --> TOOLS
    TOOLS --> CLIENT
    CLIENT --> CFG
    CLIENT -->|HTTP| API
    API --> CREDS
    API -->|HTTPS| SLACK
```

## Directory Structure

```
slack-mcp/
├── main.py            # FastMCP server + 8 tool registrations
├── slack_mcp.py       # SlackAPI class (HTTP client wrapper)
├── config.py          # Settings via pydantic-settings
├── requirements.txt   # Runtime deps
└── Dockerfile
```

## Data Flow

### Tool Invocation Flow

```mermaid
sequenceDiagram
    participant Client as MCP Client
    participant MCP as FastMCP Server
    participant Tool as Tool Function
    participant API as SlackAPI Client
    participant Backend as slack-api:3003

    Client->>MCP: MCP tool call (SSE)
    MCP->>Tool: Dispatch to tool function
    Tool->>API: Call SlackAPI method
    API->>API: Lazy-init httpx.AsyncClient
    API->>Backend: HTTP request (GET/POST/PUT)
    Backend-->>API: JSON response
    API-->>Tool: dict[str, Any]
    Tool-->>MCP: Return result
    MCP-->>Client: MCP response (SSE)
```

## API Endpoint Mapping

| Tool | HTTP Method | Backend Endpoint |
|------|-------------|-----------------|
| `send_slack_message` | POST | `/api/v1/messages` |
| `get_slack_channel_history` | GET | `/api/v1/channels/{channel}/history` |
| `get_slack_thread` | GET | `/api/v1/channels/{channel}/threads/{thread_ts}` |
| `add_slack_reaction` | POST | `/api/v1/reactions` |
| `get_slack_channel_info` | GET | `/api/v1/channels/{channel}` |
| `list_slack_channels` | GET | `/api/v1/channels` |
| `get_slack_user_info` | GET | `/api/v1/users/{user_id}` |
| `update_slack_message` | PUT | `/api/v1/messages` |

## Testing Strategy

Tests focus on **behavior**, not implementation:

- "send_slack_message sends message with correct channel and text"
- "get_slack_thread returns thread replies"
- "add_slack_reaction forwards emoji to backend"
- Uses `respx` to mock HTTP calls to slack-api service

## Integration Points

### With Agent Engine
```
Agent Engine --> SSE /sse --> Slack MCP :9003
```

### With Slack API Service
```
Slack MCP --> HTTP --> slack-api:3003 --> Slack Web API
```
