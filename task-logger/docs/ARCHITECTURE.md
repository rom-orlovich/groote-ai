# Task Logger Architecture

## Overview

The Task Logger is a dedicated microservice for structured task logging. It consumes task events from Redis stream and writes structured log files for each task, enabling audit trails and debugging.

## Design Principles

1. **Event Sourcing** - All task events captured in sequence
2. **Structured Logs** - Each task gets organized directory structure
3. **Reliable Delivery** - Redis streams with consumer groups
4. **Atomic Writes** - Temp file + rename for crash safety

## Component Architecture

```mermaid
graph TB
    subgraph Sources["Event Sources"]
        AE[Agent Engine]
        GW[API Gateway]
    end

    subgraph Queue["Redis Streams"]
        RS[(task_events Stream)]
    end

    subgraph Service["Task Logger :8090"]
        WK[Worker Loop]
        EP[Event Processor]
        FW[File Writer]
    end

    subgraph Storage["File System"]
        FS[/data/logs/tasks/]
    end

    AE -->|Publish| RS
    GW -->|Publish| RS

    RS -->|XREADGROUP| WK
    WK --> EP
    EP --> FW
    FW --> FS
```

## Directory Structure

```
task-logger/
├── main.py              # FastAPI app + Redis consumer
├── worker.py            # Event processing worker
├── logger.py            # File logging utilities
├── models.py            # Pydantic models
├── models/
│   └── knowledge_events.py # Knowledge event models
├── config.py            # Settings
└── tests/
    ├── conftest.py      # Shared fixtures
    └── test_*.py        # Test files
```

## Log Directory Structure

```mermaid
graph TB
    subgraph TaskDir["/data/logs/tasks/{task_id}/"]
        M[metadata.json]
        I[01-input.json]
        U[02-user-inputs.jsonl]
        W[03-webhook-flow.jsonl]
        A[04-agent-output.jsonl]
        K[05-knowledge-interactions.jsonl]
        F[06-final-result.json]
        R[07-response-posting.jsonl]
    end
```

### File Descriptions

| File | Type | Content |
|------|------|---------|
| metadata.json | Static | Task ID, source, agent type |
| 01-input.json | Static | Initial task input/prompt |
| 02-user-inputs.jsonl | Stream | User interactive inputs |
| 03-webhook-flow.jsonl | Stream | Webhook processing events |
| 04-agent-output.jsonl | Stream | Claude output, tool calls |
| 05-knowledge-interactions.jsonl | Stream | Knowledge service queries/results |
| 06-final-result.json | Static | Final results + metrics |
| 07-response-posting.jsonl | Stream | Response posting events |

## Event Types

### Webhook Events

```mermaid
flowchart LR
    A[webhook:received] --> B[webhook:validated]
    B --> C[webhook:matched]
    C --> D[webhook:task_created]
```

### Task Events

```mermaid
flowchart LR
    A[task:created] --> B[task:started]
    B --> C[task:output]
    C --> D{Needs Input?}
    D -->|Yes| E[task:user_input]
    E --> C
    D -->|No| F[task:completed]
    B --> G[task:failed]
```

## Redis Consumer Architecture

```mermaid
sequenceDiagram
    participant RS as Redis Stream
    participant CG as Consumer Group
    participant W1 as Worker 1
    participant W2 as Worker 2

    W1->>CG: XREADGROUP task-logger consumer-1
    CG->>RS: Read pending messages
    RS-->>W1: Events batch

    W2->>CG: XREADGROUP task-logger consumer-2
    CG->>RS: Read pending messages
    RS-->>W2: Events batch

    W1->>RS: XACK (processed)
    W2->>RS: XACK (processed)
```

## Event Processing Flow

```mermaid
sequenceDiagram
    participant RS as Redis Stream
    participant WK as Worker
    participant EP as Event Processor
    participant FW as File Writer
    participant FS as File System

    WK->>RS: XREADGROUP BLOCK 1000
    RS-->>WK: [event1, event2, ...]

    loop Each Event
        WK->>EP: Process event
        EP->>EP: Determine file type
        EP->>FW: Write event

        alt Static File
            FW->>FS: Write JSON (atomic)
        else Stream File
            FW->>FS: Append JSONL
        end
    end

    WK->>RS: XACK processed events
```

## File Write Strategy

### Atomic Writes (Static Files)

```mermaid
flowchart TB
    A[Prepare JSON] --> B[Write to temp file]
    B --> C[fsync temp file]
    C --> D[Rename to target]
    D --> E[fsync directory]
```

### Append Writes (Stream Files)

```mermaid
flowchart TB
    A[Prepare JSONL line] --> B[Open file append mode]
    B --> C[Write line]
    C --> D[Flush buffer]
```

## Event Models

### Task Created Event

```json
{
    "event_type": "task:created",
    "task_id": "uuid",
    "timestamp": "2026-01-31T12:00:00Z",
    "data": {
        "source": "github",
        "agent_type": "github-issue-handler",
        "prompt": "Fix the authentication bug"
    }
}
```

### Task Output Event

```json
{
    "event_type": "task:output",
    "task_id": "uuid",
    "timestamp": "2026-01-31T12:00:01Z",
    "data": {
        "content_type": "text",
        "content": "Analyzing the codebase..."
    }
}
```

### Task Completed Event

```json
{
    "event_type": "task:completed",
    "task_id": "uuid",
    "timestamp": "2026-01-31T12:05:00Z",
    "data": {
        "status": "completed",
        "cost_usd": 0.05,
        "input_tokens": 1000,
        "output_tokens": 500,
        "duration_seconds": 300
    }
}
```

## API Endpoints

```mermaid
graph LR
    subgraph API["/"]
        H["GET /health"]
        L["GET /tasks/{task_id}/logs"]
        M["GET /metrics"]
    end
```

## Metrics

| Metric | Description |
|--------|-------------|
| queue_depth | Pending events in stream |
| events_processed | Total events processed |
| events_failed | Failed event count |
| processing_rate | Events per second |
| disk_usage | Log directory size |

## Scaling Model

```mermaid
graph TB
    subgraph Stream["Redis Stream"]
        RS[(task_events)]
    end

    subgraph ConsumerGroup["Consumer Group: task-logger"]
        W1[Worker 1]
        W2[Worker 2]
        W3[Worker 3]
    end

    subgraph Storage["Shared Volume"]
        NFS[NFS/EFS]
    end

    RS --> ConsumerGroup
    W1 --> NFS
    W2 --> NFS
    W3 --> NFS
```

## Testing Strategy

Tests focus on **behavior**, not implementation:

- ✅ "Task created event creates metadata.json"
- ✅ "Task output events append to agent-output.jsonl"
- ✅ "Atomic write survives crash"
- ❌ "os.rename called after fsync"

## Integration Points

### With Agent Engine
```
Agent Engine → XADD task_events → Redis → Task Logger
```

### With API Gateway
```
API Gateway → XADD task_events → Redis → Task Logger
```
