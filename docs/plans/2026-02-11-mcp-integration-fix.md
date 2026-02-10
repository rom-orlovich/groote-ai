# Fix MCP Integration: Agent Uses MCP to Talk to Platforms

## Context

The agent-engine's Claude CLI should use MCP tools to interact with Jira/GitHub/Slack.
Chain: `Claude CLI → MCP Server (SSE) → API Service → OAuth Service → Platform`.

Currently MCP tools are NOT loading because:
1. `--mcp-config` flag not passed to CLI command
2. SSE format uses `"transport": "sse"` instead of `"type": "sse"` in mcp.json
3. Dead entries (sentry, llamaindex, gkg) in mcp.json
4. No GitHub MCP server exists (only the official Docker image which requires stdio)

**Decision**: Create a custom `github-mcp` SSE server (like jira-mcp/slack-mcp). This is simpler, consistent, and uses the existing `github-api:3001` service with OAuth tokens.

**Tool naming**: GitHub MCP tools match official GitHub MCP server names (no prefix) so existing skills/agents work without changes.

---

## Phase 1: TDD — Write Tests First for GitHub MCP

### 1a. Test file: `mcp-servers/github-mcp/tests/test_github_mcp.py`

Tests use `pytest` + `pytest-asyncio` + `respx` (HTTP mocking). Run with `uv`.

**Behavior tests for `GitHubAPI` client (`github_mcp.py`):**

```python
import pytest
import respx
from httpx import Response

@pytest.fixture
def github_api():
    from github_mcp import GitHubAPI
    api = GitHubAPI.__new__(GitHubAPI)
    api._base_url = "http://github-api:3001"
    api._timeout = 30
    api._client = None
    return api
```

| Test | Behavior | Assertion |
|------|----------|-----------|
| `test_get_issue_returns_issue_data` | GET `/api/v1/repos/owner/repo/issues/1` | Response has `number`, `title`, `state` |
| `test_add_issue_comment_sends_body` | POST `/api/v1/repos/owner/repo/issues/1/comments` | Request body has `body`; returns comment |
| `test_get_file_contents_with_ref` | GET `.../contents/README.md?ref=main` | Query param `ref=main` included |
| `test_get_file_contents_without_ref` | GET `.../contents/README.md` (no ref) | No `ref` query param |
| `test_search_code_passes_query_params` | GET `/api/v1/search/code?q=test&per_page=30` | Query params correct |
| `test_get_pull_request_returns_pr_data` | GET `/api/v1/repos/owner/repo/pulls/1` | Response has `number`, `title` |
| `test_get_repository_returns_data` | GET `/api/v1/repos/owner/repo` | Response has `full_name` |
| `test_create_issue_sends_payload` | POST `/api/v1/repos/owner/repo/issues` | Request has `title`, `body` |
| `test_list_branches_returns_list` | GET `/api/v1/repos/owner/repo/branches` | Returns list |
| `test_http_404_propagates` | API returns 404 | `httpx.HTTPStatusError` raised |
| `test_add_reaction_sends_content` | POST `.../issues/comments/1/reactions` | Request body has `content` |

**Business logic tests for MCP tool layer:**

| Test | Behavior | Assertion |
|------|----------|-----------|
| `test_add_issue_comment_calls_client` | MCP tool delegates to `GitHubAPI.add_issue_comment` | Correct args passed |
| `test_create_issue_with_labels` | MCP tool passes optional labels | Labels forwarded |
| `test_create_issue_without_labels` | MCP tool with no labels | `None` passed |
| `test_search_code_default_per_page` | MCP tool uses default per_page=30 | Default preserved |

### 1b. Test file: `mcp-servers/github-mcp/tests/conftest.py`

Shared fixtures: `sys.path` setup, settings override.

### 1c. Test requirements: `mcp-servers/github-mcp/requirements-dev.txt`

```
pytest>=8.0.0
pytest-asyncio>=0.23.0
respx>=0.21.0
```

### 1d. Test command

```bash
PYTHONPATH=mcp-servers/github-mcp:$PYTHONPATH uv run pytest mcp-servers/github-mcp/tests/ -v
```

