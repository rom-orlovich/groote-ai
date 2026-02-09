import httpx
import structlog

logger = structlog.get_logger(__name__)


async def post_completion(slack_api_url: str, task: dict, output: str, success: bool) -> bool:
    channel = task.get("channel")
    if not channel:
        logger.warning("missing_slack_channel", task_id=task.get("task_id"))
        return False

    prefix = "" if success else "Task failed.\n\n"
    body = f"{prefix}{output}"
    if len(body) > 4000:
        body = body[:3990] + "\n..."

    payload: dict = {"channel": channel, "text": body}
    thread_ts = task.get("thread_ts")
    if thread_ts:
        payload["thread_ts"] = thread_ts

    url = f"{slack_api_url}/api/v1/messages"
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
        logger.info(
            "slack_completion_posted",
            task_id=task.get("task_id"),
            channel=channel,
        )
        return True
    except Exception as e:
        logger.error(
            "slack_completion_failed",
            task_id=task.get("task_id"),
            error=str(e),
        )
        return False
