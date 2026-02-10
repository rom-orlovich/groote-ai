# Webhook-to-Dashboard Integration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make webhook tasks (Jira, GitHub, Slack) visible in dashboard with real-time streaming, conversation context, and full CLI autonomy via MCP tools.

**Architecture:** Agent-engine fetches conversation context from dashboard before task execution, builds enriched prompts, streams output to TaskLogger via Redis events, and delegates all platform responses to CLI via MCP tools (GitHub, Jira, Slack). Dashboard-api provides task registration endpoint and falls back to task-logger for logs.

**Tech Stack:** FastAPI, Redis, PostgreSQL, httpx, structlog, pytest, Docker

---

## Critical Context

**Current state:** Webhook tasks execute but are invisible - no TaskDB records, no conversations, no streaming, output truncated at 5000 chars, CLI uses wrong .claude directory.

**Example project:** `/Users/romo/projects/agents-prod/claude-code-agent/` - working implementation with TaskLogger, streaming, duration tracking.

**Key files:**
- `agent-engine/main.py` - Task processing engine
- `agent-engine/.claude/mcp.json` - MCP server config (GitHub, Jira, Slack)
- `agent-engine/.claude/agents/*.md` - Built-in agents (brain, executor, etc)
- `dashboard-api/api/dashboard.py` - Backend API
- `docker-compose.yml` - Service configuration

---

## Task 1: Fix task:created Event in agent-engine

**Files:**
- Modify: `agent-engine/main.py:55-70`
- Test: Manual verification via Redis

**Step 1: Add task:created event before task:started**

In `agent-engine/main.py`, line ~59 (in `_process_task`, before `_publish_task_event("task:started")`):

```python
await self._publish_task_event(
    task_id,
    "task:created",
    {
        "task_id": task_id,
        "session_id": session_id,
        "input_message": task.get("prompt", ""),
        "source": task.get("source", "unknown"),
        "assigned_agent": task.get("assigned_agent", "brain"),
    },
)
```

**Step 2: Verify event structure**

Check that the event data matches task-logger expectations from `/Users/romo/projects/agents-prod/claude-code-agent/core/task_logger.py:91-106`.

**Step 3: Test locally**

Run: `docker compose logs -f task-logger | grep "task:created"`
Expected: See event with `input_message` field

**Step 4: Commit**

```bash
git add agent-engine/main.py
git commit -m "fix: add task:created event with input_message for task-logger"
```

---

## Task 2: Fix task:completed Event with Duration Tracking

**Files:**
- Modify: `agent-engine/main.py:60-95`

**Step 1: Add start_time tracking**

In `_process_task`, line ~64 (before `_execute_task` call):

```python
start_time = time.monotonic()
```

**Step 2: Calculate duration after execution**

Line ~75 (after `_execute_task` returns):

```python
duration = time.monotonic() - start_time
```

**Step 3: Add result and duration to task:completed event**

Lines 81-92 (in existing `_publish_task_event("task:completed")` call):

```python
await self._publish_task_event(
    task_id,
    "task:completed",
    {
        "task_id": task_id,
        "session_id": session_id,
        "status": "completed" if result.success else "failed",
        "result": result.get("output", ""),  # NO TRUNCATION
        "duration_seconds": round(duration, 2),
        "cost_usd": result.cost_usd,
        "input_tokens": result.input_tokens,
        "output_tokens": result.output_tokens,
    },
)
```

**Step 4: Add time import at top of file**

Line ~5:

```python
import time
```

**Step 5: Test locally**

Run: `docker compose logs -f task-logger | grep "task:completed"`
Expected: See event with `result` (not truncated) and `duration_seconds`

**Step 6: Commit**

```bash
git add agent-engine/main.py
git commit -m "fix: add duration tracking and full result to task:completed event"
```

---

## Task 3: Fix dashboard-api task:created Event

**Files:**
- Modify: `dashboard-api/api/dashboard.py:461`

**Step 1: Add input_message to existing task:created event**

In `dashboard.py`, line 461 (in `_publish_task_event` call):

```python
await self._publish_task_event(
    task_id,
    "task:created",
    {
        "task_id": task_id,
        "session_id": session_id,
        "input_message": full_input_message,  # ADD THIS LINE
        "source": source,
        "assigned_agent": assigned_agent,
    },
)
```

**Step 2: Test locally**

Run: `docker compose logs -f task-logger | grep "task:created"`
Expected: See event from dashboard-api with `input_message`

