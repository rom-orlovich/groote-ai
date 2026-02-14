# Slack MCP - Features

## Overview

FastMCP-based MCP server that exposes 8 Slack operations as tools for AI agents. Translates MCP protocol calls into HTTP requests to the Slack API service.

## Core Features

### Messaging

Send and update messages in channels and threads.

**Capabilities:**
- Send messages to channels with optional thread replies (via thread_ts)
- Update existing messages by channel and timestamp
- Thread-aware: all message tools support Slack threading

### Channel Operations

Read channel history and metadata.

**Capabilities:**
- Get message history with time-range filtering (oldest, latest)
- Get thread replies for a specific parent message
- Get channel information (name, topic, members)
- List all channels in the workspace with cursor pagination

### Reactions

Add emoji reactions to messages for acknowledgment and feedback.

**Capabilities:**
- Add reactions by emoji name (e.g., "thumbsup", "eyes")
- React to specific messages by channel and timestamp

### User Information

Look up user details for context enrichment.

**Capabilities:**
- Get user details by ID (name, email, status)

### Credential Isolation

MCP server never stores Slack bot tokens. All requests are proxied through the Slack API service which holds the actual credentials.

**Security Model:**
- No environment variables for Slack tokens
- HTTP-only communication with slack-api service
- Complete credential isolation from agent runtime

## MCP Tools

| Tool | Description |
|------|-------------|
| `send_slack_message` | Send message to channel or thread |
| `get_slack_channel_history` | Get channel message history |
| `get_slack_thread` | Get replies in a thread |
| `add_slack_reaction` | Add emoji reaction to message |
| `get_slack_channel_info` | Get channel details |
| `list_slack_channels` | List workspace channels |
| `get_slack_user_info` | Get user details |
| `update_slack_message` | Update existing message |
