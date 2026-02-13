import time

import httpx
import structlog

logger = structlog.get_logger(__name__)

_cached_channel: str | None = None
_cache_expires_at: float = 0
_CACHE_TTL_SECONDS = 300


async def get_notification_channel(
    oauth_internal_url: str,
    service_key: str,
    fallback_channel: str,
) -> str:
    global _cached_channel, _cache_expires_at

    if _cached_channel and time.monotonic() < _cache_expires_at:
        return _cached_channel

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"{oauth_internal_url}/internal/token/slack",
                headers={"X-Internal-Service-Key": service_key},
            )
            response.raise_for_status()
            data = response.json()

        channel_id = data.get("metadata", {}).get("notification_channel_id")
        if channel_id:
            _cached_channel = channel_id
            _cache_expires_at = time.monotonic() + _CACHE_TTL_SECONDS
            logger.info("slack_channel_fetched_from_oauth", channel_id=channel_id)
            return channel_id
    except Exception as e:
        logger.warning("slack_channel_fetch_failed", error=str(e))

    return fallback_channel


async def notify_task_started(
    slack_api_url: str,
    notification_channel: str,
    source: str,
    task_id: str,
    summary: str,
) -> bool:
    if not notification_channel:
        return False
    text = f"*Task Started* ({source})\nID: `{task_id}`\n{summary}"
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