**Step 3: Commit**

```bash
git add dashboard-api/api/dashboard.py
git commit -m "fix: add input_message to task:created event in dashboard-api"
```

---

## Task 4: Change Docker Volume to Bind Mount

**Files:**
- Modify: `docker-compose.yml:278,477`

**Step 1: Update task-logger volumes**

Line 278 (in `task-logger` service):

```yaml
task-logger:
  volumes:
    - ./data/logs/tasks:/data/logs/tasks  # Changed from task_logs volume
```

**Step 2: Remove named volume definition**

Line 477 (remove from `volumes:` section):

```yaml
volumes:
  # Remove this line:
  # task_logs:
```

**Step 3: Create directory on host**

Run: `mkdir -p ./data/logs/tasks`
Expected: Directory created

**Step 4: Restart services**

Run: `docker compose down && docker compose up -d --build`
Expected: All services healthy

**Step 5: Verify bind mount**

Run: `docker compose exec task-logger ls -la /data/logs/tasks`
Expected: Directory exists and is writable

**Step 6: Commit**

```bash
git add docker-compose.yml
git commit -m "feat: change task-logger to use bind mount for host visibility"
```

---

## Task 5: Write Tests for Conversation Bridge (TDD)

**Files:**
- Create: `agent-engine/tests/test_conversation_bridge.py`

**Step 1: Write failing test for flow_id generation**

```python
import pytest
from agent_engine.services.conversation_bridge import build_flow_id


def test_build_flow_id_jira():
    task = {
        "source": "jira",
        "source_metadata": {"key": "KAN-6"}
    }
    assert build_flow_id(task) == "jira:KAN-6"


def test_build_flow_id_github_pr():
    task = {
        "source": "github",
        "source_metadata": {
            "repo": "owner/repo",
            "number": 42
        }
    }
    assert build_flow_id(task) == "github:owner/repo#42"


def test_build_flow_id_slack():
    task = {
        "source": "slack",
        "source_metadata": {
            "channel": "C12345",
            "thread_ts": "1234567890.123456"
        }
    }
    assert build_flow_id(task) == "slack:C12345:1234567890.123456"
```

**Step 2: Run test to verify it fails**

Run: `PYTHONPATH=agent-engine:$PYTHONPATH uv run pytest agent-engine/tests/test_conversation_bridge.py::test_build_flow_id_jira -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'agent_engine.services.conversation_bridge'"

**Step 3: Write more failing tests for conversation title**

```python
from agent_engine.services.conversation_bridge import build_conversation_title


def test_build_conversation_title_jira():
    task = {
        "source": "jira",
        "source_metadata": {
            "key": "KAN-6",
            "summary": "Fix login bug"
        }
    }
    title = build_conversation_title(task)
    assert "Jira: KAN-6" in title
    assert "Fix login bug" in title


def test_build_conversation_title_github_issue():
    task = {
        "source": "github",
        "source_metadata": {
            "repo": "owner/repo",
            "number": 42,
            "title": "Add feature"
        }
    }
    title = build_conversation_title(task)
    assert "GitHub: owner/repo#42" in title
    assert "Add feature" in title


def test_build_conversation_title_slack():
    task = {
        "source": "slack",
        "source_metadata": {
            "channel_name": "general",
            "text": "How do I configure OAuth?"
        }
    }
    title = build_conversation_title(task)
    assert "Slack: #general" in title
```

**Step 4: Run tests to verify they fail**

Run: `PYTHONPATH=agent-engine:$PYTHONPATH uv run pytest agent-engine/tests/test_conversation_bridge.py -v`
Expected: All tests FAIL with module not found

**Step 5: Commit tests**

```bash
git add agent-engine/tests/test_conversation_bridge.py
git commit -m "test: add failing tests for conversation bridge flow_id and title"
```

---

## Task 6: Implement Conversation Bridge Basic Functions

**Files:**
- Create: `agent-engine/services/conversation_bridge.py`

**Step 1: Write minimal implementation for flow_id**

```python
def build_flow_id(task: dict) -> str:
    """Generate deterministic flow ID from task data.

    Examples:
    - Jira: "jira:KAN-6"
    - GitHub: "github:owner/repo#42"
    - Slack: "slack:channel:thread_ts"
    """
    source = task.get("source", "unknown")
    metadata = task.get("source_metadata", {})

    if source == "jira":
        key = metadata.get("key", "unknown")
        return f"jira:{key}"

    if source == "github":
        repo = metadata.get("repo", "unknown")
        number = metadata.get("number", "unknown")
        return f"github:{repo}#{number}"

    if source == "slack":
        channel = metadata.get("channel", "unknown")
        thread_ts = metadata.get("thread_ts", "unknown")
        return f"slack:{channel}:{thread_ts}"

    return f"{source}:unknown"
