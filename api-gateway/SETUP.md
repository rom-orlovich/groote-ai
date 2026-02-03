# API Gateway Setup

The API Gateway receives and validates webhooks from external services (GitHub, Jira, Slack, Sentry).

## Overview

| Property | Value |
|----------|-------|
| Port | 8000 |
| Container | api-gateway |
| Technology | Python/FastAPI |

## Prerequisites

- Redis running on port 6379
- PostgreSQL running on port 5432

## Environment Variables

```bash
# Required
REDIS_URL=redis://redis:6379/0
DATABASE_URL=postgresql+asyncpg://agent:agent@postgres:5432/agent_system

# Webhook Secrets (for signature validation)
GITHUB_WEBHOOK_SECRET=your-github-webhook-secret
JIRA_WEBHOOK_SECRET=your-jira-webhook-secret
SLACK_WEBHOOK_SECRET=your-slack-signing-secret

# Optional
KNOWLEDGE_GRAPH_URL=http://knowledge-graph:4000
```

## Start the Service

### With Docker Compose (Recommended)

```bash
# Starts automatically with other services
make up

# Or start individually
docker-compose up -d api-gateway
```

### For Local Development

```bash
cd api-gateway

# Install dependencies
uv pip install -r requirements.txt

# Set environment variables
export REDIS_URL=redis://localhost:6379/0
export DATABASE_URL=postgresql+asyncpg://agent:agent@localhost:5432/agent_system

# Run the service
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Verify Installation

```bash
# Health check
curl http://localhost:8000/health
# Expected: {"status": "healthy"}

# Check webhook endpoints
curl http://localhost:8000/docs
# Opens Swagger UI
```

## Configure Webhooks

### GitHub Webhook

1. Go to your repository: **Settings > Webhooks > Add webhook**
2. Configure:
   - **Payload URL**: `https://your-domain.com/webhooks/github`
   - **Content type**: `application/json`
   - **Secret**: Value of `GITHUB_WEBHOOK_SECRET`
   - **Events**: Select individual events:
     - Issues
     - Issue comments
     - Pull requests
     - Pull request reviews
     - Pull request review comments

### Jira Webhook

1. Go to: **Jira Settings > System > WebHooks**
2. Configure:
   - **URL**: `https://your-domain.com/webhooks/jira`
   - **Events**:
     - Issue: created, updated
     - Comment: created, updated

### Slack Events

1. Go to [api.slack.com/apps](https://api.slack.com/apps) > Your App
2. Navigate to **Event Subscriptions**
3. Configure:
   - **Request URL**: `https://your-domain.com/webhooks/slack`
   - **Subscribe to bot events**:
     - `app_mention`
     - `message.channels`

### Sentry Webhook

1. Go to: **Sentry > Settings > Integrations > Webhooks**
2. Configure:
   - **URL**: `https://your-domain.com/webhooks/sentry`
   - **Events**: Issue alerts

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check |
| `/webhooks/github` | POST | GitHub webhook receiver |
| `/webhooks/jira` | POST | Jira webhook receiver |
| `/webhooks/slack` | POST | Slack webhook receiver |
| `/webhooks/sentry` | POST | Sentry webhook receiver |

## Logs

```bash
# View logs
docker-compose logs -f api-gateway

# Filter for errors
docker-compose logs api-gateway 2>&1 | grep -i error
```

## Troubleshooting

### Webhook signature validation fails

1. Verify the webhook secret matches exactly (no extra whitespace)
2. Check the signature header is being sent:
   - GitHub: `X-Hub-Signature-256`
   - Jira: `X-Atlassian-Webhook-Signature`
   - Slack: `X-Slack-Signature`

### Service won't start

```bash
# Check if port is in use
sudo lsof -i :8000

# Check Redis connection
docker-compose exec redis redis-cli ping

# Check PostgreSQL connection
docker-compose exec postgres pg_isready -U agent
```

## Related Documentation

- [Main Setup Guide](../SETUP.md)
- [Architecture](../docs/ARCHITECTURE.md)
