# Slack API Service - Features

## Overview

REST API wrapper for Slack operations with message posting and channel management. Supports text messages, Block Kit formatting, thread replies, and workspace management.

## Core Features

### Message Posting

Post messages to channels with text and optional Block Kit formatting.

**Capabilities:**
- Plain text messages
- Markdown formatting
- Block Kit support
- Attachments
- Emoji support

### Thread Replies

Reply to messages in threads to maintain conversation context.

**Features:**
- Reply in thread
- Broadcast to channel option
- Thread metadata retrieval
- Parent message reference

### Channel Operations

List and manage channels with history retrieval.

**Operations:**
- List public channels
- List private channels (bot member)
- Get channel info
- Get message history
- Get thread replies

### Rich Formatting (Block Kit)

Build rich, interactive messages using Slack's Block Kit.

**Block Types:**
- Section blocks
- Divider blocks
- Context blocks
- Actions blocks
- Header blocks

### User Lookup

Find and reference users in messages.

**Operations:**
- List workspace users
- Get user info by ID
- Lookup user by email

### Rate Limit Handling

Automatic retry with backoff for Slack API rate limits.

**Rate Tiers:**
- Tier 1 (chat.postMessage): 1 per second
- Tier 2 (conversations.list): 20 per minute
- Tier 3 (users.list): 50 per minute

## API Endpoints

All endpoints use the `/api/v1` prefix.

### Messages

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/messages` | POST | Send message (channel, text, thread_ts, blocks) |
| `/messages` | PUT | Update message |
| `/reactions` | POST | Add reaction |

### Channels

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/channels` | GET | List channels |
| `/channels/{channel}` | GET | Get channel info |
| `/channels/{channel}/history` | GET | Get message history |
| `/channels/{channel}/threads/{thread_ts}` | GET | Get thread replies |

### Users

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/users/{user_id}` | GET | Get user info |