```

**Step 2: Run tests to verify they pass for flow_id**

Run: `PYTHONPATH=agent-engine:$PYTHONPATH uv run pytest agent-engine/tests/test_conversation_bridge.py -k flow_id -v`
Expected: 3 tests PASS

**Step 3: Write minimal implementation for conversation title**

```python
def build_conversation_title(task: dict) -> str:
    """Generate conversation title from task data.

    Examples:
    - Jira: "Jira: KAN-6 - Fix login bug"
    - GitHub: "GitHub: repo#42 - Add feature"
    - Slack: "Slack: #channel - question"
    """
    source = task.get("source", "unknown")
    metadata = task.get("source_metadata", {})

    if source == "jira":
        key = metadata.get("key", "unknown")
        summary = metadata.get("summary", "")
        return f"Jira: {key} - {summary}" if summary else f"Jira: {key}"

    if source == "github":
        repo = metadata.get("repo", "unknown")
        number = metadata.get("number", "unknown")
        title = metadata.get("title", "")
        repo_short = repo.split("/")[-1] if "/" in repo else repo
        return f"GitHub: {repo_short}#{number} - {title}" if title else f"GitHub: {repo_short}#{number}"

    if source == "slack":
        channel_name = metadata.get("channel_name", "unknown")
        text = metadata.get("text", "")
        text_preview = text[:50] + "..." if len(text) > 50 else text
        return f"Slack: #{channel_name} - {text_preview}" if text else f"Slack: #{channel_name}"

    return f"{source.title()}: Unknown"
```

**Step 4: Run all tests to verify they pass**

Run: `PYTHONPATH=agent-engine:$PYTHONPATH uv run pytest agent-engine/tests/test_conversation_bridge.py -v`
Expected: All 6 tests PASS

**Step 5: Commit implementation**

```bash
git add agent-engine/services/conversation_bridge.py
git commit -m "feat: implement flow_id and conversation_title builders"
```

---

## Task 7: Write Tests for Async Conversation Bridge Functions

**Files:**
- Modify: `agent-engine/tests/test_conversation_bridge.py`

**Step 1: Write failing test for get_or_create_flow_conversation**

```python
import pytest
from unittest.mock import AsyncMock, patch
from agent_engine.services.conversation_bridge import get_or_create_flow_conversation


@pytest.mark.asyncio
async def test_get_or_create_flow_conversation_existing():
    task = {
        "source": "jira",
        "source_metadata": {"key": "KAN-6", "summary": "Fix bug"}
    }

    with patch("agent_engine.services.conversation_bridge.httpx.AsyncClient") as mock_client:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"conversation_id": "conv-123"}
        mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

        conv_id = await get_or_create_flow_conversation("http://dashboard:5000", task)
        assert conv_id == "conv-123"


@pytest.mark.asyncio
async def test_get_or_create_flow_conversation_new():
    task = {
        "source": "jira",
        "source_metadata": {"key": "KAN-7", "summary": "New bug"}
    }

    with patch("agent_engine.services.conversation_bridge.httpx.AsyncClient") as mock_client:
        mock_get_response = AsyncMock()
        mock_get_response.status_code = 404

        mock_post_response = AsyncMock()
        mock_post_response.status_code = 201
        mock_post_response.json.return_value = {"conversation_id": "conv-456"}

        mock_client_instance = mock_client.return_value.__aenter__.return_value
        mock_client_instance.get.return_value = mock_get_response
        mock_client_instance.post.return_value = mock_post_response

        conv_id = await get_or_create_flow_conversation("http://dashboard:5000", task)
        assert conv_id == "conv-456"
```

**Step 2: Write failing test for fetch_conversation_context**

```python
from agent_engine.services.conversation_bridge import fetch_conversation_context


@pytest.mark.asyncio
async def test_fetch_conversation_context():
    with patch("agent_engine.services.conversation_bridge.httpx.AsyncClient") as mock_client:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"role": "user", "content": "Message 1"},
            {"role": "assistant", "content": "Response 1"},
            {"role": "user", "content": "Message 2"},
        ]
        mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

        messages = await fetch_conversation_context("http://dashboard:5000", "conv-123", limit=5)
        assert len(messages) == 3
        assert messages[0]["content"] == "Message 1"