---

## Phase 2: Implement GitHub MCP Server

### 2a. `mcp-servers/github-mcp/config.py`

Same pattern as `mcp-servers/jira-mcp/config.py`:

```python
from functools import lru_cache
from pydantic import ConfigDict
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    model_config = ConfigDict(strict=True, env_file=".env", extra="ignore")
    port: int = 9001
    github_api_url: str = "http://github-api:3001"
    request_timeout: int = 30

@lru_cache
def get_settings() -> Settings:
    return Settings()
```

### 2b. `mcp-servers/github-mcp/github_mcp.py`

HTTP client wrapping `github-api:3001`. Same pattern as `mcp-servers/jira-mcp/jira_mcp.py`.

**Methods** (matching `api-services/github-api/api/routes.py`):

| Method | HTTP | Endpoint |
|--------|------|----------|
| `get_repository(owner, repo)` | GET | `/api/v1/repos/{owner}/{repo}` |
| `get_issue(owner, repo, number)` | GET | `/api/v1/repos/{owner}/{repo}/issues/{number}` |
| `create_issue(owner, repo, title, body, labels)` | POST | `/api/v1/repos/{owner}/{repo}/issues` |
| `add_issue_comment(owner, repo, number, body)` | POST | `/api/v1/repos/{owner}/{repo}/issues/{number}/comments` |
| `add_reaction(owner, repo, comment_id, content)` | POST | `/api/v1/repos/{owner}/{repo}/issues/comments/{id}/reactions` |
| `get_pull_request(owner, repo, pr_number)` | GET | `/api/v1/repos/{owner}/{repo}/pulls/{pr_number}` |
| `create_pr_review_comment(owner, repo, pr_number, body, commit_id, path, line)` | POST | `/api/v1/repos/{owner}/{repo}/pulls/{pr_number}/comments` |
| `get_file_contents(owner, repo, path, ref)` | GET | `/api/v1/repos/{owner}/{repo}/contents/{path}` |
| `search_code(query, per_page, page)` | GET | `/api/v1/search/code` |
| `list_branches(owner, repo, per_page, page)` | GET | `/api/v1/repos/{owner}/{repo}/branches` |
| `list_repos(per_page, page)` | GET | `/api/v1/installation/repos` |

### 2c. `mcp-servers/github-mcp/main.py`

FastMCP server. **Tool names match official GitHub MCP server** so existing skills/agents work:

| Tool Name | Parameters | Maps To |
|-----------|-----------|---------|
| `get_repository` | owner, repo | `github_api.get_repository` |
| `get_issue` | owner, repo, issue_number | `github_api.get_issue` |
| `create_issue` | owner, repo, title, body?, labels? | `github_api.create_issue` |
| `add_issue_comment` | owner, repo, issue_number, body | `github_api.add_issue_comment` |
| `add_reaction` | owner, repo, comment_id, content | `github_api.add_reaction` |
| `get_pull_request` | owner, repo, pr_number | `github_api.get_pull_request` |
| `create_pr_review_comment` | owner, repo, pr_number, body, commit_id, path, line | `github_api.create_pr_review_comment` |
| `get_file_contents` | owner, repo, path, ref? | `github_api.get_file_contents` |
| `search_code` | query, per_page?, page? | `github_api.search_code` |
| `list_branches` | owner, repo, per_page?, page? | `github_api.list_branches` |
| `list_repos` | per_page?, page? | `github_api.list_repos` |

### 2d. `mcp-servers/github-mcp/requirements.txt`

```
fastmcp>=0.4.0
httpx>=0.26.0
pydantic>=2.5.0
pydantic-settings>=2.1.0
uvicorn>=0.27.0
```

### 2e. `mcp-servers/github-mcp/Dockerfile`

```dockerfile
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
RUN pip install uv
COPY requirements.txt .
RUN uv pip install --no-cache-dir --system -r requirements.txt
COPY . .
ENV PORT=9001
ENV GITHUB_API_URL=http://github-api:3001
EXPOSE 9001
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import socket; s = socket.create_connection(('localhost', 9001), timeout=5); s.close()"
CMD ["python", "main.py"]
```

