# API Services Setup

> **Note**: Credentials for these services are now primarily configured through the [Setup Wizard](../SETUP.md#quick-start-setup-wizard) and managed by the [OAuth Service](../oauth-service/SETUP.md). The direct API tokens documented below are for legacy or fallback scenarios.

API Services are REST API wrappers that securely hold credentials for external services.

## Overview

| Service | Port | Purpose |
|---------|------|---------|
| GitHub API | 3001 | GitHub API wrapper |
| Jira API | 3002 | Jira API wrapper |
| Slack API | 3003 | Slack API wrapper |

## Architecture

API Services isolate credentials from other components:

```
MCP Server ──(HTTP)──> API Service ──(authenticated)──> External API
                           │
                           └── Credentials stored here ONLY
```

**Security**: Only API Services have access to API keys. MCP servers, webhooks, and agents never have direct access.

## Prerequisites

- API keys for the external services you want to use
- Network connectivity to external APIs

## Environment Variables

### GitHub API

```bash
PORT=3001
GITHUB_TOKEN=ghp_xxxxxxxxxxxx
```

### Jira API

```bash
PORT=3002
JIRA_URL=https://yourcompany.atlassian.net
JIRA_EMAIL=agent@company.com
JIRA_API_TOKEN=xxxxxxxxxxxx
```

### Slack API

```bash
PORT=3003
SLACK_BOT_TOKEN=xoxb-xxxxxxxxxxxx
```

## Start Services

### With Docker Compose (Recommended)

```bash
# All API services start automatically with:
make up

# Start specific service
docker-compose up -d github-api
docker-compose up -d jira-api
docker-compose up -d slack-api
```

## Verify Installation

```bash
# GitHub API
curl http://localhost:3001/health

# Jira API
curl http://localhost:3002/health

# Slack API
curl http://localhost:3003/health
```

## Getting API Credentials

### GitHub Personal Access Token

1. Go to [github.com/settings/tokens](https://github.com/settings/tokens)
2. Click "Generate new token (classic)"
3. Select scopes:
   - `repo` - Full control of private repositories
   - `workflow` - Update GitHub Actions workflows
4. Copy the token (starts with `ghp_`)

### Jira API Token

1. Go to [id.atlassian.com/manage-profile/security/api-tokens](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Click "Create API token"
3. Give it a label (e.g., "groote-ai")
4. Copy the token

**Note**: You also need:
- **JIRA_URL**: Your Atlassian instance URL (e.g., `https://company.atlassian.net`)
- **JIRA_EMAIL**: The email associated with your Atlassian account

### Slack Bot Token

1. Go to [api.slack.com/apps](https://api.slack.com/apps)
2. Create or select your app
3. Navigate to "OAuth & Permissions"
4. Add Bot Token Scopes:
   - `channels:history`
   - `channels:read`
   - `chat:write`
   - `users:read`
5. Install app to workspace
6. Copy the "Bot User OAuth Token" (starts with `xoxb-`)

## Individual Service Setup

### GitHub API

```bash
cd api-services/github-api

# Install dependencies
uv pip install -r requirements.txt

# Set environment
export PORT=3001
export GITHUB_TOKEN=ghp_xxxxxxxxxxxx

# Run
uvicorn main:app --host 0.0.0.0 --port 3001 --reload
```

### Jira API

```bash
cd api-services/jira-api

# Install dependencies
uv pip install -r requirements.txt

# Set environment
export PORT=3002
export JIRA_URL=https://company.atlassian.net
export JIRA_EMAIL=agent@company.com
export JIRA_API_TOKEN=xxxxxxxxxxxx

# Run
uvicorn main:app --host 0.0.0.0 --port 3002 --reload
```

### Slack API

```bash
cd api-services/slack-api

# Install dependencies
uv pip install -r requirements.txt

# Set environment
export PORT=3003
export SLACK_BOT_TOKEN=xoxb-xxxxxxxxxxxx

# Run
uvicorn main:app --host 0.0.0.0 --port 3003 --reload
```

## API Endpoints

Each API service provides similar endpoints:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check |
| `/issues` | GET | List issues |
| `/issues/{id}` | GET | Get issue |
| `/issues` | POST | Create issue |
| `/issues/{id}` | PATCH | Update issue |
| `/issues/{id}/comments` | POST | Add comment |

Specific endpoints vary by service - check individual README files for details.

## Logs

```bash
# View all API service logs
docker-compose logs -f github-api jira-api slack-api

# View specific service
docker-compose logs -f jira-api
```

## Troubleshooting

### Authentication errors

1. Verify token is correct and hasn't expired
2. Check token has required permissions/scopes
3. For Jira, verify email matches the token owner

### Connection timeouts

1. Check external API is accessible:
   ```bash
   curl https://api.github.com
   curl https://yourcompany.atlassian.net
   ```

2. Check for network issues:
   ```bash
   docker-compose exec github-api curl https://api.github.com
   ```

### Rate limiting

External APIs have rate limits:
- **GitHub**: 5000 requests/hour
- **Jira**: 10 requests/second
- **Slack**: Varies by method

Check response headers for rate limit status.

## Related Documentation

- [Main Setup Guide](../SETUP.md)
- [MCP Servers Setup](../mcp-servers/SETUP.md)
- [Architecture](../docs/ARCHITECTURE.md)
