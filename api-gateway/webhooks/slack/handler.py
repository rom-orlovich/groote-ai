import json
import uuid

import redis.asyncio as redis
import structlog
from config import get_settings
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from services.event_publisher import EventPublisher
from services.loop_prevention import LoopPrevention
from services.slack_notifier import (
    get_notification_channel,
    notify_task_failed,
    notify_task_started,
)

from .events import extract_task_info, should_process_event
from .response import send_error_response, send_immediate_response

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/webhooks/slack", tags=["slack-webhook"])

DEDUP_TTL_SECONDS = 3600


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
        await publisher.publish_webhook_payload(
            webhook_event_id=webhook_event_id,
            source="slack",
            event_type=event.get("type", "unknown"),
            payload=data,
        )

    if not should_process_event(event):
        logger.debug("slack_event_skipped", event_type=event.get("type"))
        if publisher:
            await publisher.publish_webhook_skipped(
                webhook_event_id=webhook_event_id,
                source="slack",
                event_type=event.get("type", "unknown"),
                reason="event_not_processed",
            )
        return JSONResponse(
            status_code=200,
            content={"status": "skipped", "reason": "Event not processed"},
        )

    event_id = data.get("event_id", event_ts)
    dedup_key = f"slack:dedup:{event_id}"
    try:
        redis_client = redis.from_url(settings.redis_url)
        already_processing = await redis_client.set(dedup_key, "1", nx=True, ex=DEDUP_TTL_SECONDS)
        await redis_client.aclose()
        if not already_processing:
            logger.debug("slack_event_deduplicated", event_id=event_id)
            if publisher:
                await publisher.publish_webhook_skipped(
                    webhook_event_id=webhook_event_id,
                    source="slack",
                    event_type=event.get("type", "unknown"),
                    reason="duplicate_within_cooldown",
                )
            return JSONResponse(
                status_code=200,
                content={"status": "skipped", "reason": "Duplicate event within cooldown"},
            )
    except Exception as e:
        logger.warning("slack_dedup_check_failed", error=str(e))

    if event_ts:
        try:
            redis_client = redis.from_url(settings.redis_url)
            loop_prevention = LoopPrevention(redis_client)
            if await loop_prevention.is_own_comment(event_ts):
                await redis_client.aclose()
                logger.info("slack_own_message_skipped", event_ts=event_ts)
                if publisher:
                    await publisher.publish_webhook_skipped(
                        webhook_event_id=webhook_event_id,
                        source="slack",
                        event_type=event.get("type", "unknown"),
                        reason="own_comment_loop_prevention",
                    )
                return JSONResponse(
                    status_code=200,
                    content={"status": "skipped", "reason": "Own message detected"},
                )
            await redis_client.aclose()
        except Exception as e:
            logger.warning("slack_loop_prevention_check_failed", error=str(e))

    notification_channel = await get_notification_channel(
        settings.oauth_service_url,
        settings.internal_service_key,
        settings.slack_notification_channel,
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
            notification_channel,
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
                channel=notification_channel,
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

    user_text = event.get("text", "")
    started_title = user_text[:120] if user_text else f"channel={channel} {event.get('type', 'unknown')}"
    await notify_task_started(
        settings.slack_api_url,
        notification_channel,
        "slack",
        task_id,
        started_title,
    )
    if publisher:
        await publisher.publish_notification_ops(
            webhook_event_id=webhook_event_id,
            task_id=task_id,
            source="slack",
            notification_type="task_started",
            channel=notification_channel,
        )

    logger.info("slack_task_queued", task_id=task_id, channel=channel)

    return JSONResponse(
        status_code=202,
        content={"status": "accepted", "task_id": task_id},
    )


@router.get("/health")
async def health_check():
    return {"status": "healthy", "webhook": "slack"}