```

**Step 3: Run tests to verify they fail**

Run: `PYTHONPATH=agent-engine:$PYTHONPATH uv run pytest agent-engine/tests/test_conversation_bridge.py -k async -v`
Expected: FAIL with "function not defined"

**Step 4: Commit failing tests**

```bash
git add agent-engine/tests/test_conversation_bridge.py
git commit -m "test: add failing tests for async conversation bridge functions"
```

---

## Task 8: Implement Async Conversation Bridge Functions

**Files:**
- Modify: `agent-engine/services/conversation_bridge.py`

**Step 1: Add imports**

```python
import httpx
from typing import Optional
```

**Step 2: Implement get_or_create_flow_conversation**

```python
async def get_or_create_flow_conversation(dashboard_url: str, task: dict) -> str:
    """Get or create conversation for flow_id.

    Returns conversation_id (reuses existing if flow exists).
    """
    flow_id = build_flow_id(task)

    async with httpx.AsyncClient(timeout=10.0) as client:
        # Check if conversation exists
        response = await client.get(
            f"{dashboard_url}/api/conversations/by-flow/{flow_id}"
        )

        if response.status_code == 200:
            data = response.json()
            return data["conversation_id"]

        # Create new conversation
        title = build_conversation_title(task)
        response = await client.post(
            f"{dashboard_url}/api/conversations",
            json={
                "flow_id": flow_id,
                "title": title,
                "source": task.get("source", "webhook"),
                "metadata": task.get("source_metadata", {}),
            }
        )
        response.raise_for_status()

        data = response.json()
        return data["conversation_id"]
```

**Step 3: Implement fetch_conversation_context**

```python
async def fetch_conversation_context(
    dashboard_url: str,
    conversation_id: str,
    limit: int = 5
) -> list[dict]:
    """Fetch last N messages from conversation.

    Returns list of message dicts with role and content.
    """
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            f"{dashboard_url}/api/conversations/{conversation_id}/context",
            params={"max_messages": limit}
        )
        response.raise_for_status()
        return response.json()
```

**Step 4: Run tests to verify they pass**

Run: `PYTHONPATH=agent-engine:$PYTHONPATH uv run pytest agent-engine/tests/test_conversation_bridge.py -v`
Expected: All tests PASS

**Step 5: Commit implementation**

```bash
git add agent-engine/services/conversation_bridge.py
git commit -m "feat: implement async conversation bridge functions"
```

---

## Task 9: Add Dashboard-API Task Registration Endpoint

**Files:**
- Modify: `dashboard-api/api/dashboard.py`

**Step 1: Add Pydantic model for external task creation**

Around line 30 (with other models):

```python
class ExternalTaskCreate(BaseModel):
    task_id: str
    source: str
    source_metadata: dict
    input_message: str
    assigned_agent: str = "brain"
    conversation_id: str | None = None
    flow_id: str | None = None
```

**Step 2: Write the endpoint implementation**

Around line 500:

```python
@router.post("/api/tasks")
async def create_external_task(
    payload: ExternalTaskCreate,
    db=Depends(get_db_session)
):
    """Register external task (from webhooks) in TaskDB."""

    # Ensure webhook-system session exists
    session_result = await db.execute(
        select(SessionDB).where(SessionDB.session_id == "webhook-system")
    )
    webhook_session = session_result.scalar_one_or_none()

    if not webhook_session:
        webhook_session = SessionDB(
            session_id="webhook-system",
            user_id="system",
            provider="webhook",
            active=True
        )
        db.add(webhook_session)
        await db.flush()

    # Create TaskDB record
    task = TaskDB(
        task_id=payload.task_id,
        session_id="webhook-system",
        user_id="system",
        input_message=payload.input_message,
        source=payload.source,
        source_metadata=json.dumps({
            **payload.source_metadata,
            "conversation_id": payload.conversation_id,
            "flow_id": payload.flow_id,
        }),
        assigned_agent=payload.assigned_agent,
        status="pending",
    )
    db.add(task)
    await db.commit()

    return {
        "task_id": payload.task_id,
        "conversation_id": payload.conversation_id,
    }
