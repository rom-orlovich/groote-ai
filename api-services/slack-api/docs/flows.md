# Slack API Service - Flows

## Process Flows

### Message Posting Flow

```
[Agent Engine] → POST /messages/{channel}
                          ↓
                 [Authenticate Request]
                          ↓
                 [Resolve Slack Token]
                     ↓         ↓
            [workspace_id?]  [None]
                  ↓            ↓
           [Query OAuth]  [Use SLACK_BOT_TOKEN]
                  ↓            ↓
              [Get Token]      ↓
                  └────────────┘
                          ↓
                 [Build Message Payload]
                          ↓
                 [POST chat.postMessage]
                          ↓
                 [Return ts, channel]
```

**Processing Steps:**
1. Receive POST request with channel and text/blocks
2. Authenticate internal request
3. Check for workspace_id for multi-tenant
4. Query oauth-service for workspace token or use default
5. Build message payload with text and optional blocks
6. Call Slack chat.postMessage API
7. Return message timestamp and channel

### Thread Reply Flow

```
[Agent Engine] → POST /messages/{channel}/{thread_ts}
                          ↓
                 [Resolve Token]
                          ↓
                 [Build Reply Payload]
                          ↓
                 [Include thread_ts]
                          ↓
                 [POST chat.postMessage]
                          ↓
                 [Return reply_ts]
```

**Thread Parameters:**
- `thread_ts` - Parent message timestamp
- `reply_broadcast` - Also post to channel (optional)

### Block Kit Message Flow

```
[Build Message] → [Text Content]
                        ↓
              [Add Block Elements]
                        │
         ┌──────────────┼──────────────┐
         │              │              │
         ▼              ▼              ▼
    [Section]      [Divider]     [Actions]
         │              │              │
         ▼              ▼              ▼
    [Text/Image]   [Separator]    [Buttons]
         │              │              │
         └──────────────┼──────────────┘
                        ↓
              [Serialize to JSON]
                        ↓
              [Send to Slack API]
```

**Block Kit Example:**
```json
{
  "blocks": [
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "✅ *Task Completed*"
      }
    },
    {"type": "divider"},
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "```\nCode changes applied\n```"
      }
    }
  ]
}
```

### Channel History Flow

```
[Service] → GET /channels/{channel}/history
                       ↓
              [Resolve Token]
                       ↓
          [GET conversations.history]
                       ↓
              [Parse Messages]
                       ↓
              [Include Thread Info]
                       ↓
              [Return Messages List]
```

**History Parameters:**
- `limit` - Max messages (default: 100)
- `oldest` - Start timestamp
- `latest` - End timestamp
- `inclusive` - Include boundary messages

### Rate Limit Handling Flow

```
[Slack API Call] → [Check Response]
                         ↓
                [429 Too Many Requests?]
                         ↓
                      [Yes]
                         ↓
              [Read Retry-After header]
                         ↓
              [Wait specified time]
                         ↓
              [Retry request]
```

**Rate Limit Response:**
```
HTTP/1.1 429 Too Many Requests
Retry-After: 30
```

### Error Handling Flow

```
[Slack API Response] → [Check ok field]
                            ↓
                       [ok: false?]
                            ↓
              ┌─────────────┴─────────────┐
              │                           │
              ▼                           ▼
       [error field]              [ok: true]
              │                           │
              ▼                           ▼
    [Map to HTTP error]          [Return data]
              │
              ▼
    [Return Standardized Error]
```

**Error Response Format:**
```json
{
  "error": "channel_not_found",
  "message": "Channel C99999999 not found",
  "status_code": 404,
  "details": {"channel_id": "C99999999"}
}
```

### User Lookup Flow

```
[Service] → GET /users/{user_id}
                    ↓
           [Resolve Token]
                    ↓
           [GET users.info]
                    ↓
           [Parse User Data]
                    ↓
           [Return User Object]
```

**User Response:**
```json
{
  "id": "U1234567",
  "name": "john.doe",
  "real_name": "John Doe",
  "email": "john@company.com"
}
```
