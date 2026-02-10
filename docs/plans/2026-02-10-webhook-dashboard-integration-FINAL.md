# Webhook-to-Dashboard Integration - Complete Implementation Plan

> **Architecture Goal:** Make webhook tasks (Jira, GitHub, Slack) fully visible in dashboard with real-time streaming, conversation context, and CLI autonomy via MCP tools.

**Status:** Ready for agent team execution
**Estimated Time:** 1 day (parallel) | 4-5 days (sequential)
**Team Size:** 5 specialists + 1 brain (team lead)

---

## Executive Summary

**What's Being Built:**
1. **Conversation System** - Webhook tasks create/reuse conversations with flow_id
2. **Context Awareness** - Agent fetches last 5 messages before execution
3. **Real-time Streaming** - WebSocket pushes task events to frontend
4. **Full Output** - No truncation, logs stored on host
5. **MCP Integration** - Agent posts to Jira/GitHub/Slack via MCP tools
6. **Dashboard UI** - Chat view, Ledger updates, Task detail modal

**Critical Success Factors:**
- ✅ Database schema verified/created FIRST
- ✅ API endpoints before integration
- ✅ TDD throughout (tests before implementation)
- ✅ Explicit functions per webhook type (no routing logic)
- ✅ Error handling from the start
- ✅ Frontend WebSocket subscription for real-time updates

---

## Team Structure & Ownership

**Team Lead:**
- `brain` - Coordinates phases, reviews deliverables, resolves blockers

**Specialists:**
1. `database-specialist` - Schema verification, migrations
2. `backend-specialist` - Dashboard-api endpoints, WebSocket
3. `agent-specialist` - Agent-engine integration, conversation bridge
4. `frontend-specialist` - React UI, WebSocket client
5. `testing-specialist` - All tests, E2E verification

---

## Phase 0: Pre-requisites (MCP Config + Docker Verification)

**Objective:** Fix MCP config, verify Docker .claude setup, ensure CLI can post via MCP tools
**Owner:** agent-specialist
**Can run in parallel:** Yes (with Phase 1)
**This phase is CRITICAL** - without it, CLI cannot post responses to Jira/GitHub/Slack

### Task 0.1: Remove Stale Sentry MCP Reference (agent-specialist)

**Files:** `agent-engine/.claude/mcp.json`

**Steps:**
1. Remove `sentry` entry from mcpServers (Sentry was removed in Phase 1 refactoring)
2. Verify remaining entries: `jira`, `slack`, `github`, `knowledge-graph`, `llamaindex`, `gkg`

**Commit:** `fix: remove stale sentry reference from mcp.json`

---

### Task 0.2: Verify Docker .claude Setup (agent-specialist)

**Files:** `agent-engine/Dockerfile`, `agent-engine/scripts/start.py`

**Steps:**
1. Confirm Dockerfile has `COPY --chown=agent:agent . .` (copies agent-engine/.claude/ into container)
2. Confirm `start.py` syncs `/app/.claude/` to `/home/agent/.claude/` at startup
3. Confirm docker-compose.yml only mounts credentials (`.credentials.json`, `.claude.json`) NOT the full `~/.claude/` directory
4. Verify skills, agents, and mcp.json come from the project directory, NOT from host home

**Expected state:**
```
Container filesystem:
  /app/.claude/           ← COPIED from agent-engine/.claude/ (project source)
  /home/agent/.claude/    ← SYNCED from /app/.claude/ at startup

  Only mounted from host:
  /home/agent/.claude/.credentials.json  ← Host ~/.claude/.credentials.json (read-only)
  /home/agent/.claude/.claude.json       ← Host ~/.claude/.claude.json (read-only)
```

**Verification:**
```bash
docker compose exec cli ls -la /home/agent/.claude/
docker compose exec cli ls -la /home/agent/.claude/agents/
docker compose exec cli cat /home/agent/.claude/mcp.json
```

**No changes needed if setup is correct. Document if any fixes are required.**

---

### Task 0.3: Verify MCP Tools Work Inside Container (agent-specialist)

**Files:** None (manual verification)

**Steps:**
1. Start services: `docker compose up -d`
2. Exec into CLI container: `docker compose exec cli bash`
3. Test Jira MCP connectivity:
   ```bash
   curl -s http://jira-mcp:9002/health
   ```
4. Test Slack MCP connectivity:
   ```bash
   curl -s http://slack-mcp:9003/health
   ```
5. Test GitHub MCP connectivity (uses external Copilot API):
   ```bash
   curl -s -H "Authorization: Bearer $GITHUB_TOKEN" https://api.githubcopilot.com/mcp/
   ```
6. Verify CLI can list MCP tools:
   ```bash
   claude --list-tools 2>&1 | grep -E "(jira|slack|github)"
   ```

**Expected:** All MCP servers reachable, tools listed

---

### Task 0.4: Verify OAuth Token Flow (agent-specialist)

**Files:** None (manual verification)

**Steps:**
1. Test Jira OAuth flow:
   ```bash
   docker compose exec jira-api curl -s http://oauth-service:8010/internal/token/jira \
     -H "X-Internal-Service-Key: $INTERNAL_SERVICE_KEY"
   ```
2. Test Slack OAuth flow:
   ```bash
   docker compose exec slack-api curl -s http://oauth-service:8010/internal/token/slack \
     -H "X-Internal-Service-Key: $INTERNAL_SERVICE_KEY"
   ```
3. Verify tokens are returned with `"available": true`
4. If OAuth not configured, verify static fallback tokens exist in environment

**Expected:** Tokens returned, or static fallback working

---

### Task 0.5: Document CLI Response Strategy (agent-specialist)

**Rationale:** The CLI handles posting responses to platforms via MCP tools autonomously. Python code only handles:
- **Immediate acknowledgments** (e.g., reaction emoji on webhook receipt)
- **Failure notifications** (e.g., error comment if task crashes before CLI starts)
- **Internal bookkeeping** (system messages to dashboard conversations)

**The CLI receives platform instructions in the enriched prompt** (from `task_routing.py`):
- Jira: "Post your analysis using the `jira:add_jira_comment` MCP tool"
- GitHub: "Post your response using the `github:add_issue_comment` MCP tool"
- Slack: "Post a summary using the `slack:send_slack_message` MCP tool"

**What Python code does NOT do:**
- Post task results to Jira/GitHub/Slack (CLI does this via MCP)
- Format responses for platforms (CLI handles formatting)

