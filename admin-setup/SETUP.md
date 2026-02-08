# Admin Setup Service

Port: **8015**

The Admin Setup Service is a system-administration tool for configuring OAuth app credentials with admin authentication.

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

## Usage

### Authenticate

All admin endpoints require the `X-Admin-Token` header:

```bash
curl -H "X-Admin-Token: $ADMIN_SETUP_TOKEN" \
  http://localhost:8015/api/setup/status
```

### Get Setup Status

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

### Complete Setup

```bash
curl -X POST \
  -H "X-Admin-Token: $ADMIN_SETUP_TOKEN" \
  http://localhost:8015/api/setup/complete
```

## Architecture

- **Port**: 8015
- **Authentication**: Token-based via `X-Admin-Token` header
- **Database**: PostgreSQL (saves OAuth credentials to `setup_config` table with `scope=admin`)
- **Frontend**: React 19 + TypeScript + Vite

## Security Notes

- The `ADMIN_SETUP_TOKEN` should be strong and stored securely in `.env`
- OAuth app credentials are encrypted when stored in the database
- All sensitive values are masked in logs and responses
- Only accessible with valid admin token

## Development

```bash
cd admin-setup

# Install dependencies
pip install -r requirements.txt

# Run tests
uv run pytest src/

# Run server
uv run uvicorn src/main:app --host 0.0.0.0 --port 8015
```
