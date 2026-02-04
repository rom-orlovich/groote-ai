# Agent Engine - Flows

## Process Flows

### Task Execution Flow

```
[Redis Queue] → BRPOP agent:tasks → [Task Worker]
                                         ↓
                               [Update: in_progress]
                                         ↓
                               [Select CLI Provider]
                                         ↓
                               [Build Agent Prompt]
                                         ↓
                               [Execute CLI Process]
                                         ↓
                          [Stream Output to Pub/Sub]
                                         ↓
                           [Capture Result + Metrics]
                                         ↓
                               [Update: completed]
                                         ↓
                             [Trigger Response Post]
```

**Execution Steps:**
1. Worker executes BRPOP on `agent:tasks` Redis list
2. Task picked up, status updated to `in_progress` in PostgreSQL
3. CLI provider selected based on `CLI_PROVIDER` env var
4. Agent prompt built from task metadata and agent definition
5. CLI process spawned with streaming output
6. Output chunks published to Redis Pub/Sub channel
7. Process completes, result captured with cost/tokens
8. Task status updated to `completed`
9. Response posting triggered via api-services

### Task State Machine Flow

```
              ┌─────────────────────────────────────┐
              │                                     │
              ▼                                     │
         [QUEUED] ──────────────────────────────────┤
              │                                     │
              │ pickup                              │
              ▼                                     │
         [RUNNING] ─────────────────────────────────┤
         ↙   │   ↘                                  │
        ↓    │    ↓                                 │
   [FAILED]  │  [COMPLETED]                    [CANCELLED]
             │
             │ needs input
             ▼
     [WAITING_INPUT]
             │
             │ input received
             ▼
         [RUNNING]
```

**State Transitions:**
- `QUEUED → RUNNING`: Worker picks up task
- `RUNNING → COMPLETED`: Successful execution
- `RUNNING → FAILED`: Execution error
- `RUNNING → WAITING_INPUT`: Agent needs user response
- `WAITING_INPUT → RUNNING`: User provides input
- `QUEUED/RUNNING → CANCELLED`: User cancellation

### Session Cost Tracking Flow

```
[User Connects] → [Create Session]
                        ↓
               [Initialize Counters]
                        ↓
    ┌──────────────────┴──────────────────┐
    │                                      │
    ▼                                      ▼
[Task Completes]                    [Task Fails]
    │                                      │
    │ add cost                             │ no cost added
    ▼                                      ▼
[Aggregate total_cost_usd]         [Continue Session]
    │
    │ increment count
    ▼
[Update total_tasks]
    │
    ▼
[Check Rate Limits]
    │
    ├── exceeded → [Session Inactive]
    │
    └── ok → [Continue Session]
```

**Session Lifecycle:**
1. Session created when user connects with `user_id` and `machine_id`
2. Counters initialized: `total_cost_usd = 0`, `total_tasks = 0`
3. On task completion: cost added, task count incremented
4. Failed tasks don't add cost (no API usage)
5. Rate limits checked against configured thresholds
6. Session data preserved on disconnect for reconnection

### Agent Routing Flow

```
[Incoming Task] → [Extract source + event_type]
                            ↓
                  [Lookup Routing Table]
                            ↓
               ┌────────────┴────────────┐
               │                         │
               ▼                         ▼
         [Found]                    [Not Found]
               │                         │
               │                         │
               ▼                         ▼
      [Return Agent Type]         [Return None]
               │                         │
               ▼                         ▼
      [Route to Agent]           [Use Default Agent]
```

**Routing Logic:**
1. Task arrives with `source` (github, jira, slack, sentry)
2. Task has `event_type` (issues, pull_request, etc.)
3. Routing table lookup: `ROUTING[source][event_type]`
4. If found, return specific agent type
5. If not found, return None (uses brain as default)

### CLI Provider Selection Flow

```
[Task with Agent Type] → [Check Agent Category]
                                 ↓
                    ┌────────────┴────────────┐
                    │                         │
                    ▼                         ▼
            [Complex Agent]           [Execution Agent]
            (brain, planning,         (executor, handlers)
             verifier)
                    │                         │
                    ▼                         ▼
         [Check CLI_PROVIDER]       [Check CLI_PROVIDER]
                    │                         │
         ┌─────────┴─────────┐     ┌─────────┴─────────┐
         │                   │     │                   │
         ▼                   ▼     ▼                   ▼
    [Claude]            [Cursor]  [Claude]        [Cursor]
         │                   │     │                   │
         ▼                   ▼     ▼                   ▼
      [opus]     [claude-sonnet-4.5] [sonnet]   [composer-1]
```

**Selection Rules:**
- Complex agents require deeper reasoning → use more capable models
- Execution agents need speed → use faster models
- Claude provider: opus for complex, sonnet for execution
- Cursor provider: claude-sonnet-4.5 for complex, composer-1 for execution

### Output Streaming Flow

```
[CLI Process] → stdout → [Parse JSON Lines]
                                 ↓
                      [Extract Content Type]
                                 ↓
            ┌────────────────────┼────────────────────┐
            │                    │                    │
            ▼                    ▼                    ▼
       [Text]              [Tool Call]           [Cost]
            │                    │                    │
            ▼                    ▼                    ▼
    [Publish to          [Log Tool           [Accumulate
     Pub/Sub]             Execution]          Metrics]
            │                    │                    │
            └────────────────────┼────────────────────┘
                                 │
                                 ▼
                      [Dashboard WebSocket]
```

**Streaming Pipeline:**
1. CLI process outputs JSON lines to stdout
2. Each line parsed and content type extracted
3. Text content published to Redis Pub/Sub
4. Tool calls logged for audit
5. Cost/token metrics accumulated
6. Dashboard API subscribes and forwards to WebSocket
