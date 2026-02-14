# Migrate from --append-system-prompt-file to --agent Flag

## Context

The agent engine currently uses a hacky approach to invoke Claude CLI agents: Python-side routing picks the target agent name, then passes the agent's `.md` file via `--append-system-prompt-file`. This treats the agent as raw text appended to the system prompt, bypassing Claude CLI's native agent system — frontmatter fields like `model`, `skills`, and `memory` are ignored.

The fix: replace `--append-system-prompt-file` with `--agent` (singular), which properly invokes the agent through Claude CLI's native agent resolution. Python keeps doing the fast, deterministic routing (no `--agents` plural — that would add LLM cost/latency for a simple lookup).

## Current Architecture (as of this branch)

### Worker Flow (`agent-engine/worker.py`)

```
TaskWorker._process_task()
  → task_routing.resolve_target_agent(source, event_type, task) → "jira-code-plan"
  → task["assigned_agent"] = target_agent
  → _build_webhook_context() → enriched prompt with flow_id, conversation, context
  → _execute_task() → run_cli(agents=target_agent)
  → _publish_structured_events() → tool_events, thinking_blocks, raw_output
  → clean_agent_output() → strips thinking/markers
  → detect_mcp_posting(full_output) → prevents double-posting
  → _handle_response_posting() → MCP or fallback
```

Key refactored modules (current state):
- `services/dashboard_client.py` — `post_assistant_message()`, `update_dashboard_task()`
- `services/redis_ops.py` — `publish_task_event()`, `update_task_status()`, `persist_output()`
- `cli/event_collector.py` — `handle_assistant_message()`, `handle_user_message()`, `determine_error_message()`
- `cli/sanitization.py` — sensitive data detection and sanitization
- `services/output_validation.py` — `clean_agent_output()`, `detect_auth_failure()`, `FINAL_RESPONSE_MARKER`

### CLIResult (`cli/base.py`)

```python
@dataclass
class CLIResult:
    success: bool
    output: str          # Full accumulated output (with [TOOL] markers)
    clean_output: str    # result_text from CLI result event, or cleaned stream
    cost_usd: float
    input_tokens: int
    output_tokens: int
    error: str | None = None
    tool_events: list[dict] | None = None       # NEW: structured tool call/result pairs
    thinking_blocks: list[dict] | None = None   # NEW: thinking content blocks
```

### CLI Command Builder (`cli/providers/claude.py:209-250`)

```python
def _build_command(self, prompt, model, allowed_tools, agents, debug_mode):
    cmd = ["claude", "-p", "--output-format", "stream-json",
           "--verbose", "--dangerously-skip-permissions", "--include-partial-messages"]

    if agents:
        agent_file = Path(f"/home/agent/.claude/agents/{agents}.md")  # ← HACKY
        if agent_file.exists():
            cmd.extend(["--append-system-prompt-file", str(agent_file)])  # ← TO CHANGE

    if model:
        cmd.extend(["--model", model])
    ...
```

## Target Flow (After)

```python
if agents:
    cmd.extend(["--agent", agents])  # ← Native agent invocation

if model and not agents:
    cmd.extend(["--model", model])   # ← Skip model when agent has frontmatter
```

**Benefits:**
- Claude CLI resolves the agent natively (reads frontmatter, loads skills, sets model)
- No hardcoded file paths — CLI finds agents in `~/.claude/agents/` automatically
- Agent `model` field respected (opus for brain/planning, sonnet for execution agents)
- Agent `skills` field auto-loaded by CLI

## Changes

### Phase 1: CLI Command Change

**File: `agent-engine/cli/providers/claude.py` (line 227-230)**

```python
# BEFORE:
if agents:
    agent_file = Path(f"/home/agent/.claude/agents/{agents}.md")
    if agent_file.exists():
        cmd.extend(["--append-system-prompt-file", str(agent_file)])

# AFTER:
if agents:
    cmd.extend(["--agent", agents])
```

**Same file (line 238-239)** — skip `--model` when agent is set:

```python
# BEFORE:
if model:
    cmd.extend(["--model", model])

# AFTER:
if model and not agents:
    cmd.extend(["--model", model])
```

