# Service Specialist - Agent Memory

## FastMCP Testing Patterns

- **FunctionTool objects**: `@mcp.tool()` wraps functions into `FunctionTool` objects. To call the underlying function in tests, use `.fn()` (e.g., `await add_issue_comment.fn("owner", "repo", 42, "Hello")`)
- **httpx compact JSON**: httpx serializes JSON without spaces. Don't assert against byte strings with spaces. Use `json.loads(route.calls[0].request.content)` for comparison.
- **respx mocking with base_url**: Use `respx.mock(base_url="http://service:port")` to mock HTTP calls. Routes match relative paths.
- **GitHubAPI test fixture**: Use `__new__` to bypass `__init__` and set `_base_url`, `_timeout`, `_client` directly for unit testing without config.

## MCP Server Structure (jira-mcp pattern)

```
mcp-servers/{name}-mcp/
  config.py          - Settings (BaseSettings with lru_cache)
  {name}_mcp.py      - HTTP client class wrapping api-service
  main.py            - FastMCP server with tool definitions
  requirements.txt   - Runtime deps
  requirements-dev.txt - Test deps
  Dockerfile         - Python 3.11-slim + uv
  tests/
    __init__.py
    conftest.py      - sys.path setup + fixtures
    test_{name}_mcp.py - respx-based behavior tests
```

## Test Command Pattern

```bash
PYTHONPATH=mcp-servers/{name}-mcp:$PYTHONPATH uv run --with pytest --with pytest-asyncio --with respx --with httpx --with fastmcp --with pydantic-settings pytest mcp-servers/{name}-mcp/tests/ -v
```
