# Plan: Full Webhook-to-Dashboard Integration

## Context

Webhook tasks (Jira, GitHub, Slack) execute successfully but are invisible in the dashboard. Multiple gaps:

1. **No TaskDB record** — webhook tasks bypass `POST /api/chat` where TaskDB is created
2. **No conversation** — no `conversation_id`, so nothing in Chat view
3. **No CLI output streaming** — output never written to Redis `task:{id}:output`
4. **Logs not on host** — `task_logs` is a Docker named volume, not a bind mount
5. **Agent responses** — the engine currently posts to Slack ops channel, but ALL substantive responses to source platforms (Jira, GitHub, Slack) must be done by the agent itself via MCP tools (the agents already have these instructions)
6. **No conversation context** — CLI doesn't get prior flow messages, so agents lack context

## Phase 0: Fix Task-Logger Data Gaps (IMMEDIATE)

Two bugs cause null data in task-logger log files:

### Bug 1: `01-input.json` → `"message": null`

**Root cause**: Agent-engine publishes `task:started` but never `task:created`. The task-logger expects `task:created` with an `input_message` field. Dashboard-api publishes `task:created` but omits `input_message`.

**Fix A** — `agent-engine/main.py` `_process_task` (add before `task:started` event, ~line 59):
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

**Fix B** — `dashboard-api/api/dashboard.py` line 461: Add `"input_message": full_input_message` to the existing `task:created` event data.

### Bug 2: `06-final-result.json` → `"result": null`, `"duration_seconds": null`

**Root cause**: Agent-engine's `task:completed` event (line 81-92) sends `cost_usd`, `input_tokens`, `output_tokens` but NOT `result` or `duration_seconds`. No duration tracking exists.

**Fix** — `agent-engine/main.py` `_process_task`:
1. Record `start_time = time.monotonic()` before `_execute_task`
2. Calculate `duration = time.monotonic() - start_time` after
3. Add to `task:completed` event data:
```python
"result": result.get("output", "")[:5000],
"duration_seconds": round(duration, 2),
```

### Files to change:
- `agent-engine/main.py` — add `task:created` event + duration tracking + result in completed event
- `dashboard-api/api/dashboard.py` — add `input_message` to existing `task:created` event

---

## Phase 1: Docker Volume Bind Mount

**File: `docker-compose.yml`** (line ~278 and ~477)

Change task-logger volume from named volume to bind mount:
```yaml
# Before
task-logger:
  volumes:
    - task_logs:/data/logs/tasks
# ...
volumes:
  task_logs:

# After
task-logger:
  volumes:
    - ./data/logs/tasks:/data/logs/tasks
# Remove task_logs from named volumes
```

This makes `/data/logs/tasks/` visible at `./data/logs/tasks/` on the host machine.

## Phase 2: Dashboard-API Task Creation Endpoint

**File: `dashboard-api/api/dashboard.py`** (ADD ~40 lines)

Add `POST /api/tasks` endpoint for external task registration. Handles the `session_id` FK requirement by auto-creating a `webhook-system` session if needed.

```python
@router.post("/api/tasks")
async def create_external_task(payload: ExternalTaskCreate, db=Depends(get_db_session)):
    # Ensure webhook-system session exists (create if not)
    # Create TaskDB with source="webhook", flow_id, conversation_id in source_metadata
    # Return task_id + conversation_id
```

Model:
```python
class ExternalTaskCreate(BaseModel):
    task_id: str
    source: str                              # "jira", "github", "slack"
    source_metadata: dict                    # platform-specific context
    input_message: str
    assigned_agent: str = "brain"
    conversation_id: str | None = None       # Link to existing conversation
    flow_id: str | None = None               # For grouping tasks in same flow
```

## Phase 3: Conversation Bridge (agent-engine)

**File: `agent-engine/services/conversation_bridge.py`** (CREATE, ~120 lines)

Functions:
- `get_or_create_flow_conversation(dashboard_url, task)` — checks if `flow_id` already has a conversation, reuses it; otherwise creates new one
- `register_task(dashboard_url, task, conversation_id)` — POST `/api/tasks` to create TaskDB
- `post_system_message(dashboard_url, conversation_id, task)` — posts formatted webhook context as system message
- `fetch_conversation_context(dashboard_url, conversation_id, limit=5)` — GET `/api/conversations/{id}/context?max_messages=5`
- `build_conversation_title(task)` — "Jira: KAN-6 - Fix login bug" / "GitHub: repo#42 - Add feature" / "Slack: #channel - question"
- `build_flow_id(task)` — deterministic: `{source}:{unique_key}` (e.g., `jira:KAN-6`, `github:owner/repo#42`, `slack:channel:thread_ts`)

Flow ID logic ensures same Jira ticket or same GitHub issue/PR reuses the same conversation across multiple webhook events.

## Phase 4: Enhance build_prompt with Conversation Context

**File: `agent-engine/services/task_routing.py`** (MODIFY, ~60 lines total)

Update `build_prompt()` to accept conversation context (last 5 messages) and include platform-specific response instructions:

```python
def build_prompt(task: dict, conversation_context: str = "") -> str:
```

**Jira tasks**: Include issue key, prompt, conversation context, instruction to post via `jira:add_jira_comment`

**GitHub tasks**:
- Issue/comment: post analysis via `github:add_issue_comment`
- PR opened (from Jira): post solution summary via `github:add_issue_comment`
- PR comment: post detailed response via `github:add_issue_comment`