### Phase 2: Update Tests

**File: `agent-engine/tests/test_cli_agent_system.py` (line 72-86)**

```python
# BEFORE:
def test_agent_prompt_file_passthrough(self):
    from unittest.mock import patch
    runner = ClaudeCLIRunner()
    with patch("pathlib.Path.exists", return_value=True):
        cmd = runner._build_command(
            prompt="test", model=None, allowed_tools=None,
            agents="jira-code-plan", debug_mode=None,
        )
    assert "--append-system-prompt-file" in cmd
    idx = cmd.index("--append-system-prompt-file")
    assert "jira-code-plan.md" in cmd[idx + 1]

# AFTER:
def test_agent_flag_passthrough(self):
    runner = ClaudeCLIRunner()
    cmd = runner._build_command(
        prompt="test", model=None, allowed_tools=None,
        agents="jira-code-plan", debug_mode=None,
    )
    assert "--agent" in cmd
    idx = cmd.index("--agent")
    assert cmd[idx + 1] == "jira-code-plan"

def test_model_flag_skipped_when_agent_set(self):
    runner = ClaudeCLIRunner()
    cmd = runner._build_command(
        prompt="test", model="sonnet", allowed_tools=None,
        agents="jira-code-plan", debug_mode=None,
    )
    assert "--agent" in cmd
    assert "--model" not in cmd
```

### Phase 3: Verify Agent Frontmatter

All agents already have proper frontmatter with `model` field:

| Agent | Model | Skills |
|-------|-------|--------|
| `brain.md` | opus | (delegates to sub-agents) |
| `github-issue-handler.md` | sonnet | github-operations, slack-operations, discovery |
| `github-pr-review.md` | opus | github-operations, slack-operations, verification |
| `jira-code-plan.md` | sonnet | jira-operations, github-operations, slack-operations, discovery |
| `slack-inquiry.md` | sonnet | slack-operations, discovery, knowledge-graph |
| `executor.md` | sonnet | testing, code-refactoring, github-operations |
| `planning.md` | opus | discovery, github-operations, knowledge-graph |
| `verifier.md` | sonnet | verification, testing |
| `service-integrator.md` | sonnet | github-operations, jira-operations, slack-operations |

No agent file changes needed.

## What Does NOT Change

- **Python-side routing** (`task_routing.py`) — stays as-is, deterministic lookup via `AGENT_ROUTING`
- **Worker flow** (`worker.py`) — `resolve_target_agent()` still picks the agent name, `_build_webhook_context()` unchanged
- **Agent `.md` files** — already have proper frontmatter
- **MANIFEST.md** — stays as documentation
- **MCP config** — `mcp.json` still loaded via `--mcp-config` flag
- **Event collector** (`cli/event_collector.py`) — `handle_assistant_message()`, `handle_user_message()` unchanged
- **Output validation** (`services/output_validation.py`) — `clean_agent_output()`, `detect_auth_failure()` unchanged
- **Dashboard client** (`services/dashboard_client.py`) — `post_assistant_message()`, `update_dashboard_task()` unchanged
- **Redis ops** (`services/redis_ops.py`) — `publish_task_event()`, `update_task_status()`, `persist_output()` unchanged
- **Response poster** (`services/response_poster.py`) — `post_response_to_platform()` unchanged
- **Conversation bridge** (`services/conversation_bridge.py`) — `build_flow_id()`, `get_or_create_flow_conversation()` unchanged
- **Knowledge layer** — knowledge service separate from agent invocation (see audit below)

## Files Modified

| File | Change |
|------|--------|
| `agent-engine/cli/providers/claude.py` | Replace `--append-system-prompt-file` with `--agent`, skip `--model` when agent set |
| `agent-engine/tests/test_cli_agent_system.py` | Update test to check `--agent` flag, add model skip test |

---

## End-to-End Webhook Lifecycle Audit

### Audit A: Jira Full Flow (Primary — exercises every system component)

**Trigger:** Change assignee of a real Jira ticket to `ai-agent` (e.g. KAN-18 or create new ticket with AI-Fix label)