---

## Phase 3: Update docker-compose.yml

Replace the official `github-mcp` service (lines 81-91 with `stdin_open/tty`) with custom build:

```yaml
github-mcp:
  build: ./mcp-servers/github-mcp
  ports:
    - "9001:9001"
  environment:
    - PORT=9001
    - GITHUB_API_URL=http://github-api:3001
  networks:
    - agent-network
  restart: unless-stopped
```

---

## Phase 4: Fix MCP Config (`agent-engine/.claude/mcp.json`)

```json
{
  "mcpServers": {
    "github": {
      "type": "sse",
      "url": "http://github-mcp:9001/sse"
    },
    "jira": {
      "type": "sse",
      "url": "http://jira-mcp:9002/sse"
    },
    "slack": {
      "type": "sse",
      "url": "http://slack-mcp:9003/sse"
    },
    "knowledge-graph": {
      "type": "sse",
      "url": "http://knowledge-graph-mcp:9005/sse"
    }
  }
}
```

Changes: `"type": "sse"` (was `"transport": "sse"`), removed dead entries.

---

## Phase 5: Pass `--mcp-config` to CLI

**File**: `agent-engine/cli/providers/claude.py` line 206

Add before `cmd.extend(["--", prompt])`:

```python
mcp_config = Path("/app/.claude/mcp.json")
if mcp_config.exists():
    cmd.extend(["--mcp-config", str(mcp_config)])
```

---

## Phase 6: Update Skills & Agents for Correct Tool Names

### 6a. Skill/Agent Tool Name Alignment

**GitHub tools** — Our custom server uses official names. No changes needed for:
- `github:add_issue_comment` → matches our `add_issue_comment` tool
- `github:get_file_content` → close to `get_file_contents` (model handles)
- `github:search_code` → matches our `search_code` tool
- `github:get_pull_request` → matches our `get_pull_request` tool

**Fix** `github:get_file_content` → `github:get_file_contents` (add trailing 's') in:
- `agent-engine/.claude/skills/github-operations/SKILL.md`
- `agent-engine/.claude/skills/github-operations/flow.md`
- `agent-engine/.claude/agents/github-issue-handler.md`
- `agent-engine/.claude/agents/github-pr-review.md`
- `agent-engine/.claude/agents/jira-code-plan.md`
- `agent-engine/.claude/agents/slack-inquiry.md`

**Slack tools** — Fix `slack:post_message` → `slack:send_slack_message` in:
- `agent-engine/.claude/skills/slack-operations/SKILL.md` (line 14)
- `agent-engine/.claude/skills/slack-operations/flow.md` (all `slack:post_message` refs)
- `agent-engine/.claude/skills/slack-operations/templates.md` (if applicable)

**Jira tools** — Already aligned. No changes needed.

### 6b. Note missing tools in skills

Add note to `github-operations/SKILL.md` that `create_pull_request` and `create_or_update_file` are not yet available. Agents should use `git push` + local commands for PR creation.

---

## Phase 7: Restore MCP Tool Instructions in Prompts

**File**: `agent-engine/services/task_routing.py` — `_build_platform_instructions()`

Update to instruct agent to use MCP tools:

```python
def _build_platform_instructions(source: str) -> str:
    if source == "jira":
        return """
## Response Instructions

Use the `jira:add_jira_comment` MCP tool to post your analysis as a comment on the Jira ticket.
You have access to MCP tools: jira:get_jira_issue, jira:add_jira_comment, jira:search_jira_issues, jira:transition_jira_issue.
"""
    if source == "github":
        return """
## Response Instructions

Use the `github:add_issue_comment` MCP tool to post your analysis as a comment.
You have access to MCP tools: github:get_issue, github:add_issue_comment, github:get_pull_request, github:get_file_contents, github:search_code.
"""
    if source == "slack":
        return """
## Response Instructions

Use the `slack:send_slack_message` MCP tool to reply in the Slack thread.
You have access to MCP tools: slack:send_slack_message, slack:add_slack_reaction, slack:get_slack_thread.
"""
    return ""
```

