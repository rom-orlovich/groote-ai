# Implementer Memory

## Redis Stream Event Publishing Pattern

When creating event publishers for Redis streams:
- Use `redis.asyncio` with `decode_responses=True` for automatic string conversion
- Use `xadd()` to publish to streams with field dictionaries
- Always include timestamp in ISO format: `datetime.now(UTC).isoformat()`
- Serialize complex data as JSON strings before publishing
- Create a helper `_publish()` method to avoid duplication across event types
- Use static methods for ID generation (like webhook_event_id)
- Lazy-initialize Redis client in `_get_client()` to avoid connection issues during instantiation
- Always provide a `close()` method for cleanup

## Event Publisher Design

For webhook event publishers:
- Generate correlation IDs (webhook_event_id) once per webhook flow and pass to all events
- Event types follow pattern: `{category}:{action}` (e.g., "webhook:received")
- Data payload includes all context needed by consumers (source, event_type, etc.)
- Use structured logging with event name + key fields, not full data dumps
- Factory functions should accept config values (like redis_url) not full settings objects

## Task-Logger Event Format

Task-logger consumes events from `task_events` stream expecting:
- `type` field starting with prefix (webhook:, task:, knowledge:)
- `timestamp` in ISO format
- `data` as JSON string (gets parsed by consumer)
- Optional `webhook_event_id` for event correlation
- Optional `task_id` (if missing, events are buffered by webhook_event_id)