#### A1. API Gateway (port 8000) — `api-gateway/webhooks/jira/handler.py`

| Step | What to verify | Log/Check |
|------|---------------|-----------|
| 1 | Webhook received | `jira_webhook_received` in api-gateway logs |
| 2 | Event validated | `is_bot_comment()` returns False (`jira/events.py:39-60`) |
| 3 | `should_process_event()` → True | Assignee is `ai-agent` OR labels contain `AI-Fix` (`jira/events.py:63-84`) |
| 4 | Immediate ack to Jira | `send_immediate_response()` → "Agent is analyzing..." via `jira-api:3002` (`jira/response.py:24-25`) |
| 5 | Notification channel resolved | `get_notification_channel()` from OAuth service or fallback to `settings.slack_notification_channel` |
| 6 | Task queued to Redis | `LPUSH agent:tasks` → `jira_task_queued` logged |
| 7 | Slack ops notification | `notify_task_started()` → notification channel receives "Task started" |
| 8 | Event publisher lifecycle | `webhook:received → webhook:validated → webhook:matched → webhook:task_created` |

```bash
docker logs groote-ai-api-gateway-1 --tail 50 | grep jira
```

#### A2. Redis Queue

| Step | What to verify | Check |
|------|---------------|-------|
| 1 | Task in queue | `docker exec groote-ai-redis-1 redis-cli LLEN agent:tasks` |
| 2 | Task payload | `source: "jira"`, `event_type`, `issue.key`, `issue.summary`, `prompt`, `jira_base_url` present |
| 3 | Dedup key | `jira:dedup:{issue_key}:{event}` set with TTL |

#### A3. Agent Engine — Worker (port 8080) — `agent-engine/worker.py`

| Step | What to verify | Log/Check |
|------|---------------|-----------|
| 1 | Task picked up | `task_started` with task_id (`worker.py:56`) |
| 2 | Agent routing | `resolve_target_agent("jira", ...)` → `"jira-code-plan"` (`task_routing.py:34-43`) |
| 3 | `assigned_agent` set | `task["assigned_agent"] = "jira-code-plan"` (`worker.py:61`) |
| 4 | Events published | `task:created` (with source, assigned_agent), `task:started` (with conversation_id) (`worker.py:63-74`) |

```bash
docker logs groote-ai-cli-1 --tail 100 | grep -E "task_started|assigned_agent"
```

#### A4. Conversation Bridge — `agent-engine/services/conversation_bridge.py`

Called via `worker.py:80` → `_build_webhook_context()`

| Step | What to verify | Log/Check |
|------|---------------|-----------|
| 1 | Flow ID | `build_flow_id()` → `"jira:KAN-18"` (deterministic, `conversation_bridge.py:53-71`) |
| 2 | Conversation | `get_or_create_flow_conversation()` → finds by `GET /api/conversations/by-flow/jira%3AKAN-18` or creates new (`conversation_bridge.py:107-137`) |
| 3 | Title | `build_conversation_title()` → `"Jira: KAN-18 - {summary}"` (`conversation_bridge.py:74-104`) |
| 4 | Task registered | `register_task()` → `POST /api/tasks` with task_id, source, conversation_id, flow_id (`conversation_bridge.py:152-168`) |
| 5 | System message | `post_system_message()` → "Jira Webhook Triggered" with ticket link (`conversation_bridge.py:191-211`) |
| 6 | Context fetched | `fetch_conversation_context()` → last 5 messages for history (`conversation_bridge.py:140-149`) |
| 7 | Enriched prompt | `build_task_context()` → includes Source, Event, Target-Agent, metadata, history (`task_routing.py:46-71`) |
| 8 | Context event | `task:context_built` published with enriched_prompt, flow_id, conversation_id (`worker.py:87-93`) |

```bash
docker logs groote-ai-cli-1 --tail 100 | grep -E "webhook_flow|webhook_conversation|webhook_task|webhook_context"
```

#### A5. CLI Execution (CRITICAL — validates --agent flag) — `agent-engine/cli/providers/claude.py`

