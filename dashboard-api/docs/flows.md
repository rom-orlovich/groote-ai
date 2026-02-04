# Dashboard API - Flows

## Process Flows

### Real-Time Task Streaming Flow

```
[Agent Engine] → PUBLISH task:{id}:output → [Redis Pub/Sub]
                                                   ↓
                                          [Redis Subscriber]
                                                   ↓
                                          [WebSocket Hub]
                                                   ↓
                                       [Subscribed Clients]
```

**Streaming Steps:**
1. Agent Engine publishes output to Redis Pub/Sub channel
2. Dashboard API Redis subscriber receives message
3. WebSocket Hub identifies subscribed clients for channel
4. Message forwarded to all subscribed WebSocket connections
5. Frontend receives and displays output in real-time

### WebSocket Connection Flow

```
[Client] → Connect /ws → [WebSocket Hub]
                               ↓
                      [Assign Client ID]
                               ↓
                      [Store Connection]
                               ↓
[Client] → Subscribe task:123 → [Add to Channel]
                               ↓
[Client] → Unsubscribe → [Remove from Channel]
                               ↓
[Client] → Disconnect → [Cleanup Connection]
```

**Connection Lifecycle:**
1. Client connects to `/ws` endpoint
2. Hub assigns unique client ID
3. Connection stored in active connections map
4. Client subscribes to channels (e.g., `task:123`)
5. Client added to channel subscriber set
6. On disconnect, cleanup all subscriptions

### WebSocket Message Protocol

**Subscribe:**
```json
Client → {"type": "subscribe", "channel": "task:123"}
Server → {"type": "subscribed", "channel": "task:123"}
```

**Task Output:**
```json
Server → {"type": "task_output", "task_id": "123", "output": "..."}
```

**Task Status:**
```json
Server → {"type": "task_status", "task_id": "123", "status": "completed"}
```

### Analytics Calculation Flow

```
[Request /api/analytics/summary]
           ↓
   [Query PostgreSQL]
           ↓
    ┌──────┴──────┐
    │             │
    ▼             ▼
[Tasks]     [Sessions]
    │             │
    ▼             ▼
[Aggregate    [Aggregate
 costs]        duration]
    │             │
    └──────┬──────┘
           ↓
   [Build Response]
           ↓
    [Return JSON]
```

**Aggregation Queries:**
- `SUM(cost_usd)` - Total cost
- `AVG(cost_usd)` - Average cost per task
- `SUM(input_tokens + output_tokens)` - Total tokens
- `COUNT(*) WHERE status='completed' / COUNT(*)` - Success rate
- `AVG(completed_at - created_at)` - Average duration

### Cost Histogram Flow

```
[Request /api/analytics/costs/histogram?period=hour]
           ↓
   [Query Tasks with GROUP BY]
           ↓
   [date_trunc('hour', created_at)]
           ↓
   [Aggregate per bucket]
           ↓
   [Return time-series data]
```

**Histogram Response:**
```json
{
  "period": "hour",
  "data": [
    {"timestamp": "2026-02-03T10:00:00Z", "cost": 0.05, "tasks": 3},
    {"timestamp": "2026-02-03T11:00:00Z", "cost": 0.12, "tasks": 5}
  ]
}
```

### Conversation Flow

```
[User] → POST /api/conversations
              ↓
      [Create Conversation]
              ↓
      [Return conversation_id]
              ↓
[User] → Submit message via WebSocket
              ↓
      [Create Message record]
              ↓
      [Create Task for agent]
              ↓
      [Agent processes task]
              ↓
      [Response streamed to client]
              ↓
      [Save agent response as message]
```

**Conversation Lifecycle:**
1. User creates new conversation
2. Messages submitted via WebSocket or REST
3. User messages create tasks for appropriate agent
4. Agent response streamed back
5. Both user and agent messages persisted

### Task Retrieval Flow

```
[Request GET /api/tasks?status=running]
              ↓
      [Parse Query Parameters]
              ↓
      [Build SQLAlchemy Query]
              ↓
      [Apply Filters]
              │
    ┌─────────┼─────────┐
    │         │         │
    ▼         ▼         ▼
[Status]  [Agent]   [Date]
    │         │         │
    └─────────┼─────────┘
              ↓
      [Apply Pagination]
              ↓
      [Execute Query]
              ↓
      [Serialize Results]
              ↓
      [Return Paginated Response]
```

**Pagination Response:**
```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "per_page": 20,
  "pages": 5
}
```

### Webhook Status Flow

```
[Request GET /api/webhooks]
              ↓
      [Load Webhook Configs]
              ↓
      [Query Recent Events]
              ↓
      [Calculate Stats per Source]
              │
    ┌─────────┼─────────┐
    │         │         │
    ▼         ▼         ▼
[GitHub]  [Jira]   [Slack]
    │         │         │
    └─────────┼─────────┘
              ↓
      [Build Status Response]
              ↓
      [Return Configuration + Stats]
```

**Webhook Status Response:**
```json
{
  "sources": [
    {
      "name": "github",
      "configured": true,
      "last_event": "2026-02-03T12:00:00Z",
      "events_24h": 45,
      "success_rate": 0.98
    }
  ]
}
```