**What Python code DOES do:**
- Post system messages to dashboard conversations (internal)
- Send failure notifications if task crashes before CLI can respond
- Track task status and metrics

**Add to agent-engine CLAUDE.md or rules file.**

---

## Phase 1: Foundation (Database + Event Logging)

**Objective:** Establish database schema and fix event logging
**Owner:** database-specialist, agent-specialist
**Can run in parallel:** Yes

### Task 1.1: Verify Database Schema (database-specialist)

**Files:** `dashboard-api/database/models.py`, `dashboard-api/database/init.sql`

**Steps:**
1. Check if `conversations` table exists with columns:
   - `conversation_id` (PK, UUID)
   - `flow_id` (unique, indexed)
   - `title` (string)
   - `source` (string: jira/github/slack)
   - `metadata` (JSONB)
   - `created_at`, `updated_at`

2. Check if `conversation_messages` table exists with columns:
   - `message_id` (PK, UUID)
   - `conversation_id` (FK to conversations)
   - `role` (string: system/user/assistant)
   - `content` (text)
   - `created_at`

3. Check if `tasks` table has `conversation_id` column (nullable FK)

4. If missing, create migration SQL and run

**Verification:**
```sql
SELECT * FROM conversations LIMIT 1;
SELECT * FROM conversation_messages LIMIT 1;
SELECT conversation_id FROM tasks LIMIT 1;
```

**Commit:** `feat: add conversation tables for webhook integration`

---

### Task 1.2: Fix Event Logging in agent-engine (agent-specialist)

**Files:** `agent-engine/main.py`

**Steps:**
1. Add `import time` at top of file
2. Add `task:created` event before `task:started` with `input_message` field
3. Add `start_time = time.monotonic()` before `_execute_task`
4. Add `duration = time.monotonic() - start_time` after execution
5. Update `task:completed` event with:
   - `duration_seconds`: `round(duration, 2)`
   - `result`: Full output (NO truncation)
   - `cost_usd`, `input_tokens`, `output_tokens`
6. Remove `[:5000]` truncation from Redis storage

**Test:**
```bash
docker compose logs -f task-logger | grep "task:created"
docker compose logs -f task-logger | grep "duration_seconds"
```

**Verification:** Events have `input_message` and `duration_seconds`, no truncation

**Commit:** `fix: add complete event logging with duration and full output`

---

### Task 1.3: Change Docker to Bind Mount (agent-specialist)

**Files:** `docker-compose.yml`

**Steps:**
1. Change task-logger volume from named volume to bind mount:
   ```yaml
   volumes:
     - ./data/logs/tasks:/data/logs/tasks
   ```
2. Remove `task_logs` from volumes section
3. Create directory: `mkdir -p ./data/logs/tasks`
4. Restart services: `docker compose down && docker compose up -d --build`

**Verification:**
```bash
ls -la ./data/logs/tasks/
docker compose exec task-logger ls -la /data/logs/tasks
```

**Commit:** `feat: use bind mount for host-visible task logs`

---

### Task 1.4: Fix dashboard-api Event (backend-specialist)

**Files:** `dashboard-api/api/dashboard.py`

**Steps:**
1. Find existing `task:created` event emission (around line 461)
2. Add `input_message` field to event data
3. Test with manual task creation

**Test:**
```bash
docker compose logs -f task-logger | grep "input_message"
```

**Verification:** Dashboard-api events include `input_message`

**Commit:** `fix: add input_message to task:created events`

---

## Phase 2: Conversation API (Backend Foundation)

**Objective:** Build all conversation-related API endpoints
**Owner:** backend-specialist
**Depends on:** Phase 1 (database schema)

### Task 2.1: Add Pydantic Models (backend-specialist)

**Files:** `dashboard-api/api/dashboard.py`

**Steps:**
Add models near top of file (around line 30):

```python
class ConversationCreate(BaseModel):
    flow_id: str
    title: str
    source: str
    metadata: dict = {}

class MessageCreate(BaseModel):
    role: str  # system, user, assistant
    content: str

class ExternalTaskCreate(BaseModel):
    task_id: str
    source: str
    source_metadata: dict
    input_message: str
    assigned_agent: str = "brain"
    conversation_id: str | None = None
    flow_id: str | None = None
```

**Verification:** Models import without errors

---

### Task 2.2: POST /api/conversations (backend-specialist)

**Files:** `dashboard-api/api/dashboard.py`

**Implementation:**
```python
@router.post("/api/conversations")
async def create_conversation(
    payload: ConversationCreate,
    db=Depends(get_db_session)
):
    """Create new conversation with flow_id."""
    conversation = ConversationDB(
        conversation_id=str(uuid.uuid4()),
        flow_id=payload.flow_id,
        title=payload.title,
        source=payload.source,
        metadata=json.dumps(payload.metadata),
    )
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)

    return {
        "conversation_id": conversation.conversation_id,
        "flow_id": conversation.flow_id,
        "title": conversation.title,
    }
```

**Test:**
```bash
curl -X POST http://localhost:5000/api/conversations \
  -H "Content-Type: application/json" \
  -d '{
    "flow_id": "jira:KAN-6",
    "title": "Jira: KAN-6 - Fix bug",
    "source": "jira",
    "metadata": {"key": "KAN-6"}
  }'
```

**Verification:** Returns `conversation_id`

---

### Task 2.3: GET /api/conversations/by-flow/{flow_id} (backend-specialist)

**Files:** `dashboard-api/api/dashboard.py`

**Implementation:**
```python
@router.get("/api/conversations/by-flow/{flow_id}")
async def get_conversation_by_flow(
    flow_id: str,
    db=Depends(get_db_session)
):
    """Find conversation by flow_id."""
    result = await db.execute(
        select(ConversationDB).where(ConversationDB.flow_id == flow_id)
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return {
        "conversation_id": conversation.conversation_id,
        "flow_id": conversation.flow_id,
        "title": conversation.title,
    }
```

**Test:**
```bash
curl http://localhost:5000/api/conversations/by-flow/jira:KAN-6
```

**Verification:** Returns conversation or 404

---

### Task 2.4: POST /api/conversations/{id}/messages (backend-specialist)

**Files:** `dashboard-api/api/dashboard.py`

**Implementation:**
```python
@router.post("/api/conversations/{conversation_id}/messages")
async def add_message(
    conversation_id: str,
    payload: MessageCreate,
    db=Depends(get_db_session)
):
    """Add message to conversation."""
    message = ConversationMessageDB(
        message_id=str(uuid.uuid4()),
        conversation_id=conversation_id,
        role=payload.role,
        content=payload.content,
    )
    db.add(message)
    await db.commit()

    return {"message_id": message.message_id}
```

