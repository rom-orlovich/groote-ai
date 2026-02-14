# Slack API Service

REST API wrapper for Slack operations with message posting and channel management.

## Development

- Port: 3003
- Language: Python
- Framework: FastAPI
- Max 300 lines per file, no comments, strict types, async/await for I/O
- Tests: `uv run pytest api-services/slack-api/tests/ -v`

## Key Features

- Message posting to channels with Block Kit support
- Thread replies and message updates
- Channel operations (list, get info, history)
- Reaction management
- User information lookup
- Credential isolation (stored only in this container)

## Environment

```bash
SLACK_BOT_TOKEN=xoxb-xxx
PORT=3003
```
