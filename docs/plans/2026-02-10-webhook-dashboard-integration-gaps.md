# Webhook-Dashboard Integration Plan - Gap Analysis

## Missing from Original Plan

### 1. Dashboard API - Missing Conversation Endpoints ⚠️ CRITICAL

**Referenced but not implemented:**

```python
# Task 8 references these endpoints but they don't exist:
GET /api/conversations/by-flow/{flow_id}  # Check if conversation exists
POST /api/conversations                   # Create new conversation
POST /api/conversations/{id}/messages     # Post system/user messages
```

**Required endpoints:**
- `GET /api/conversations/by-flow/{flow_id}` - Find conversation by flow_id
- `POST /api/conversations` - Create conversation with flow_id, title, source
- `POST /api/conversations/{id}/messages` - Add message to conversation
- `GET /api/conversations/{id}/messages` - List messages (for frontend)
- `GET /api/conversations` - List all conversations (for Chat view)

### 2. WebSocket Streaming ⚠️ CRITICAL

**Goal says "real-time streaming" but plan has:**
- ❌ No WebSocket endpoint in dashboard-api
- ❌ No Redis stream subscription forwarding
- ❌ No frontend WebSocket client
- ❌ No task status updates pushed to frontend

**Required:**
- `dashboard-api/websocket.py` - WebSocket endpoint at `/ws`
- Redis stream subscription (`XREAD` from task-logger stream)
- Forward task events to connected WebSocket clients
- Frontend: WebSocket hook + subscription to task updates

### 3. Frontend Dashboard Updates ⚠️ CRITICAL

**Completely missing - no frontend work planned:**

