# Slack API Service Architecture

## Overview

The Slack API service provides REST endpoints for Slack operations, including message posting, thread replies, channel management, and user lookups. It abstracts the Slack Web API for internal services.

## Design Principles

1. **Token Abstraction** - Internal services don't handle Slack tokens
2. **Thread Awareness** - Support for threaded conversations
3. **Block Kit Support** - Rich message formatting
4. **Rate Limit Handling** - Automatic retry with backoff

## Component Architecture

```mermaid
graph TB
    subgraph Clients["Internal Clients"]
        AE[Agent Engine]
        MCP[Slack MCP Server]
    end

    subgraph Service["Slack API :3003"]
        MW[Auth Middleware]
        RT[Route Handlers]
        SC[Slack Client]
    end

    subgraph External["External"]
        SL[Slack Web API]
    end

    AE --> MW
    MCP --> MW

    MW --> RT
    RT --> SC
    SC -->|Bearer Token| SL
```

## Directory Structure

```
slack-api/
├── main.py                    # FastAPI application
├── api/
│   ├── routes.py              # API route definitions
│   └── server.py              # FastAPI app creation
├── client/
│   └── slack_client.py        # Slack API client
├── middleware/
│   ├── auth.py                # Authentication middleware
│   └── error_handler.py       # Error handling
└── config/
    └── settings.py            # Configuration
```

## Authentication Flow

```mermaid
flowchart TB
    A[Request Received] --> B{Has workspace_id?}
    B -->|Yes| C[Query OAuth Service]
    B -->|No| D[Use SLACK_BOT_TOKEN]

    C --> E{Token Found?}
    E -->|Yes| F[Use OAuth Token]
    E -->|No| D

    D --> G[Make Slack API Call]
    F --> G
```

## API Endpoints

### Messages API (prefix: `/api/v1`)

```mermaid
graph LR
    subgraph Messages["/messages + /reactions"]
        M1["POST /messages - Send Message"]
        M2["PUT /messages - Update Message"]
        M3["POST /reactions - Add Reaction"]
    end
```

### Channels API (prefix: `/api/v1`)

```mermaid
graph LR
    subgraph Channels["/channels"]
        C1["GET / - List Channels"]
        C2["GET /{channel} - Get Channel Info"]
        C3["GET /{channel}/history - Get Messages"]
        C4["GET /{channel}/threads/{ts} - Get Thread Replies"]
    end
```

### Users API (prefix: `/api/v1`)

```mermaid
graph LR
    subgraph Users["/users"]
        U1["GET /{user_id} - Get User Info"]
    end
```

## Slack Client Protocol

```mermaid
classDiagram
    class SlackClientProtocol {
        <<interface>>
        +post_message(channel, text, blocks) Message
        +reply_thread(channel, thread_ts, text) Message
        +update_message(channel, ts, text) Message
        +delete_message(channel, ts) void
        +get_channel(channel_id) Channel
        +list_channels() List~Channel~
    }

    class SlackClient {
        -token: str
        +post_message(channel, text, blocks)
        +reply_thread(channel, thread_ts, text)
        +update_message(channel, ts, text)
    }

    SlackClientProtocol <|.. SlackClient
```

## Data Flow

### Thread Reply Flow

```mermaid
sequenceDiagram
    participant AE as Agent Engine
    participant API as Slack API Service
    participant OS as OAuth Service
    participant SL as Slack

    AE->>API: POST /messages/reply
    Note right of API: {channel, thread_ts, text}

    API->>OS: GET /oauth/token/slack?workspace_id={ws}
    OS-->>API: {access_token: "xoxb-..."}

    API->>SL: POST chat.postMessage
    Note right of SL: thread_ts included

    SL-->>API: {ok: true, ts: "..."}
    API-->>AE: {ts: "...", channel: "..."}
```

## Message Formatting

### Block Kit Support

```mermaid
graph TB
    subgraph Blocks["Block Types"]
        S[Section Block]
        D[Divider Block]
        C[Context Block]
        A[Actions Block]
    end

    subgraph Elements["Elements"]
        T[Text]
        B[Button]
        I[Image]
        MD[Markdown]
    end

    S --> T
    S --> MD
    A --> B
    C --> I
```

### Example Block Message

```json
{
    "channel": "C01234567",
    "blocks": [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "✅ *Task Completed*"
            }
        },
        {
            "type": "divider"
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "```\nCode changes applied\n```"
            }
        }
    ]
}
```

## Rate Limiting

```mermaid
graph TB
    A[API Request] --> B[Make Slack Call]
    B --> C{Rate Limited?}
    C -->|No| D[Return Response]
    C -->|Yes| E[Read Retry-After]
    E --> F[Wait]
    F --> B
```

| Tier | Methods | Rate |
|------|---------|------|
| Tier 1 | chat.postMessage | 1/sec |
| Tier 2 | conversations.list | 20/min |
| Tier 3 | users.list | 50/min |

## Error Handling

### Error Response Format

```json
{
    "error": "channel_not_found",
    "message": "Channel C99999999 not found",
    "status_code": 404,
    "details": {
        "channel_id": "C99999999"
    }
}
```

### Error Mapping

| Slack Error | Service Error | Message |
|-------------|---------------|---------|
| channel_not_found | not_found | Channel not found |
| invalid_auth | unauthorized | Invalid token |
| ratelimited | rate_limited | Rate limited |
| not_in_channel | forbidden | Bot not in channel |

## Testing Strategy

Tests focus on **behavior**, not implementation:

- ✅ "Post message returns message timestamp"
- ✅ "Thread reply includes parent ts"
- ✅ "Rate limit triggers retry"
- ❌ "Slack SDK called with correct arguments"

## Integration Points

### With OAuth Service
```
Slack API → GET /oauth/token/slack?workspace_id={ws} → OAuth Service
```

### With Agent Engine
```
Agent Engine → POST /messages/reply → Slack API → Slack
```

### With MCP Server
```
Slack MCP → GET /channels/{id}/history → Slack API → Slack
```