---

## Phase 8: Add Fallback Detection + Dashboard Notification

**File**: `agent-engine/main.py` — `_process_task()` around line 158

Check if CLI already posted via MCP. If not, use fallback AND notify the dashboard conversation:

```python
output = result.get("output", "")
mcp_posted = any(
    marker in (output or "")
    for marker in ("add_jira_comment", "add_issue_comment", "send_slack_message")
)

if source in ("github", "jira", "slack"):
    if mcp_posted:
        logger.info("mcp_response_posted", task_id=task_id, source=source)
    else:
        from services.response_poster import post_response_to_platform

        posted = await post_response_to_platform(task, result)
        logger.info("fallback_response_posted", task_id=task_id, source=source, posted=posted)

        if webhook_conversation_id:
            await conversation_bridge.post_fallback_notice(
                dashboard_url, webhook_conversation_id, source, posted
            )
```

**File**: `agent-engine/services/conversation_bridge.py` — Add `post_fallback_notice`:

```python
async def post_fallback_notice(
    dashboard_url: str, conversation_id: str, source: str, posted: bool
) -> None:
    if posted:
        content = (
            f"⚠️ **MCP tools unavailable** — Response was posted to {source} "
            f"via fallback (direct API). Check the platform for the response."
        )
    else:
        content = (
            f"❌ **Response delivery failed** — MCP tools unavailable and "
            f"fallback to {source} also failed. Manual intervention needed."
        )

    async with httpx.AsyncClient(timeout=10.0) as client:
        await client.post(
            f"{dashboard_url}/api/conversations/{conversation_id}/messages",
            json={"role": "system", "content": content},
        )
```

---

## Phase 9: End-to-End Platform Verification

### 9a. Jira Full Flow

```
Webhook trigger (toggle AI-Fix on KAN-6)
  → api-gateway/webhooks/jira (validates, deduplicates, queues to Redis)
  → agent-engine picks up from Redis queue
  → conversation_bridge creates/gets dashboard conversation (flow_id: jira:KAN-6)
  → task_routing.build_enriched_prompt() adds Jira context + MCP instructions
  → CLI runs with --mcp-config → Claude loads jira MCP server
  → Brain agent routes to jira-code-plan agent (via agents/jira-code-plan.md)
  → jira-code-plan uses jira-operations skill
  → Agent calls jira:get_jira_issue MCP tool → jira-mcp → jira-api → Jira API
  → Agent calls jira:add_jira_comment MCP tool → jira-mcp → jira-api → Jira API
  → Response appears on KAN-6 as a comment
  → Dashboard conversation shows the interaction
```

### 9b. GitHub Full Flow

```
Webhook trigger (create issue or comment on issue)
  → api-gateway/webhooks/github (validates signature, queues)
  → agent-engine picks up task
  → conversation_bridge creates conversation (flow_id: github:owner/repo#N)
  → CLI runs with --mcp-config → Claude loads github MCP server
  → Brain routes to github-issue-handler agent
  → github-issue-handler uses github-operations skill
  → Agent calls github:get_issue → github-mcp → github-api → GitHub API
  → Agent calls github:add_issue_comment → github-mcp → github-api → GitHub API
  → Response appears as comment on the GitHub issue
```

### 9c. Slack Full Flow

```
Webhook trigger (@agent mention or DM)
  → api-gateway/webhooks/slack (validates signing secret, queues)
  → agent-engine picks up task
  → conversation_bridge creates conversation (flow_id: slack:channel:thread_ts)
  → CLI runs with --mcp-config → Claude loads slack MCP server
  → Brain routes to slack-inquiry agent
  → slack-inquiry uses slack-operations skill
  → Agent calls slack:add_slack_reaction (eyes emoji for acknowledgment)
  → Agent calls slack:send_slack_message (reply in thread)
  → slack-mcp → slack-api → Slack API
  → Response appears in Slack thread
```

### 9d. Fallback Verification

1. Temporarily break MCP config (wrong URL)
2. Trigger a Jira webhook
3. Verify `response_poster.py` posts the response via direct API
4. Verify dashboard conversation shows "⚠️ MCP tools unavailable" system message
5. Restore MCP config

