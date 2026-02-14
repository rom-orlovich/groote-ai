# Groote AI - System Features

## Overview

Groote AI is a containerized multi-agent system that receives webhooks from GitHub, Jira, and Slack, processes tasks with AI agents (Claude Code CLI or Cursor CLI), and posts responses back to the originating service. This document provides a system-level feature index with references to per-service documentation.

## Feature Index

### Webhook Reception and Routing

Receives HTTP webhooks from GitHub, Jira, and Slack. Validates signatures, extracts metadata, creates tasks, and enqueues to Redis for asynchronous processing. Returns HTTP 200/202 within 50ms.

**Service:** API Gateway (port 8000)
**Details:** [api-gateway/docs/features.md](../api-gateway/docs/features.md)

**Supported Sources:**
- GitHub: Issues, pull requests, comments, push events
- Jira: Ticket creation, updates, comments (requires `ai-agent` label)
- Slack: App mentions, direct messages

### AI Agent Execution

Picks up tasks from Redis queue and executes them using Claude Code CLI or Cursor CLI. 13 specialized agents handle different task types. Supports horizontal scaling via multiple CLI instances.

**Service:** Agent Engine (port 8080-8089)
**Details:** [agent-engine/docs/features.md](../agent-engine/docs/features.md)

**Agents:**
- `brain` - Main orchestrator for complex tasks
- `planning` - Discovery and planning phase
- `executor` - TDD implementation
- `verifier` - Quality assurance
- `github-issue-handler` - GitHub issue processing
- `github-pr-review` - PR code review
- `jira-code-plan` - Jira ticket code planning
- `slack-inquiry` - Slack Q&A with knowledge layer
- `service-integrator` - Cross-platform coordination

### MCP Tool Interface

Model Context Protocol servers provide tool interfaces for agents to interact with external services. Agents never hold API credentials; all access goes through MCP servers to API services.

**Services:** MCP Servers (ports 9001-9007)
**Details:** See individual MCP server docs in `mcp-servers/*/docs/`

**Tool Servers:**
- GitHub MCP (9001) - PRs, issues, comments, code search
- Jira MCP (9002) - Tickets, transitions, comments, search
- Slack MCP (9003) - Messages, channels, threads
- Knowledge Graph MCP (9005) - Code search, references, call graphs
- LlamaIndex MCP (9006) - Hybrid search (optional)
- GKG MCP (9007) - Code graph queries (optional)

### Real-Time Dashboard

React monitoring UI with real-time task status via WebSocket. Shows task progress, conversation history, and agent activity.

**Services:** External Dashboard (port 3005), Dashboard API (port 5000)
**Details:** [external-dashboard/docs/features.md](../external-dashboard/docs/features.md), [dashboard-api/docs/features.md](../dashboard-api/docs/features.md)

**Capabilities:**
- Real-time task monitoring via WebSocket
- Conversation view with message history
- Agent activity tracking
- OAuth integration management
- AI provider configuration

### OAuth and Authentication

Centralized OAuth flows for GitHub, Jira, and Slack with automatic token refresh and Fernet encryption at rest.

**Service:** OAuth Service (port 8010)
**Details:** [oauth-service/docs/features.md](../oauth-service/docs/features.md)

**Providers:**
- GitHub App Installation (auto-refresh)
- Jira PKCE OAuth 2.0 (refresh token)
- Slack OAuth 2.0

### Credential Isolation

API keys are stored only in API service containers. MCP servers, agents, and the API Gateway never have direct access to credentials.

**Services:** API Services (ports 3001-3003)

**Credential-Free Zone:**
- API Gateway (no API keys)
- MCP Servers (no API keys)
- Agent Engine (no API keys)

### Knowledge Layer (Optional)

Advanced knowledge capabilities for code search, dependency analysis, and hybrid RAG queries. Indexes GitHub repos, Jira tickets, and Confluence pages.

**Services:** LlamaIndex Service (8002), GKG Service (8003), Indexer Worker, Knowledge Graph (4000)
**Details:** [docs/KNOWLEDGE-LAYER.md](KNOWLEDGE-LAYER.md), [docs/SETUP-KNOWLEDGE.md](SETUP-KNOWLEDGE.md)

**Capabilities:**
- Vector similarity search via ChromaDB
- Code relationship graph analysis
- Hybrid RAG combining vectors and graphs
- Background indexing from GitHub, Jira, Confluence
- Code entity tracking (functions, classes, imports)

### Task Logging

Captures task output from Redis pub/sub and writes structured logs for audit and debugging.

**Service:** Task Logger (port 8090)
**Details:** [task-logger/docs/features.md](../task-logger/docs/features.md)

### Loop Prevention

Prevents infinite webhook loops from agent-posted comments triggering new tasks. Uses Redis-based tracking with TTL expiration.

**Service:** API Gateway (built-in)
**Details:** [api-gateway/docs/features.md](../api-gateway/docs/features.md)

**Methods:**
- Comment ID tracking with 1-hour TTL
- Bot username detection
- Redis dedup keys for Jira (60s TTL)

### Admin Setup

Token-authenticated admin interface for initial OAuth app configuration. Stores credentials in `setup_config` table with admin scope.

**Service:** Admin Setup (port 8015)
**Details:** [admin-setup/SETUP.md](../admin-setup/SETUP.md)

### End-to-End System Audit

Automated audit framework that fires real webhooks through the full pipeline and evaluates response quality across 10 dimensions with 10 component health checks.

**Tool:** `scripts/audit/`
**Details:** [scripts/audit/docs/features.md](../scripts/audit/docs/features.md)

**Capabilities:**
- 8 registered audit flows covering Slack, Jira, GitHub, and cross-platform
- Real webhook triggers with proper signatures
- 10-dimension quality scoring with configurable thresholds
- 10-component pipeline health verification
- Evidence collection and report generation

## Service Port Reference

| Service | Port(s) | Category |
|---------|---------|----------|
| API Gateway | 8000 | Core |
| Agent Engine (CLI) | 8080-8089 | Core |
| Dashboard API | 5000 | Core |
| External Dashboard | 3005 | Core |
| OAuth Service | 8010 | Core |
| Admin Setup | 8015 | Core |
| Task Logger | 8090 | Core |
| Knowledge Graph | 4000 | Core |
| GitHub MCP | 9001 | MCP |
| Jira MCP | 9002 | MCP |
| Slack MCP | 9003 | MCP |
| Knowledge Graph MCP | 9005 | MCP |
| LlamaIndex MCP | 9006 | MCP (Optional) |
| GKG MCP | 9007 | MCP (Optional) |
| GitHub API | 3001 | API Service |
| Jira API | 3002 | API Service |
| Slack API | 3003 | API Service |
| ChromaDB | 8001 | Knowledge (Optional) |
| LlamaIndex Service | 8002 | Knowledge (Optional) |
| GKG Service | 8003 | Knowledge (Optional) |
| Indexer Worker | 8004 | Knowledge (Optional) |
| Redis | 6379 | Storage |
| PostgreSQL | 5432 | Storage |
