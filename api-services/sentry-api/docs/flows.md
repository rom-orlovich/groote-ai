# Sentry API Service - Flows

## Process Flows

### Issue Retrieval Flow

```
[Internal Service] → GET /issues/{issue_id}
                            ↓
                   [Authenticate Request]
                            ↓
                   [Load SENTRY_AUTH_TOKEN]
                            ↓
              [GET sentry/api/0/issues/{id}/]
                            ↓
                   [Parse Issue Data]
                            ↓
                   [Return Formatted Issue]
```

**Processing Steps:**
1. Receive GET request with issue_id
2. Authenticate internal request
3. Load Sentry auth token from environment
4. Call Sentry API for issue details
5. Parse response including metadata
6. Return formatted issue data

### Event Analysis Flow

```
[Service] → GET /issues/{id}/events
                     ↓
        [GET sentry/api/0/issues/{id}/events/]
                     ↓
              [Parse Events]
                     ↓
        [For each event with stacktrace:]
                     ↓
        [GET sentry/api/0/events/{event_id}/]
                     ↓
              [Extract Stacktrace]
                     ↓
              [Format Frames]
                     ↓
              [Return Events List]
```

**Event Response:**
```json
{
  "events": [
    {
      "event_id": "abc123",
      "timestamp": "2026-02-03T12:00:00Z",
      "message": "TypeError: undefined is not a function",
      "stacktrace": {...}
    }
  ]
}
```

### Stacktrace Processing Flow

```
[Event Data] → [Extract exception]
                      ↓
              [Get stacktrace values]
                      ↓
              [For each frame:]
                      │
         ┌────────────┼────────────┐
         │            │            │
         ▼            ▼            ▼
    [filename]   [function]   [lineno]
         │            │            │
         └────────────┼────────────┘
                      ↓
              [Add context lines]
                      ↓
              [Mark in_app frames]
                      ↓
              [Return formatted stacktrace]
```

**Stacktrace Format:**
```json
{
  "frames": [
    {
      "filename": "src/main.py",
      "function": "process_request",
      "lineno": 42,
      "in_app": true,
      "context_line": "    result = await handler(request)",
      "pre_context": ["    try:", "        validate(request)"],
      "post_context": ["    except Exception as e:", "        log_error(e)"]
    }
  ]
}
```

### Issue Status Update Flow

```
[Agent Engine] → PUT /issues/{id}/status
                         ↓
                [Parse Status Value]
                         ↓
               [Validate Status]
                    ↓
    ┌───────────────┼───────────────┐
    │               │               │
    ▼               ▼               ▼
[resolved]     [ignored]     [unresolved]
    │               │               │
    └───────────────┼───────────────┘
                    ↓
        [PUT sentry/api/0/issues/{id}/]
                    ↓
               [Return Updated Issue]
```

**Status Request:**
```json
{"status": "resolved"}
```

### Comment Posting Flow

```
[Agent Engine] → POST /issues/{id}/comments
                          ↓
                 [Parse Comment Body]
                          ↓
       [POST sentry/api/0/issues/{id}/comments/]
                          ↓
                 [Return Comment ID]
```

**Comment Request:**
```json
{"text": "Investigating this issue..."}
```

### Issue Lifecycle Flow

```
           [New Error Event]
                  ↓
           [UNRESOLVED]
              ↙    ↘
             ↓      ↓
        [Ignore]  [Resolve]
             ↓      ↓
       [IGNORED] [RESOLVED]
             ↓      ↓
        [Unignore] [Regression]
             ↓      ↓
           [UNRESOLVED]
```

**State Transitions:**
- `UNRESOLVED → RESOLVED`: Issue fixed
- `UNRESOLVED → IGNORED`: Suppress issue
- `RESOLVED → UNRESOLVED`: Regression detected
- `IGNORED → UNRESOLVED`: Un-ignore issue

### Impact Analysis Flow

```
[Service] → GET /issues/{id}/affected-users
                       ↓
          [GET sentry/api/0/issues/{id}/]
                       ↓
              [Extract userCount]
                       ↓
          [GET sentry/api/0/issues/{id}/tags/user/]
                       ↓
              [Aggregate user list]
                       ↓
              [Return impact data]
```

**Impact Response:**
```json
{
  "total_users": 150,
  "total_events": 1234,
  "first_seen": "2026-02-01T10:00:00Z",
  "last_seen": "2026-02-03T12:00:00Z"
}
```

### Error Handling Flow

```
[Sentry API Response] → [Check Status Code]
                              ↓
              ┌───────────────┼───────────────┐
              │               │               │
              ▼               ▼               ▼
         [2xx OK]        [4xx Error]     [5xx Error]
              │               │               │
              ▼               ▼               ▼
       [Return Data]   [Map to Error]   [Retry/Return]
                              ↓
                    [Return Standardized Error]
```

**Error Response Format:**
```json
{
  "error": "not_found",
  "message": "Issue 99999 not found",
  "status_code": 404,
  "details": {"issue_id": "99999"}
}
```
