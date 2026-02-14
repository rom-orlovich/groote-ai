# MCP Servers - Features

## Overview

Six FastMCP-based servers exposing 55 tools total for AI agents to interact with external services and internal knowledge stores via the Model Context Protocol.

## Feature Summary by Server

### GitHub MCP (15 tools)

| Category | Tools | Description |
|----------|-------|-------------|
| Repository | `get_repository`, `list_repos` | Read repo metadata |
| Issues | `get_issue`, `create_issue`, `add_issue_comment`, `add_reaction` | Full issue lifecycle |
| Pull Requests | `get_pull_request`, `create_pull_request`, `create_pr_review_comment` | PR management + reviews |
| Branches | `list_branches`, `get_branch_sha`, `create_branch` | Branch operations |
| Files | `get_file_contents`, `search_code`, `create_or_update_file` | Code access + writes |

### Jira MCP (10 tools)

| Category | Tools | Description |
|----------|-------|-------------|
| Issues | `get_jira_issue`, `create_jira_issue`, `update_jira_issue`, `add_jira_comment` | Issue CRUD |
| Search | `search_jira_issues` | JQL search with pagination |
| Workflow | `get_jira_transitions`, `transition_jira_issue` | Status transitions |
| Projects | `create_jira_project` | Project creation |
| Boards | `get_jira_boards`, `create_jira_board` | Board management |

### Slack MCP (8 tools)

| Category | Tools | Description |
|----------|-------|-------------|
| Messaging | `send_slack_message`, `update_slack_message` | Send and edit messages |
| History | `get_slack_channel_history`, `get_slack_thread` | Read messages |
| Reactions | `add_slack_reaction` | Emoji reactions |
| Channels | `get_slack_channel_info`, `list_slack_channels` | Channel metadata |
| Users | `get_slack_user_info` | User lookup |

### Knowledge Graph MCP (12 tools)

| Category | Tools | Description |
|----------|-------|-------------|
| Code Search | `search_codebase`, `find_symbol_references`, `get_code_structure` | Find code entities |
| Dependencies | `find_dependencies`, `find_code_path`, `get_code_neighbors` | Navigate relationships |
| Statistics | `get_graph_stats` | Graph metrics |
| Vector Store | `knowledge_store`, `knowledge_query` | Document storage + search |
| Collections | `knowledge_collections`, `knowledge_update`, `knowledge_delete` | Document lifecycle |

### LlamaIndex MCP (5 tools)

| Category | Tools | Description |
|----------|-------|-------------|
| Hybrid Search | `knowledge_query` | Multi-source search |
| Code | `code_search`, `find_related_code` | Code search + graph |
| Tickets | `search_jira_tickets` | Semantic Jira search |
| Docs | `search_confluence` | Confluence search |

### GKG MCP (5 tools)

| Category | Tools | Description |
|----------|-------|-------------|
| Dependencies | `analyze_dependencies` | File dependency trees |
| Symbols | `find_usages` | Symbol usage tracking |
| Call Graph | `get_call_graph` | Function call relationships |
| Inheritance | `get_class_hierarchy` | Class hierarchy |
| Relationships | `get_related_entities` | General entity relationships |

## Cross-Cutting Features

### Credential Isolation

All 6 servers follow the same security model: no API keys stored in MCP servers. Credentials are managed by backend API services.

### SSE Transport

All servers expose an `/sse` endpoint for MCP protocol communication and a `/health` endpoint for health checks.

### Structured Logging

Knowledge servers (LlamaIndex MCP, GKG MCP) use `structlog` with JSON output for structured logging. External service wrappers rely on FastMCP's built-in logging.

### Event Publishing

LlamaIndex MCP publishes query and result events to Redis streams (`task_events`) for observability. Other servers do not publish events.
