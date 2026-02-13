import asyncio
import json
import logging
from collections import defaultdict
from datetime import UTC, datetime

import redis.asyncio as redis
from config import settings
from event_handlers import (
    process_knowledge_event,
    process_notification_event,
    process_response_event,
)
from logger import TaskLogger
from models import TaskEventType

logger = logging.getLogger(__name__)

loggers_cache: dict[str, TaskLogger] = {}
webhook_buffer: dict[str, list[dict]] = defaultdict(list)
running = True


def get_or_create_logger(task_id: str) -> TaskLogger:
    if task_id not in loggers_cache:
        loggers_cache[task_id] = TaskLogger(task_id, settings.logs_dir)
    return loggers_cache[task_id]


async def process_webhook_event(event: dict):
    webhook_event_id = event.get("webhook_event_id")
    event_type = event.get("type")
    data = event.get("data", {})
    timestamp = event.get("timestamp", datetime.now(UTC).isoformat())

    if isinstance(data, str):
        data = json.loads(data)

    task_id = data.get("task_id")

    if not task_id:
        webhook_buffer[webhook_event_id].append(
            {
                "timestamp": timestamp,
                "stage": event_type.split(":")[1],
                "data": data,
            }
        )
        return

    task_logger = get_or_create_logger(task_id)

    for buffered in webhook_buffer.pop(webhook_event_id, []):
        task_logger.append_webhook_event(buffered)

    task_logger.append_webhook_event(
        {"timestamp": timestamp, "stage": event_type.split(":")[1], "data": data}
    )


async def process_task_event(event: dict):
    task_id = event.get("task_id")
    if not task_id:
        logger.warning("task_event_missing_id event=%s", event)
        return

    event_type = event.get("type")
    data = event.get("data", {})
    timestamp = event.get("timestamp", datetime.now(UTC).isoformat())

    if isinstance(data, str):
        data = json.loads(data)

    task_logger = get_or_create_logger(task_id)

    if event_type == TaskEventType.TASK_CREATED:
        task_logger.write_metadata(data)
        task_logger.write_input({"message": data.get("input_message")})

    elif event_type == TaskEventType.TASK_OUTPUT:
        task_logger.append_agent_output(
            {"timestamp": timestamp, "type": "output", "content": data.get("content")}
        )

    elif event_type == TaskEventType.TASK_USER_INPUT:
        task_logger.append_user_input(
            {
                "timestamp": timestamp,
                "type": "user_response",
                "question_type": data.get("question_type", "clarification"),
                "content": data.get("content"),
            }
        )

    elif event_type == TaskEventType.TASK_COMPLETED:
        task_logger.write_final_result(
            {
                "success": True,
                "result": data.get("result"),
                "metrics": {
                    "cost_usd": data.get("cost_usd"),
                    "duration_seconds": data.get("duration_seconds"),
                    "input_tokens": data.get("input_tokens"),
                    "output_tokens": data.get("output_tokens"),
                },
                "completed_at": timestamp,
            }
        )

    elif event_type == TaskEventType.TASK_FAILED:
        task_logger.write_final_result(
            {"success": False, "error": data.get("error"), "completed_at": timestamp}
        )

    elif event_type == TaskEventType.TASK_CONTEXT_BUILT:
        task_logger.enrich_input(
            {
                "enriched_prompt": data.get("enriched_prompt"),
                "conversation_context": data.get("conversation_context"),
                "source_metadata": data.get("source_metadata"),
            }
        )
        task_logger.enrich_metadata(
            {
                "flow_id": data.get("flow_id"),
                "conversation_id": data.get("conversation_id"),
            }
        )

    elif event_type == TaskEventType.TASK_THINKING:
        task_logger.append_agent_output(
            {
                "timestamp": timestamp,
                "type": "thinking",
                "content": data.get("content", ""),
            }
        )

    elif event_type == TaskEventType.TASK_TOOL_CALL:
        task_logger.append_agent_output(
            {
                "timestamp": timestamp,
                "type": "tool_call",
                "name": data.get("name", ""),
                "input": data.get("input", {}),
            }
        )

    elif event_type == TaskEventType.TASK_TOOL_RESULT:
        task_logger.append_agent_output(
            {
                "timestamp": timestamp,
                "type": "tool_result",
                "name": data.get("name", ""),
                "content": data.get("content", ""),
                "is_error": data.get("is_error", False),
            }
        )

    elif event_type == TaskEventType.TASK_RAW_OUTPUT:
        task_logger.append_agent_output(
            {
                "timestamp": timestamp,
                "type": "raw_output",
                "content": data.get("raw_output", data.get("content", "")),
            }
        )

    elif event_type == TaskEventType.TASK_RESPONSE_POSTED:
        task_logger.append_response_posting(
            {
                "timestamp": timestamp,
                "method": data.get("method"),
                "source": data.get("source"),
                "mcp_detected": data.get("mcp_detected"),
                "fallback_posted": data.get("fallback_posted"),
            }
        )


async def process_event(event: dict):
    event_type = event.get("type")

    if event_type.startswith("webhook:"):
        await process_webhook_event(event)
    elif event_type.startswith("response:"):
        await process_response_event(event, get_or_create_logger, webhook_buffer)
    elif event_type.startswith("notification:"):
        await process_notification_event(event, get_or_create_logger, webhook_buffer)
    elif event_type.startswith("task:"):
        await process_task_event(event)
    elif event_type.startswith("knowledge:"):
        await process_knowledge_event(event, get_or_create_logger)
    else:
        logger.warning("unknown_event_type event_type=%s", event_type)


async def run():
    redis_client = redis.from_url(settings.redis_url, decode_responses=True)

    try:
        await redis_client.xgroup_create(
            settings.redis_stream, settings.redis_consumer_group, id="0", mkstream=True
        )
        logger.info("consumer_group_created group=%s", settings.redis_consumer_group)
    except redis.ResponseError as e:
        if "BUSYGROUP" not in str(e):
            raise
        logger.info("consumer_group_exists group=%s", settings.redis_consumer_group)

    logger.info("worker_started stream=%s", settings.redis_stream)

    while running:
        try:
            events = await redis_client.xreadgroup(
                groupname=settings.redis_consumer_group,
                consumername="worker-1",
                streams={settings.redis_stream: ">"},
                count=settings.max_batch_size,
                block=5000,
            )

            for _stream_name, messages in events:
                for message_id, event_data in messages:
                    try:
                        await process_event(event_data)
                        await redis_client.xack(
                            settings.redis_stream,
                            settings.redis_consumer_group,
                            message_id,
                        )
                    except Exception as e:
                        logger.error(
                            "event_processing_failed message_id=%s error=%s",
                            message_id,
                            str(e),
                            exc_info=True,
                        )

        except asyncio.CancelledError:
            logger.info("worker_cancelled")
            break
        except Exception as e:
            logger.error("worker_error error=%s", str(e), exc_info=True)
            await asyncio.sleep(5)

    await redis_client.close()
    logger.info("worker_stopped")


if __name__ == "__main__":
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    asyncio.run(run())
