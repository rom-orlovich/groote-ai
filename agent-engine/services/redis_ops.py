import json
import time
from typing import Any

import redis.asyncio as redis


async def update_task_status(
    redis_client: redis.Redis | None,
    task_id: str,
    status: str,
    result: dict[str, Any] | None = None,
) -> None:
    if redis_client:
        update: dict[str, Any] = {"status": status}
        if result:
            update["result"] = result
        await redis_client.hset(f"task:{task_id}", mapping={"data": json.dumps(update)})
        await redis_client.publish(f"task:{task_id}:status", json.dumps(update))


async def publish_task_event(
    redis_client: redis.Redis | None,
    task_id: str,
    event_type: str,
    data: dict[str, Any],
) -> None:
    if redis_client:
        await redis_client.xadd(
            "task_events",
            {
                "type": event_type,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "task_id": task_id,
                "data": json.dumps(data),
            },
        )


async def persist_output(redis_client: redis.Redis | None, task_id: str, output: str) -> None:
    if redis_client:
        key = f"task:{task_id}:output"
        await redis_client.set(key, output)
        await redis_client.expire(key, 3600)
