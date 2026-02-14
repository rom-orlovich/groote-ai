# Admin Setup Service

**Port**: 8015

A system-administration tool for configuring OAuth app credentials with secure token-based authentication. This service provides a guided setup interface for initializing Groote AI's platform integrations.

## Purpose

The Admin Setup Service helps administrators:

- Configure OAuth credentials for GitHub, Jira, and Slack integrations
- Verify infrastructure health (database, Redis, core services)
- Complete initial system setup with a web-based wizard
- Securely store encrypted platform credentials

## Quick Start

```bash
# Build and start
docker build -t admin-setup ./admin-setup
docker-compose up admin-setup

# Check health
curl http://localhost:8015/health
```

## Configuration

Set these environment variables in `.env`:

```bash
ADMIN_SETUP_TOKEN=your-secure-token
DATABASE_URL=postgresql+asyncpg://agent:password@localhost:5432/agent_system
REDIS_URL=redis://localhost:6379/0
DASHBOARD_URL=http://localhost:3005
```

## API Endpoints

All admin endpoints require the `X-Admin-Token` header for authentication.

### GET /health

Health check endpoint (no auth required).

```bash
curl http://localhost:8015/health
```

### GET /api/setup/status

Get the current setup status and progress.

```bash
curl -H "X-Admin-Token: $ADMIN_SETUP_TOKEN" \
  http://localhost:8015/api/setup/status
```

Response:

```json
{
  "is_authenticated": true,
  "steps": [
    {
      "id": "infrastructure",
      "title": "Infrastructure Health",
      "description": "Check database and Redis connectivity",
      "status": "pending"
    },
    ...
  ],
  "progress": 0
}
```

### POST /api/setup/complete

Complete the setup process and save OAuth credentials.

```bash
curl -X POST \
  -H "X-Admin-Token: $ADMIN_SETUP_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"github_app_id": "...", "github_private_key": "...", ...}' \
  http://localhost:8015/api/setup/complete
```

## Architecture

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Backend | FastAPI + Python 3.13 | REST API with token auth |
| Frontend | React 19 + TypeScript + Vite | Web-based setup wizard |
| Database | PostgreSQL | Stores encrypted OAuth credentials in `setup_config` table with `scope=admin` |
| Cache | Redis | Session and state management |
| Port | 8015 | HTTP server |

## Security

- `ADMIN_SETUP_TOKEN` should be strong and stored securely in `.env`
- OAuth app credentials are encrypted before storage in the database
- All sensitive values are masked in logs and API responses
- Only accessible with valid admin token via `X-Admin-Token` header
- Credentials stored with `scope=admin` in the `setup_config` table

## Development

```bash
cd admin-setup

# Install dependencies
uv pip install -r requirements.txt

# Run tests
uv run pytest src/

# Run server locally
uv run uvicorn src/main:app --host 0.0.0.0 --port 8015 --reload
```

### Tech Stack

- **Backend**: FastAPI, Pydantic, SQLAlchemy, asyncpg
- **Frontend**: React 19, TypeScript, Vite, pnpm
- **Encryption**: cryptography library (Fernet symmetric encryption)
- **Authentication**: JWT tokens via PyJWT

## Common Issues

### 401 Unauthorized

Ensure `X-Admin-Token` header matches `ADMIN_SETUP_TOKEN` environment variable.

### Database Connection Failed

Verify `DATABASE_URL` is correct and PostgreSQL is running:

```bash
docker-compose ps postgres
```

### Frontend Build Fails

Ensure Node.js 22+ and pnpm are installed:

```bash
corepack enable
corepack prepare pnpm@latest --activate
cd admin-setup/frontend
pnpm install
pnpm build
```

## Integration with Groote AI

The Admin Setup Service is the first-run configuration tool for Groote AI. After setup:

1. OAuth credentials are stored in the database with `scope=admin`
2. Services (api-gateway, mcp-servers) read credentials at runtime
3. The setup token can be rotated or disabled after initial configuration
4. The service can remain running for credential updates or be stopped after setup

## Documentation

- [Architecture](docs/ARCHITECTURE.md) - Component diagrams and data flows
- [Features](docs/features.md) - Feature list and capabilities
- [Flows](docs/flows.md) - Process flow documentation

## See Also

- [CLAUDE.md](./CLAUDE.md) - Development guide for AI agents
- [SETUP.md](./SETUP.md) - Original setup documentation
- [src/main.py](./src/main.py) - FastAPI application entry point
- [frontend/](./frontend/) - React frontend source
