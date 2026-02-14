# LlamaIndex MCP - Features

## Overview

FastMCP-based MCP server that exposes 5 hybrid search tools across code, Jira, and Confluence. Queries the LlamaIndex RAG service and publishes query events to Redis for observability.

## Core Features

### Hybrid Knowledge Search

Query across all indexed knowledge sources using natural language with combined vector and graph search.

**Capabilities:**
- Search across code, Jira, and Confluence simultaneously
- Filter by source types (comma-separated: "code,jira,confluence")
- Configurable result count (top_k)
- Results include relevance scores and content previews

### Code Search

Search specifically in indexed code repositories with repository and language filtering.

**Capabilities:**
- Natural language or code-pattern queries
- Repository glob pattern filtering (e.g., "backend-*")
- Programming language filter
- Results include file paths, line ranges, and syntax-highlighted snippets

### Graph-Based Code Relationships

Find code entities related through the knowledge graph (calls, imports, extends).

**Capabilities:**
- Find entities related to a function, class, module, or file
- Filter by relationship type (calls, imports, extends, all)
- Results grouped by relationship type with file locations

### Jira Ticket Search

Semantic search across indexed Jira tickets with project and status filtering.

**Capabilities:**
- Natural language search across ticket content
- Project key filtering
- Status filtering (Open, In Progress, Done)
- Results include key, summary, status, priority, and labels

### Confluence Search

Semantic search across indexed Confluence documentation.

**Capabilities:**
- Natural language search across documentation
- Space key filtering
- Results include page title, space, last modified date, and content preview

### Query Event Publishing

Publishes query telemetry to Redis streams for observability and debugging.

**Capabilities:**
- Query events with tool name, query text, org_id, and source types
- Result events with count, preview, query time, and cache status
- Configurable via `PUBLISH_KNOWLEDGE_EVENTS` setting
- Non-blocking: publish failures do not affect tool responses

## MCP Tools

| Tool | Description |
|------|-------------|
| `knowledge_query` | Hybrid search across code, Jira, Confluence |
| `code_search` | Code-specific search with repo/language filters |
| `find_related_code` | Graph-based code relationship queries |
| `search_jira_tickets` | Semantic Jira ticket search |
| `search_confluence` | Confluence documentation search |