| Step | What to verify | Log/Check |
|------|---------------|-----------|
| 1 | CLI command | `--agent jira-code-plan` in command (NOT `--append-system-prompt-file`) (`claude.py:227-230`) |
| 2 | No `--model` flag | Agent frontmatter handles model selection (`sonnet` for jira-code-plan) (`claude.py:238-239`) |
| 3 | MCP config | `--mcp-config /app/.claude/mcp.json` present (github, jira, slack, knowledge-graph, llamaindex, gkg) (`claude.py:244-246`) |
| 4 | Process started | `starting_claude_cli` log with PID, agent name (`claude.py:33-38`) |
| 5 | Agent Discovery Protocol | CLI reads `~/.claude/agents/jira-code-plan.md` → loads frontmatter → loads skills |
| 6 | Skills loaded | `jira-operations`, `github-operations`, `slack-operations`, `discovery` from frontmatter |
| 7 | MCP tools available | `jira:get_jira_issue`, `jira:add_jira_comment`, `github:*` via SSE connections |

```bash
docker logs groote-ai-cli-1 --tail 100 | grep -E "starting_claude_cli|--agent|cmd_args"
```

#### A6. Agent MCP Tool Usage — captured by `cli/event_collector.py`

| Step | What to verify | Log/Check |
|------|---------------|-----------|
| 1 | Tool calls logged | `handle_assistant_message()` → `[TOOL] Using jira:get_jira_issue` → `output_queue` (`event_collector.py:31-47`) |
| 2 | Tool results logged | `handle_user_message()` → `[TOOL RESULT]` with content (`event_collector.py:50-76`) |
| 3 | Sensitive data sanitized | `contains_sensitive_data()` / `sanitize_sensitive_content()` from `cli/sanitization.py` |
| 4 | Structured events captured | `tool_events` list: `{"type": "tool_call", "name": ..., "input": ...}` and `{"type": "tool_result", ...}` |
| 5 | Jira comment posted via MCP | `[TOOL] Using jira:add_jira_comment` in accumulated output |
| 6 | Result text | `result` event in stream-json → `result_text` captured (`claude.py:104-112`) |
| 7 | `FINAL_RESPONSE` marker | Output contains `<!-- FINAL_RESPONSE -->` separator |

#### A7. Output Processing — `agent-engine/worker.py:104-116`

| Step | What to verify | Log/Check |
|------|---------------|-----------|
| 1 | Structured events published | `_publish_structured_events()` → `task:thinking`, `task:tool_call`, `task:tool_result`, `task:raw_output` (`worker.py:196-215`) |
| 2 | `result_text` as clean output | `CLIResult.clean_output` = `result_text` (from `result` event) or fallback to stream (`claude.py:155`) |
| 3 | `raw_output` preserved | `result["raw_output"]` = full `accumulated_output` with `[TOOL]` markers (`worker.py:269`) |
| 4 | MCP detection on raw | `detect_mcp_posting(full_output)` checks `raw_output` for `[TOOL] Using add_jira_comment` (`worker.py:108`) |
| 5 | Clean output | `clean_agent_output(raw_output)` → `extract_final_response()` strips before `<!-- FINAL_RESPONSE -->` (`output_validation.py:55-70`) |
| 6 | Auth check | `detect_auth_failure(output)` → no auth error patterns (`output_validation.py:39-44`) |
| 7 | Output persisted | `persist_output()` → `task:{task_id}:output` in Redis, TTL 3600 (`redis_ops.py:37-43`) |

#### A8. Dashboard Updates — `agent-engine/services/dashboard_client.py`

| Step | What to verify | Log/Check |
|------|---------------|-----------|
| 1 | Task → running | `update_dashboard_task()` → `PATCH /api/tasks/{task_id}` with `{"status": "running"}` (`worker.py:96`) |
| 2 | Task → completed | `update_dashboard_task()` → status, output, cost, tokens, duration (`worker.py:134-142`) |
| 3 | Assistant message | `post_assistant_message()` → `POST /api/conversations/{id}/messages` role=assistant (`worker.py:144-148`) |
| 4 | Target conversation | `conversation_id or webhook_conversation_id` — uses webhook conv for webhook tasks (`worker.py:144`) |
| 5 | Events published | `task:output`, `task:completed` to Redis stream (`worker.py:113-132`) |
| 6 | WebSocket broadcast | Dashboard API picks up Redis pub/sub → broadcasts to connected clients |

