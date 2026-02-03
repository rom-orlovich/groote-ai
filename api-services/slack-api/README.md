# Slack API Service

> REST API wrapper for Slack operations with message posting and channel management.

## Purpose

The Slack API service provides REST endpoints for Slack operations, including message posting, thread replies, channel information, and message history retrieval.

## Architecture

```
Agent Engine / MCP Server
         │
         │ HTTP Request (no credentials)
         ▼
┌─────────────────────────────────────┐
│      Slack API :3003                │
│                                     │
│  1. Receive HTTP request           │
│  2. Authenticate (internal token)  │
│  3. Get Slack Bot Token            │
│  4. Call Slack Web API             │
│  5. Return standardized response    │
└─────────────────────────────────────┘
         │
         │ HTTPS (Bearer Token)
         ▼
    Slack Web API
```

## Business Logic

### Core Responsibilities

1. **Message Posting**: Post messages to channels with text and blocks
2. **Thread Replies**: Reply to messages in threads for conversation continuity
3. **Channel Operations**: List channels, get channel info, retrieve history
4. **Rich Formatting**: Support Block Kit for rich message formatting
5. **Response Posting**: Post agent responses back to Slack threads

## API Endpoints

### Messages

| Endpoint                         | Method | Purpose              |
| -------------------------------- | ------ | -------------------- |
| `/messages/{channel}`            | POST   | Post message         |
| `/messages/{channel}/{thread}`   | POST   | Reply in thread      |

### Channels

| Endpoint                         | Method | Purpose              |
| -------------------------------- | ------ | -------------------- |
| `/channels`                      | GET    | List channels        |
| `/channels/{channel}`            | GET    | Get channel info     |
| `/channels/{channel}/history`    | GET    | Get message history  |

## Environment Variables

```bash
SLACK_BOT_TOKEN=xoxb-xxx
PORT=3003
LOG_LEVEL=INFO
```

## Usage Examples

### Post Message

```bash
curl -X POST http://localhost:3003/messages/C1234567890 \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Task completed successfully!"
  }'
```

### Reply in Thread

```bash
curl -X POST http://localhost:3003/messages/C1234567890/1706702300.000001 \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Here is the analysis result..."
  }'
```

### Post with Blocks

```bash
curl -X POST http://localhost:3003/messages/C1234567890 \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Task complete",
    "blocks": [
      {"type": "section", "text": {"type": "mrkdwn", "text": "*Task Complete*"}}
    ]
  }'
```

## Error Handling

Standardized error responses:

```json
{
  "error": "channel_not_found",
  "message": "Channel not found",
  "status_code": 404
}
```

## Health Check

```bash
curl http://localhost:3003/health
```

## Documentation

- [Features](docs/features.md) - Feature list with test coverage
- [Flows](docs/flows.md) - Process flow documentation

## Related Services

- **agent-engine**: Uses this service for response posting
- **mcp-servers/slack-mcp**: Calls this service for Slack operations
