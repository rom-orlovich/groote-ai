import json
import uuid
from typing import Annotated

import redis.asyncio as redis
import structlog
from config import get_settings
from fastapi import APIRouter, Header, Request
from fastapi.responses import JSONResponse
from services.event_publisher import EventPublisher
from services.slack_notifier import notify_task_failed, notify_task_started

from .events import extract_task_info, should_process_event
from .response import send_error_response, send_immediate_response

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/webhooks/github", tags=["github-webhook"])


def _get_publisher(request: Request) -> EventPublisher | None:
    return getattr(request.app.state, "event_publisher", None)


def _extract_github_context(data: dict, event_type: str) -> dict:
    repo = data.get("repository", {})
    full_name = repo.get("full_name", "")
    parts = full_name.split("/", 1)
    owner = parts[0] if len(parts) == 2 else ""
    repo_name = parts[1] if len(parts) == 2 else ""
    comment_id = data.get("comment", {}).get("id")
    issue_number = None
    if event_type in ("issues", "issue_comment"):
        issue_number = data.get("issue", {}).get("number")
    elif event_type in ("pull_request", "pull_request_review_comment"):
        issue_number = data.get("pull_request", {}).get("number")
    return {
        "owner": owner,
        "repo_name": repo_name,
        "full_name": full_name,
        "comment_id": comment_id,
        "issue_number": issue_number,
    }


@router.post("")
async def handle_github_webhook(
    request: Request,
    x_github_event: Annotated[str, Header()],
):
    payload = await request.body()
    data = json.loads(payload)
    action = data.get("action")
    settings = get_settings()
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

    if not should_process_event(x_github_event, action, payload=data):
        logger.debug("github_event_skipped", event_type=x_github_event, action=action)
        return JSONResponse(
            status_code=200,
            content={"status": "skipped", "reason": "Event type not processed"},
        )

    ctx = _extract_github_context(data, x_github_event)
    task_info = extract_task_info(x_github_event, data)
    task_id = str(uuid.uuid4())
    task_info["task_id"] = task_id

    try:
        await send_immediate_response(
            github_api_url=settings.github_api_url,
            event_type=x_github_event,
            owner=ctx["owner"],
            repo=ctx["repo_name"],
            comment_id=ctx["comment_id"],
            issue_number=ctx["issue_number"],
        )
        if publisher:
            await publisher.publish_response_immediate(
                webhook_event_id=webhook_event_id,
                task_id=task_id,
                source="github",
                response_type="eyes_reaction",
                target=f"{ctx['full_name']}#{ctx['issue_number']}",
            )
    except Exception as e:
        logger.warning("github_immediate_response_failed", error=str(e))

    if publisher:
        handler_name = "github-issue-handler" if "issue" in x_github_event else "github-pr-review"
        await publisher.publish_webhook_matched(
            webhook_event_id=webhook_event_id,
            source="github",
            event_type=x_github_event,
            matched_handler=handler_name,
        )

    try:
        redis_client = redis.from_url(settings.redis_url)
        await redis_client.lpush("agent:tasks", json.dumps(task_info))
        await redis_client.aclose()
    except Exception as e:
        logger.error("github_task_queue_failed", error=str(e), task_id=task_id)
        await send_error_response(
            github_api_url=settings.github_api_url,
            event_type=x_github_event,
            owner=ctx["owner"],
            repo=ctx["repo_name"],
            comment_id=ctx["comment_id"],
            issue_number=ctx["issue_number"],
            error=str(e),
        )
        await notify_task_failed(
            settings.slack_api_url,
            settings.slack_notification_channel,
            "github",
            task_id,
            str(e),
        )
        if publisher:
            await publisher.publish_notification_ops(
                webhook_event_id=webhook_event_id,
                task_id=task_id,
                source="github",
                notification_type="task_failed",
                channel=settings.slack_notification_channel,
            )
        return JSONResponse(status_code=500, content={"status": "error", "error": str(e)})

    if publisher:
        await publisher.publish_webhook_task_created(
            webhook_event_id=webhook_event_id,
            task_id=task_id,
            source="github",
            event_type=x_github_event,
            input_message=task_info.get("prompt", ""),
        )

    await notify_task_started(
        settings.slack_api_url,
        settings.slack_notification_channel,
        "github",
        task_id,
        f"{ctx['full_name']} #{ctx['issue_number']} {x_github_event}",
    )
    if publisher:
        await publisher.publish_notification_ops(
            webhook_event_id=webhook_event_id,
            task_id=task_id,
            source="github",
            notification_type="task_started",
            channel=settings.slack_notification_channel,
        )

    logger.info("github_task_queued", task_id=task_id, event_type=x_github_event)

    return JSONResponse(
        status_code=202,
        content={"status": "accepted", "task_id": task_id},
    )


@router.get("/health")
async def health_check():
    return {"status": "healthy", "webhook": "github"}