```bash
curl -s http://localhost:5000/api/conversations | python3 -m json.tool | head -30
```

#### A9. Response Posting — `agent-engine/worker.py:150-154` → `_handle_response_posting()`

| Step | What to verify | Log/Check |
|------|---------------|-----------|
| 1 | MCP detected | `mcp_already_posted = True` → `[TOOL] Using jira:add_jira_comment` found in raw output (`worker.py:108`) |
| 2 | No fallback | `mcp_posted = True` → `post_response_to_platform()` NOT called (`worker.py:222-226`) |
| 3 | OR fallback | If MCP missed → `response_poster.post_response_to_platform()` posts via `jira-api:3002` (`response_poster.py:37-57`) |
| 4 | Fallback notice | If fallback used → `post_fallback_notice()` adds system message to conversation (`conversation_bridge.py:214-232`) |
| 5 | Response event | `task:response_posted` published with method=mcp/fallback/failed (`worker.py:239-243`) |

#### A10. Task Logger (port 8090) — `task-logger/main.py`

| Step | What to verify | Log/Check |
|------|---------------|-----------|
| 1 | Events consumed | Task logger reads from `task_events` Redis stream |
| 2 | Log directory | `/data/logs/tasks/{task_id}/` created |
| 3 | metadata.json | task_id, source, assigned_agent |
| 4 | 01-input.json | Original prompt and task metadata |
| 5 | 02-webhook-flow.jsonl | `webhook:received → validated → matched → task_created` |
| 6 | 04-agent-output.jsonl | Agent output (including `task:thinking`, `task:tool_call`, `task:tool_result`, `task:raw_output`) |
| 7 | 06-final-result.json | Status, output, cost, tokens, duration |

```bash
curl -s http://localhost:8090/tasks/{task_id}/logs | python3 -m json.tool
```

#### A11. Platform Verification (Jira)

| Step | What to verify | Check |
|------|---------------|-------|
| 1 | Immediate ack | "Agent is analyzing this issue..." (from API Gateway via `jira/response.py`) |
| 2 | Agent result | Final analysis/plan posted via MCP `jira:add_jira_comment` |
| 3 | No duplicates | Exactly 2 comments (ack + result), NOT 3 (no fallback duplicate) |
| 4 | Comment quality | Clean final response — no thinking, no `[TOOL]` markers, no `<!-- FINAL_RESPONSE -->` |

#### A12. Slack Ops Notifications

| Step | What to verify | Check |
|------|---------------|-------|
| 1 | Task started | Notification channel receives "Task started: jira KAN-18..." |
| 2 | No failed notification | (unless actual failure) |

---

### Audit B: GitHub Flow

**Trigger:** Create a new issue or comment on existing issue in a repo with webhook configured

#### B1. API Gateway — `api-gateway/webhooks/github/handler.py`

| Step | What to verify | Log/Check |
|------|---------------|-----------|
| 1 | Webhook received | `github_webhook_received` with event_type, action, repository |
| 2 | HMAC valid | `X-Hub-Signature-256` validated against `GITHUB_WEBHOOK_SECRET` |
| 3 | Installation events | `x_github_event == "installation"` → acknowledged, not processed (`handler.py:77-86`) |
| 4 | `should_process_event()` → True | Event in `SUPPORTED_EVENTS`, action matches, `is_bot_sender()` = False (`events.py:25-39`) |
| 5 | Context extracted | `_extract_github_context()` → owner, repo_name, issue_number, comment_id (`handler.py:24-42`) |
| 6 | Immediate response | Eyes reaction on comment OR "I'll analyze this issue..." on new issue (`response.py:57-75`) |
| 7 | Handler matched | `github-issue-handler` for issues, `github-pr-review` for PRs (`handler.py:127`) |
| 8 | Task queued | `LPUSH agent:tasks` → `github_task_queued` logged |