**Test:**
```bash
curl -X POST http://localhost:5000/api/conversations/{conv-id}/messages \
  -H "Content-Type: application/json" \
  -d '{"role": "system", "content": "Test message"}'
```

**Verification:** Returns `message_id`

---

### Task 2.5: GET /api/conversations/{id}/context (backend-specialist)

**Files:** `dashboard-api/api/dashboard.py`

**Implementation:**
```python
@router.get("/api/conversations/{conversation_id}/context")
async def get_conversation_context(
    conversation_id: str,
    max_messages: int = 5,
    db=Depends(get_db_session)
):
    """Fetch last N messages for context."""
    result = await db.execute(
        select(ConversationMessageDB)
        .where(ConversationMessageDB.conversation_id == conversation_id)
        .order_by(ConversationMessageDB.created_at.desc())
        .limit(max_messages)
    )
    messages = result.scalars().all()
    messages = list(reversed(messages))

    return [
        {
            "role": msg.role,
            "content": msg.content,
            "created_at": msg.created_at.isoformat(),
        }
        for msg in messages
    ]
```

**Test:**
```bash
curl http://localhost:5000/api/conversations/{conv-id}/context?max_messages=5
```

**Verification:** Returns array of messages

---

### Task 2.6: POST /api/tasks (backend-specialist)

**Files:** `dashboard-api/api/dashboard.py`

**Implementation:**
```python
@router.post("/api/tasks")
async def create_external_task(
    payload: ExternalTaskCreate,
    db=Depends(get_db_session)
):
    """Register external task from webhooks."""

    # Ensure webhook-system session exists
    session_result = await db.execute(
        select(SessionDB).where(SessionDB.session_id == "webhook-system")
    )
    session = session_result.scalar_one_or_none()

    if not session:
        session = SessionDB(
            session_id="webhook-system",
            user_id="system",
            provider="webhook",
            active=True
        )
        db.add(session)
        await db.flush()

    # Create task
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
        conversation_id=payload.conversation_id,
    )
    db.add(task)
    await db.commit()

    return {
        "task_id": payload.task_id,
        "conversation_id": payload.conversation_id,
    }
```

**Test:**
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

**Verification:** Returns `task_id` and `conversation_id`

**Commit:** `feat: add conversation API endpoints for webhook integration`

---

### Task 2.7: GET /api/tasks/{id}/logs with Fallback (backend-specialist)

**Files:** `dashboard-api/api/dashboard.py`

**Implementation:**
```python
@router.get("/api/tasks/{task_id}/logs")
async def get_task_logs(task_id: str):
    """Fetch task logs with task-logger fallback."""

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

**Add to .env.example:**
```
TASK_LOGGER_URL=http://task-logger:8090
```

**Test:**
```bash
curl http://localhost:5000/api/tasks/test-123/logs
```

**Verification:** Returns logs or empty output

**Commit:** `feat: add task logs endpoint with task-logger fallback`

---

## Phase 3: Conversation Bridge (Agent-Engine Integration)

**Objective:** Agent-engine fetches conversation context and enriches prompts
**Owner:** agent-specialist
**Depends on:** Phase 2 (conversation API)

### Task 3.1: Write TDD Tests for flow_id and title (agent-specialist)

**Files:** `agent-engine/tests/test_conversation_bridge.py`

**Create file with tests:**
```python
import pytest
from agent_engine.services.conversation_bridge import (
    build_flow_id,
    build_conversation_title,
)


def test_build_flow_id_jira():
    task = {
        "source": "jira",
        "source_metadata": {"key": "KAN-6"}
    }
    assert build_flow_id(task) == "jira:KAN-6"


def test_build_flow_id_github():
    task = {
        "source": "github",
        "source_metadata": {"repo": "owner/repo", "number": 42}
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


def test_build_conversation_title_jira():
    task = {
        "source": "jira",
        "source_metadata": {"key": "KAN-6", "summary": "Fix bug"}
    }
    title = build_conversation_title(task)
    assert "Jira: KAN-6" in title
    assert "Fix bug" in title


def test_build_conversation_title_github():
    task = {
        "source": "github",
        "source_metadata": {
            "repo": "owner/repo",
            "number": 42,
            "title": "Add feature"
        }
    }
    title = build_conversation_title(task)
    assert "GitHub" in title
    assert "#42" in title


def test_build_conversation_title_slack():
    task = {
        "source": "slack",
        "source_metadata": {
            "channel_name": "general",
            "text": "How do I configure OAuth?"
        }
    }
    title = build_conversation_title(task)
    assert "Slack" in title
    assert "general" in title
```

**Run tests (should fail):**
```bash
PYTHONPATH=agent-engine:$PYTHONPATH uv run pytest agent-engine/tests/test_conversation_bridge.py -v
```

**Verification:** All tests FAIL (module not found)

**Commit:** `test: add failing tests for conversation bridge`

---

### Task 3.2: Implement flow_id and title builders (agent-specialist)

**Files:** `agent-engine/services/conversation_bridge.py`

**Create file with explicit per-platform functions:**
```python
# --- flow_id builders (one per platform) ---

def build_jira_flow_id(metadata: dict) -> str:
    key = metadata.get("key", "unknown")
    return f"jira:{key}"


def build_github_flow_id(metadata: dict) -> str:
    repo = metadata.get("repo", "unknown")
    number = metadata.get("number", "unknown")
    return f"github:{repo}#{number}"


def build_slack_flow_id(metadata: dict) -> str:
    channel = metadata.get("channel", "unknown")
    thread_ts = metadata.get("thread_ts", "unknown")
    return f"slack:{channel}:{thread_ts}"


FLOW_ID_BUILDERS = {
    "jira": build_jira_flow_id,
    "github": build_github_flow_id,
    "slack": build_slack_flow_id,
}


def build_flow_id(task: dict) -> str:
    """Generate deterministic flow ID from task data."""
    source = task.get("source", "unknown")
    metadata = task.get("source_metadata", {})
    builder = FLOW_ID_BUILDERS.get(source)
    return builder(metadata) if builder else f"{source}:unknown"


# --- conversation title builders (one per platform) ---

def build_jira_title(metadata: dict) -> str:
    key = metadata.get("key", "unknown")
    summary = metadata.get("summary", "")
    return f"Jira: {key} - {summary}" if summary else f"Jira: {key}"


def build_github_title(metadata: dict) -> str:
    repo = metadata.get("repo", "unknown")
    number = metadata.get("number", "unknown")
    title = metadata.get("title", "")
    repo_short = repo.split("/")[-1] if "/" in repo else repo
    return f"GitHub: {repo_short}#{number} - {title}" if title else f"GitHub: {repo_short}#{number}"


def build_slack_title(metadata: dict) -> str:
    channel_name = metadata.get("channel_name", "unknown")
    text = metadata.get("text", "")
    text_preview = text[:50] + "..." if len(text) > 50 else text
    return f"Slack: #{channel_name} - {text_preview}" if text else f"Slack: #{channel_name}"


TITLE_BUILDERS = {
    "jira": build_jira_title,
    "github": build_github_title,
    "slack": build_slack_title,
}


def build_conversation_title(task: dict) -> str:
    """Generate conversation title from task data."""
    source = task.get("source", "unknown")
    metadata = task.get("source_metadata", {})
    builder = TITLE_BUILDERS.get(source)
    return builder(metadata) if builder else f"{source.title()}: Unknown"
```

**Run tests (should pass):**
```bash
PYTHONPATH=agent-engine:$PYTHONPATH uv run pytest agent-engine/tests/test_conversation_bridge.py -v
```

**Verification:** All tests PASS

**Commit:** `feat: implement flow_id and conversation_title builders`

---

### Task 3.3: Write TDD Tests for Async Functions (agent-specialist)

**Files:** `agent-engine/tests/test_conversation_bridge.py`

**Add to test file:**
```python
from unittest.mock import AsyncMock, patch
from agent_engine.services.conversation_bridge import (
    get_or_create_flow_conversation,
    fetch_conversation_context,
)


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


@pytest.mark.asyncio
async def test_fetch_conversation_context():
    with patch("agent_engine.services.conversation_bridge.httpx.AsyncClient") as mock_client:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"role": "user", "content": "Message 1"},
            {"role": "assistant", "content": "Response 1"},
        ]
        mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

        messages = await fetch_conversation_context("http://dashboard:5000", "conv-123", limit=5)
        assert len(messages) == 2
        assert messages[0]["content"] == "Message 1"
