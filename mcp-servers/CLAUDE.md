# MCP Servers

MCP servers connect to agent engine via SSE. They call API services for actual API operations.

## Services

- GitHub MCP (9001) - Official Node.js
- Jira MCP (9002) - Custom FastMCP (Python)
- Slack MCP (9003) - Custom FastMCP (Python)

## Environment Variables

Each MCP server needs: `{PROVIDER}_API_URL=http://{provider}-api:300{port}`

## Health Checks

```bash
curl http://localhost:9001/health  # GitHub
curl http://localhost:9002/health  # Jira
curl http://localhost:9003/health  # Slack
```
