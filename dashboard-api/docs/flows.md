# dashboard-api - Flows

Auto-generated on 2026-02-03

## Process Flows

### Analytics Calculation Flow [TESTED]

**Steps:**
1. Query completed tasks from database
2. Calculate cost using token counts and model pricing
3. Aggregate costs by day/agent
4. Calculate success rate (completed/total)
5. Calculate average duration
6. Return analytics summary

**Related Tests:**
- `test_opus_cost_calculation`
- `test_sonnet_cost_calculation`
- `test_daily_cost_aggregation`
- `test_success_rate_calculation`
- `test_average_duration_calculation`
- `test_cost_by_agent_breakdown`
- `test_total_cost_matches_breakdown`

### Conversation Flow [TESTED]

**Steps:**
1. Create conversation with machine_id
2. Add messages to conversation
3. Retrieve messages for display
4. Track conversation state

**Related Tests:**
- `test_conversation_created_with_defaults`
- `test_conversation_requires_machine_id`
- `test_message_creation`
- `test_conversation_can_add_messages`

### Webhook Monitoring Flow [TESTED]

**Steps:**
1. Load webhook configurations
2. Validate webhook URL and provider
3. Track webhook events
4. Report webhook statistics

**Related Tests:**
- `test_webhook_config_created_with_defaults`
- `test_webhook_validation_requires_url`
- `test_webhook_requires_valid_url`
- `test_webhook_requires_valid_provider`

### WebSocket Subscription Flow [NEEDS TESTS]

**Steps:**
1. Client connects to /ws
2. Client sends subscribe message with channel
3. Server adds client to channel
4. Server broadcasts task updates to subscribers
5. Client receives real-time updates

## Flow Coverage Summary

| Metric | Count |
|--------|-------|
| Total Flows | 4 |
| Fully Tested | 3 |
| Partially Tested | 0 |
| Missing Tests | 1 |
| **Coverage** | **75.0%** |