---

## Files Summary

| File | Status | Change |
|------|--------|--------|
| **GitHub MCP Server** | | |
| `mcp-servers/github-mcp/config.py` | NEW | Settings (port, github_api_url) |
| `mcp-servers/github-mcp/github_mcp.py` | NEW | HTTP client wrapping github-api:3001 |
| `mcp-servers/github-mcp/main.py` | NEW | FastMCP server with 11 tools |
| `mcp-servers/github-mcp/Dockerfile` | NEW | Python 3.11-slim + uv |
| `mcp-servers/github-mcp/requirements.txt` | NEW | fastmcp, httpx, pydantic-settings |
| `mcp-servers/github-mcp/requirements-dev.txt` | NEW | pytest, pytest-asyncio, respx |
| `mcp-servers/github-mcp/tests/__init__.py` | NEW | Package init |
| `mcp-servers/github-mcp/tests/conftest.py` | NEW | Shared fixtures |
| `mcp-servers/github-mcp/tests/test_github_mcp.py` | NEW | 15 behavior tests |
| **Infrastructure** | | |
| `agent-engine/.claude/mcp.json` | EDIT | Fix format, add github SSE, remove dead entries |
| `docker-compose.yml` | EDIT | Replace official github-mcp with custom build |
| `agent-engine/cli/providers/claude.py` | EDIT | Add `--mcp-config` flag |
| **Agent Engine** | | |
| `agent-engine/services/task_routing.py` | EDIT | Restore MCP tool names in prompts |
| `agent-engine/services/conversation_bridge.py` | EDIT | Add `post_fallback_notice()` function |
| `agent-engine/main.py` | EDIT | Add fallback detection + dashboard notification |
| **Skills & Agents (tool name fixes)** | | |
| `agent-engine/.claude/skills/github-operations/SKILL.md` | EDIT | `get_file_content` → `get_file_contents`, note missing tools |
| `agent-engine/.claude/skills/github-operations/flow.md` | EDIT | `get_file_content` → `get_file_contents` |
| `agent-engine/.claude/skills/slack-operations/SKILL.md` | EDIT | `post_message` → `send_slack_message` |
| `agent-engine/.claude/skills/slack-operations/flow.md` | EDIT | `post_message` → `send_slack_message` |
| `agent-engine/.claude/agents/github-issue-handler.md` | EDIT | `get_file_content` → `get_file_contents` |
| `agent-engine/.claude/agents/github-pr-review.md` | EDIT | `get_file_content` → `get_file_contents` |
| `agent-engine/.claude/agents/jira-code-plan.md` | EDIT | `get_file_content` → `get_file_contents` |
| `agent-engine/.claude/agents/slack-inquiry.md` | EDIT | `get_file_content` → `get_file_contents` |

## Test Commands

```bash
# GitHub MCP unit tests (TDD - run BEFORE implementation)
PYTHONPATH=mcp-servers/github-mcp:$PYTHONPATH uv run pytest mcp-servers/github-mcp/tests/ -v

# Agent engine tests (must still pass)
PYTHONPATH=agent-engine:$PYTHONPATH uv run pytest agent-engine/tests/ -v
```

## Verification (End-to-End)

1. Run GitHub MCP tests: `PYTHONPATH=mcp-servers/github-mcp uv run pytest mcp-servers/github-mcp/tests/ -v`
2. Build: `docker compose build github-mcp cli`
3. Start: `docker compose up -d github-mcp jira-mcp slack-mcp cli`
4. Health check: `curl http://localhost:9001/health`
5. MCP list: `docker compose exec cli claude mcp list` → should show github, jira, slack, knowledge-graph
6. Trigger Jira webhook on KAN-6 (toggle AI-Fix label)
7. Watch logs: `docker compose logs cli --follow`
8. Confirm agent uses MCP tool (look for `add_jira_comment` in output)
9. Check KAN-6 comments for agent response posted via MCP
10. If MCP post fails, verify fallback `response_poster` kicks in
