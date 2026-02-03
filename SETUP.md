# Groote AI Setup Guide

Complete step-by-step guide to set up and run the Groote AI system.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Detailed Setup](#detailed-setup)
4. [Service Integration](#service-integration)
5. [Verification](#verification)
6. [Troubleshooting](#troubleshooting)
7. [Service-Specific Setup](#service-specific-setup)

---

## Prerequisites

### Required Software

| Software | Version | Purpose |
|----------|---------|---------|
| Docker | 20.10+ | Container runtime |
| Docker Compose | 2.0+ | Service orchestration |
| Git | 2.30+ | Version control |

### Optional (for local development)

| Software | Version | Purpose |
|----------|---------|---------|
| Python | 3.11+ | Local development |
| Node.js | 18+ | Dashboard development |
| uv | latest | Python package manager |

### Required Credentials

You need API keys from at least one of these services to use the system:

| Service | Required For | How to Get |
|---------|--------------|------------|
| Anthropic API Key | Claude CLI | [console.anthropic.com](https://console.anthropic.com) |
| GitHub Token | GitHub integration | [github.com/settings/tokens](https://github.com/settings/tokens) |
| Jira API Token | Jira integration | [id.atlassian.com/manage-profile/security/api-tokens](https://id.atlassian.com/manage-profile/security/api-tokens) |
| Slack Bot Token | Slack integration | [api.slack.com/apps](https://api.slack.com/apps) |
| Sentry Auth Token | Sentry integration | [sentry.io/settings/auth-tokens](https://sentry.io/settings/auth-tokens) |

---

## Quick Start

For users who want to get started quickly with minimal configuration:

```bash
# 1. Clone the repository
git clone <repository-url>
cd groote-ai

# 2. Initialize the project (copies .env.example to .env)
make init

# 3. Edit .env with your API keys (minimum: ANTHROPIC_API_KEY or CURSOR_API_KEY)
nano .env

# 4. Start all services
make up

# 5. Start the AI agent CLI
make cli-claude    # or: make cli-cursor

# 6. Verify everything is running
make health
```

The system is now running at:
- **API Gateway**: http://localhost:8000
- **Dashboard UI**: http://localhost:3005
- **Dashboard API**: http://localhost:5000

---

## Detailed Setup

### Step 1: Clone Repository

```bash
git clone <repository-url>
cd groote-ai
```

### Step 2: Create Environment File

```bash
# Copy the example environment file
cp .env.example .env
```

### Step 3: Configure Environment Variables

Edit `.env` with your credentials. Here's what each section needs:

#### 3.1 CLI Provider (Required - choose one)

```bash
# Option A: Claude CLI (recommended)
CLI_PROVIDER=claude
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxx

# Option B: Cursor CLI
CLI_PROVIDER=cursor
CURSOR_API_KEY=cur_xxxxxxxxxxxx
```

#### 3.2 Database (use defaults or customize)

```bash
POSTGRES_PASSWORD=agent
POSTGRES_USER=agent
POSTGRES_DB=agent_system
```

#### 3.3 External Services (configure based on your needs)

**GitHub Integration:**
```bash
GITHUB_TOKEN=ghp_xxxxxxxxxxxx
GITHUB_WEBHOOK_SECRET=your-webhook-secret
```

**Jira Integration:**
```bash
JIRA_URL=https://yourcompany.atlassian.net
JIRA_EMAIL=your-email@company.com
JIRA_API_TOKEN=xxxxxxxxxxxx
JIRA_WEBHOOK_SECRET=your-webhook-secret
```

**Slack Integration:**
```bash
SLACK_BOT_TOKEN=xoxb-xxxxxxxxxxxx
SLACK_SIGNING_SECRET=your-signing-secret
```

**Sentry Integration:**
```bash
SENTRY_DSN=https://xxx@sentry.io/xxx
SENTRY_AUTH_TOKEN=xxxxxxxxxxxx
SENTRY_ORG_SLUG=your-org-slug
```

### Step 4: Build and Start Services

```bash
# Build all Docker images
make build

# Start all services
make up
```

### Step 5: Start the CLI Agent

```bash
# Start Claude CLI with 1 instance
make cli-claude

# Or start with multiple instances for parallel processing
make cli PROVIDER=claude SCALE=3
```

### Step 6: Apply Database Migrations

```bash
# Run database migrations
make db-upgrade
```

---

## Service Integration

### How Services Connect

```
External Services (GitHub/Jira/Slack/Sentry)
         |
         | (Webhooks)
         v
API Gateway :8000  ──────────────────> Redis :6379
         |                                  |
         v                                  v
PostgreSQL :5432                    Agent Engine :8080
                                           |
                                           | (MCP Protocol)
                                           v
                                    MCP Servers :9001-9007
                                           |
                                           | (HTTP)
                                           v
                                    API Services :3001-3004
                                           |
                                           v
                                    External Service APIs
```

### Service Startup Order

The services start in this order (handled automatically by docker-compose):

1. **Infrastructure**: Redis, PostgreSQL
2. **Core Services**: API Gateway, Dashboard API
3. **MCP Servers**: GitHub MCP, Jira MCP, Slack MCP, Sentry MCP
4. **API Services**: GitHub API, Jira API, Slack API, Sentry API
5. **Supporting**: OAuth Service, Task Logger, Knowledge Graph
6. **UI**: External Dashboard
7. **Agent Engine**: CLI (started separately)

### Configuring Webhooks

To receive events from external services, configure webhooks pointing to your API Gateway:

**GitHub Webhook:**
```
URL: https://your-domain.com/webhooks/github
Secret: (value of GITHUB_WEBHOOK_SECRET)
Events: Issues, Pull requests, Issue comments, Pull request reviews
```

**Jira Webhook:**
```
URL: https://your-domain.com/webhooks/jira
Secret: (value of JIRA_WEBHOOK_SECRET)
Events: Issue created, Issue updated, Comment created
```

**Slack Events:**
```
URL: https://your-domain.com/webhooks/slack
Signing Secret: (value of SLACK_SIGNING_SECRET)
Events: app_mention, message.channels
```

**Sentry Webhook:**
```
URL: https://your-domain.com/webhooks/sentry
Events: Issue alerts
```

---

## Verification

### Check Service Health

```bash
# Check all services at once
make health

# Or check individual services
curl http://localhost:8000/health      # API Gateway
curl http://localhost:8080/health      # Agent Engine
curl http://localhost:5000/health      # Dashboard API
curl http://localhost:8010/health      # OAuth Service
curl http://localhost:8090/health      # Task Logger
curl http://localhost:4000/health      # Knowledge Graph
```

### Expected Responses

All health endpoints should return:
```json
{"status": "healthy"}
```

### Check Service Logs

```bash
# View all logs
make logs

# View specific service logs
docker-compose logs -f api-gateway
docker-compose logs -f cli
docker-compose logs -f dashboard-api
```

### Check CLI Status

```bash
make cli-status PROVIDER=claude
```

### Access the Dashboard

Open http://localhost:3005 in your browser to see the monitoring dashboard.

---

## Troubleshooting

### Common Issues

#### Services fail to start

```bash
# Check if ports are already in use
sudo lsof -i :8000  # API Gateway
sudo lsof -i :5432  # PostgreSQL
sudo lsof -i :6379  # Redis

# Stop all services and restart
make down
make up
```

#### Database connection errors

```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check logs
docker-compose logs postgres

# Restart PostgreSQL
docker-compose restart postgres
```

#### Redis connection errors

```bash
# Check Redis is running
docker-compose ps redis

# Test Redis connection
docker-compose exec redis redis-cli ping
# Should return: PONG
```

#### CLI agent not processing tasks

```bash
# Check CLI logs
make cli-logs PROVIDER=claude

# Check if CLI is connected to Redis
docker-compose logs cli | grep "Connected to Redis"

# Restart CLI
make cli-down PROVIDER=claude
make cli-claude
```

#### Webhook signature validation fails

1. Verify webhook secrets in `.env` match the configured secrets in external services
2. Check that the webhook URL is correctly configured
3. Check API Gateway logs: `docker-compose logs api-gateway`

### Reset Everything

```bash
# Stop all services
make down

# Remove all data (WARNING: deletes databases)
docker-compose down -v

# Rebuild and start fresh
make build
make up
```

---

## Service-Specific Setup

For detailed setup instructions for each service, see:

| Service | Setup Guide |
|---------|-------------|
| API Gateway | [api-gateway/SETUP.md](api-gateway/SETUP.md) |
| Agent Engine | [agent-engine/SETUP.md](agent-engine/SETUP.md) |
| Dashboard API | [dashboard-api/SETUP.md](dashboard-api/SETUP.md) |
| External Dashboard | [external-dashboard/SETUP.md](external-dashboard/SETUP.md) |
| OAuth Service | [oauth-service/SETUP.md](oauth-service/SETUP.md) |
| MCP Servers | [mcp-servers/SETUP.md](mcp-servers/SETUP.md) |
| API Services | [api-services/SETUP.md](api-services/SETUP.md) |
| Knowledge Services | [docs/SETUP-KNOWLEDGE.md](docs/SETUP-KNOWLEDGE.md) |

---

## Optional: Knowledge Services

The knowledge layer provides advanced code search and semantic retrieval. It's optional but enhances agent capabilities.

### Enable Knowledge Services

```bash
# Start with knowledge profile
docker-compose --profile knowledge up -d

# Or use make command
make knowledge-up
```

### Knowledge Services Ports

| Service | Port | Purpose |
|---------|------|---------|
| LlamaIndex | 8002 | Hybrid RAG |
| GKG Service | 8003 | Code graph |
| Indexer Worker | 8004 | Background indexing |
| LlamaIndex MCP | 9006 | Search tools |
| GKG MCP | 9007 | Graph tools |

See [docs/SETUP-KNOWLEDGE.md](docs/SETUP-KNOWLEDGE.md) for detailed knowledge layer setup.

---

## Next Steps

After setup is complete:

1. **Configure webhooks** in your external services (GitHub, Jira, Slack, Sentry)
2. **Test the integration** by creating a test issue or PR
3. **Monitor the dashboard** at http://localhost:3005
4. **Scale the CLI** as needed: `make cli PROVIDER=claude SCALE=3`

For architecture details, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).
