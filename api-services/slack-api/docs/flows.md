# api-services/slack-api - Flows

Auto-generated on 2026-02-03

## Process Flows

### Message Posting Flow [TESTED]

**Steps:**
1. Receive POST request with channel and text
2. Authenticate request
3. Get Slack Bot Token
4. Format message (text + optional blocks)
5. Call Slack chat.postMessage API
6. Return message timestamp and channel

**Related Tests:**
- `test_post_message_to_channel`
- `test_post_message_with_blocks`

### Thread Reply Flow [TESTED]

**Steps:**
1. Receive POST request with channel, thread_ts, and text
2. Authenticate request
3. Get Slack Bot Token
4. Include thread_ts in message payload
5. Call Slack chat.postMessage API
6. Return reply timestamp

**Related Tests:**
- `test_reply_in_thread`

### Channel Info Flow [TESTED]

**Steps:**
1. Receive GET request for channel
2. Authenticate request
3. Call Slack conversations.info API
4. Return channel metadata

**Related Tests:**
- `test_get_channel_info`
- `test_list_channels`

### Message History Flow [TESTED]

**Steps:**
1. Receive GET request for channel history
2. Authenticate request
3. Call Slack conversations.history API
4. Return message list with pagination

**Related Tests:**
- `test_get_channel_history`

## Flow Coverage Summary

| Metric | Count |
|--------|-------|
| Total Flows | 4 |
| Fully Tested | 4 |
| Partially Tested | 0 |
| Missing Tests | 0 |
| **Coverage** | **100.0%** |
