# Knowledge Graph MCP Development Guide

## Overview

This is a thin MCP (Model Context Protocol) wrapper around the Knowledge Graph service. It exposes semantic code search and dependency tracking capabilities as tools for Claude Code CLI.

## Key Principles

1. **Thin Wrapper** - No business logic, just protocol translation
2. **Passthrough Design** - All parameters passed directly to backend
3. **Formatted Output** - Results formatted for LLM consumption

## Structure

```
knowledge-graph-mcp/
├── main.py                 # FastMCP server entry point
├── kg_client.py            # Knowledge Graph client
├── config.py               # Configuration
└── requirements.txt        # Dependencies
```

## Adding a New Tool

1. Add tool function in `main.py`:
   ```python
   @mcp.tool()
   async def new_query(
       query: str,
       org_id: str,
   ) -> str:
       """Docstring becomes tool description."""
       async with httpx.AsyncClient() as client:
           response = await client.post(
               f"{settings.knowledge_graph_url}/new-endpoint",
               json={"query": query, "org_id": org_id},
           )
           response.raise_for_status()
           return response.json().get("formatted_output", "No results")
   ```

2. Ensure corresponding endpoint exists in Knowledge Graph service

## Important Notes

- Tool docstrings define how Claude understands the tool
- Keep output markdown-formatted for readability
- Handle empty results gracefully with descriptive messages
- Timeouts should match expected Knowledge Graph query times

## Testing Locally

```bash
# Start Knowledge Graph service first
docker-compose --profile knowledge up knowledge-graph

# Then start MCP server
python main.py

# Test with curl
curl http://localhost:9005/sse
```

## File Size

This server should remain small. Complex logic belongs in Knowledge Graph service.

## Development

- Port: 9005
- Language: Python
- Framework: FastMCP
- Max 300 lines per file, no comments, strict types, async/await for I/O