#### B2. Agent Engine

| Step | What to verify | Log/Check |
|------|---------------|-----------|
| 1 | Agent routing | `resolve_target_agent("github", "issues")` → `"github-issue-handler"` |
| 2 | OR for PRs | `resolve_target_agent("github", "pull_request")` → `"github-pr-review"` |
| 3 | OR improve mode | `_is_pr_improve_request()` checks PR + keywords → `"github-pr-review"` (`task_routing.py:25-36`) |
| 4 | CLI command | `--agent github-issue-handler` (NOT `--append-system-prompt-file`) |
| 5 | Flow ID | `build_flow_id()` → `"github:owner/repo#42"` |
| 6 | Conversation | Title: `"GitHub: repo#42 - Issue Title"` |

#### B3. Agent Execution

| Step | What to verify | Log/Check |
|------|---------------|-----------|
| 1 | MCP tools | `github:get_file_contents`, `github:add_issue_comment`, `github:search_code` |
| 2 | Issue read | Agent uses issue context from enriched prompt or MCP tools |
| 3 | Comment posted | `[TOOL] Using github:add_issue_comment` in raw output |
| 4 | MCP detection | `detect_mcp_posting()` → True (pattern matches `add_issue_comment`) |
| 5 | No fallback | `post_response_to_platform` NOT called |

#### B4. Platform Verification

| Step | What to verify | Check |
|------|---------------|-------|
| 1 | Agent comment | Exactly ONE substantive comment from agent on the issue |
| 2 | No duplicate | Fallback did not also post |
| 3 | Clean output | No thinking, no tool markers, no `<!-- FINAL_RESPONSE -->` |
| 4 | Dashboard | Conversation with system message + assistant message |

---

### Audit C: Slack Flow

**Trigger:** Send `@agent` mention in a configured Slack channel

| Stage | Key Differences from Jira/GitHub |
|-------|----------------------------------|
| API Gateway | `url_verification` challenge handled (`handler.py:28-29`), `should_process_event()` checks event type (`events.py`) |
| Agent Engine | Routes to `slack-inquiry` agent |
| CLI Command | `--agent slack-inquiry` |
| Agent Skills | `slack-operations`, `discovery`, `knowledge-graph` |
| MCP Tools | `slack:send_slack_message` with `thread_ts` for thread replies |
| Flow ID | `slack:{channel}:{event_ts}` |
| MCP Detection | `detect_mcp_posting()` matches `send_slack_message` |
| Platform check | Reply in thread (not new message), exactly ONE reply |

---

### Audit D: Knowledge Layer Integration

The knowledge layer is **orthogonal to the --agent flag change** but should be verified as part of the full flow.

#### D1. Knowledge Service Initialization — `agent-engine/main.py:28-44`

| Step | What to verify | Log/Check |
|------|---------------|-----------|
| 1 | Config | `KNOWLEDGE_SERVICES_ENABLED` in settings (`config/settings.py`) |
| 2 | If enabled | `KnowledgeService(llamaindex_url, gkg_url, enabled=True)` initialized |
| 3 | Health check | `knowledge_services_initialized` with `llamaindex_available`, `gkg_available` |
| 4 | If disabled | `NoopKnowledgeService()` → returns empty results, graceful |
| 5 | Detailed health | `/health/detailed` endpoint shows knowledge component status (`main.py:120-152`) |

```bash
curl -s http://localhost:8080/health/detailed | python3 -m json.tool
```

#### D2. MCP-Based Knowledge (via agents) — `agent-engine/.claude/mcp.json`

Knowledge available via MCP tools:

| MCP Server | Port | SSE URL | Tools |
|------------|------|---------|-------|
| `knowledge-graph` | 9005 | `http://knowledge-graph-mcp:9005/sse` | `knowledge-graph:search_codebase`, entity queries |
| `llamaindex` | 9006 | `http://llamaindex-mcp:9006/sse` | `llamaindex:knowledge_query`, RAG search |
| `gkg` | 9007 | `http://gkg-mcp:9007/sse` | GitLab Knowledge Graph queries |

