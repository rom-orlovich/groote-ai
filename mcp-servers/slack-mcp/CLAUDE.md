# Slack MCP Development Guide

## Overview

This is a thin MCP (Model Context Protocol) wrapper around the Slack API service. It exposes Slack operations as tools for Claude Code CLI and other MCP clients.

## Key Principles

1. **Thin Wrapper** - No business logic, just protocol translation
2. **Passthrough Design** - All parameters passed directly to backend
3. **Formatted Output** - Results formatted for LLM consumption

## Structure

```
slack-mcp/
├── main.py         # FastMCP server entry point
├── slack_mcp.py    # MCP tool definitions
├── config.py       # Settings
└── requirements.txt # Dependencies
```

## Adding a New Tool

1. Add tool function in `slack_mcp.py`:
   ```python
   @mcp.tool()
   async def new_operation(
       channel: str,
       param: str,
   ) -> str:
       """Docstring becomes tool description."""
       async with httpx.AsyncClient() as client:
           response = await client.post(
               f"{settings.slack_api_url}/new-endpoint",
               json={"channel": channel, "param": param},
           )
           response.raise_for_status()
           return response.json().get("formatted_output", "No results")
   ```

2. Ensure corresponding endpoint exists in Slack API service

## Important Notes

- Tool docstrings define how Claude understands the tool
- Keep output markdown-formatted for readability
- Never store credentials - delegate to slack-api service
- Handle thread context properly (use `thread_ts` for replies)
- Handle empty results gracefully with descriptive messages

## Testing Locally

```bash
# Start Slack API service first
docker-compose --profile api up slack-api

# Then start MCP server
python main.py

# Test with curl
curl http://localhost:9003/sse
```

## File Size

This server should remain small. Complex logic belongs in Slack API service.

## Development

- Port: 9003
- Language: Python
- Framework: FastMCP
- Max 300 lines per file, no comments, strict types, async/await for I/O