```

**Step 3: Add necessary imports**

Top of file:

```python
import json
from sqlalchemy import select
from database.models import TaskDB, SessionDB
```

**Step 4: Test manually with curl**

Run:
```bash
curl -X POST http://localhost:5000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "test-123",
    "source": "jira",
    "source_metadata": {"key": "KAN-6"},
    "input_message": "Fix the bug",
    "conversation_id": "conv-123"
  }'
```
Expected: `{"task_id": "test-123", "conversation_id": "conv-123"}`

**Step 5: Commit**

```bash
git add dashboard-api/api/dashboard.py
git commit -m "feat: add POST /api/tasks endpoint for external task registration"
```

---

## Task 10: Add Conversation Context Endpoint in Dashboard-API

**Files:**
- Modify: `dashboard-api/api/dashboard.py`

**Step 1: Write endpoint to fetch conversation context**

Around line 550:

```python
@router.get("/api/conversations/{conversation_id}/context")
async def get_conversation_context(
    conversation_id: str,
    max_messages: int = 5,
    db=Depends(get_db_session)
):
    """Fetch last N messages from conversation for context."""

    messages_result = await db.execute(
        select(ConversationMessageDB)
        .where(ConversationMessageDB.conversation_id == conversation_id)
        .order_by(ConversationMessageDB.created_at.desc())
        .limit(max_messages)
    )
    messages = messages_result.scalars().all()

    # Reverse to chronological order
    messages = list(reversed(messages))

    return [
        {
            "role": msg.role,
            "content": msg.content,
            "created_at": msg.created_at.isoformat() if msg.created_at else None,
        }
        for msg in messages
    ]
```

**Step 2: Add import**

Top of file:

```python
from database.models import ConversationMessageDB
```

**Step 3: Test manually**

Run:
```bash
curl http://localhost:5000/api/conversations/conv-123/context?max_messages=5
```
Expected: JSON array of messages

**Step 4: Commit**

```bash
git add dashboard-api/api/dashboard.py
git commit -m "feat: add GET /api/conversations/{id}/context endpoint"
```

---

## Task 11: Write Tests for Task Routing with Context

**Files:**
- Create: `agent-engine/tests/test_task_routing.py`

**Step 1: Write failing tests**

```python
import pytest
from agent_engine.services.task_routing import build_prompt


def test_build_prompt_basic():
    task = {"prompt": "Fix the bug", "source": "jira"}
    prompt = build_prompt(task)
    assert "Fix the bug" in prompt


def test_build_prompt_with_context():
    task = {"prompt": "Fix the bug", "source": "jira"}
    context = [
        {"role": "user", "content": "Previous message 1"},
        {"role": "assistant", "content": "Previous response 1"},
        {"role": "user", "content": "Previous message 2"},
    ]

    prompt = build_prompt(task, context)
    assert "Previous message 1" in prompt
    assert "Previous response 1" in prompt
    assert "Fix the bug" in prompt


def test_build_prompt_jira_instructions():
    task = {"prompt": "Analyze ticket", "source": "jira"}
    prompt = build_prompt(task)
    assert "jira:add_jira_comment" in prompt


def test_build_prompt_github_instructions():
    task = {"prompt": "Review PR", "source": "github"}
    prompt = build_prompt(task)
    assert "github:add_issue_comment" in prompt


def test_build_prompt_slack_instructions():
    task = {"prompt": "Answer question", "source": "slack"}
    prompt = build_prompt(task)
    assert "slack:send_slack_message" in prompt
```

**Step 2: Run tests to verify they fail**

Run: `PYTHONPATH=agent-engine:$PYTHONPATH uv run pytest agent-engine/tests/test_task_routing.py -v`
Expected: All tests FAIL with module not found

**Step 3: Commit tests**

```bash
git add agent-engine/tests/test_task_routing.py
git commit -m "test: add failing tests for task_routing build_prompt"
```

---

## Task 12: Implement Task Routing with Context

**Files:**
- Create: `agent-engine/services/task_routing.py`

**Step 1: Implement build_prompt function**

```python
def build_prompt(task: dict, conversation_context: list[dict] = None) -> str:
    """Build enriched prompt with conversation history and platform instructions.

    Args:
        task: Task data with prompt, source, metadata
        conversation_context: Last 5 messages from dashboard conversation

    Returns:
        Complete prompt with context and platform instructions
    """
    source = task.get("source", "unknown")
    base_prompt = task.get("prompt", "")
    metadata = task.get("source_metadata", {})

    # Build context section
    context_section = ""
    if conversation_context:
        context_section = "\n## Previous Conversation\n\n"
        for msg in conversation_context:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            context_section += f"**{role.title()}**: {content}\n\n"

    # Build source context
    source_context = _build_source_context(source, metadata)

    # Build platform instructions
    platform_instructions = _build_platform_instructions(source)

    # Combine all parts
    return f"""
{source_context}

{context_section}

## Task

{base_prompt}

{platform_instructions}
""".strip()


