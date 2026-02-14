# Jira MCP Development Guide

## Overview

This is a thin MCP (Model Context Protocol) wrapper around the Jira API service. It exposes Jira operations as tools for Claude Code CLI and other MCP clients.

## Key Principles

1. **Thin Wrapper** - No business logic, just protocol translation
2. **Passthrough Design** - All parameters passed directly to backend
3. **Formatted Output** - Results formatted for LLM consumption

## Structure

```
jira-mcp/
├── main.py         # FastMCP server entry point
├── jira_mcp.py     # MCP tool definitions
├── config.py       # Settings
└── requirements.txt # Dependencies
```

## Adding a New Tool

1. Add tool function in `jira_mcp.py`:
   ```python
   @mcp.tool()
   async def new_operation(
       issue_key: str,
       param: str,
   ) -> str:
       """Docstring becomes tool description."""
       async with httpx.AsyncClient() as client:
           response = await client.post(
               f"{settings.jira_api_url}/new-endpoint",
               json={"issue_key": issue_key, "param": param},
           )
           response.raise_for_status()
           return response.json().get("formatted_output", "No results")
   ```

2. Ensure corresponding endpoint exists in Jira API service

## Important Notes

- Tool docstrings define how Claude understands the tool
- Keep output markdown-formatted for readability
- Never store credentials - delegate to jira-api service
- Handle empty results gracefully with descriptive messages

## Testing Locally

```bash
# Start Jira API service first
docker-compose --profile api up jira-api

# Then start MCP server
python main.py

# Test with curl
curl http://localhost:9002/sse
```

## File Size

This server should remain small. Complex logic belongs in Jira API service.

## Development

- Port: 9002
- Language: Python
- Framework: FastMCP
- Max 300 lines per file, no comments, strict types, async/await for I/O
