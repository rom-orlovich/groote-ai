# agent-engine - Features

Auto-generated on 2026-02-03

## Overview

Scalable task execution engine with multi-CLI provider support (Claude Code CLI and Cursor CLI). Consumes tasks from Redis queue, executes them using CLI providers, orchestrates 13 specialized agents, and posts results back to sources.

## Features

### Task Consumption [TESTED]

Polls Redis queue (`BRPOP agent:tasks`)

**Related Tests:**
- `test_task_created_in_queued_status`
- `test_task_transitions_to_running_when_picked_up`
- `test_complete_task_flow_success`

### CLI Execution [TESTED]

Spawns CLI provider with agent prompts

**Related Tests:**
- `test_complex_agents_use_opus_model`
- `test_execution_agents_use_sonnet_model`
- `test_cursor_complex_agents_use_pro_model`
- `test_cursor_execution_agents_use_standard_model`
- `test_provider_selection_claude`
- `test_provider_selection_cursor`
- `test_unknown_provider_uses_default`

### Agent Orchestration [TESTED]

Routes to 13 specialized agents

**Related Tests:**
- `test_github_issue_routes_to_issue_handler`
- `test_github_issue_comment_routes_to_issue_handler`
- `test_github_pr_routes_to_pr_review`
- `test_github_pr_review_comment_routes_to_pr_review`
- `test_jira_ticket_routes_to_code_plan`
- `test_jira_updated_routes_to_code_plan`
- `test_jira_comment_routes_to_code_plan`
- `test_slack_message_routes_to_inquiry`
- `test_slack_dm_routes_to_inquiry`
- `test_sentry_alert_routes_to_error_handler`
- `test_sentry_regression_routes_to_error_handler`
- `test_discovery_task_routes_to_planning`
- `test_implementation_task_routes_to_executor`
- `test_question_task_routes_to_brain`

### Result Processing [TESTED]

Captures cost, tokens, stdout, stderr

**Related Tests:**
- `test_task_cost_accumulated_correctly`
- `test_task_duration_calculated_on_completion`
- `test_session_aggregates_task_costs`

### Session Management [TESTED]

Per-user session tracking and cost aggregation

**Related Tests:**
- `test_session_created_with_defaults`
- `test_session_requires_user_and_machine`
- `test_session_has_unique_id`
- `test_session_aggregates_task_costs`
- `test_session_tracks_task_count`
- `test_session_becomes_inactive_on_rate_limit`
- `test_disconnected_session_preserves_data`
- `test_session_active_by_default`
- `test_session_can_be_rate_limited`
- `test_session_cost_accumulation_multiple_tasks`
- `test_failed_tasks_dont_add_cost`

### Task Lifecycle [TESTED]

State machine governing all agent executions

**Related Tests:**
- `test_task_created_in_queued_status`
- `test_task_requires_input_message`
- `test_task_has_unique_id`
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
- `test_complete_task_flow_success`
- `test_complete_task_flow_with_user_input`
- `test_complete_task_flow_failure`
- `test_all_valid_transitions_defined`
- `test_terminal_states_have_no_transitions`
- `test_non_terminal_states_have_transitions`

### Model Selection [TESTED]

Complex vs execution agent model mapping

**Related Tests:**
- `test_complex_agents_use_opus_model`
- `test_execution_agents_use_sonnet_model`
- `test_cursor_complex_agents_use_pro_model`
- `test_cursor_execution_agents_use_standard_model`
- `test_agent_type_determines_model`
- `test_case_insensitive_matching`

### Routing Table [TESTED]

Complete agent-to-handler routing

**Related Tests:**
- `test_all_sources_have_routes`
- `test_github_has_all_event_types`
- `test_jira_has_all_event_types`
- `test_unknown_source_returns_none`
- `test_unknown_event_type_returns_none`

### GET /health [NEEDS TESTS]

Health check endpoint

### GET /status [NEEDS TESTS]

Service status endpoint

### POST /tasks [NEEDS TESTS]

Create task (internal)

### GET /tasks/{task_id} [NEEDS TESTS]

Get task status

## Test Coverage Summary

| Metric | Count |
|--------|-------|
| Total Features | 12 |
| Fully Tested | 8 |
| Partially Tested | 0 |
| Missing Tests | 4 |
| **Coverage** | **66.7%** |
