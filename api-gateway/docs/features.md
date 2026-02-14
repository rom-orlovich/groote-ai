# API Gateway - Features

## Overview

Central webhook reception and routing service for groote-ai system. Receives webhooks from GitHub, Jira, Slack, validates signatures, extracts routing metadata, and enqueues tasks to Redis.

## Core Features

### Webhook Reception

Receives HTTP POST requests from external services (GitHub, Jira, Slack) and processes them asynchronously. Each webhook source has a dedicated endpoint with source-specific handling logic.

**Supported Sources:**
- GitHub: Issues, pull requests, comments, push events
- Jira: Ticket creation, updates, comments
- Slack: App mentions, direct messages, slash commands

### Security Validation

HMAC signature verification implemented as middleware for each webhook source. Invalid signatures are rejected immediately with 401 Unauthorized before any processing occurs.

**Security Features:**
- HMAC-SHA256 signature validation
- Per-source secret configuration
- Timing-safe comparison
- Request body integrity verification

### Event Parsing

Extracts routing metadata from webhook payloads to determine how tasks should be processed. Metadata extraction is source-specific.

**Extracted Metadata:**
- GitHub: owner, repo, PR/issue number, comment ID, labels
- Jira: ticket key, project, labels, assignee
- Slack: channel ID, thread timestamp, user ID

### Task Creation

Generates unique task IDs and creates task metadata structures for processing by agent-engine. Tasks contain all information needed for autonomous processing.

**Task Structure:**
- Unique UUID task_id
- Source identification
- Event type classification
- Extracted prompt text
- Source-specific metadata
- Agent type routing
- Repository path

### Queue Management

Enqueues tasks to Redis for consumption by agent-engine workers. Uses Redis LPUSH for reliable delivery with BRPOP consumption on the worker side.

**Queue Features:**
- Atomic task enqueue
- Redis list-based queue
- Task persistence until consumed
- Multiple consumer support

### Immediate Response

Returns HTTP response within 50ms to prevent webhook timeouts. Actual task processing happens asynchronously after response.

**Response Types:**
- `202 Accepted`: Task queued successfully
- `200 OK`: Event acknowledged but skipped
- `401 Unauthorized`: Invalid signature
- `400 Bad Request`: Invalid payload

### Loop Prevention

Prevents infinite loops from agent-posted comments triggering new tasks.

**GitHub Prevention:**
- Comment ID tracking with TTL (1 hour)
- Bot username detection
- User type checking

**Jira Prevention:**
- Bot comment detection by author displayName matching `JIRA_AI_AGENT_NAME`
- Atlassian `accountType: "app"` detection
- Bot comment body marker matching (e.g. "Agent is analyzing this issue")
- Redis dedup key per issue+event with 60s TTL to prevent burst duplicates

### Event Filtering

Only processes relevant event types and actions. Ignores unsupported events to reduce noise.

**Processed Events:**
- GitHub: issues (opened, edited, labeled), issue_comment (created), pull_request (opened, synchronize, reopened), push
- Jira: `jira:issue_created`, `jira:issue_updated`, `comment_created` (only when issue has `ai-agent` label)
- Slack: app_mention, message (DM only)

### Agent Routing

Routes webhooks to appropriate agent types based on source and event type.

**Routing Map:**
- GitHub issues → `github-issue-handler`
- GitHub PRs → `github-pr-review`
- Jira tickets → `jira-code-plan`
- Slack mentions → `slack-inquiry`

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/webhooks/github` | POST | GitHub webhook events |
| `/webhooks/jira` | POST | Jira webhook events |
| `/webhooks/slack` | POST | Slack Events API |
| `/health` | GET | Health check endpoint |