def _build_jira_source_context(metadata: dict) -> str:
    """Build Jira-specific context header."""
    key = metadata.get("key", "unknown")
    return f"## Jira Ticket: {key}\n"


def _build_github_source_context(metadata: dict) -> str:
    """Build GitHub-specific context header."""
    repo = metadata.get("repo", "unknown")
    number = metadata.get("number", "unknown")
    return f"## GitHub Issue/PR: {repo}#{number}\n"


def _build_slack_source_context(metadata: dict) -> str:
    """Build Slack-specific context header."""
    channel = metadata.get("channel_name", "unknown")
    return f"## Slack Channel: #{channel}\n"


def _build_source_context(source: str, metadata: dict) -> str:
    """Route to platform-specific context builder."""
    if source == "jira":
        return _build_jira_source_context(metadata)
    if source == "github":
        return _build_github_source_context(metadata)
    if source == "slack":
        return _build_slack_source_context(metadata)
    return f"## Source: {source}\n"


def _build_jira_platform_instructions() -> str:
    """Build Jira-specific response instructions."""
    return """
## Response Instructions

Post your analysis as a comment on the Jira ticket using the `jira:add_jira_comment` MCP tool.
"""


def _build_github_platform_instructions() -> str:
    """Build GitHub-specific response instructions."""
    return """
## Response Instructions

Post your response as a comment on the GitHub issue/PR using the `github:add_issue_comment` MCP tool.
"""


def _build_slack_platform_instructions() -> str:
    """Build Slack-specific response instructions."""
    return """
## Response Instructions

Post a summary (max 3000 chars) to the Slack thread using the `slack:send_slack_message` MCP tool.
If a PR is involved, include the PR link with a brief summary.
"""


def _build_platform_instructions(source: str) -> str:
    """Route to platform-specific instructions builder."""
    if source == "jira":
        return _build_jira_platform_instructions()
    if source == "github":
        return _build_github_platform_instructions()
    if source == "slack":
        return _build_slack_platform_instructions()
    return ""
```

**Step 2: Run tests to verify they pass**

Run: `PYTHONPATH=agent-engine:$PYTHONPATH uv run pytest agent-engine/tests/test_task_routing.py -v`
Expected: All tests PASS

**Step 3: Commit**

```bash
git add agent-engine/services/task_routing.py
git commit -m "feat: implement task routing with conversation context"
```

---

## Task 13: Integrate Conversation Bridge into Agent-Engine

**Files:**
- Modify: `agent-engine/main.py:55-95`

**Step 1: Add imports**

Top of file (~line 10):

```python
import time
from services import conversation_bridge, task_routing
```

**Step 2: Add conversation flow before CLI execution**

In `_process_task`, lines ~55-70 (before `_execute_task`):

```python
# Get dashboard URL from settings
dashboard_url = os.getenv("DASHBOARD_API_URL", "http://dashboard-api:5000")

# Build flow_id from task data
flow_id = conversation_bridge.build_flow_id(task)
logger.info("webhook_flow_started", task_id=task_id, flow_id=flow_id)

# Get or create conversation
conversation_id = await conversation_bridge.get_or_create_flow_conversation(
    dashboard_url,
    task
)
logger.info("webhook_conversation_ready", task_id=task_id, conversation_id=conversation_id)

# Register task in dashboard-api
await conversation_bridge.register_task(dashboard_url, task, conversation_id)
logger.info("webhook_task_registered", task_id=task_id)

# Post system message with webhook context
source = task.get("source")
metadata = task.get("source_metadata", {})

# Function mapping - no if/elif routing
system_message_funcs = {
    "jira": conversation_bridge.post_jira_system_message,
    "github": conversation_bridge.post_github_system_message,
    "slack": conversation_bridge.post_slack_system_message,
}

post_func = system_message_funcs.get(source)
if post_func:
    await post_func(dashboard_url, conversation_id, metadata)

# Fetch last 5 messages for context
conversation_context = await conversation_bridge.fetch_conversation_context(
    dashboard_url,
    conversation_id,
    limit=5
)
logger.info("webhook_context_fetched", task_id=task_id, messages_count=len(conversation_context))

