# dashboard-api - Features

Auto-generated on 2026-02-03

## Overview

Backend API for groote-ai dashboard with real-time task streaming, analytics, and conversation management. Provides REST endpoints and WebSocket connections for the dashboard.

## Features

### Task Management [PARTIAL]

List, filter, retrieve task details

**Related Tests:**
- `test_daily_task_count`

### Real-Time Streaming [NEEDS TESTS]

WebSocket streaming of task outputs

### Analytics [TESTED]

Cost tracking, performance metrics, histograms

**Related Tests:**
- `test_opus_cost_calculation`
- `test_sonnet_cost_calculation`
- `test_unknown_model_uses_sonnet_pricing`
- `test_daily_cost_aggregation`
- `test_daily_task_count`
- `test_success_rate_calculation`
- `test_success_rate_with_no_tasks`
- `test_success_rate_all_completed`
- `test_average_duration_calculation`
- `test_average_duration_excludes_failed`
- `test_average_duration_no_completed_tasks`
- `test_cost_by_agent_breakdown`
- `test_total_cost_matches_breakdown`

### Conversations [TESTED]

Chat interface for agent interactions

**Related Tests:**
- `test_conversation_created_with_defaults`
- `test_conversation_requires_machine_id`
- `test_message_creation`
- `test_conversation_can_add_messages`

### Webhook Status [TESTED]

Monitor webhook configurations and events

**Related Tests:**
- `test_webhook_config_created_with_defaults`
- `test_webhook_validation_requires_url`
- `test_webhook_requires_valid_url`
- `test_webhook_requires_valid_provider`

### WebSocket Hub [NEEDS TESTS]

Manage WebSocket connections for live updates

### GET /api/status [NEEDS TESTS]

Machine status endpoint

### GET /api/tasks [NEEDS TESTS]

List tasks with pagination

### GET /api/analytics/summary [PARTIAL]

Analytics summary

**Related Tests:**
- `test_success_rate_calculation`

### GET /api/analytics/costs/histogram [TESTED]

Cost breakdown by time

**Related Tests:**
- `test_daily_cost_aggregation`
- `test_cost_by_agent_breakdown`

### GET /api/analytics/performance [TESTED]

Performance metrics

**Related Tests:**
- `test_average_duration_calculation`
- `test_average_duration_excludes_failed`

## Test Coverage Summary

| Metric | Count |
|--------|-------|
| Total Features | 12 |
| Fully Tested | 5 |
| Partially Tested | 2 |
| Missing Tests | 5 |
| **Coverage** | **50.0%** |
