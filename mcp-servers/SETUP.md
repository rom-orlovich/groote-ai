# MCP Servers Setup

> **Note**: Service credentials are managed through the [Setup Wizard](../SETUP.md#quick-start-setup-wizard) and [OAuth Service](../oauth-service/SETUP.md). MCP servers proxy requests to API Services which hold the actual credentials.

MCP (Model Context Protocol) servers provide tool interfaces for AI agents to interact with external services.

## Overview

| Server | Port | Purpose |
|--------|------|---------|
| GitHub MCP | 9001 | GitHub operations |
| Jira MCP | 9002 | Jira operations |
| Slack MCP | 9003 | Slack messaging |
| Knowledge Graph MCP | 9005 | Code search |
| LlamaIndex MCP | 9006 | Hybrid search (optional) |
| GKG MCP | 9007 | Code graph (optional) |

## Architecture

MCP servers act as a bridge between AI agents and API services:

```
Agent Engine ──(MCP/SSE)──> MCP Server ──(HTTP)──> API Service ──> External API
```

**Key principle**: MCP servers do NOT store credentials. They forward requests to API services which hold the credentials.

## Prerequisites

- Corresponding API services running
- Network connectivity between services

## Environment Variables

### GitHub MCP (Official Server)

```bash
GITHUB_TOOLSETS=repos,issues,pull_requests
```

Credentials are managed through the OAuth Service; the GitHub MCP receives an authenticated token at runtime.

### Jira MCP

```bash
PORT=9002
JIRA_API_URL=http://jira-api:3002
```

### Slack MCP

```bash
PORT=9003
SLACK_API_URL=http://slack-api:3003
```

### Knowledge Graph MCP

```bash
KG_PORT=9005
KG_KNOWLEDGE_GRAPH_URL=http://knowledge-graph:4000
CHROMA_HOST=chromadb
CHROMA_PORT=8000
CHROMA_COLLECTION=agent_knowledge
```

## Start Services

### With Docker Compose (Recommended)

```bash
# All MCP servers start automatically with:
make up

# Start specific MCP server
docker-compose up -d jira-mcp
docker-compose up -d slack-mcp
docker-compose up -d knowledge-graph-mcp
```

### Start Optional Knowledge MCP Servers

```bash
# Start with knowledge profile
docker-compose --profile knowledge up -d llamaindex-mcp gkg-mcp
```

## Verify Installation

Each MCP server exposes a health endpoint:

```bash
# Jira MCP
curl http://localhost:9002/health

# Slack MCP
curl http://localhost:9003/health

# Knowledge Graph MCP
curl http://localhost:9005/health
```

## MCP Transport

All MCP servers use Server-Sent Events (SSE) transport:

- **Endpoint**: `/sse`
- **Protocol**: MCP over HTTP with SSE

### Connection from Agent Engine

The Agent Engine connects to MCP servers using the configuration in `.claude/mcp.json`:

```json
{
  "mcpServers": {
    "github": {
      "url": "http://github-mcp:9001/sse",
      "transport": "sse"
    },
    "jira": {
      "url": "http://jira-mcp:9002/sse",
      "transport": "sse"
    },
    "slack": {
      "url": "http://slack-mcp:9003/sse",
      "transport": "sse"
    },
    "knowledge-graph": {
      "url": "http://knowledge-graph-mcp:9005/sse",
      "transport": "sse"
    }
  }
}
```

## Available Tools by Server

### GitHub MCP

| Tool | Purpose |
|------|---------|
| `create_pull_request` | Create a new PR |
| `get_file_contents` | Read file from repo |
| `create_branch` | Create a branch |
| `add_comment` | Comment on issue/PR |
| `search_code` | Search code in repos |

### Jira MCP

| Tool | Purpose |
|------|---------|
| `get_issue` | Get issue details |
| `create_issue` | Create new issue |
| `update_issue` | Update issue fields |
| `add_comment` | Add comment to issue |
| `search_issues` | Search with JQL |
| `transition_issue` | Change issue status |

### Slack MCP

| Tool | Purpose |
|------|---------|
| `post_message` | Post to channel |
| `reply_in_thread` | Reply in thread |
| `get_conversations` | List conversations |
| `list_channels` | List channels |

### Knowledge Graph MCP

| Tool | Purpose |
|------|---------|
| `search_code` | Search indexed code |
| `find_references` | Find code references |
| `get_call_graph` | Get function calls |
| `get_dependencies` | Get dependencies |

## Individual Server Setup

### Jira MCP

```bash
cd mcp-servers/jira-mcp

# Install dependencies
uv pip install -r requirements.txt

# Run locally
PORT=9002 JIRA_API_URL=http://localhost:3002 uvicorn main:app --port 9002
```

### Slack MCP

```bash
cd mcp-servers/slack-mcp

# Install dependencies
uv pip install -r requirements.txt

# Run locally
PORT=9003 SLACK_API_URL=http://localhost:3003 uvicorn main:app --port 9003
```

## Logs

```bash
# View all MCP server logs
docker-compose logs -f jira-mcp slack-mcp knowledge-graph-mcp

# View specific server
docker-compose logs -f jira-mcp
```

## Troubleshooting

### MCP connection fails from Agent Engine

1. Check MCP server is running:
   ```bash
   docker-compose ps | grep mcp
   ```

2. Verify SSE endpoint is accessible:
   ```bash
   curl http://localhost:9002/sse
   # Should hang (SSE stream) or return connection info
   ```

3. Check network connectivity:
   ```bash
   docker-compose exec cli curl http://jira-mcp:9002/health
   ```

### Tool calls fail

1. Check corresponding API service is running:
   ```bash
   docker-compose ps | grep api
   ```

2. Review MCP server logs:
   ```bash
   docker-compose logs jira-mcp | tail -50
   ```

3. Test API service directly:
   ```bash
   curl http://localhost:3002/health
   ```

## Related Documentation

- [Main Setup Guide](../SETUP.md)
- [API Services Setup](../api-services/SETUP.md)
- [Architecture](../docs/ARCHITECTURE.md)
