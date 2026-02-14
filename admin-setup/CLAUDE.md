# Admin Setup

System administration tool for configuring OAuth app credentials (port 8015). FastAPI backend with React frontend, token-based authentication, and encrypted credential storage.

## API Endpoints

- `/health` - Health check (no auth)
- `POST /api/auth` - Authenticate with admin token
- `GET /api/setup/status` - Get setup progress
- `GET /api/setup/infrastructure` - Check Postgres + Redis health
- `POST /api/setup/steps/{step_id}` - Save step config or skip
- `GET /api/setup/steps/{step_id}/config` - Get saved config for step
- `POST /api/setup/validate/{service}` - Validate credentials against external APIs
- `GET /api/setup/summary` - Get masked config summary
- `GET /api/setup/export` - Export .env content
- `POST /api/setup/complete` - Mark setup as complete
- `POST /api/setup/reset` - Reset setup and delete configs

## Setup Flow

1. Admin authenticates with `ADMIN_SETUP_TOKEN`
2. Welcome step (intro)
3. Configure Public URL
4. Configure GitHub OAuth app credentials
5. Configure Jira OAuth app credentials
6. Configure Slack OAuth app credentials
7. Review and export .env

## Folder Structure

```
admin-setup/
├── src/
│   ├── main.py              # FastAPI app, lifespan, SPA serving
│   ├── routes.py            # API router (12 endpoints)
│   ├── service.py           # Business logic (state, config CRUD)
│   ├── models.py            # Pydantic request/response models
│   ├── config.py            # Settings via pydantic-settings
│   ├── db.py                # SQLAlchemy models (setup_state, setup_config)
│   ├── validators.py        # Infrastructure + credential validation
│   └── encryption.py        # Fernet encrypt/decrypt helpers
├── frontend/
│   ├── src/
│   │   ├── App.tsx           # React app root
│   │   ├── components/       # AuthGate, DashboardView, Layout, etc.
│   │   └── steps/            # WelcomeStep, ServiceStep, ReviewStep
│   └── package.json
├── requirements.txt
├── Dockerfile
└── docs/                     # Architecture, features, flows docs
```

## Testing

```bash
PYTHONPATH=admin-setup/src:$PYTHONPATH uv run pytest admin-setup/src/ -v

cd admin-setup/frontend && pnpm test
```

## Database Tables

- `setup_state` - Single-row wizard progress (current step, completion, progress %)
- `setup_config` - Key-value config storage with encryption, scope="admin"

## Authentication

All `/api/setup/*` endpoints require `admin_session` cookie set via `POST /api/auth`. Cookie contains the admin token, validated against `ADMIN_SETUP_TOKEN` env var.

## Sensitive Key Handling

These keys are encrypted before storage: `GITHUB_CLIENT_SECRET`, `GITHUB_WEBHOOK_SECRET`, `JIRA_CLIENT_SECRET`, `SLACK_CLIENT_SECRET`, `SLACK_SIGNING_SECRET`, `SLACK_STATE_SECRET`.

## Environment Variables

```bash
ADMIN_SETUP_TOKEN=your-secure-token
DATABASE_URL=postgresql+asyncpg://agent:agent@postgres:5432/agent_system
REDIS_URL=redis://redis:6379/0
DASHBOARD_URL=http://localhost:3005
TOKEN_ENCRYPTION_KEY=fernet-key-base64
LOG_LEVEL=INFO
```

## Development Rules

- Maximum 300 lines per file
- NO `any` types - use strict Pydantic models
- NO comments - self-explanatory code only
- Tests must run fast (< 5 seconds), no real network calls
- Use async/await for all I/O operations
- Use `uv` for Python, `pnpm` for frontend
