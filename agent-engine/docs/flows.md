# agent-engine - Flows

Auto-generated on 2026-02-03

## Process Flows

### Task Execution Flow [TESTED]

**Steps:**
1. Pop task from Redis
2. Update status: in_progress
3. Select CLI provider
4. Build agent prompt
5. Execute CLI with prompt
6. Stream output to Redis/WS
7. Capture result (cost, tokens)
8. Update status: completed
9. Trigger response posting

**Related Tests:**
- `test_task_transitions_to_running_when_picked_up`
- `test_running_task_can_complete`
- `test_task_cost_accumulated_correctly`
- `test_complete_task_flow_success`

### Task State Machine Flow [TESTED]

**Steps:**
1. QUEUED → RUNNING (on pickup)
2. RUNNING → COMPLETED (on success)
3. RUNNING → FAILED (on error)
4. RUNNING → WAITING_INPUT (on user input needed)
5. WAITING_INPUT → RUNNING (on input received)
6. QUEUED/RUNNING → CANCELLED (on cancel)

**Related Tests:**
- `test_task_created_in_queued_status`
- `test_task_transitions_to_running_when_picked_up`
- `test_running_task_can_complete`
- `test_running_task_can_fail`
- `test_running_task_can_wait_for_input`
- `test_waiting_task_can_resume`
- `test_task_can_be_cancelled_from_queued`
- `test_task_can_be_cancelled_from_running`
- `test_task_cannot_transition_from_completed`
- `test_task_cannot_transition_from_failed`
- `test_task_cannot_transition_from_cancelled`
- `test_all_valid_transitions_defined`
- `test_terminal_states_have_no_transitions`
- `test_non_terminal_states_have_transitions`

### Session Cost Tracking Flow [TESTED]

**Steps:**
1. Create session with user_id and machine_id
2. Task completes with cost_usd
3. Session.add_completed_task() called
4. Session aggregates total_cost_usd
5. Session tracks total_tasks count
6. Session preserves data on disconnect

**Related Tests:**
- `test_session_created_with_defaults`
- `test_session_aggregates_task_costs`
- `test_session_tracks_task_count`
- `test_disconnected_session_preserves_data`
- `test_session_cost_accumulation_multiple_tasks`
- `test_failed_tasks_dont_add_cost`

### Agent Routing Flow [TESTED]

**Steps:**
1. Receive task with source and event_type
2. Lookup routing table for source
3. Find agent for event_type
4. Return agent type (or None if unknown)
5. Route task to appropriate agent

**Related Tests:**
- `test_github_issue_routes_to_issue_handler`
- `test_github_pr_routes_to_pr_review`
- `test_jira_ticket_routes_to_code_plan`
- `test_slack_message_routes_to_inquiry`
- `test_sentry_alert_routes_to_error_handler`
- `test_discovery_task_routes_to_planning`
- `test_implementation_task_routes_to_executor`
- `test_question_task_routes_to_brain`
- `test_unknown_source_returns_none`
- `test_unknown_event_type_returns_none`

### CLI Provider Selection Flow [TESTED]

**Steps:**
1. Determine agent type (complex vs execution)
2. Check CLI_PROVIDER setting (claude/cursor)
3. Select appropriate model
4. Complex agents → opus/claude-sonnet-4.5
5. Execution agents → sonnet/composer-1

**Related Tests:**
- `test_complex_agents_use_opus_model`
- `test_execution_agents_use_sonnet_model`
- `test_cursor_complex_agents_use_pro_model`
- `test_cursor_execution_agents_use_standard_model`
- `test_provider_selection_claude`
- `test_provider_selection_cursor`
- `test_unknown_provider_uses_default`
- `test_agent_type_determines_model`

## Flow Coverage Summary

| Metric | Count |
|--------|-------|
| Total Flows | 5 |
| Fully Tested | 5 |
| Partially Tested | 0 |
| Missing Tests | 0 |
| **Coverage** | **100.0%** |
