# MCP Servers

MCP servers connect to agent engine via SSE. They call API services for actual API operations.

## Services

| Server | Port | Backend | Framework | Tools |
|--------|------|---------|-----------|-------|
| GitHub MCP | 9001 | github-api:3001 | FastMCP (Python) | 15 |
| Jira MCP | 9002 | jira-api:3002 | FastMCP (Python) | 10 |
| Slack MCP | 9003 | slack-api:3003 | FastMCP (Python) | 8 |
| Knowledge Graph MCP | 9005 | knowledge-graph:4000 + ChromaDB | FastMCP (Python) | 12 |
| LlamaIndex MCP | 9006 | llamaindex-service:8002 | FastMCP (Python) | 5 |
| GKG MCP | 9007 | gkg-service:8003 | FastMCP (Python) | 5 |

## Environment Variables

Each MCP server needs its backend URL:

```bash
GITHUB_API_URL=http://github-api:3001
JIRA_API_URL=http://jira-api:3002
SLACK_API_URL=http://slack-api:3003
KG_KNOWLEDGE_GRAPH_URL=http://knowledge-graph:4000
LLAMAINDEX_URL=http://llamaindex-service:8002
GKG_URL=http://gkg-service:8003
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

## Testing

```bash
PYTHONPATH=mcp-servers/{name}-mcp:$PYTHONPATH uv run --with pytest --with pytest-asyncio --with respx --with httpx --with fastmcp --with pydantic-settings pytest mcp-servers/{name}-mcp/tests/ -v
```

## Development Rules

- Maximum 300 lines per file
- NO `any` types - use strict Pydantic models
- NO comments - self-explanatory code only
- Tests must run fast (< 5 seconds), no real network calls
- Use async/await for all I/O operations