```

**Run tests (should fail):**
```bash
PYTHONPATH=agent-engine:$PYTHONPATH uv run pytest agent-engine/tests/test_conversation_bridge.py -k async -v
```

**Verification:** Tests FAIL (functions not defined)

**Commit:** `test: add failing tests for async conversation functions`

---

### Task 3.4: Implement Async Conversation Functions (agent-specialist)

**Files:** `agent-engine/services/conversation_bridge.py`

**Add to file:**
```python
import httpx


async def get_or_create_flow_conversation(dashboard_url: str, task: dict) -> str:
    """Get or create conversation for flow_id."""
    flow_id = build_flow_id(task)

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(
                f"{dashboard_url}/api/conversations/by-flow/{flow_id}"
            )
            if response.status_code == 200:
                data = response.json()
                return data["conversation_id"]
        except Exception:
            pass

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


async def fetch_conversation_context(
    dashboard_url: str,
    conversation_id: str,
    limit: int = 5
) -> list[dict]:
    """Fetch last N messages from conversation."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            f"{dashboard_url}/api/conversations/{conversation_id}/context",
            params={"max_messages": limit}
        )
        response.raise_for_status()
        return response.json()


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

**Run tests (should pass):**
```bash
PYTHONPATH=agent-engine:$PYTHONPATH uv run pytest agent-engine/tests/test_conversation_bridge.py -v
```

**Verification:** All tests PASS

**Commit:** `feat: implement async conversation bridge functions`

---

### Task 3.5: Implement Explicit System Message Functions (agent-specialist)

**Files:** `agent-engine/services/conversation_bridge.py`

**Add to file (explicit functions per webhook type):**
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

**Design Note:** Explicit functions per webhook type (no if/else routing) - follows simplicity principle

**Commit:** `feat: implement explicit system message functions per webhook type`

---

### Task 3.6: Write TDD Tests for Task Routing (agent-specialist)

**Files:** `agent-engine/tests/test_task_routing.py`

**Create file:**
```python
import pytest
from agent_engine.services.task_routing import build_prompt


def test_build_prompt_basic():
    task = {"prompt": "Fix the bug", "source": "jira", "source_metadata": {}}
    prompt = build_prompt(task)
    assert "Fix the bug" in prompt


def test_build_prompt_with_context():
    task = {"prompt": "Fix the bug", "source": "jira", "source_metadata": {}}
    context = [
        {"role": "user", "content": "Previous message 1"},
        {"role": "assistant", "content": "Previous response 1"},
    ]

    prompt = build_prompt(task, context)
    assert "Previous message 1" in prompt
    assert "Previous response 1" in prompt
    assert "Fix the bug" in prompt


def test_build_prompt_jira_instructions():
    task = {"prompt": "Analyze ticket", "source": "jira", "source_metadata": {}}
    prompt = build_prompt(task)
    assert "jira:add_jira_comment" in prompt


def test_build_prompt_github_instructions():
    task = {"prompt": "Review PR", "source": "github", "source_metadata": {}}
    prompt = build_prompt(task)
    assert "github:add_issue_comment" in prompt


def test_build_prompt_slack_instructions():
    task = {"prompt": "Answer question", "source": "slack", "source_metadata": {}}
    prompt = build_prompt(task)
    assert "slack:send_slack_message" in prompt
```

**Run tests (should fail):**
```bash
PYTHONPATH=agent-engine:$PYTHONPATH uv run pytest agent-engine/tests/test_task_routing.py -v
```

**Verification:** Tests FAIL (module not found)

**Commit:** `test: add failing tests for task routing`

---

### Task 3.7: Implement Task Routing (agent-specialist)

**Files:** `agent-engine/services/task_routing.py`

**Create file:**
```python
def build_prompt(task: dict, conversation_context: list[dict] = None) -> str:
    """Build enriched prompt with conversation history and platform instructions."""
    source = task.get("source", "unknown")
    base_prompt = task.get("prompt", "")
    metadata = task.get("source_metadata", {})

    context_section = ""
    if conversation_context:
        context_section = "\n## Previous Conversation\n\n"
        for msg in conversation_context:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            context_section += f"**{role.title()}**: {content}\n\n"

    build_context = SOURCE_CONTEXT_BUILDERS.get(source)
    source_context = build_context(metadata) if build_context else f"## Source: {source}\n"

    build_instructions = PLATFORM_INSTRUCTION_BUILDERS.get(source)
    platform_instructions = build_instructions() if build_instructions else ""

    return f"""
{source_context}