**Slack tasks**: Post summary only via `slack:send_slack_message` with `thread_ts`. Keep under 3000 chars. If PR involved, include link with summary.

**All sources**: If user @mentions agent name with a command, execute that command and respond.

The agents already have detailed instructions in `.claude/agents/` for each platform. The prompt just needs to provide:
1. Source context (issue key, PR number, etc.)
2. Conversation history (last 5 messages)
3. The actual task prompt
4. Reminder to post response back via MCP tools

## Phase 5: Modify agent-engine _process_task

**File: `agent-engine/main.py`** (MODIFY `_process_task`, ~30 lines changed)

Before CLI execution:
```
1. Build flow_id from task data
2. Get or create conversation via conversation_bridge
3. Register task in dashboard-api via POST /api/tasks
4. Post system message with webhook context
5. Fetch last 5 messages from conversation for context
6. Build enriched prompt with context + platform instructions
```

After CLI completion:
```
1. Write full output to Redis task:{id}:output (for dashboard streaming)
2. Post assistant message to dashboard conversation (for Chat view)
3. Update task status to completed with metrics
```

On failure:
```
1. Post error to dashboard conversation
2. Notify ops Slack channel (existing _notify_platform_failure)
```

Key change: Remove `_notify_ops_completion` for SUCCESS cases — the agent itself posts to source platforms via MCP tools. Keep failure notifications from engine since failed agents can't post.

## Phase 6: Stream CLI Output to Redis

**File: `agent-engine/main.py`** (in `_process_task` after `_execute_task`)

Write the full CLI output to Redis for dashboard streaming:
```python
if result.get("output"):
    await self._redis.set(f"task:{task_id}:output", result["output"][:50000], ex=3600)
```

Also update TaskDB output_stream field via dashboard-api.

## Phase 7: Dashboard-API Task-Logger Fallback

**File: `dashboard-api/api/dashboard.py`** (MODIFY `get_task_logs`, ~15 lines)

When task has no output in Redis, fetch from task-logger service:
```
GET http://task-logger:8090/tasks/{task_id}/logs
```

Add `TASK_LOGGER_URL` to dashboard-api config.

## Phase 8: Tests

**File: `agent-engine/tests/test_conversation_bridge.py`** (CREATE, ~120 lines)
- flow_id generation for Jira/GitHub/Slack
- Conversation title building
- Conversation reuse when flow_id exists
- HTTP mocking for dashboard-api calls
- Context fetching with message limit

**File: `agent-engine/tests/test_task_routing.py`** (CREATE, ~80 lines)
- Prompt building with conversation context
- Platform-specific instructions in prompt
- @mention handling in prompt

## Files Summary

| File | Action | ~Lines |
|------|--------|--------|
| `docker-compose.yml` | MODIFY | 3 |
| `dashboard-api/api/dashboard.py` | MODIFY | +40 |
| `agent-engine/services/conversation_bridge.py` | CREATE | 120 |
| `agent-engine/services/task_routing.py` | MODIFY | 60 total |
| `agent-engine/main.py` | MODIFY | ~35 changed |
| `agent-engine/tests/test_conversation_bridge.py` | CREATE | 120 |
| `agent-engine/tests/test_task_routing.py` | CREATE | 80 |

## Flow After Implementation

```
Webhook → API Gateway → Redis queue
  → Agent Engine picks up task
  → Builds flow_id (jira:KAN-6)
  → Gets/creates conversation (reuses if flow exists)         [NEW]
  → Registers TaskDB via POST /api/tasks                      [NEW]
  → Posts system message (webhook context)                     [NEW]
  → Fetches last 5 messages for context                       [NEW]
  → Builds enriched prompt (context + platform instructions)   [ENHANCED]
  → Executes CLI (agent uses MCP tools to respond to source)   [AGENT HANDLES]
  → Writes output to Redis task:{id}:output                   [NEW]
  → Posts result to dashboard conversation                     [NEW]
  → Updates TaskDB status + metrics                           [NEW]
```

## Where to See Data

| What | Where |
|------|-------|
| Conversations | Dashboard Chat — auto-created per webhook flow |
| Task list | Dashboard Ledger — TaskDB created by engine |
| CLI output stream | Ledger → task detail modal → Redis output |
| Webhook process data | `./data/logs/tasks/{id}/` on host machine |
| Detailed logs | task-logger API or dashboard fallback |
| Platform responses | On Jira/GitHub/Slack — posted by agent via MCP |

## Verification

1. `docker compose down && docker compose up -d --build --force-recreate`
2. Verify `./data/logs/tasks/` directory exists on host
3. Trigger Jira webhook (assign ai-agent to KAN-6)
4. Dashboard Chat: conversation "Jira: KAN-6 - ..." with system + assistant messages
5. Dashboard Ledger: task in table with status, cost, duration
6. Click task: modal shows CLI output stream
7. Jira ticket: agent posted comment via MCP tools
8. Host machine: `ls ./data/logs/tasks/` shows task directory with log files
9. Same Jira ticket triggers again: reuses same conversation (same flow_id)
10. Tests: `PYTHONPATH=agent-engine:$PYTHONPATH uv run pytest agent-engine/tests/test_conversation_bridge.py agent-engine/tests/test_task_routing.py -v`
