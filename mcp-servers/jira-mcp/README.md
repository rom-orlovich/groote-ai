# Jira MCP Server

> FastMCP-based MCP server for Jira operations.

## Purpose

The Jira MCP server provides a Model Context Protocol interface for Jira operations. It translates MCP tool calls into HTTP requests to the Jira API service, keeping credentials isolated.

## Architecture

```
Agent Engine (via mcp.json)
         |
         | SSE Connection
         v
+-----------------------------------------+
|      Jira MCP :9002                      |
|                                          |
|  1. Receive MCP tool call               |
|  2. Translate to HTTP request            |
|  3. Call jira-api service               |
|     (no credentials)                     |
|  4. Return standardized response         |
+-----------------------------------------+
         |
         | HTTP (no credentials)
         v
+-----------------------------------------+
|      Jira API Service :3002              |
|  (Has credentials, makes API call)       |
+-----------------------------------------+
```

## Folder Structure

```
jira-mcp/
├── main.py            # FastMCP server + 10 tool registrations
├── jira_mcp.py        # JiraAPI HTTP client class
├── config.py          # Settings
├── requirements.txt   # Dependencies
└── Dockerfile
```

## MCP Tools (10)

### Issue Management

| Tool | Description |
|------|-------------|
| `get_jira_issue` | Get issue details by key (e.g., PROJ-123) |
| `create_jira_issue` | Create issue with project_key, summary, description, type |
| `update_jira_issue` | Update issue fields by key |
| `add_jira_comment` | Add comment to an issue |
| `search_jira_issues` | Search using JQL with pagination |

### Workflow

| Tool | Description |
|------|-------------|
| `get_jira_transitions` | Get available status transitions |
| `transition_jira_issue` | Move issue to new status |

### Project & Board Management

| Tool | Description |
|------|-------------|
| `create_jira_project` | Create a new project (software, business, service_desk) |
| `get_jira_boards` | List boards (optionally filtered by project) |
| `create_jira_board` | Create Kanban or Scrum board |

## Environment Variables

```bash
JIRA_API_URL=http://jira-api:3002
PORT=9002
REQUEST_TIMEOUT=30
```

## SSE Endpoint

MCP clients connect via Server-Sent Events:

```
GET /sse HTTP/1.1
Host: jira-mcp:9002
Accept: text/event-stream
```

## Health Check

```bash
curl http://localhost:9002/health
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md) - Component diagrams and data flows
- [Features](docs/features.md) - Feature list and capabilities
- [Flows](docs/flows.md) - Process flow documentation

## Related Services

- **jira-api**: Provides actual Jira API operations (port 3002)
- **agent-engine**: Connects to this MCP server via SSE
