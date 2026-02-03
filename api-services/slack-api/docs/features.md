# api-services/slack-api - Features

Auto-generated on 2026-02-03

## Overview

REST API wrapper for Slack operations with message posting and channel management. Supports text messages, Block Kit formatting, and thread replies.

## Features

### Message Posting [TESTED]

Post messages to channels with text and blocks

**Related Tests:**
- `test_post_message_to_channel`
- `test_post_message_with_blocks`

### Thread Replies [TESTED]

Reply to messages in threads for conversation continuity

**Related Tests:**
- `test_reply_in_thread`

### Channel Operations [TESTED]

List channels, get channel info, retrieve history

**Related Tests:**
- `test_get_channel_info`
- `test_list_channels`
- `test_get_channel_history`

### Rich Formatting [TESTED]

Support Block Kit for rich message formatting

**Related Tests:**
- `test_post_message_with_blocks`

### Response Posting [TESTED]

Post agent responses back to Slack threads

**Related Tests:**
- `test_post_message_to_channel`
- `test_reply_in_thread`

### POST /messages/{channel} [TESTED]

Post message to channel

**Related Tests:**
- `test_post_message_to_channel`
- `test_post_message_with_blocks`

### POST /messages/{channel}/{thread} [TESTED]

Reply in thread

**Related Tests:**
- `test_reply_in_thread`

### GET /channels [TESTED]

List channels

**Related Tests:**
- `test_list_channels`

### GET /channels/{channel} [TESTED]

Get channel info

**Related Tests:**
- `test_get_channel_info`

### GET /channels/{channel}/history [TESTED]

Get message history

**Related Tests:**
- `test_get_channel_history`

### GET /health [NEEDS TESTS]

Health check endpoint

### Error Handling [PARTIAL]

Handle invalid channels and API errors

**Related Tests:**
- `test_invalid_channel_handling`

## Test Coverage Summary

| Metric | Count |
|--------|-------|
| Total Features | 12 |
| Fully Tested | 10 |
| Partially Tested | 1 |
| Missing Tests | 1 |
| **Coverage** | **87.5%** |
