import httpx
import structlog

from services.conversation_bridge import get_source_metadata

logger = structlog.get_logger(__name__)

JIRA_API_URL = "http://jira-api:3002"
GITHUB_API_URL = "http://github-api:3001"
SLACK_API_URL = "http://slack-api:3003"


async def post_response_to_platform(task: dict, result: dict) -> bool:
    source = task.get("source", "")
    output = result.get("output", "")

    if not output or not source:
        return False

    metadata = get_source_metadata(task)

    try:
        if source == "jira":
            return await _post_jira_comment(metadata, output)
        if source == "github":
            return await _post_github_comment(metadata, output)
        if source == "slack":
            return await _post_slack_message(task, output)
    except Exception:
        logger.exception("response_post_failed", source=source)
        return False

    return False


async def _post_jira_comment(metadata: dict, output: str) -> bool:
    issue_key = metadata.get("key", "")
    if not issue_key:
        return False

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{JIRA_API_URL}/api/v1/issues/{issue_key}/comments",
            json={"body": output},
        )
        response.raise_for_status()

    logger.info("response_posted", platform="jira", issue_key=issue_key)
    return True


async def _post_github_comment(metadata: dict, output: str) -> bool:
    repo = metadata.get("repo", "")
    number = metadata.get("number", "")
    if not repo or not number:
        return False

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{GITHUB_API_URL}/api/v1/repos/{repo}/issues/{number}/comments",
            json={"body": output},
        )
        response.raise_for_status()

    logger.info("response_posted", platform="github", repo=repo, number=number)
    return True


async def _post_slack_message(task: dict, output: str) -> bool:
    channel = task.get("channel", "")
    thread_ts = task.get("thread_ts", "")
    if not channel:
        return False

    truncated = output[:3000] if len(output) > 3000 else output

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{SLACK_API_URL}/api/v1/messages",
            json={
                "channel": channel,
                "text": truncated,
                "thread_ts": thread_ts or None,
            },
        )
        response.raise_for_status()

    logger.info("response_posted", platform="slack", channel=channel)
    return True
