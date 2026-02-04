# Dashboard API - Features

## Overview

Backend API for groote-ai dashboard with real-time task streaming, analytics, and conversation management. Provides REST endpoints and WebSocket connections for the frontend.

## Core Features

### Task Management

List, filter, and retrieve task details with pagination support. Tasks can be filtered by status, agent type, source, and date range.

**Capabilities:**
- Paginated task listing
- Status filtering (queued, running, completed, failed)
- Agent type filtering
- Date range queries
- Full task detail retrieval

### Real-Time Streaming

WebSocket hub for live task output streaming. Clients subscribe to task channels and receive output in real-time.

**WebSocket Features:**
- Connection management per client
- Channel-based subscriptions
- Redis Pub/Sub integration
- Automatic reconnection support

### Analytics

Cost tracking, performance metrics, and usage histograms for monitoring and optimization.

**Metrics Provided:**
- Total cost (USD)
- Average cost per task
- Token usage (input/output)
- Task success rate
- Average task duration
- Tasks per time period

**Histogram Types:**
- Cost per hour/day
- Task count per hour/day
- Token usage per hour/day

### Conversations

Chat interface for agent interactions with message history and task correlation.

**Conversation Features:**
- Create new conversations
- List user conversations
- Retrieve message history
- Link tasks to conversations

### Webhook Status Monitoring

Monitor webhook configurations and event history across all integrated sources.

**Monitoring Features:**
- Webhook configuration status
- Recent event history
- Success/failure rates
- Last received timestamp

### OAuth Status

Display OAuth installation status for GitHub, Jira, and Slack integrations.

**OAuth Information:**
- Installation status per platform
- Connected organizations
- Token expiration status
- Scope information

### Data Source Management

Manage knowledge sources for RAG integration (GitHub repos, Jira projects, Confluence spaces).

**Source Types:**
- GitHub repositories
- Jira projects
- Confluence spaces

**Operations:**
- List configured sources
- Add new sources
- Remove sources
- Trigger re-indexing

## API Endpoints

### Dashboard

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/status` | GET | Machine status |
| `/api/tasks` | GET | List tasks with pagination |
| `/api/tasks/{task_id}` | GET | Task details |
| `/api/tasks/{task_id}/logs/full` | GET | Complete task logs |
| `/api/agents` | GET | List available agents |

### Analytics

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/analytics/summary` | GET | Analytics summary |
| `/api/analytics/costs/histogram` | GET | Cost breakdown by time |
| `/api/analytics/performance` | GET | Performance metrics |

### Conversations

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/conversations` | GET | List conversations |
| `/api/conversations` | POST | Create conversation |
| `/api/conversations/{id}/messages` | GET | Get messages |

### Webhooks

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/webhooks` | GET | Webhook configurations |
| `/api/webhooks/events` | GET | Webhook events |
| `/api/webhooks/stats` | GET | Webhook statistics |

### WebSocket

| Endpoint | Protocol | Description |
|----------|----------|-------------|
| `/ws` | WebSocket | Real-time updates |
