import httpx
import structlog

logger = structlog.get_logger(__name__)

MESSAGE_PROCESSING = "Processing your request..."
REACTION_EYES = "eyes"


async def send_slack_message(
    slack_api_url: str, channel: str, text: str, thread_ts: str | None = None
) -> bool:
    try:
        payload: dict = {"channel": channel, "text": text}
        if thread_ts:
            payload["thread_ts"] = thread_ts
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{slack_api_url}/api/v1/messages",
                json=payload,
            )
            response.raise_for_status()
        logger.info("slack_message_sent", channel=channel)
        return True
    except Exception as e:
        logger.warning("slack_message_failed", error=str(e), channel=channel)
        return False


async def send_slack_reaction(slack_api_url: str, channel: str, timestamp: str, emoji: str) -> bool:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{slack_api_url}/api/v1/reactions",
                json={"channel": channel, "timestamp": timestamp, "emoji": emoji},
            )
            response.raise_for_status()
        return True
    except Exception as e:
        logger.warning("slack_reaction_failed", error=str(e))
        return False


async def send_immediate_response(
    slack_api_url: str, channel: str, thread_ts: str | None, event_ts: str
) -> bool:
    await send_slack_reaction(slack_api_url, channel, event_ts, REACTION_EYES)
    return await send_slack_message(
        slack_api_url, channel, MESSAGE_PROCESSING, thread_ts or event_ts
    )


async def send_error_response(
    slack_api_url: str, channel: str, thread_ts: str | None, event_ts: str, error: str
) -> bool:
    await send_slack_reaction(slack_api_url, channel, event_ts, "x")
    return await send_slack_message(
        slack_api_url, channel, f"Failed to process: {error}", thread_ts or event_ts
    )


async def post_completion_message(
    slack_api_url: str, channel: str, thread_ts: str | None, output: str, success: bool
) -> bool:
    prefix = "" if success else "Task failed.\n\n"
    body = f"{prefix}{output}"
    if len(body) > 4000:
        body = body[:3990] + "\n..."
    return await send_slack_message(slack_api_url, channel, body, thread_ts)
