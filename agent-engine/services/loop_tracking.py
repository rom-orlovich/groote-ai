import json

import redis.asyncio as aioredis
import structlog

logger = structlog.get_logger(__name__)

LOOP_PREVENTION_PREFIX = "posted_comments"
LOOP_PREVENTION_TTL = 3600

POSTING_TOOL_NAMES = {"send_slack_message", "add_issue_comment", "add_jira_comment"}


def extract_posted_comment_ids(tool_events: list[dict] | None) -> list[str]:
    if not tool_events:
        return []
    ids: list[str] = []
    for event in tool_events:
        if event.get("type") != "tool_result":
            continue
        content = event.get("content", "")
        if not content:
            continue
        try:
            result_data = json.loads(content) if isinstance(content, str) else content
            if isinstance(result_data, dict):
                comment_id = result_data.get("id") or result_data.get("ts") or result_data.get("comment_id")
                if comment_id:
                    ids.append(str(comment_id))
        except (json.JSONDecodeError, TypeError):
            pass
    return ids


async def track_posted_comments(
    redis_client: aioredis.Redis | None,
    comment_ids: list[str],
    task_id: str,
    method: str,
) -> None:
    if not comment_ids or not redis_client:
        return
    for comment_id in comment_ids:
        key = f"{LOOP_PREVENTION_PREFIX}:{comment_id}"
        await redis_client.setex(key, LOOP_PREVENTION_TTL, "1")
    logger.info(
        "loop_prevention_tracked",
        task_id=task_id,
        method=method,
        comment_ids=comment_ids,
    )
