import asyncio
import json
import logging

import redis.asyncio as aioredis

logger = logging.getLogger(__name__)

STREAM_NAME = "task_events"
BLOCK_MS = 1000


class RedisEventMonitor:
    def __init__(self, redis_url: str) -> None:
        self._redis_url = redis_url
        self._redis: aioredis.Redis | None = None
        self._task: asyncio.Task[None] | None = None
        self._running = False
        self._last_id = "$"
        self._events: dict[str, list[dict]] = {}
        self._source_events: dict[str, list[dict]] = {}
        self._source_epoch: dict[str, int] = {}
        self._epoch_counter = 0
        self._waiters: dict[tuple[str, str], asyncio.Event] = {}
        self._waiter_data: dict[tuple[str, str], dict] = {}
        self._source_waiters: dict[tuple[str, str], asyncio.Event] = {}
        self._source_waiter_data: dict[tuple[str, str], dict] = {}

    async def start(self) -> None:
        self._redis = aioredis.from_url(self._redis_url, decode_responses=True)
        self._running = True
        self._task = asyncio.create_task(self._read_loop())
        logger.info("redis_monitor_started")

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        if self._redis:
            await self._redis.aclose()
            self._redis = None
        logger.info("redis_monitor_stopped")

    async def _read_loop(self) -> None:
        if not self._redis:
            return

        while self._running:
            try:
                results = await self._redis.xread(
                    {STREAM_NAME: self._last_id},
                    block=BLOCK_MS,
                    count=100,
                )
                if not results:
                    continue

                for _stream_name, entries in results:
                    for entry_id, fields in entries:
                        self._last_id = entry_id
                        self._dispatch_event(fields)

            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("redis_monitor_read_error")
                await asyncio.sleep(1)

    def _dispatch_event(self, fields: dict) -> None:
        event_type = fields.get("type", "")
        raw_data = fields.get("data", "{}")

        try:
            data = json.loads(raw_data)
        except (json.JSONDecodeError, TypeError):
            data = {}

        event_record = {
            "type": event_type,
            "webhook_event_id": fields.get("webhook_event_id"),
            "timestamp": fields.get("timestamp"),
            "data": data,
            "_epoch": self._epoch_counter,
        }

        task_id = data.get("task_id", "")
        source = data.get("source", "")

        if task_id:
            self._events.setdefault(task_id, []).append(event_record)
            key = (task_id, event_type)
            if key in self._waiters:
                self._waiter_data[key] = event_record
                self._waiters[key].set()

        if source:
            self._source_events.setdefault(source, []).append(event_record)
            source_key = (source, event_type)
            if source_key in self._source_waiters:
                self._source_waiter_data[source_key] = event_record
                self._source_waiters[source_key].set()

        logger.debug(
            "event_dispatched",
            extra={"type": event_type, "task_id": task_id, "source": source},
        )

    async def wait_for_event(
        self, task_id: str, event_type: str, timeout: float
    ) -> dict | None:
        key = (task_id, event_type)

        existing = self._find_existing_event(task_id, event_type)
        if existing:
            return existing

        event = asyncio.Event()
        self._waiters[key] = event

        try:
            await asyncio.wait_for(event.wait(), timeout=timeout)
            return self._waiter_data.get(key)
        except TimeoutError:
            logger.warning(
                "wait_for_event_timeout",
                extra={"task_id": task_id, "event_type": event_type, "timeout": timeout},
            )
            return None
        finally:
            self._waiters.pop(key, None)

    async def wait_for_source_event(
        self, source: str, event_type: str, timeout: float
    ) -> dict | None:
        key = (source, event_type)
        min_epoch = self._source_epoch.get(source, 0)

        existing = self._find_fresh_source_event(source, event_type, min_epoch)
        if existing:
            return existing

        event = asyncio.Event()
        self._source_waiters[key] = event

        try:
            await asyncio.wait_for(event.wait(), timeout=timeout)
            result = self._source_waiter_data.pop(key, None)
            if result and result.get("_epoch", 0) < min_epoch:
                return None
            return result
        except TimeoutError:
            logger.warning(
                "wait_for_source_event_timeout",
                extra={"source": source, "event_type": event_type, "timeout": timeout},
            )
            return None
        finally:
            self._source_waiters.pop(key, None)

    def _find_existing_event(self, task_id: str, event_type: str) -> dict | None:
        for evt in self._events.get(task_id, []):
            if evt["type"] == event_type:
                return evt
        return None

    def _find_fresh_source_event(
        self, source: str, event_type: str, min_epoch: int
    ) -> dict | None:
        for evt in self._source_events.get(source, []):
            if evt["type"] == event_type and evt.get("_epoch", 0) >= min_epoch:
                return evt
        return None

    async def get_events_for_task(self, task_id: str) -> list[dict]:
        return list(self._events.get(task_id, []))

    async def get_tool_calls(self, task_id: str) -> list[dict]:
        return [
            evt
            for evt in self._events.get(task_id, [])
            if evt["type"] == "task:tool_call"
        ]

    def clear_source_events(self, source: str) -> None:
        self._epoch_counter += 1
        self._source_epoch[source] = self._epoch_counter
        self._source_events.pop(source, None)
        keys_to_remove = [k for k in self._source_waiter_data if k[0] == source]
        for k in keys_to_remove:
            self._source_waiter_data.pop(k, None)