# Build enriched prompt
enriched_prompt = task_routing.build_prompt(task, conversation_context)

# Record start time for duration tracking
start_time = time.monotonic()
```

**Step 3: Update CLI execution to use enriched prompt**

Line ~75:

```python
result = await self._execute_task(
    task_id=task_id,
    prompt=enriched_prompt,  # Use enriched prompt instead of task["prompt"]
    agent_dir=agent_dir,
    output_queue=output_queue
)
```

**Step 4: Test locally**

Run: `docker compose logs -f agent-engine | grep "webhook_flow_started"`
Expected: See flow_id generation and conversation creation logs

**Step 5: Commit**

```bash
git add agent-engine/main.py
git commit -m "feat: integrate conversation bridge into agent-engine task processing"
```

---

## Task 14: Implement Missing Conversation Bridge Functions

**Files:**
- Modify: `agent-engine/services/conversation_bridge.py`

**Step 1: Implement register_task**

```python
async def register_task(dashboard_url: str, task: dict, conversation_id: str) -> None:
    """Register task in dashboard via POST /api/tasks."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            f"{dashboard_url}/api/tasks",
            json={
                "task_id": task["task_id"],
                "source": task.get("source", "webhook"),
                "source_metadata": task.get("source_metadata", {}),
                "input_message": task.get("prompt", ""),
                "assigned_agent": task.get("assigned_agent", "brain"),
                "conversation_id": conversation_id,
                "flow_id": build_flow_id(task),
            }
        )
        response.raise_for_status()
```

**Step 2: Implement platform-specific system message functions**

```python
async def post_jira_system_message(
    dashboard_url: str,
    conversation_id: str,
    metadata: dict
) -> None:
    """Post Jira webhook context as system message."""
    key = metadata.get("key", "unknown")
    summary = metadata.get("summary", "")
    content = f"🎫 **Jira Webhook Triggered**\n\nTicket: {key}\nSummary: {summary}"

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            f"{dashboard_url}/api/conversations/{conversation_id}/messages",
            json={"role": "system", "content": content}
        )
        response.raise_for_status()


async def post_github_system_message(
    dashboard_url: str,
    conversation_id: str,
    metadata: dict
) -> None:
    """Post GitHub webhook context as system message."""
    repo = metadata.get("repo", "unknown")
    number = metadata.get("number", "unknown")
    title = metadata.get("title", "")
    content = f"🐙 **GitHub Webhook Triggered**\n\nRepo: {repo}\nIssue/PR: #{number}\nTitle: {title}"

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            f"{dashboard_url}/api/conversations/{conversation_id}/messages",
            json={"role": "system", "content": content}
        )
        response.raise_for_status()


async def post_slack_system_message(
    dashboard_url: str,
    conversation_id: str,
    metadata: dict
) -> None:
    """Post Slack webhook context as system message."""
    channel = metadata.get("channel_name", "unknown")
    content = f"💬 **Slack Webhook Triggered**\n\nChannel: #{channel}"

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            f"{dashboard_url}/api/conversations/{conversation_id}/messages",
            json={"role": "system", "content": content}
        )
        response.raise_for_status()
```

**Step 3: Test locally**

Run webhook and check dashboard conversations for system messages

**Step 4: Commit**

```bash
git add agent-engine/services/conversation_bridge.py
git commit -m "feat: implement register_task and post_system_message"
```

---

## Task 15: Add Task-Logger Fallback in Dashboard-API

**Files:**
- Modify: `dashboard-api/api/dashboard.py`

**Step 1: Add endpoint to fetch logs with fallback**

Around line 600:

```python
@router.get("/api/tasks/{task_id}/logs")
async def get_task_logs(task_id: str):
    """Fetch task logs with fallback to task-logger service."""

    # Try Redis first
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
    redis_client = await aioredis.from_url(redis_url)
    redis_output = await redis_client.get(f"task:{task_id}:output")

    if redis_output:
        return {"output": redis_output.decode("utf-8")}

    # Fallback to task-logger service
    task_logger_url = os.getenv("TASK_LOGGER_URL", "http://task-logger:8090")

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(f"{task_logger_url}/tasks/{task_id}/logs")
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.warning("task_logger_fallback_failed", task_id=task_id, error=str(e))

    return {"output": ""}
```

**Step 2: Add imports**

Top of file:

```python
import os
import aioredis
import httpx
```

**Step 3: Add environment variable to .env.example**

```bash
TASK_LOGGER_URL=http://task-logger:8090
```

**Step 4: Test manually**

Run:
```bash
curl http://localhost:5000/api/tasks/test-123/logs
```
Expected: Task logs or empty output

**Step 5: Commit**

```bash
git add dashboard-api/api/dashboard.py .env.example
git commit -m "feat: add task-logger fallback endpoint in dashboard-api"
```

---

## Task 16: Add Full Output Storage (Remove Truncation)

**Files:**
- Modify: `agent-engine/main.py:85-92`

**Step 1: Update task:completed event to store full output**

In `_publish_task_event("task:completed")` call:

```python
await self._publish_task_event(
    task_id,
    "task:completed",
    {
        "task_id": task_id,
        "session_id": session_id,
        "status": "completed" if result.success else "failed",
        "result": result.get("output", ""),  # NO [:5000] truncation
        "duration_seconds": round(duration, 2),
        "cost_usd": result.cost_usd,
        "input_tokens": result.input_tokens,
        "output_tokens": result.output_tokens,
    },
)
```

**Step 2: Update Redis storage to remove truncation**

Around line 90:

```python
if result.get("output"):
    await self._redis.set(
        f"task:{task_id}:output",
        result["output"],  # NO [:5000] truncation
        ex=3600
    )
```

**Step 3: Test with long output task**

Trigger webhook that generates > 5000 char output
Expected: Full output visible in dashboard

**Step 4: Commit**

```bash
git add agent-engine/main.py
git commit -m "fix: remove output truncation - store full results"
```

---

## Task 17: End-to-End Integration Test

**Files:**
- Test manually with real webhook

**Step 1: Rebuild all services**

Run:
```bash
docker compose down
docker compose up -d --build --force-recreate
```
Expected: All services healthy

**Step 2: Verify bind mount exists**

Run:
```bash
ls -la ./data/logs/tasks/
```
Expected: Directory exists

**Step 3: Trigger Jira webhook**

Assign ai-agent to Jira ticket KAN-6
Expected: Webhook received

**Step 4: Verify conversation created**

Check dashboard Chat view
Expected: Conversation "Jira: KAN-6 - ..." with system + user messages

**Step 5: Verify task in ledger**

Check dashboard Ledger
Expected: Task with status, cost, duration

**Step 6: Verify CLI output**

Click task in ledger
Expected: Modal shows full CLI output (not truncated)

**Step 7: Verify Jira comment**

Check Jira ticket KAN-6
Expected: Agent posted comment via MCP tools

**Step 8: Verify logs on host**

Run:
```bash
ls ./data/logs/tasks/{task-id}/
```
Expected: Files: metadata.json, 01-input.json (with message), 02-webhook-flow.jsonl, 03-agent-output.jsonl, 04-final-result.json (with result + duration)

**Step 9: Verify conversation reuse**

Trigger same Jira ticket again
Expected: Reuses same conversation (same flow_id)

**Step 10: Run automated tests**

Run:
```bash
PYTHONPATH=agent-engine:$PYTHONPATH uv run pytest agent-engine/tests/ -v
```
Expected: All tests PASS

---

## Verification Checklist

After completing all tasks:

- [ ] Docker bind mount works - `./data/logs/tasks/` visible on host
- [ ] Webhook tasks create conversations in Chat view
- [ ] Conversations have correct titles (Jira: KAN-6, GitHub: repo#42, etc)
- [ ] Tasks appear in Ledger with status, cost, duration
- [ ] CLI output visible in task detail modal (NOT truncated)
- [ ] Agent responses posted to Jira/GitHub/Slack via MCP tools
- [ ] Task logs on host have all files with correct data
- [ ] Same webhook flow reuses same conversation
- [ ] All automated tests pass
- [ ] Skills loaded from `agent-engine/.claude/agents/*.md`
- [ ] MCP servers loaded from `agent-engine/.claude/mcp.json`

---

## Rollback Plan

If issues occur:

1. **Revert bind mount**: Change back to named volume in docker-compose.yml
2. **Revert agent-engine changes**: `git revert <commit-hash>` for main.py changes
3. **Revert dashboard-api changes**: `git revert <commit-hash>` for dashboard.py changes
4. **Rebuild**: `docker compose down && docker compose up -d --build`

Critical files to backup before starting:
- `docker-compose.yml`
- `agent-engine/main.py`
- `dashboard-api/api/dashboard.py`
