# Dashboard API

Backend API for groote-ai dashboard (port 5000). Provides REST endpoints, WebSocket hub for real-time updates, analytics, and conversation management.

## API Endpoints

- `/api/tasks` - Task listing, details, logs, and lifecycle
- `/api/chat` - Chat with brain agent (conversation context)
- `/api/analytics/*` - Cost tracking, performance metrics
- `/api/conversations` - Conversation management
- `/api/webhooks` - Webhook configurations, events, stats
- `/api/cli/*` - CLI start/stop/status control
- `/api/credentials/*` - Claude credentials management
- `/api/oauth-status/*` - OAuth connection status
- `/api/setup/*` - Setup configuration
- `/api/user-settings/*` - Per-user settings
- `/api/sources/*` - Source management
- `/ws` - WebSocket for real-time updates
- `/api/health` - Health check

## Core Responsibilities

1. **Task Management**: List, filter, retrieve task details and logs
2. **Chat Interface**: Send messages to brain with conversation context
3. **Real-Time Streaming**: WebSocket streaming of task/CLI status
4. **Analytics**: Cost tracking, performance metrics, histograms
5. **Conversations**: Conversation management with flow_id support
6. **Webhook Status**: Monitor webhook configurations and events
7. **CLI Control**: Start/stop/status of CLI providers
8. **User Settings**: Per-user configuration management

## Folder Structure

```
dashboard-api/
├── main.py              # FastAPI application
├── api/                 # REST endpoints (12 modules)
│   ├── dashboard.py     # Tasks, chat, agents, webhooks
│   ├── analytics.py     # Cost/performance metrics
│   ├── conversations.py # Conversation management
│   ├── cli_control.py   # CLI start/stop/status
│   ├── credentials.py   # Claude credentials
│   ├── user_settings.py # Per-user settings
│   └── websocket.py     # WebSocket handler
├── core/                # Database, WebSocket hub
├── shared/              # Shared models
├── middleware/           # CORS configuration
└── tests/               # Co-located tests
```

## Testing

Tests are co-located with the service for portability.

```bash
# From groote-ai root
make test-dashboard

# Or directly
cd groote-ai
PYTHONPATH=dashboard-api:$PYTHONPATH uv run pytest dashboard-api/tests/ -v
```

### Test Factories

Import factories from `tests/factories/`:

```python
from .factories import TaskFactory, SessionFactory, TaskStatus
from .factories import ConversationFactory, WebhookFactory
from .factories.webhook_factory import WebhookValidationError
```

## Environment Variables

```bash
DATABASE_URL=postgresql+asyncpg://agent:agent@postgres:5432/agent_system
REDIS_URL=redis://redis:6379/0
AGENT_ENGINE_URL=http://agent-engine:8080
CORS_ORIGINS=http://localhost:3005,http://localhost:3002
PORT=5000
```

## WebSocket Protocol

**Subscribe**: `{"type": "subscribe", "channel": "task:{task_id}"}`

**Task Output**: `{"type": "task_output", "task_id": "...", "output": "..."}`

**Task Status**: `{"type": "task_status", "task_id": "...", "status": "completed"}`

## Development Rules

- Maximum 300 lines per file
- NO `any` types - use strict Pydantic models
- NO comments - self-explanatory code only
- Tests must run fast (< 5 seconds), no real network calls
- Use async/await for all I/O operations
