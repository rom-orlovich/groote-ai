import json
import uuid

import redis.asyncio as redis
import structlog
from config import get_settings
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from services.event_publisher import EventPublisher
from services.slack_notifier import notify_task_failed, notify_task_started

from .events import extract_task_info, should_process_event
from .response import send_error_response, send_immediate_response

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/webhooks/slack", tags=["slack-webhook"])


def _get_publisher(request: Request) -> EventPublisher | None:
    return getattr(request.app.state, "event_publisher", None)


@router.post("")
async def handle_slack_webhook(request: Request):
    payload = await request.body()
    data = json.loads(payload)

    if data.get("type") == "url_verification":
        return JSONResponse(content={"challenge": data.get("challenge")})

    event = data.get("event", {})
    team_id = data.get("team_id", "")
    channel = event.get("channel", "")
    event_ts = event.get("ts", "")
    thread_ts = event.get("thread_ts")
    settings = get_settings()
    publisher = _get_publisher(request)
    webhook_event_id = EventPublisher.generate_webhook_event_id() if publisher else ""

    logger.info(
        "slack_webhook_received",
        event_type=event.get("type"),
        channel=channel,
    )

    if publisher:
        await publisher.publish_webhook_received(
            webhook_event_id=webhook_event_id,
            source="slack",
            event_type=event.get("type", "unknown"),
            payload_size=len(payload),
        )
        await publisher.publish_webhook_validated(
            webhook_event_id=webhook_event_id,
            source="slack",
            signature_valid=True,
        )

    if not should_process_event(event):
        logger.debug("slack_event_skipped", event_type=event.get("type"))
        return JSONResponse(
            status_code=200,
            content={"status": "skipped", "reason": "Event not processed"},
        )

    task_info = extract_task_info(event, team_id)
    task_id = str(uuid.uuid4())
    task_info["task_id"] = task_id

    try:
        await send_immediate_response(settings.slack_api_url, channel, thread_ts, event_ts)
        if publisher:
            await publisher.publish_response_immediate(
                webhook_event_id=webhook_event_id,
                task_id=task_id,
                source="slack",
                response_type="thread_reply",
                target=f"channel={channel}",
            )
    except Exception as e:
        logger.warning("slack_immediate_response_failed", error=str(e))

    if publisher:
        await publisher.publish_webhook_matched(
            webhook_event_id=webhook_event_id,
            source="slack",
            event_type=event.get("type", "unknown"),
            matched_handler="slack-inquiry",
        )

    try:
        redis_client = redis.from_url(settings.redis_url)
        await redis_client.lpush("agent:tasks", json.dumps(task_info))
        await redis_client.aclose()
    except Exception as e:
        logger.error("slack_task_queue_failed", error=str(e), task_id=task_id)
        await send_error_response(settings.slack_api_url, channel, thread_ts, event_ts, str(e))
        await notify_task_failed(
            settings.slack_api_url,
            settings.slack_notification_channel,
            "slack",
            task_id,
            str(e),
        )
        if publisher:
            await publisher.publish_notification_ops(
                webhook_event_id=webhook_event_id,
                task_id=task_id,
                source="slack",
                notification_type="task_failed",
                channel=settings.slack_notification_channel,
            )
        return JSONResponse(status_code=500, content={"status": "error", "error": str(e)})

    if publisher:
        await publisher.publish_webhook_task_created(
            webhook_event_id=webhook_event_id,
            task_id=task_id,
            source="slack",
            event_type=event.get("type", "unknown"),
            input_message=task_info.get("prompt", ""),
        )

    await notify_task_started(
        settings.slack_api_url,
        settings.slack_notification_channel,
        "slack",
        task_id,
        f"channel={channel} {event.get('type', 'unknown')}",
    )
    if publisher:
        await publisher.publish_notification_ops(
            webhook_event_id=webhook_event_id,
            task_id=task_id,
            source="slack",
            notification_type="task_started",
            channel=settings.slack_notification_channel,
        )

    logger.info("slack_task_queued", task_id=task_id, channel=channel)

    return JSONResponse(
        status_code=202,
        content={"status": "accepted", "task_id": task_id},
    )


@router.get("/health")
async def health_check():
    return {"status": "healthy", "webhook": "slack"}