{context_section}

## Task

{base_prompt}

{platform_instructions}
""".strip()


# --- source context builders (one per platform) ---

def build_jira_source_context(metadata: dict) -> str:
    key = metadata.get("key", "unknown")
    return f"## Jira Ticket: {key}\n"


def build_github_source_context(metadata: dict) -> str:
    repo = metadata.get("repo", "unknown")
    number = metadata.get("number", "unknown")
    return f"## GitHub Issue/PR: {repo}#{number}\n"


def build_slack_source_context(metadata: dict) -> str:
    channel = metadata.get("channel_name", "unknown")
    return f"## Slack Channel: #{channel}\n"


SOURCE_CONTEXT_BUILDERS = {
    "jira": build_jira_source_context,
    "github": build_github_source_context,
    "slack": build_slack_source_context,
}


# --- platform instruction builders (one per platform) ---

def build_jira_platform_instructions() -> str:
    return """
## Response Instructions

Post your analysis as a comment on the Jira ticket using the `jira:add_jira_comment` MCP tool.
"""


def build_github_platform_instructions() -> str:
    return """
## Response Instructions

Post your response as a comment on the GitHub issue/PR using the `github:add_issue_comment` MCP tool.
"""


def build_slack_platform_instructions() -> str:
    return """
## Response Instructions

Post a summary (max 3000 chars) to the Slack thread using the `slack:send_slack_message` MCP tool.
If a PR is involved, include the PR link with a brief summary.
"""


PLATFORM_INSTRUCTION_BUILDERS = {
    "jira": build_jira_platform_instructions,
    "github": build_github_platform_instructions,
    "slack": build_slack_platform_instructions,
}
```

**Run tests (should pass):**
```bash
PYTHONPATH=agent-engine:$PYTHONPATH uv run pytest agent-engine/tests/test_task_routing.py -v
```

**Verification:** All tests PASS

**Commit:** `feat: implement task routing with conversation context`

---

### Task 3.8: Integrate into agent-engine main.py (agent-specialist)

**Files:** `agent-engine/main.py`

**Steps:**

1. **Add imports** (top of file):
```python
import time
from services import conversation_bridge, task_routing
```

2. **Add conversation flow** in `_process_task` (before `_execute_task`):
```python
# Get dashboard URL from environment
dashboard_url = os.getenv("DASHBOARD_API_URL", "http://dashboard-api:5000")

# Build flow_id from task data
flow_id = conversation_bridge.build_flow_id(task)
logger.info("webhook_flow_started", task_id=task_id, flow_id=flow_id)

# Get or create conversation
try:
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

except Exception as e:
    logger.error("conversation_bridge_failed", task_id=task_id, error=str(e))
    # Fallback to original prompt if dashboard unavailable
    enriched_prompt = task.get("prompt", "")
    conversation_id = None

# Record start time for duration tracking
start_time = time.monotonic()

# Execute task with enriched prompt
result = await self._execute_task(
    task_id=task_id,
    prompt=enriched_prompt,
    agent_dir=agent_dir,
    output_queue=output_queue
)

# Calculate duration
duration = time.monotonic() - start_time
```

**Test locally:**
```bash
docker compose logs -f agent-engine | grep "webhook_flow_started"
```

**Verification:** See flow_id generation, conversation creation, context fetch in logs

**Commit:** `feat: integrate conversation bridge into agent-engine task processing`

---

### Task 3.9: Add Failure Notification (Python-only fallback) (agent-specialist)

**Files:** `agent-engine/main.py`, `agent-engine/services/conversation_bridge.py`

**Rationale:** CLI posts responses to platforms via MCP tools autonomously.
Python only posts to platforms when CLI **fails before it can respond** (crash, timeout, etc.).

**Step 1: Add failure notification in main.py exception handler**

In `_process_task`, after CLI execution fails:

```python
except Exception as e:
    duration = time.monotonic() - start_time
    logger.error("task_execution_failed", task_id=task_id, error=str(e))

    # CLI failed - post failure notification to platform (Python fallback)
    source = task.get("source")
    metadata = task.get("source_metadata", {})
    notify_func = FAILURE_NOTIFIERS.get(source)
    if notify_func and conversation_id:
        await notify_func(dashboard_url, conversation_id, task_id, str(e))
```

**Step 2: Add failure notifier functions in conversation_bridge.py**

```python
async def notify_jira_failure(
    dashboard_url: str,
    conversation_id: str,
    task_id: str,
    error: str
) -> None:
    """Post failure message to dashboard conversation (Jira task failed)."""
    content = f"❌ **Task Failed**\n\nTask: {task_id}\nError: {error}"
    async with httpx.AsyncClient(timeout=10.0) as client:
        await client.post(
            f"{dashboard_url}/api/conversations/{conversation_id}/messages",
            json={"role": "system", "content": content}
        )


async def notify_github_failure(
    dashboard_url: str,
    conversation_id: str,
    task_id: str,
    error: str
) -> None:
    """Post failure message to dashboard conversation (GitHub task failed)."""
    content = f"❌ **Task Failed**\n\nTask: {task_id}\nError: {error}"
    async with httpx.AsyncClient(timeout=10.0) as client:
        await client.post(
            f"{dashboard_url}/api/conversations/{conversation_id}/messages",
            json={"role": "system", "content": content}
        )


async def notify_slack_failure(
    dashboard_url: str,
    conversation_id: str,
    task_id: str,
    error: str
) -> None:
    """Post failure message to dashboard conversation (Slack task failed)."""
    content = f"❌ **Task Failed**\n\nTask: {task_id}\nError: {error}"
    async with httpx.AsyncClient(timeout=10.0) as client:
        await client.post(
            f"{dashboard_url}/api/conversations/{conversation_id}/messages",
            json={"role": "system", "content": content}
        )


FAILURE_NOTIFIERS = {
    "jira": notify_jira_failure,
    "github": notify_github_failure,
    "slack": notify_slack_failure,
}
```

**Key principle:** These only post to the **dashboard conversation** (internal).
The CLI is responsible for posting to the **external platform** (Jira/GitHub/Slack) via MCP tools.

**Commit:** `feat: add failure notification fallback for crashed tasks`

---

## Phase 4: WebSocket Streaming (Real-time Updates)

**Objective:** Push task events to frontend in real-time
**Owner:** backend-specialist
**Depends on:** Phase 1 (event logging)

### Task 4.1: Create WebSocket Endpoint (backend-specialist)

**Files:** `dashboard-api/websocket.py` (new file)

**Create file:**
```python
import asyncio
import json
from fastapi import WebSocket, WebSocketDisconnect
from redis import asyncio as aioredis
import structlog

logger = structlog.get_logger()


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("websocket_connected", total_connections=len(self.active_connections))

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info("websocket_disconnected", total_connections=len(self.active_connections))

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error("websocket_send_failed", error=str(e))


manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time task updates."""
    await manager.connect(websocket)

    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


