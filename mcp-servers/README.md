# MCP Servers

> Model Context Protocol (MCP) servers that provide standardized interfaces to external services.

## Purpose

MCP Servers implement the Model Context Protocol to provide standardized interfaces for agent-engine to interact with external services. They translate MCP protocol calls into HTTP requests to API services, keeping credentials isolated.

## Architecture

```
Agent Engine (via mcp.json)
         |
         | SSE Connection
         v
+-------------------------------------+
|      MCP Server                     |
|                                     |
|  1. Receive MCP tool call          |
|  2. Translate to HTTP request       |
|  3. Call API service (no creds)    |
|  4. Return standardized response    |
+-------------------------------------+
         |
         | HTTP (no credentials)
         v
+-------------------------------------+
|      API Service                    |
|  (Has credentials, makes API call)  |
+-------------------------------------+
```

## Folder Structure

```
mcp-servers/
├── README.md
├── CLAUDE.md
├── SETUP.md
├── docker-compose.mcp.yml
├── github-mcp/              # GitHub operations (15 tools)
│   ├── main.py
│   ├── github_mcp.py
│   └── config.py
├── jira-mcp/                # Jira operations (10 tools)
│   ├── main.py
│   ├── jira_mcp.py
│   └── config.py
├── slack-mcp/               # Slack messaging (8 tools)
│   ├── main.py
│   ├── slack_mcp.py
│   └── config.py
├── knowledge-graph-mcp/     # Code search + vector store (12 tools)
│   ├── main.py
│   ├── kg_client.py
│   ├── chroma_client.py
│   └── config.py
├── llamaindex-mcp/          # Hybrid RAG search (5 tools)
│   ├── llamaindex_mcp.py
│   ├── main.py
│   ├── event_publisher.py
│   └── config.py
└── gkg-mcp/                 # Code graph analysis (5 tools)
    ├── gkg_mcp.py
    ├── main.py
    └── config.py
```

## MCP Servers

| Service | Port | Backend | Framework | Tools |
|---------|------|---------|-----------|-------|
| GitHub MCP | 9001 | github-api:3001 | FastMCP (Python) | 15 |
| Jira MCP | 9002 | jira-api:3002 | FastMCP (Python) | 10 |
| Slack MCP | 9003 | slack-api:3003 | FastMCP (Python) | 8 |
| Knowledge Graph MCP | 9005 | knowledge-graph:4000 + ChromaDB | FastMCP (Python) | 12 |
| LlamaIndex MCP | 9006 | llamaindex-service:8002 | FastMCP (Python) | 5 |
| GKG MCP | 9007 | gkg-service:8003 | FastMCP (Python) | 5 |

## Security Model

**Key Principle**: MCP servers NEVER store API keys.

- MCP servers call API services via HTTP
- API services have credentials and make actual API calls
- Complete credential isolation

## GitHub MCP

**Purpose**: GitHub operations via github-api service.

**Tools (15):**
- `get_repository` - Get repository details
- `get_issue` / `create_issue` - Issue management
- `add_issue_comment` / `add_reaction` - Comments and reactions
- `get_pull_request` / `create_pull_request` - PR management
- `create_pr_review_comment` - Inline PR review comments
- `get_file_contents` / `search_code` - Code access
- `list_branches` / `get_branch_sha` / `create_branch` - Branch operations
- `list_repos` - List installation repositories
- `create_or_update_file` - File creation/updates via Contents API

## Jira MCP

**Purpose**: Jira operations via jira-api service.

**Tools (10):**
- `get_jira_issue` / `create_jira_issue` / `update_jira_issue` - Issue CRUD
- `add_jira_comment` - Add comments
- `search_jira_issues` - JQL search with pagination
- `get_jira_transitions` / `transition_jira_issue` - Workflow transitions
- `create_jira_project` - Project creation
- `get_jira_boards` / `create_jira_board` - Board management

## Slack MCP

**Purpose**: Slack messaging via slack-api service.

**Tools (8):**
- `send_slack_message` - Send messages to channels/threads
- `get_slack_channel_history` - Channel message history
- `get_slack_thread` - Thread replies
- `add_slack_reaction` - Emoji reactions
- `get_slack_channel_info` / `list_slack_channels` - Channel info
- `get_slack_user_info` - User details
- `update_slack_message` - Update existing messages

## Knowledge Graph MCP

**Purpose**: Code search (Knowledge Graph) + vector storage (ChromaDB).

**Graph Tools (7):**
- `search_codebase` - Search code entities
- `find_symbol_references` - Find symbol usages
- `get_code_structure` - Repository file structure
- `find_dependencies` - Code dependencies (incoming/outgoing)
- `find_code_path` - Path between entities
- `get_code_neighbors` - Neighboring entities
- `get_graph_stats` - Graph statistics

**Vector Tools (5):**
- `knowledge_store` / `knowledge_query` - Store and search documents
- `knowledge_collections` - Manage collections (list/create/delete)
- `knowledge_update` / `knowledge_delete` - Document lifecycle

## LlamaIndex MCP

**Purpose**: Hybrid RAG search across code, Jira, and Confluence.

**Tools (5):**
- `knowledge_query` - Hybrid search across all sources
- `code_search` - Code-specific search with repo/language filters
- `find_related_code` - Graph-based code relationships
- `search_jira_tickets` - Semantic Jira ticket search
- `search_confluence` - Confluence documentation search

## GKG MCP

**Purpose**: Code graph analysis via GKG service.

**Tools (5):**
- `analyze_dependencies` - File dependency analysis
- `find_usages` - Symbol usage search
- `get_call_graph` - Function call relationships
- `get_class_hierarchy` - Class inheritance
- `get_related_entities` - General relationship queries

## Environment Variables

```bash
GITHUB_API_URL=http://github-api:3001
JIRA_API_URL=http://jira-api:3002
SLACK_API_URL=http://slack-api:3003
KG_KNOWLEDGE_GRAPH_URL=http://knowledge-graph:4000
LLAMAINDEX_URL=http://llamaindex-service:8002
GKG_URL=http://gkg-service:8003
CHROMA_HOST=chromadb
CHROMA_PORT=8000
REDIS_URL=redis://redis:6379/0
```

## SSE Endpoint

MCP clients connect via Server-Sent Events:

```
GET /sse HTTP/1.1
Host: {service}-mcp:{port}
Accept: text/event-stream
```

## Health Checks

```bash
curl http://localhost:9001/health  # GitHub
curl http://localhost:9002/health  # Jira
curl http://localhost:9003/health  # Slack
curl http://localhost:9005/health  # Knowledge Graph
curl http://localhost:9006/health  # LlamaIndex
curl http://localhost:9007/health  # GKG
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md) - Component diagrams and data flows
- [Features](docs/features.md) - Feature list and capabilities
- [Flows](docs/flows.md) - Process flow documentation
- [Setup Guide](SETUP.md) - Installation and configuration

## Related Services

- **agent-engine**: Connects to MCP servers via SSE
- **api-services**: MCP servers call API services for actual operations
- **knowledge-graph**: Knowledge Graph MCP wraps knowledge-graph service
- **llamaindex-service**: LlamaIndex MCP wraps LlamaIndex RAG service
- **gkg-service**: GKG MCP wraps GKG graph analysis service
