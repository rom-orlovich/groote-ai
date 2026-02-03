# Task Logger - Features

## Overview

Dedicated service for structured task logging. Consumes task events from Redis stream and writes structured log files per task for audit trails and debugging.

## Core Features

### Task Directory Creation

Create unique log directory for each task with organized structure.

**Directory Structure:**
```
/data/logs/tasks/{task_id}/
├── metadata.json
├── 01-input.json
├── 02-webhook-flow.jsonl
├── 03-agent-output.jsonl
├── 03-user-inputs.jsonl
└── 04-final-result.json
```

### Metadata Writing

Write task metadata as static JSON at task creation.

**Metadata Contents:**
- Task ID
- Source (github, jira, slack, sentry)
- Agent type
- User ID
- Machine ID
- Created timestamp

### Event Streaming

Consume events from Redis stream with reliable delivery.

**Event Types:**
- `task:created` - Task metadata
- `task:started` - Execution begins
- `task:output` - Streaming agent output
- `task:user_input` - User interactive input
- `task:completed` - Final results
- `task:failed` - Error information

### Webhook Flow Logging

Log webhook processing steps for debugging.

**Logged Events:**
- `webhook:received` - Raw payload received
- `webhook:validated` - Signature verified
- `webhook:matched` - Command matched
- `webhook:task_created` - Task queued

### Agent Output Logging

Stream and persist agent output for audit.

**Output Types:**
- Text output (thoughts, explanations)
- Tool calls (file edits, searches)
- Cost/token metrics
- Error messages

### Final Result Writing

Write completion results with metrics.

**Result Contents:**
- Status (completed/failed)
- Cost (USD)
- Input/output tokens
- Duration (seconds)
- Exit code

### Atomic File Writes

Crash-safe file writing using temp + rename.

**Write Process:**
1. Write to temp file
2. fsync temp file
3. Rename to target
4. fsync directory

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/tasks/{task_id}/logs` | GET | Get task logs |
| `/metrics` | GET | Queue depth, stats |
