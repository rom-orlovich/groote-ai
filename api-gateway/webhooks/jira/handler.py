import json
import uuid

import redis.asyncio as redis
import structlog
from config import get_settings
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from services.event_publisher import EventPublisher
from services.loop_prevention import LoopPrevention
from services.oauth_config import get_jira_site_url
from services.slack_notifier import (
    get_notification_channel,
    notify_task_failed,
    notify_task_started,
)

from .events import extract_task_info, should_process_event
from .response import send_error_response, send_immediate_response

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/webhooks/jira", tags=["jira-webhook"])

DEDUP_TTL_SECONDS = 3600


def _get_publisher(request: Request) -> EventPublisher | None:
    return getattr(request.app.state, "event_publisher", None)


@router.post("")
async def handle_jira_webhook(request: Request):
    payload = await request.body()
    data = json.loads(payload)
    webhook_event = data.get("webhookEvent", "")
    issue = data.get("issue", {})
    issue_key = issue.get("key", "")
    settings = get_settings()
    publisher = _get_publisher(request)
    webhook_event_id = EventPublisher.generate_webhook_event_id() if publisher else ""

    logger.info(
        "jira_webhook_received",
        event_type=webhook_event,
        issue_key=issue_key,
    )

    if publisher:
        await publisher.publish_webhook_received(
            webhook_event_id=webhook_event_id,
            source="jira",
            event_type=webhook_event,
            payload_size=len(payload),
        )
        await publisher.publish_webhook_validated(
            webhook_event_id=webhook_event_id,
            source="jira",
            signature_valid=True,
        )
        await publisher.publish_webhook_payload(
            webhook_event_id=webhook_event_id,
            source="jira",
            event_type=webhook_event,
            payload=data,
        )

    comment = data.get("comment")
    if not should_process_event(
        webhook_event, issue, ai_agent_name=settings.jira_ai_agent_name, comment_data=comment
    ):
        logger.debug(
            "jira_event_skipped",
            event_type=webhook_event,
            reason="Bot comment, missing ai-agent label, or unsupported event",
        )
        if publisher:
            await publisher.publish_webhook_skipped(
                webhook_event_id=webhook_event_id,
                source="jira",
                event_type=webhook_event,
                reason="event_not_processed",
            )
        return JSONResponse(
            status_code=200,
            content={"status": "skipped", "reason": "Event not processed"},
        )

    comment_id = comment.get("id") if comment else None
    dedup_suffix = f":{comment_id}" if comment_id else f":{webhook_event}"
    dedup_key = f"jira:dedup:{issue_key}{dedup_suffix}"
    try:
        redis_client = redis.from_url(settings.redis_url)
        already_processing = await redis_client.set(dedup_key, "1", nx=True, ex=DEDUP_TTL_SECONDS)
        await redis_client.aclose()
        if not already_processing:
            logger.debug(
                "jira_event_deduplicated",
                issue_key=issue_key,
                event_type=webhook_event,
            )
            if publisher:
                await publisher.publish_webhook_skipped(
                    webhook_event_id=webhook_event_id,
                    source="jira",
                    event_type=webhook_event,
                    reason="duplicate_within_cooldown",
                )
            return JSONResponse(
                status_code=200,
                content={"status": "skipped", "reason": "Duplicate event within cooldown"},
            )
    except Exception as e:
        logger.warning("jira_dedup_check_failed", error=str(e))

    if webhook_event == "comment_created" and comment:
        comment_id = comment.get("id")
        if comment_id:
            try:
                redis_client = redis.from_url(settings.redis_url)
                loop_prevention = LoopPrevention(redis_client)
                if await loop_prevention.is_own_comment(str(comment_id)):
                    await redis_client.aclose()
                    logger.info("jira_own_comment_skipped", comment_id=comment_id)
                    if publisher:
                        await publisher.publish_webhook_skipped(
                            webhook_event_id=webhook_event_id,
                            source="jira",
                            event_type=webhook_event,
                            reason="own_comment_loop_prevention",
                        )
                    return JSONResponse(
                        status_code=200,
                        content={"status": "skipped", "reason": "Own comment detected"},
                    )
                await redis_client.aclose()
            except Exception as e:
                logger.warning("jira_loop_prevention_check_failed", error=str(e))

    notification_channel = await get_notification_channel(
        settings.oauth_service_url,
        settings.internal_service_key,
        settings.slack_notification_channel,
    )

    jira_site = await get_jira_site_url(
        settings.oauth_service_url,
        settings.internal_service_key,
    )
    task_info = extract_task_info(webhook_event, data, jira_site_url=jira_site)
    task_id = str(uuid.uuid4())
    task_info["task_id"] = task_id

    try:
        immediate_result = await send_immediate_response(settings.jira_api_url, issue_key)
        immediate_comment_id = (
            immediate_result.get("comment_id") if isinstance(immediate_result, dict) else None
        )
        if immediate_comment_id:
            try:
                track_redis = redis.from_url(settings.redis_url)
                loop_prev = LoopPrevention(track_redis)
                await loop_prev.track_posted_comment(str(immediate_comment_id))
                await track_redis.aclose()
            except Exception as track_err:
                logger.warning("jira_immediate_tracking_failed", error=str(track_err))
        if publisher:
            await publisher.publish_response_immediate(
                webhook_event_id=webhook_event_id,
                task_id=task_id,
                source="jira",
                response_type="processing_comment",
                target=issue_key,
            )
    except Exception as e:
        logger.warning("jira_immediate_response_failed", error=str(e))

    if publisher:
        await publisher.publish_webhook_matched(
            webhook_event_id=webhook_event_id,
            source="jira",
            event_type=webhook_event,
            matched_handler="jira-code-plan",
        )

    try:
        redis_client = redis.from_url(settings.redis_url)
        await redis_client.lpush("agent:tasks", json.dumps(task_info))
        await redis_client.aclose()
    except Exception as e:
        logger.error("jira_task_queue_failed", error=str(e), task_id=task_id)
        await send_error_response(settings.jira_api_url, issue_key, str(e))
        await notify_task_failed(
            settings.slack_api_url,
            notification_channel,
            "jira",
            task_id,
            str(e),
        )
        if publisher:
            await publisher.publish_notification_ops(
                webhook_event_id=webhook_event_id,
                task_id=task_id,
                source="jira",
                notification_type="task_failed",
                channel=notification_channel,
            )
        return JSONResponse(status_code=500, content={"status": "error", "error": str(e)})

    if publisher:
        await publisher.publish_webhook_task_created(
            webhook_event_id=webhook_event_id,
            task_id=task_id,
            source="jira",
            event_type=webhook_event,
            input_message=task_info.get("prompt", ""),
        )

    issue_summary = task_info.get("issue", {}).get("summary", issue_key)
    assigned_agent = task_info.get("assigned_agent", "")
    await notify_task_started(
        settings.slack_api_url,
        notification_channel,
        "jira",
        task_id,
        f"{issue_key}: {issue_summary}" if issue_summary else issue_key,
        agent=assigned_agent,
    )
    if publisher:
        await publisher.publish_notification_ops(
            webhook_event_id=webhook_event_id,
            task_id=task_id,
            source="jira",
            notification_type="task_started",
            channel=notification_channel,
        )

    logger.info("jira_task_queued", task_id=task_id, issue_key=issue_key)

    return JSONResponse(
        status_code=202,
        content={"status": "accepted", "task_id": task_id},
    )


@router.get("/health")
async def health_check():
    return {"status": "healthy", "webhook": "jira"}
