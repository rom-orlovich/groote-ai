import json
import logging
from datetime import UTC, datetime

from models import TaskEventType

logger = logging.getLogger(__name__)


async def process_knowledge_event(
    event: dict,
    get_or_create_logger,
):
    task_id = event.get("task_id")
    if not task_id:
        logger.warning("knowledge_event_missing_task_id event=%s", event)
        return

    event_type = event.get("type")
    data = event.get("data", {})
    timestamp = event.get("timestamp", datetime.now(UTC).isoformat())

    if isinstance(data, str):
        data = json.loads(data)

    task_logger = get_or_create_logger(task_id)

    if event_type == TaskEventType.KNOWLEDGE_QUERY:
        task_logger.append_knowledge_interaction(
            {
                "timestamp": timestamp,
                "type": "query",
                "tool_name": data.get("tool_name", "unknown"),
                "query": data.get("query", ""),
                "source_types": data.get("source_types", []),
                "org_id": data.get("org_id"),
            }
        )

    elif event_type == TaskEventType.KNOWLEDGE_RESULT:
        task_logger.append_knowledge_interaction(
            {
                "timestamp": timestamp,
                "type": "result",
                "tool_name": data.get("tool_name", "unknown"),
                "query": data.get("query", ""),
                "results_count": data.get("results_count", 0),
                "results_preview": data.get("results_preview", [])[:5],
                "query_time_ms": data.get("query_time_ms", 0.0),
                "cached": data.get("cached", False),
            }
        )

    elif event_type == TaskEventType.KNOWLEDGE_TOOL_CALL:
        task_logger.append_knowledge_interaction(
            {
                "timestamp": timestamp,
                "type": "tool_call",
                "tool_name": data.get("tool_name", "unknown"),
                "parameters": data.get("parameters", {}),
            }
        )

    elif event_type == TaskEventType.KNOWLEDGE_CONTEXT_USED:
        task_logger.append_knowledge_interaction(
            {
                "timestamp": timestamp,
                "type": "context_used",
                "tool_name": data.get("tool_name", "unknown"),
                "contexts_count": data.get("contexts_count", 0),
                "relevance_scores": data.get("relevance_scores", []),
                "total_tokens": data.get("total_tokens"),
            }
        )


async def process_response_event(
    event: dict,
    get_or_create_logger,
    webhook_buffer: dict[str, list[dict]],
):
    data = event.get("data", {})
    timestamp = event.get("timestamp", datetime.now(UTC).isoformat())
    webhook_event_id = event.get("webhook_event_id")

    if isinstance(data, str):
        data = json.loads(data)

    task_id = data.get("task_id")

    if not task_id:
        webhook_buffer[webhook_event_id].append(
            {"timestamp": timestamp, "stage": "response_immediate", "data": data}
        )
        return

    task_logger = get_or_create_logger(task_id)

    for buffered in webhook_buffer.pop(webhook_event_id, []):
        task_logger.append_webhook_event(buffered)

    task_logger.append_webhook_event(
        {"timestamp": timestamp, "stage": "response_immediate", "data": data}
    )


async def process_notification_event(
    event: dict,
    get_or_create_logger,
    webhook_buffer: dict[str, list[dict]],
):
    task_id = event.get("task_id")
    data = event.get("data", {})
    timestamp = event.get("timestamp", datetime.now(UTC).isoformat())
    webhook_event_id = event.get("webhook_event_id")

    if isinstance(data, str):
        data = json.loads(data)

    task_id = task_id or data.get("task_id")
    if not task_id:
        logger.warning("notification_event_missing_task_id event=%s", event)
        return

    task_logger = get_or_create_logger(task_id)

    if webhook_event_id:
        for buffered in webhook_buffer.pop(webhook_event_id, []):
            task_logger.append_webhook_event(buffered)

    task_logger.append_webhook_event(
        {"timestamp": timestamp, "stage": "notification_ops", "data": data}
    )
