# task-logger - Flows

Auto-generated on 2026-02-03

## Process Flows

### Task Logging Flow [TESTED]

**Steps:**
1. Create task directory: `/data/logs/tasks/{task_id}/`
2. Write metadata.json (static task info)
3. Write 01-input.json (initial task input)
4. Append to 02-user-inputs.jsonl (user responses)
5. Append to 03-webhook-flow.jsonl (webhook events)
6. Append to 04-agent-output.jsonl (Claude output)
7. Append to 05-knowledge-interactions.jsonl (knowledge queries)
8. Write 06-final-result.json (results + metrics)

**Related Tests:**
- `test_create_task_directory`
- `test_write_metadata`
- `test_write_input`
- `test_append_user_input`
- `test_append_webhook_event`
- `test_append_agent_output`
- `test_append_knowledge_interaction`
- `test_write_final_result`
- `test_log_file_ordering`

### Event Consumption Flow [NEEDS TESTS]

**Steps:**
1. Connect to Redis stream (task_events)
2. Join consumer group (task-logger)
3. Read batch of events (MAX_BATCH_SIZE)
4. Parse event type from payload
5. Route to appropriate logger method
6. Acknowledge processed events

### Webhook Event Flow [TESTED]

**Steps:**
1. Receive webhook:received event
2. Log raw payload
3. Receive webhook:validated event
4. Log validation result
5. Receive webhook:task_created event
6. Log task creation

**Related Tests:**
- `test_append_webhook_event`

### Agent Output Flow [TESTED]

**Steps:**
1. Receive task:started event
2. Log execution start
3. Receive task:output events (streaming)
4. Append each output chunk
5. Receive task:completed event
6. Write final result

**Related Tests:**
- `test_append_agent_output`
- `test_write_final_result`

## Flow Coverage Summary

| Metric | Count |
|--------|-------|
| Total Flows | 4 |
| Fully Tested | 3 |
| Partially Tested | 0 |
| Missing Tests | 1 |
| **Coverage** | **75.0%** |