async def redis_stream_listener():
    """Listen to Redis stream and broadcast to WebSocket clients."""
    redis_url = "redis://redis:6379"
    redis_client = await aioredis.from_url(redis_url)

    stream_key = "task_events"
    last_id = "0-0"

    logger.info("redis_stream_listener_started", stream_key=stream_key)

    while True:
        try:
            # Read from Redis stream
            streams = await redis_client.xread(
                {stream_key: last_id},
                block=1000,
                count=10
            )

            for stream_name, messages in streams:
                for message_id, data in messages:
                    last_id = message_id

                    # Parse event
                    event_type = data.get(b"event_type", b"").decode("utf-8")
                    event_data = json.loads(data.get(b"data", b"{}").decode("utf-8"))

                    # Broadcast to all WebSocket clients
                    await manager.broadcast({
                        "event_type": event_type,
                        "data": event_data,
                    })

                    logger.debug("event_broadcasted", event_type=event_type)

        except Exception as e:
            logger.error("redis_stream_error", error=str(e))
            await asyncio.sleep(1)
```

**Verification:** File created, no syntax errors

---

### Task 4.2: Mount WebSocket Route (backend-specialist)

**Files:** `dashboard-api/main.py`

**Steps:**

1. **Add import:**
```python
from websocket import websocket_endpoint, redis_stream_listener
```

2. **Mount WebSocket route:**
```python
@app.websocket("/ws")
async def websocket_route(websocket: WebSocket):
    await websocket_endpoint(websocket)
```

3. **Start background task:**
```python
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(redis_stream_listener())
```

**Test with websocat:**
```bash
websocat ws://localhost:5000/ws
```

**Verification:** WebSocket connects, receives events when tasks run

**Commit:** `feat: add WebSocket endpoint for real-time task streaming`

---

## Phase 5: Frontend UI (Dashboard Updates)

**Objective:** Display webhook conversations and stream task output
**Owner:** frontend-specialist
**Depends on:** Phase 2 (conversation API), Phase 4 (WebSocket)

### Task 5.1: Create WebSocket Hook (frontend-specialist)

**Files:** `external-dashboard/src/hooks/useWebSocket.ts` (new file)

**Create file:**
```typescript
import { useEffect, useRef, useState } from 'react';

export function useWebSocket(url: string) {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<any>(null);
  const ws = useRef<WebSocket | null>(null);

  useEffect(() => {
    const connect = () => {
      ws.current = new WebSocket(url);

      ws.current.onopen = () => {
        setIsConnected(true);
        console.log('WebSocket connected');
      };

      ws.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        setLastMessage(data);
      };

      ws.current.onclose = () => {
        setIsConnected(false);
        console.log('WebSocket disconnected, reconnecting...');
        setTimeout(connect, 3000);
      };

      ws.current.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
    };

    connect();

    return () => {
      ws.current?.close();
    };
  }, [url]);

  return { isConnected, lastMessage };
}
```

**Verification:** Hook compiles, no TypeScript errors

---

### Task 5.2: Create Task Stream Hook (frontend-specialist)

**Files:** `external-dashboard/src/hooks/useTaskStream.ts` (new file)

**Create file:**
```typescript
import { useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useWebSocket } from './useWebSocket';

export function useTaskStream() {
  const queryClient = useQueryClient();
  const { lastMessage } = useWebSocket('ws://localhost:5000/ws');

  useEffect(() => {
    if (!lastMessage) return;

    const { event_type, data } = lastMessage;

    if (event_type === 'task:created') {
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
    }

    if (event_type === 'task:completed') {
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
      queryClient.invalidateQueries({ queryKey: ['task', data.task_id] });
    }

    if (event_type === 'task:output') {
      // Update task output in cache
      queryClient.setQueryData(['task', data.task_id, 'output'], (old: string) => {
        return (old || '') + data.chunk;
      });
    }
  }, [lastMessage, queryClient]);

  return { lastMessage };
}
```

**Verification:** Hook compiles, no TypeScript errors

---

### Task 5.3: Create Conversation Query Hooks (frontend-specialist)

**Files:** `external-dashboard/src/hooks/useConversations.ts` (new file)

**Create file:**
```typescript
import { useQuery } from '@tanstack/react-query';

interface Conversation {
  conversation_id: string;
  flow_id: string;
  title: string;
  source: string;
  created_at: string;
}

export function useConversations() {
  return useQuery({
    queryKey: ['conversations'],
    queryFn: async () => {
      const response = await fetch('/api/conversations');
      if (!response.ok) throw new Error('Failed to fetch conversations');
      return response.json() as Promise<Conversation[]>;
    },
  });
}

export function useConversationMessages(conversationId: string | null) {
  return useQuery({
    queryKey: ['conversations', conversationId, 'messages'],
    queryFn: async () => {
      if (!conversationId) return [];
      const response = await fetch(`/api/conversations/${conversationId}/messages`);
      if (!response.ok) throw new Error('Failed to fetch messages');
      return response.json();
    },
    enabled: !!conversationId,
  });
}
```

**Verification:** Hooks compile, no TypeScript errors

---

### Task 5.4: Add GET /api/conversations List Endpoint (backend-specialist)

**Files:** `dashboard-api/api/dashboard.py`

**Add endpoint:**
```python
@router.get("/api/conversations")
async def list_conversations(
    limit: int = 50,
    db=Depends(get_db_session)
):
    """List all conversations."""
    result = await db.execute(
        select(ConversationDB)
        .order_by(ConversationDB.created_at.desc())
        .limit(limit)
    )
    conversations = result.scalars().all()

    return [
        {
            "conversation_id": conv.conversation_id,
            "flow_id": conv.flow_id,
            "title": conv.title,
            "source": conv.source,
            "created_at": conv.created_at.isoformat(),
        }
        for conv in conversations
    ]
