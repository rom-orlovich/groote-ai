# Dashboard API Setup

The Dashboard API provides the backend for the monitoring UI, including REST endpoints and WebSocket connections.

## Overview

| Property | Value |
|----------|-------|
| Port | 5000 |
| Container | dashboard-api |
| Technology | Python/FastAPI |

## Prerequisites

- Redis running on port 6379
- PostgreSQL running on port 5432

## Environment Variables

```bash
# Required
REDIS_URL=redis://redis:6379/0
DATABASE_URL=postgresql+asyncpg://agent:agent@postgres:5432/agent_system

# Agent Engine Connection
AGENT_ENGINE_URL=http://cli:8080

# CORS Configuration
CORS_ORIGINS=http://localhost:3005,http://external-dashboard:80

# Setup Wizard (optional for local, required for cloud)
TOKEN_ENCRYPTION_KEY=            # Fernet key for encrypting stored credentials
DEPLOYMENT_MODE=local            # local | cloud | kubernetes | ecs | cloudrun
```

## Start the Service

### With Docker Compose (Recommended)

```bash
# Starts automatically with other services
make up

# Or start individually
docker-compose up -d dashboard-api
```

### For Local Development

```bash
cd dashboard-api

# Install dependencies
uv pip install -r requirements.txt

# Set environment variables
export REDIS_URL=redis://localhost:6379/0
export DATABASE_URL=postgresql+asyncpg://agent:agent@localhost:5432/agent_system
export CORS_ORIGINS=http://localhost:3005

# Run the service
uvicorn main:app --host 0.0.0.0 --port 5000 --reload
```

## Verify Installation

```bash
# Health check
curl http://localhost:5000/health
# Expected: {"status": "healthy"}

# API documentation
curl http://localhost:5000/docs
# Opens Swagger UI
```

## API Endpoints

### Health & Status

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check |
| `/api/health` | GET | API health check |

### Tasks

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/tasks` | GET | List all tasks |
| `/api/tasks/{id}` | GET | Get task by ID |
| `/api/tasks/{id}/logs` | GET | Get task logs |

### Analytics

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/analytics/summary` | GET | Task summary stats |
| `/api/analytics/by-source` | GET | Tasks by source |
| `/api/analytics/timeline` | GET | Task timeline |

### Setup Wizard

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/setup/status` | GET | Current setup state (progress, completed steps) |
| `/api/setup/steps/{step}` | POST | Save configuration for a wizard step |
| `/api/setup/steps/{step}/config` | GET | Retrieve saved config for a step |
| `/api/setup/validate/{service}` | POST | Test connection to an external service |
| `/api/setup/complete` | POST | Mark setup as complete |
| `/api/setup/reset` | POST | Reset setup state to start over |
| `/api/setup/export?format=env` | GET | Export config (env, k8s, docker-secrets, github-actions) |
| `/api/setup/infrastructure` | GET | Check PostgreSQL and Redis health |

### WebSocket

| Endpoint | Purpose |
|----------|---------|
| `/ws` | Real-time task updates |

## WebSocket Connection

The Dashboard API provides real-time updates via WebSocket.

### Connect

```javascript
const ws = new WebSocket('ws://localhost:5000/ws');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Task update:', data);
};
```

### Message Format

```json
{
  "type": "task_update",
  "task_id": "abc123",
  "status": "running",
  "output": "Processing..."
}
```

## Logs

```bash
# View logs
docker-compose logs -f dashboard-api

# Filter for WebSocket connections
docker-compose logs dashboard-api 2>&1 | grep "WebSocket"
```

## Troubleshooting

### WebSocket connection fails

1. Check CORS configuration allows your frontend origin
2. Verify the service is running:
   ```bash
   curl http://localhost:5000/health
   ```

### No task data showing

1. Check database connection:
   ```bash
   docker-compose logs dashboard-api | grep "database"
   ```

2. Verify tasks exist:
   ```bash
   curl http://localhost:5000/api/tasks
   ```

## Related Documentation

- [Main Setup Guide](../SETUP.md)
- [External Dashboard Setup](../external-dashboard/SETUP.md)
- [Architecture](../docs/ARCHITECTURE.md)
