import httpx
import structlog

logger = structlog.get_logger(__name__)


async def notify_task_completed(
    slack_api_url: str,
    notification_channel: str,
    source: str,
    task_id: str,
    summary: str,
) -> bool:
    if not notification_channel:
        return False
    text = f"*Task Completed* ({source})\nID: `{task_id}`\n{summary}"
    return await _send(slack_api_url, notification_channel, text)


async def notify_task_failed(
    slack_api_url: str,
    notification_channel: str,
    source: str,
    task_id: str,
    error: str,
) -> bool:
    if not notification_channel:
        return False
    text = f"*Task Failed* ({source})\nID: `{task_id}`\nError: {error}"
    return await _send(slack_api_url, notification_channel, text)


async def _send(slack_api_url: str, channel: str, text: str) -> bool:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{slack_api_url}/api/v1/messages",
                json={"channel": channel, "text": text},
            )
            response.raise_for_status()
        logger.info("slack_notification_sent", channel=channel)
        return True
    except Exception as e:
        logger.warning("slack_notification_failed", error=str(e))
        return False