```

**Commit:** `feat: add GET /api/conversations list endpoint`

---

### Task 5.5: Add GET /api/conversations/{id}/messages Endpoint (backend-specialist)

**Files:** `dashboard-api/api/dashboard.py`

**Add endpoint:**
```python
@router.get("/api/conversations/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: str,
    db=Depends(get_db_session)
):
    """Get all messages in conversation."""
    result = await db.execute(
        select(ConversationMessageDB)
        .where(ConversationMessageDB.conversation_id == conversation_id)
        .order_by(ConversationMessageDB.created_at.asc())
    )
    messages = result.scalars().all()

    return [
        {
            "message_id": msg.message_id,
            "role": msg.role,
            "content": msg.content,
            "created_at": msg.created_at.isoformat(),
        }
        for msg in messages
    ]
```

**Commit:** `feat: add GET /api/conversations/{id}/messages endpoint`

---

### Task 5.6: Create ConversationList Component (frontend-specialist)

**Files:** `external-dashboard/src/components/ConversationList.tsx` (new file)

**Create component:**
```typescript
import { useConversations } from '../hooks/useConversations';

export function ConversationList() {
  const { data: conversations, isLoading } = useConversations();

  if (isLoading) return <div>Loading...</div>;

  return (
    <div className="conversation-list">
      <h2>Conversations</h2>
      {conversations?.map((conv) => (
        <div key={conv.conversation_id} className="conversation-item">
          <div className="conversation-title">{conv.title}</div>
          <div className="conversation-source">
            {conv.source === 'jira' && '🎫 Jira'}
            {conv.source === 'github' && '🐙 GitHub'}
            {conv.source === 'slack' && '💬 Slack'}
          </div>
          <div className="conversation-time">
            {new Date(conv.created_at).toLocaleString()}
          </div>
        </div>
      ))}
    </div>
  );
}
```

**Verification:** Component renders, shows conversations

---

### Task 5.7: Create TaskDetailModal Component (frontend-specialist)

**Files:** `external-dashboard/src/components/TaskDetailModal.tsx` (new file)

**Create component:**
```typescript
import { useQuery } from '@tanstack/react-query';
import { useTaskStream } from '../hooks/useTaskStream';

interface TaskDetailModalProps {
  taskId: string;
  onClose: () => void;
}

export function TaskDetailModal({ taskId, onClose }: TaskDetailModalProps) {
  const { data: logs } = useQuery({
    queryKey: ['task', taskId, 'logs'],
    queryFn: async () => {
      const response = await fetch(`/api/tasks/${taskId}/logs`);
      if (!response.ok) throw new Error('Failed to fetch logs');
      return response.json();
    },
  });

  useTaskStream(); // Subscribe to real-time updates

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Task: {taskId}</h2>
          <button onClick={onClose}>✕</button>
        </div>
        <div className="modal-body">
          <pre className="task-output">{logs?.output || 'Loading...'}</pre>
        </div>
      </div>
    </div>
  );
}
```

**Verification:** Modal opens, shows task output, streams updates

---

### Task 5.8: Update Chat Page (frontend-specialist)

**Files:** `external-dashboard/src/pages/Chat.tsx`

**Update to include ConversationList:**
```typescript
import { ConversationList } from '../components/ConversationList';
import { useTaskStream } from '../hooks/useTaskStream';

export function Chat() {
  useTaskStream(); // Subscribe to real-time updates

  return (
    <div className="chat-page">
      <h1>Conversations</h1>
      <ConversationList />
    </div>
  );
}
```

**Verification:** Chat page shows webhook conversations

**Commit:** `feat: add conversation UI components for webhook tasks`

---

## Phase 6: Testing & Documentation

**Objective:** Verify everything works and document the system
**Owner:** testing-specialist, all specialists
**Depends on:** All previous phases

### Task 6.1: Run All Unit Tests (testing-specialist)

**Commands:**
```bash
# Agent-engine tests
PYTHONPATH=agent-engine:$PYTHONPATH uv run pytest agent-engine/tests/ -v

# Dashboard-api tests
cd dashboard-api && uv run pytest tests/ -v
```

**Verification:** All tests PASS

---

### Task 6.2: End-to-End Test - Jira Webhook (testing-specialist)

**Steps:**
1. Rebuild services: `docker compose down && docker compose up -d --build`
2. Verify bind mount: `ls ./data/logs/tasks/`
3. Trigger Jira webhook by assigning ai-agent to ticket KAN-6
4. Check dashboard Chat view - should see conversation "Jira: KAN-6 - ..."
5. Check Ledger - should see task with duration, cost
6. Click task - modal should show full output (not truncated)
7. Check Jira ticket - should have comment from agent via MCP
8. Check host logs: `ls ./data/logs/tasks/{task-id}/`
9. Trigger same ticket again - should reuse same conversation

**Verification:** All steps pass

---

### Task 6.3: End-to-End Test - GitHub Webhook (testing-specialist)

**Steps:**
1. Trigger GitHub webhook by mentioning ai-agent in issue
2. Check dashboard Chat view - should see conversation "GitHub: repo#42 - ..."
3. Check GitHub issue - should have comment from agent
4. Verify WebSocket updates in browser console

**Verification:** All steps pass

---

### Task 6.4: End-to-End Test - Slack Webhook (testing-specialist)

**Steps:**
1. Trigger Slack webhook by mentioning ai-agent
2. Check dashboard Chat view - should see conversation "Slack: #channel - ..."
3. Check Slack thread - should have response from agent
4. Verify WebSocket updates

**Verification:** All steps pass

---

### Task 6.5: Verify MCP Tools (testing-specialist)

**Files:** `agent-engine/.claude/mcp.json`

**Steps:**
1. Read MCP config: `cat agent-engine/.claude/mcp.json`
2. Verify GitHub MCP server configured
3. Verify Jira MCP server configured
4. Verify Slack MCP server configured
5. Test each MCP tool manually if possible

**Verification:** All MCP servers configured and working

---

### Task 6.6: Update Documentation (all specialists)

**Files:**
- `.claude/rules/microservices.md`
- `docs/webhook-integration-guide.md` (new)

**Add to microservices.md:**
```markdown
## Webhook Integration

Webhooks from Jira, GitHub, and Slack create conversations in the dashboard:

**Flow:**
1. Webhook received by API Gateway
2. Task queued in Redis
3. Agent-engine picks up task
4. Generates flow_id: `jira:KAN-6`, `github:repo#42`, `slack:channel:thread`
5. Gets or creates conversation via flow_id
6. Fetches last 5 messages for context
7. Enriches prompt with conversation history
8. Executes task via CLI
9. Posts response via MCP tools (jira:add_jira_comment, etc)
10. Streams output to dashboard via WebSocket