**Which agents use knowledge?**

| Agent | Knowledge Skills in Frontmatter | When Used |
|-------|--------------------------------|-----------|
| `slack-inquiry` | `knowledge-graph` | Answering code questions from Slack |
| `planning` | `knowledge-graph` | Discovery and architecture analysis |
| `brain` | (delegates) | Routes to agents with knowledge skills |

**Verification for knowledge in Slack flow:**

| Step | What to verify | Log/Check |
|------|---------------|-----------|
| 1 | Agent loads skill | `slack-inquiry.md` frontmatter has `skills: [..., knowledge-graph]` |
| 2 | MCP servers up | `knowledge-graph-mcp:9005`, `llamaindex-mcp:9006` respond to SSE |
| 3 | Agent queries | `[TOOL] Using knowledge-graph:search_codebase` in raw output (when relevant) |
| 4 | Graceful degradation | If MCP unavailable, agent proceeds with other tools (no crash) |

```bash
curl -s http://localhost:9005/health  # knowledge-graph MCP
curl -s http://localhost:9006/health  # llamaindex MCP
curl -s http://localhost:9007/health  # gkg MCP
```

#### D3. Knowledge Service Architecture

| Component | Status | How Knowledge is Accessed |
|-----------|--------|--------------------------|
| `KnowledgeService` (Python, `services/knowledge.py`) | Initialized + health-checked, but NOT called in `_process_task()` flow | For future direct-API use |
| MCP tools (agent-level) | Active — agents call `knowledge-graph:*`, `llamaindex:*` during CLI execution | Via Claude CLI + `mcp.json` |
| `NoopKnowledgeService` | Used when `KNOWLEDGE_SERVICES_ENABLED=false` | Returns empty results everywhere |

The `--agent` flag change does NOT affect knowledge access — it works via MCP tools at the agent layer.

---

### Audit E: Cross-Cutting Verification

| # | Check | How to Verify |
|---|-------|---------------|
| 1 | No `--append-system-prompt-file` | `docker logs groote-ai-cli-1 \| grep append-system-prompt` → empty |
| 2 | All webhooks use `--agent {name}` | `docker logs groote-ai-cli-1 \| grep -- "--agent"` → shows agent names |
| 3 | Agent model respected | brain/planning/pr-review → opus, others → sonnet |
| 4 | No `--model` when `--agent` set | `docker logs groote-ai-cli-1 \| grep -- "--model"` → empty |
| 5 | No double-posting | Jira: 2 comments (ack + result). GitHub: 1 comment. Slack: 1 thread reply. |
| 6 | Dashboard conversations | System message + assistant message for each webhook |
| 7 | Task logger complete | `curl http://localhost:8090/tasks/{id}/logs` shows all stages |
| 8 | Live logs clean | Dashboard LIVE_LOGS_STREAM shows `[TOOL]`, `[TOOL RESULT]`, `[CLI]`, `[LOG]` — NOT agent thinking |
| 9 | Structured events | `task:thinking`, `task:tool_call`, `task:tool_result`, `task:raw_output` in Redis stream |
| 10 | Knowledge MCP health | All 3 knowledge MCP servers respond to `/health` |
| 11 | Output quality | Final response is clean — no thinking, no markers, no `[TOOL]` output |
| 12 | Sensitive data | `cli/sanitization.py` catches and sanitizes secrets in tool results |

---

## Rollback

If `--agent` flag doesn't work in the Docker container:

```python
if agents:
    agent_file = Path(f"/home/agent/.claude/agents/{agents}.md")
    if agent_file.exists():
        cmd.extend(["--append-system-prompt-file", str(agent_file)])
```

## Files Modified

| File | Change |
|------|--------|
| `agent-engine/cli/providers/claude.py` | Replace `--append-system-prompt-file` with `--agent`, skip `--model` when agent set |
| `agent-engine/tests/test_cli_agent_system.py` | Update test to check `--agent` flag, add model skip test |