**Chat View:**
- Display webhook conversations alongside manual conversations
- Show conversation title (Jira: KAN-6, GitHub: repo#42, etc)
- Show system messages (webhook triggered context)
- Show user messages (task prompts)
- Show assistant responses (CLI output)

**Ledger View:**
- Show webhook tasks with source badge (Jira/GitHub/Slack)
- Click task to open modal with full output
- Show duration, cost, tokens
- Link to conversation

**Task Detail Modal:**
- Stream output in real-time (via WebSocket)
- Show status updates (pending → running → completed)
- Show full output (not truncated)
- Link to source (Jira ticket, GitHub PR, Slack thread)

**Components needed:**
- `ConversationList.tsx` - List conversations in Chat
- `ConversationThread.tsx` - Show messages in conversation
- `TaskDetailModal.tsx` - Full task output modal
- `useWebSocket.ts` - WebSocket subscription hook
- `useTaskStream.ts` - Subscribe to task updates

### 4. MCP Tool Verification

**Plan assumes MCP tools work but doesn't verify:**
- ❌ No check that `agent-engine/.claude/mcp.json` has GitHub, Jira, Slack
- ❌ No test that GitHub MCP tools work (`github:add_issue_comment`)
- ❌ No test that Jira MCP tools work (`jira:add_jira_comment`)
- ❌ No test that Slack MCP tools work (`slack:send_slack_message`)
- ❌ No error handling for MCP failures

**Required:**
- Verify MCP servers configured
- Test each MCP tool with mock data
- Add error handling for MCP failures
- Fallback behavior if MCP unavailable

### 5. Error Handling

**No error handling for:**
- Dashboard-api down during task execution
- Conversation creation fails
- Context fetch fails
- Task registration fails
- MCP tool calls fail
- Redis unavailable

**Required:**
- Graceful degradation if dashboard unavailable
- Retry logic for transient failures
- Error messages back to dashboard
- Task status: "failed" with error details

### 6. Documentation

**No tasks for:**
- Updating `.claude/rules/microservices.md`
- API documentation for new endpoints
- User-facing guide for webhook flows
- Troubleshooting guide

### 7. Database Schema

**Missing:**
- Do `conversations` and `conversation_messages` tables exist?
- Does `tasks` table have `conversation_id` column?
- Migration needed?

### 8. Agent Response Posting

**Plan says "delegates all platform responses to CLI via MCP tools" but:**
- No verification that CLI has access to MCP servers
- No test that CLI can call MCP tools
- No verification that responses actually post

---

## Micro-Task Breakdown for Agent Teams

### Team Structure

**Team Lead:**
- `brain` - Coordinates, reviews, integrates

**Specialists:**
- `agent-engine-specialist` - Owns `agent-engine/` changes
- `dashboard-api-specialist` - Owns `dashboard-api/` changes
- `frontend-specialist` - Owns `external-dashboard/` changes
- `testing-specialist` - Writes and runs tests
- `documentation-specialist` - Updates docs

---

## Workstream 1: Event Logging (agent-engine-specialist)

**Owner:** agent-engine-specialist
**Files:** `agent-engine/main.py`, `docker-compose.yml`

### Tasks:
1.1. Add `task:created` event with `input_message` field
1.2. Add duration tracking to `_process_task`
1.3. Add `task:completed` event with `duration_seconds` and full `result`
1.4. Remove output truncation from Redis storage
1.5. Change docker-compose to bind mount for task-logger
1.6. Test event flow with `docker compose logs -f task-logger`
1.7. Commit: "fix: add complete event logging with duration and full output"

**Dependencies:** None
**Verification:** See events in task-logger logs, files in `./data/logs/tasks/`

---

## Workstream 2: Conversation API (dashboard-api-specialist)

**Owner:** dashboard-api-specialist
**Files:** `dashboard-api/api/dashboard.py`, `dashboard-api/database/models.py`

### Tasks:
2.1. Verify `conversations` and `conversation_messages` tables exist (or create)
2.2. Add Pydantic models: `ConversationCreate`, `MessageCreate`
2.3. Implement `POST /api/conversations` endpoint
2.4. Implement `GET /api/conversations/by-flow/{flow_id}` endpoint
2.5. Implement `POST /api/conversations/{id}/messages` endpoint
2.6. Implement `GET /api/conversations/{id}/messages` endpoint
2.7. Implement `GET /api/conversations` list endpoint
2.8. Add `POST /api/tasks` endpoint for external task registration
2.9. Add `GET /api/conversations/{id}/context` endpoint
2.10. Add `GET /api/tasks/{id}/logs` with task-logger fallback
2.11. Fix `task:created` event to include `input_message`
2.12. Test all endpoints with curl
2.13. Commit: "feat: add conversation API endpoints for webhook integration"

**Dependencies:** None
**Verification:** All curl tests pass, endpoints return expected data

---

## Workstream 3: Conversation Bridge (agent-engine-specialist)

**Owner:** agent-engine-specialist
**Files:** `agent-engine/services/conversation_bridge.py`, `agent-engine/tests/test_conversation_bridge.py`

### Tasks:
3.1. Write TDD tests for `build_flow_id` (Jira, GitHub, Slack)
3.2. Implement `build_flow_id` function
3.3. Write TDD tests for `build_conversation_title`
3.4. Implement `build_conversation_title` function
3.5. Run tests - verify they pass
3.6. Write TDD tests for `get_or_create_flow_conversation` (async)
3.7. Implement `get_or_create_flow_conversation` function
3.8. Write TDD tests for `fetch_conversation_context` (async)
3.9. Implement `fetch_conversation_context` function
3.10. Implement `register_task` function
3.11. Write TDD tests for `post_jira_system_message`
3.12. Implement `post_jira_system_message` (explicit function)
3.13. Write TDD tests for `post_github_system_message`
3.14. Implement `post_github_system_message` (explicit function)
3.15. Write TDD tests for `post_slack_system_message`
3.16. Implement `post_slack_system_message` (explicit function)
3.17. Run all tests - verify they pass
3.18. Commit: "feat: implement conversation bridge with explicit webhook functions"

**Design Note:** Each webhook type has its own explicit function instead of one function with if/else routing. This follows the principle of simplicity and explicitness.

**Dependencies:** Workstream 2 (needs conversation API endpoints)
**Verification:** All tests pass

---

## Workstream 4: Task Routing (agent-engine-specialist)

**Owner:** agent-engine-specialist
**Files:** `agent-engine/services/task_routing.py`, `agent-engine/tests/test_task_routing.py`

### Tasks:
4.1. Write TDD tests for `build_prompt` basic functionality
4.2. Write TDD tests for `build_prompt` with conversation context
4.3. Write TDD tests for platform-specific instructions (Jira, GitHub, Slack)
4.4. Implement `build_prompt` function
4.5. Implement `_build_source_context` with platform routers
4.6. Implement `_build_platform_instructions` with platform routers
4.7. Run all tests - verify they pass
4.8. Commit: "feat: implement task routing with conversation context"

**Dependencies:** None (pure functions)
**Verification:** All tests pass

---

## Workstream 5: Agent-Engine Integration (agent-engine-specialist)

**Owner:** agent-engine-specialist
**Files:** `agent-engine/main.py`

### Tasks:
5.1. Add imports: `time`, `conversation_bridge`, `task_routing`
5.2. Get dashboard URL from environment
5.3. Generate `flow_id` from task
5.4. Call `get_or_create_flow_conversation`
5.5. Call `register_task` in dashboard
5.6. Call `post_system_message` with webhook context
5.7. Fetch conversation context (last 5 messages)
5.8. Build enriched prompt with `task_routing.build_prompt`
5.9. Update CLI execution to use enriched prompt
5.10. Add start time tracking before execution
5.11. Calculate duration after execution
5.12. Test locally with webhook trigger
5.13. Commit: "feat: integrate conversation bridge into agent-engine"

**Dependencies:** Workstream 2, 3, 4
**Verification:** Webhook creates conversation, logs show flow

---

## Workstream 6: WebSocket Streaming (dashboard-api-specialist)

**Owner:** dashboard-api-specialist
**Files:** `dashboard-api/websocket.py`, `dashboard-api/main.py`

### Tasks:
6.1. Create `websocket.py` with WebSocket endpoint at `/ws`
6.2. Implement Redis stream subscription (`XREAD BLOCK`)
6.3. Subscribe to task-logger Redis stream
6.4. Parse task events (task:created, task:started, task:output, task:completed)
6.5. Forward events to connected WebSocket clients
6.6. Add connection management (connect, disconnect, send)
6.7. Mount WebSocket route in `main.py`
6.8. Test WebSocket with `websocat` or curl upgrade
6.9. Commit: "feat: add WebSocket streaming for real-time task updates"

**Dependencies:** Workstream 1 (needs events in Redis)
**Verification:** WebSocket connects, receives task events

---

## Workstream 7: Frontend - WebSocket Client (frontend-specialist)

**Owner:** frontend-specialist
**Files:** `external-dashboard/src/hooks/useWebSocket.ts`, `external-dashboard/src/hooks/useTaskStream.ts`

### Tasks:
7.1. Create `useWebSocket` hook with reconnection logic
7.2. Create `useTaskStream` hook to subscribe to task updates
7.3. Parse incoming WebSocket messages
7.4. Update React Query cache on task events
7.5. Add error handling and reconnection
7.6. Test WebSocket connection in browser
7.7. Commit: "feat: add WebSocket client hooks for real-time updates"

**Dependencies:** Workstream 6
**Verification:** Frontend receives WebSocket messages, updates UI

---

## Workstream 8: Frontend - Conversation UI (frontend-specialist)

**Owner:** frontend-specialist
**Files:** `external-dashboard/src/components/`, `external-dashboard/src/pages/`

### Tasks:
8.1. Add `useConversations` query hook
8.2. Add `useConversationMessages` query hook
8.3. Create `ConversationList` component for Chat view
8.4. Create `ConversationThread` component to show messages
8.5. Update Chat page to list webhook conversations
8.6. Add source badge (Jira/GitHub/Slack) to conversations
8.7. Show system messages with webhook context
8.8. Test Chat view with mock data
8.9. Commit: "feat: add conversation UI for webhook tasks"

**Dependencies:** Workstream 2 (needs conversation API)
**Verification:** Chat view shows webhook conversations

---

## Workstream 9: Frontend - Task Detail Modal (frontend-specialist)

**Owner:** frontend-specialist
**Files:** `external-dashboard/src/components/TaskDetailModal.tsx`

### Tasks:
9.1. Create `TaskDetailModal` component
9.2. Subscribe to task updates via `useTaskStream`
9.3. Stream output in real-time (append as events arrive)
9.4. Show status updates (pending → running → completed)
9.5. Show duration, cost, tokens
9.6. Link to source (Jira ticket, GitHub PR, Slack thread)
9.7. Handle long output (scroll to bottom, expandable)
9.8. Update Ledger to open modal on task click
9.9. Test modal with streaming task
9.10. Commit: "feat: add task detail modal with real-time streaming"

**Dependencies:** Workstream 7
**Verification:** Modal shows streaming output, updates in real-time

---

## Workstream 10: MCP Tool Verification (agent-engine-specialist)

**Owner:** agent-engine-specialist
**Files:** `agent-engine/.claude/mcp.json`, `agent-engine/tests/test_mcp_tools.py`

### Tasks:
10.1. Read `agent-engine/.claude/mcp.json` - verify GitHub MCP configured
10.2. Verify Jira MCP configured
10.3. Verify Slack MCP configured
10.4. Write test for GitHub `add_issue_comment` MCP tool
10.5. Write test for Jira `add_jira_comment` MCP tool
10.6. Write test for Slack `send_slack_message` MCP tool
10.7. Mock MCP responses for testing
10.8. Add error handling for MCP failures in agent-engine
10.9. Test MCP tools with real webhook
10.10. Commit: "test: verify MCP tools configured and working"

**Dependencies:** None
**Verification:** MCP tools work, agent posts to Jira/GitHub/Slack

---

## Workstream 11: Error Handling (all specialists)

**Owner:** agent-engine-specialist, dashboard-api-specialist
**Files:** `agent-engine/main.py`, `dashboard-api/api/dashboard.py`

### Tasks:
11.1. Add try/except around dashboard API calls in agent-engine
11.2. Graceful degradation if dashboard unavailable
11.3. Retry logic for transient failures (max 3 retries)
11.4. Set task status to "failed" on errors
11.5. Store error messages in task metadata
11.6. Add error logging with context
11.7. Test error scenarios (dashboard down, API 500, timeout)
11.8. Commit: "feat: add error handling and graceful degradation"

**Dependencies:** Workstream 5
**Verification:** Errors logged, task marked failed, system continues

---

## Workstream 12: End-to-End Testing (testing-specialist)

**Owner:** testing-specialist
**Files:** `agent-engine/tests/`, `dashboard-api/tests/`

### Tasks:
12.1. Run all unit tests - verify they pass
12.2. Rebuild all services with `docker compose up -d --build`
12.3. Verify bind mount: `ls ./data/logs/tasks/`
12.4. Trigger Jira webhook - assign ai-agent to ticket
12.5. Verify conversation created in Chat view
12.6. Verify task in Ledger with duration, cost
12.7. Verify CLI output in task detail modal (not truncated)
12.8. Verify Jira comment posted via MCP
12.9. Verify logs on host: `ls ./data/logs/tasks/{task-id}/`
12.10. Trigger same Jira ticket - verify conversation reused
12.11. Trigger GitHub webhook - verify flow works
12.12. Trigger Slack webhook - verify flow works
12.13. Document test results
12.14. Commit: "test: end-to-end verification of webhook integration"

**Dependencies:** All workstreams
**Verification:** All verification checklist items ✅

---

## Workstream 13: Documentation (documentation-specialist)

**Owner:** documentation-specialist
**Files:** `.claude/rules/microservices.md`, `docs/`, `README.md`

### Tasks:
13.1. Update `.claude/rules/microservices.md` with conversation API
13.2. Update with WebSocket endpoint documentation
13.3. Add API documentation for new endpoints
13.4. Write user guide: "How Webhook Flows Work"
13.5. Add troubleshooting guide for common issues
13.6. Document conversation reuse behavior
13.7. Document MCP tool integration
13.8. Update README with webhook features
13.9. Commit: "docs: add webhook integration documentation"

**Dependencies:** All workstreams
**Verification:** Docs are clear and accurate

---

## Execution Strategy

### Option 1: Sequential Execution (Current Plan)
- Implement tasks 1-17 sequentially
- Slower but simpler
- Good for solo developer

### Option 2: Parallel Team Execution (Recommended)
- Use `superpowers:executing-plans` skill
- Spawn `brain` agent as team lead
- Assign specialists to workstreams
- Parallel execution of independent workstreams
- Brain reviews and integrates

**Recommended team command:**
```bash
# From Claude Code CLI
/superpowers:executing-plans
```

---

## Critical Path

**Must complete in order:**
1. **Workstream 2** (Conversation API) - Everything depends on this
2. **Workstream 3** (Conversation Bridge) - Depends on Workstream 2
3. **Workstream 5** (Integration) - Depends on Workstreams 2, 3, 4
4. **Workstream 6** (WebSocket) - Depends on Workstream 1
5. **Workstream 7-9** (Frontend) - Depends on Workstreams 2, 6

**Can run in parallel:**
- Workstream 1 (Event Logging) - Independent
- Workstream 4 (Task Routing) - Independent
- Workstream 10 (MCP Verification) - Independent
- Workstream 13 (Documentation) - Can start anytime

---

## Estimated Complexity

**Original Plan:** 17 tasks, ~2-3 days solo
**Complete Plan:** 100+ micro-tasks, 13 workstreams

**With agent teams:** ~1 day (parallel execution)
**Without agent teams:** ~4-5 days (sequential execution)

---

## Recommendation

✅ **Use agent teams for this plan**
✅ **Spawn brain agent as team lead**
✅ **Assign specialists to workstreams**
✅ **Run Workstreams 1, 2, 4, 10 in parallel first**
✅ **Then run Workstreams 3, 5, 6 in parallel**
✅ **Finally run Workstreams 7-9 in parallel**
✅ **Workstreams 11-13 run last**