**API Endpoints:**
- `GET /api/conversations` - List all conversations
- `GET /api/conversations/by-flow/{flow_id}` - Find by flow_id
- `POST /api/conversations` - Create conversation
- `POST /api/conversations/{id}/messages` - Add message
- `GET /api/conversations/{id}/context` - Get last N messages
- `POST /api/tasks` - Register external task
- `GET /api/tasks/{id}/logs` - Get task logs with fallback
- `WS /ws` - WebSocket for real-time task updates
```

**Create webhook-integration-guide.md:**
```markdown
# Webhook Integration Guide

## Overview

Groote AI integrates with Jira, GitHub, and Slack webhooks to provide AI assistance on platform-native tasks.

## How It Works

### 1. Conversation Reuse

Each webhook source creates a unique flow_id:
- Jira: `jira:KAN-6`
- GitHub: `github:owner/repo#42`
- Slack: `slack:C12345:1234567890.123456`

Multiple webhook triggers with the same flow_id reuse the same conversation, providing context continuity.

### 2. Context Awareness

Before task execution, the agent fetches the last 5 messages from the conversation to understand context.

### 3. Platform Instructions

The agent receives platform-specific instructions:
- Jira: Post comment via `jira:add_jira_comment`
- GitHub: Post comment via `github:add_issue_comment`
- Slack: Post summary via `slack:send_slack_message`

### 4. Real-time Streaming

Task output streams to the dashboard via WebSocket, allowing users to see progress in real-time.

## Troubleshooting

**Conversation not created:**
- Check dashboard-api logs: `docker compose logs dashboard-api | grep conversation`
- Verify database tables exist: `psql $POSTGRES_URL -c "SELECT * FROM conversations LIMIT 1;"`

**Context not fetched:**
- Check agent-engine logs: `docker compose logs agent-engine | grep context_fetched`
- Verify conversation has messages: `psql $POSTGRES_URL -c "SELECT * FROM conversation_messages WHERE conversation_id='...';"`

**Output truncated:**
- Verify agent-engine has no `[:5000]` truncation
- Check task-logger logs for full result

**MCP tools not working:**
- Verify MCP config: `cat agent-engine/.claude/mcp.json`
- Check agent-engine logs for MCP errors
```

**Commit:** `docs: add webhook integration documentation`

---

## Final Verification Checklist

**Phase 0: Pre-requisites:**
- [ ] Stale `sentry` removed from `agent-engine/.claude/mcp.json`
- [ ] Docker .claude setup verified - skills/agents/mcp.json come from `agent-engine/.claude/`, NOT `~/.claude/`
- [ ] MCP servers reachable from CLI container (jira-mcp:9002, slack-mcp:9003)
- [ ] OAuth token flow works (API services → OAuth service → tokens)
- [ ] CLI can list MCP tools inside container (`jira:add_jira_comment`, `slack:send_slack_message`, etc.)
- [ ] CLI response strategy documented (CLI posts to platforms, Python only for failures)

**Phase 1-3: Backend:**
- [ ] All unit tests pass
- [ ] Docker bind mount works - `./data/logs/tasks/` visible on host
- [ ] Conversation API endpoints respond correctly
- [ ] Conversation bridge creates/reuses conversations by flow_id

**Phase 4-5: Frontend + Streaming:**
- [ ] WebSocket connects and receives task events
- [ ] Chat view shows webhook conversations with correct titles
- [ ] Task detail modal shows full output (not truncated)
- [ ] Output streams in real-time via WebSocket

**End-to-End:**
- [ ] Jira webhook → conversation created → CLI executes → CLI posts comment to Jira via MCP
- [ ] GitHub webhook → conversation created → CLI executes → CLI posts comment to GitHub via MCP
- [ ] Slack webhook → conversation created → CLI executes → CLI posts message to Slack via MCP
- [ ] Same webhook flow reuses same conversation (flow_id matching)
- [ ] Tasks appear in Ledger with status, cost, duration
- [ ] Task logs on host have all files with correct data
- [ ] Failed task → Python fallback posts failure notification to dashboard
- [ ] Documentation updated and accurate

---

## Rollback Plan

**If critical issues occur:**

1. **Revert bind mount:**
   ```bash
   git revert <commit-hash>  # Revert docker-compose.yml changes
   docker compose down && docker compose up -d
   ```

2. **Revert agent-engine integration:**
   ```bash
   git revert <commit-hash>  # Revert agent-engine/main.py changes
   docker compose restart agent-engine
   ```

3. **Revert dashboard-api changes:**
   ```bash
   git revert <commit-hash>  # Revert dashboard-api/api/dashboard.py changes
   docker compose restart dashboard-api
   ```

4. **Full rollback:**
   ```bash
   git reset --hard HEAD~N  # N = number of commits to revert
   docker compose down && docker compose up -d --build
   ```

**Critical files to backup before starting:**
- `docker-compose.yml`
- `agent-engine/main.py`
- `dashboard-api/api/dashboard.py`
- `external-dashboard/src/` (entire directory)

---

## Execution Strategy

### Option 1: Sequential Execution (Solo Developer)

Execute phases 1-6 in order, tasks within each phase sequentially.

**Estimated time:** 4-5 days

### Option 2: Parallel Team Execution (Recommended)

**Use agent teams with brain as coordinator:**

```bash
# From Claude Code CLI
/superpowers:executing-plans
```

**Team assignments:**
- Phase 0: agent-specialist (FIRST - verify MCP, Docker, OAuth)
- Phase 1: database-specialist + agent-specialist (parallel with Phase 0)
- Phase 2: backend-specialist (depends on Phase 1)
- Phase 3: agent-specialist (depends on Phase 0 + Phase 2)
- Phase 4: backend-specialist (parallel with Phase 3, depends on Phase 1)
- Phase 5: frontend-specialist (depends on Phase 2 + 4)
- Phase 6: testing-specialist (depends on all phases)

**Estimated time:** 1 day

---

## Success Metrics

**Integration is successful when:**
1. ✅ Webhook triggers visible in dashboard within 1 second
2. ✅ Conversations reused correctly (same flow_id = same conversation)
3. ✅ Full output visible (no truncation)
4. ✅ Real-time streaming works in browser
5. ✅ Agent posts to correct platform via MCP tools
6. ✅ All tests pass
7. ✅ Documentation complete and accurate

---

**Plan Status:** ✅ Ready for Execution
**Last Updated:** 2026-02-10
**Author:** Brain (Team Lead) + Claude Code
