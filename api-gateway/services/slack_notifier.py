import time
from typing import Any

import httpx
import structlog

logger = structlog.get_logger(__name__)

_cached_channel: str | None = None
_cache_expires_at: float = 0
_CACHE_TTL_SECONDS = 300

SOURCE_EMOJI = {
    "jira": ":jira:",
    "github": ":github:",
    "slack": ":slack:",
}


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


def _build_started_blocks(
    source: str, task_id: str, title: str, agent: str = "",
) -> list[dict[str, Any]]:
    emoji = SOURCE_EMOJI.get(source, ":rocket:")
    blocks: list[dict[str, Any]] = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"{emoji} *Task Started*\n*{title}*",
            },
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": (
                        f"*Source:* {source} | *Task ID:* `{task_id}`"
                        + (f" | *Agent:* {agent}" if agent else "")
                    ),
                },
            ],
        },
    ]
    return blocks


def _build_completed_blocks(
    source: str, task_id: str, summary: str, view_url: str = "",
) -> list[dict[str, Any]]:
    truncated = summary[:500] + "..." if len(summary) > 500 else summary
    blocks: list[dict[str, Any]] = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f":white_check_mark: *Task Completed*\n{truncated}",
            },
        },
    ]
    if view_url:
        blocks.append({
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "View"},
                    "url": view_url,
                    "action_id": f"view_{task_id}",
                },
            ],
        })
    blocks.append({
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": f"*Source:* {source} | *Task ID:* `{task_id}`",
            },
        ],
    })
    return blocks


def _build_failed_blocks(
    source: str, task_id: str, error: str,
) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f":x: *Task Failed*\n{error}",
            },
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"*Source:* {source} | *Task ID:* `{task_id}`",
                },
            ],
        },
    ]
    return blocks


async def notify_task_started(
    slack_api_url: str,
    notification_channel: str,
    source: str,
    task_id: str,
    title: str,
    agent: str = "",
) -> bool:
    if not notification_channel:
        return False
    text = f"Task Started ({source}): {title} | ID: {task_id}"
    blocks = _build_started_blocks(source, task_id, title, agent)
    return await _send(slack_api_url, notification_channel, text, blocks)


async def notify_task_failed(
    slack_api_url: str,
    notification_channel: str,
    source: str,
    task_id: str,
    error: str,
) -> bool:
    if not notification_channel:
        return False
    text = f"Task Failed ({source}): {error} | ID: {task_id}"
    blocks = _build_failed_blocks(source, task_id, error)
    return await _send(slack_api_url, notification_channel, text, blocks)


async def notify_task_completed(
    slack_api_url: str,
    notification_channel: str,
    source: str,
    task_id: str,
    summary: str,
    view_url: str = "",
) -> bool:
    if not notification_channel:
        return False
    text = f"Task Completed ({source}): {summary[:200]} | ID: {task_id}"
    blocks = _build_completed_blocks(source, task_id, summary, view_url)
    return await _send(slack_api_url, notification_channel, text, blocks)


async def _send(
    slack_api_url: str,
    channel: str,
    text: str,
    blocks: list[dict[str, Any]] | None = None,
) -> bool:
    try:
        payload: dict[str, Any] = {"channel": channel, "text": text}
        if blocks:
            payload["blocks"] = blocks
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{slack_api_url}/api/v1/messages",
                json=payload,
            )
            response.raise_for_status()
        logger.info("slack_notification_sent", channel=channel)
        return True
    except Exception as e:
        logger.warning("slack_notification_failed", error=str(e))
        return False
