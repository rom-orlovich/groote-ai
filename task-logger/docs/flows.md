# Task Logger - Flows

## Process Flows

### Task Logging Flow

```
[Redis Stream: task_events] → XREADGROUP → [Task Logger Worker]
                                                    ↓
                                          [Parse Event Type]
                                                    ↓
               ┌────────────────────────────────────┼────────────────────────────────────┐
               │                                    │                                    │
               ▼                                    ▼                                    ▼
      [task:created]                        [task:output]                        [task:completed]
               │                                    │                                    │
               ▼                                    ▼                                    ▼
   [Create Directory]                    [Append to JSONL]                    [Write Final JSON]
               │                                    │                                    │
               ▼                                    │                                    │
   [Write metadata.json]                            │                                    │
               │                                    │                                    │
               └────────────────────────────────────┼────────────────────────────────────┘
                                                    ↓
                                            [XACK Event]
```

**Processing Steps:**
1. Worker reads from Redis stream using XREADGROUP
2. Event parsed to determine type
3. Appropriate handler processes event
4. File operations performed atomically
5. Event acknowledged with XACK

### Directory Creation Flow

```
[task:created Event] → [Extract task_id]
                              ↓
                    [Create directory path]
                              ↓
              /data/logs/tasks/{task_id}/
                              ↓
                    [os.makedirs(exist_ok=True)]
                              ↓
                    [Write metadata.json]
                              ↓
                    [Write 01-input.json]
```

**Directory Contents:**
```
/data/logs/tasks/abc-123/
├── metadata.json                      # Static task info
├── 01-input.json                      # Initial prompt/task
├── 02-user-inputs.jsonl               # User responses (append)
├── 03-webhook-flow.jsonl              # Webhook events (append)
├── 04-agent-output.jsonl              # Agent output (append)
├── 05-knowledge-interactions.jsonl    # Knowledge queries (append)
├── 06-final-result.json               # Final metrics
└── 07-response-posting.jsonl          # Response posting (append)
```

### Event Consumption Flow

```
[Redis Stream] ← XREADGROUP task-logger consumer-1 BLOCK 1000
                              ↓
                    [Batch of Events]
                              ↓
                    [Process Each Event]
                              ↓
                    [File I/O Operations]
                              ↓
                    [XACK Processed Events]
```

**Consumer Group:**
- Group name: `task-logger`
- Consumer ID: `consumer-{replica_id}`
- Block timeout: 1000ms
- Batch size: 10 events

### Atomic Write Flow (Static Files)

```
[JSON Data] → [Serialize to string]
                     ↓
             [Generate temp path]
                     ↓
             [Write to temp file]
                     ↓
             [os.fsync(fd)]
                     ↓
             [os.rename(temp, target)]
                     ↓
             [os.fsync(dir_fd)]
```

**Why Atomic:**
- Crash during write leaves old file
- Rename is atomic on POSIX
- fsync ensures durability

### Append Write Flow (Stream Files)

```
[JSONL Event] → [Serialize line + newline]
                        ↓
                [Open file append mode]
                        ↓
                [Write line]
                        ↓
                [Flush buffer]
```

**JSONL Format:**
```jsonl
{"timestamp": "...", "type": "output", "content": "Analyzing..."}
{"timestamp": "...", "type": "tool_call", "tool": "Read", "args": {...}}
{"timestamp": "...", "type": "output", "content": "Found the issue..."}
```

### Final Result Flow

```
[task:completed Event] → [Extract metrics]
                               ↓
                    [Build result object]
                               │
            ┌──────────────────┼──────────────────┐
            │                  │                  │
            ▼                  ▼                  ▼
       [status]           [cost_usd]        [duration]
            │                  │                  │
            └──────────────────┼──────────────────┘
                               ↓
                    [Atomic write 06-final-result.json]
```

**Final Result Format:**
```json
{
  "task_id": "abc-123",
  "status": "completed",
  "cost_usd": 0.05,
  "input_tokens": 1000,
  "output_tokens": 500,
  "duration_seconds": 45.2,
  "completed_at": "2026-02-03T12:00:00Z"
}
```

### Log Retrieval Flow

```
[GET /tasks/{task_id}/logs] → [Validate task_id]
                                     ↓
                            [Build directory path]
                                     ↓
                            [Read all files]
                                     ↓
               ┌─────────────────────┼─────────────────────┐
               │                     │                     │
               ▼                     ▼                     ▼
        [metadata.json]      [*.jsonl files]      [final-result.json]
               │                     │                     │
               └─────────────────────┼─────────────────────┘
                                     ↓
                            [Combine into response]
                                     ↓
                            [Return JSON]
```

**Log Response:**
```json
{
  "task_id": "abc-123",
  "metadata": {...},
  "input": {...},
  "webhook_flow": [...],
  "agent_output": [...],
  "user_inputs": [...],
  "final_result": {...}
}
```

### Scaling Model

```
[Redis Stream: task_events]
              ↓
     [Consumer Group: task-logger]
              │
    ┌─────────┼─────────┐
    │         │         │
    ▼         ▼         ▼
[consumer-1] [consumer-2] [consumer-3]
    │         │         │
    └─────────┼─────────┘
              ↓
     [Shared Storage (NFS/EFS)]
```

**Scaling Features:**
- Consumer group distributes load
- Each consumer processes different events
- Shared storage for log files
- Horizontal scaling with replicas
