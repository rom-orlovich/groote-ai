import json
import uuid

import redis.asyncio as redis
import structlog
from config import get_settings
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from services.event_publisher import EventPublisher

from .events import extract_task_info, should_process_event

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/webhooks/jira", tags=["jira-webhook"])


def _get_publisher(request: Request) -> EventPublisher | None:
    return getattr(request.app.state, "event_publisher", None)


@router.post("")
async def handle_jira_webhook(request: Request):
    payload = await request.body()
    data = json.loads(payload)
    webhook_event = data.get("webhookEvent", "")
    issue = data.get("issue", {})
    publisher = _get_publisher(request)
    webhook_event_id = EventPublisher.generate_webhook_event_id() if publisher else ""

    logger.info(
        "jira_webhook_received",
        event_type=webhook_event,
        issue_key=issue.get("key"),
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

    settings = get_settings()

    if not should_process_event(webhook_event, issue, ai_agent_name=settings.jira_ai_agent_name):
        logger.debug(
            "jira_event_skipped",
            event_type=webhook_event,
            reason="Missing AI-Fix label or ai-agent assignee, or unsupported event",
        )
        return JSONResponse(
            status_code=200,
            content={"status": "skipped", "reason": "Event not processed"},
        )

    task_info = extract_task_info(webhook_event, data)
    task_id = str(uuid.uuid4())
    task_info["task_id"] = task_id

    if publisher:
        await publisher.publish_webhook_matched(
            webhook_event_id=webhook_event_id,
            source="jira",
            event_type=webhook_event,
            matched_handler="jira-code-plan",
        )

    redis_client = redis.from_url(settings.redis_url)
    await redis_client.lpush("agent:tasks", json.dumps(task_info))
    await redis_client.aclose()

    if publisher:
        await publisher.publish_webhook_task_created(
            webhook_event_id=webhook_event_id,
            task_id=task_id,
            source="jira",
            event_type=webhook_event,
            input_message=task_info.get("prompt", ""),
        )

    logger.info("jira_task_queued", task_id=task_id, issue_key=issue.get("key"))

    return JSONResponse(
        status_code=202,
        content={"status": "accepted", "task_id": task_id},
    )


@router.get("/health")
async def health_check():
    return {"status": "healthy", "webhook": "jira"}
