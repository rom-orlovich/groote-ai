import json
import uuid
from typing import Annotated

import redis.asyncio as redis
import structlog
from config import get_settings
from fastapi import APIRouter, Header, Request
from fastapi.responses import JSONResponse
from services.event_publisher import EventPublisher

from .events import extract_task_info, should_process_event

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/webhooks/github", tags=["github-webhook"])


def _get_publisher(request: Request) -> EventPublisher | None:
    return getattr(request.app.state, "event_publisher", None)


@router.post("")
async def handle_github_webhook(
    request: Request,
    x_github_event: Annotated[str, Header()],
):
    payload = await request.body()
    data = json.loads(payload)
    action = data.get("action")
    publisher = _get_publisher(request)
    webhook_event_id = EventPublisher.generate_webhook_event_id() if publisher else ""

    logger.info(
        "github_webhook_received",
        event_type=x_github_event,
        action=action,
        repository=data.get("repository", {}).get("full_name"),
    )

    if publisher:
        await publisher.publish_webhook_received(
            webhook_event_id=webhook_event_id,
            source="github",
            event_type=x_github_event,
            payload_size=len(payload),
        )
        await publisher.publish_webhook_validated(
            webhook_event_id=webhook_event_id,
            source="github",
            signature_valid=True,
        )

    if x_github_event == "installation":
        logger.info(
            "github_installation_event",
            action=action,
            installation_id=data.get("installation", {}).get("id"),
        )
        return JSONResponse(
            status_code=200,
            content={"status": "acknowledged", "event": "installation", "action": action},
        )

    if not should_process_event(x_github_event, action):
        logger.debug("github_event_skipped", event_type=x_github_event, action=action)
        return JSONResponse(
            status_code=200,
            content={"status": "skipped", "reason": "Event type not processed"},
        )

    task_info = extract_task_info(x_github_event, data)
    task_id = str(uuid.uuid4())
    task_info["task_id"] = task_id

    if publisher:
        handler_name = "github-issue-handler" if "issue" in x_github_event else "github-pr-review"
        await publisher.publish_webhook_matched(
            webhook_event_id=webhook_event_id,
            source="github",
            event_type=x_github_event,
            matched_handler=handler_name,
        )

    settings = get_settings()
    redis_client = redis.from_url(settings.redis_url)
    await redis_client.lpush("agent:tasks", json.dumps(task_info))
    await redis_client.aclose()

    if publisher:
        await publisher.publish_webhook_task_created(
            webhook_event_id=webhook_event_id,
            task_id=task_id,
            source="github",
            event_type=x_github_event,
            input_message=task_info.get("prompt", ""),
        )

    logger.info("github_task_queued", task_id=task_id, event_type=x_github_event)

    return JSONResponse(
        status_code=202,
        content={"status": "accepted", "task_id": task_id},
    )


@router.get("/health")
async def health_check():
    return {"status": "healthy", "webhook": "github"}
