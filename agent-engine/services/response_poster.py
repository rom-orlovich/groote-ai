import httpx
import structlog

from services.conversation_bridge import get_source_metadata

logger = structlog.get_logger(__name__)

JIRA_API_URL = "http://jira-api:3002"
GITHUB_API_URL = "http://github-api:3001"
SLACK_API_URL = "http://slack-api:3003"

MAX_JIRA_LENGTH = 5000
MAX_GITHUB_LENGTH = 5000
MAX_SLACK_LENGTH = 3000


def _truncate(text: str, max_length: int) -> str:
    if len(text) <= max_length:
        return text
    return text[: max_length - 20] + "\n\n_(truncated)_"


def _format_jira_response(output: str, metadata: dict) -> str:
    key = metadata.get("key", "")
    header = f"*Agent Response for {key}*\n\n" if key else ""
    return _truncate(f"{header}{output}", MAX_JIRA_LENGTH)


def _format_github_response(output: str) -> str:
    return _truncate(output, MAX_GITHUB_LENGTH)


def _format_slack_response(output: str) -> str:
    return _truncate(output, MAX_SLACK_LENGTH)


async def post_response_to_platform(task: dict, result: dict) -> dict[str, object]:
    source = task.get("source", "")
    output = result.get("output", "")

    if not output or not source:
        return {"posted": False, "comment_id": None}

    metadata = get_source_metadata(task)

    try:
        if source == "jira":
            post_result = await _post_jira_comment(metadata, output)
            return (
                post_result
                if isinstance(post_result, dict)
                else {"posted": post_result, "comment_id": None}
            )
        if source == "github":
            post_result = await _post_github_comment(metadata, output)
            return (
                post_result
                if isinstance(post_result, dict)
                else {"posted": post_result, "comment_id": None}
            )
        if source == "slack":
            post_result = await _post_slack_message(task, output)
            return (
                post_result
                if isinstance(post_result, dict)
                else {"posted": post_result, "comment_id": None}
            )
    except Exception:
        logger.exception("response_post_failed", source=source)
        return {"posted": False, "comment_id": None}

    return {"posted": False, "comment_id": None}


async def _post_jira_comment(metadata: dict, output: str) -> dict[str, object]:
    issue_key = metadata.get("key", "")
    if not issue_key:
        return {"posted": False, "comment_id": None}

    body = _format_jira_response(output, metadata)

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{JIRA_API_URL}/api/v1/issues/{issue_key}/comments",
            json={"body": body},
        )
        response.raise_for_status()

    comment_id = None
    try:
        resp_data = response.json()
        comment_id = resp_data.get("id") or resp_data.get("comment_id")
    except Exception:
        pass

    logger.info("response_posted", platform="jira", issue_key=issue_key, comment_id=comment_id)
    return {"posted": True, "comment_id": comment_id}


async def _post_github_comment(metadata: dict, output: str) -> dict[str, object]:
    repo = metadata.get("repo", "")
    number = metadata.get("number", "")
    if not repo or not number:
        return {"posted": False, "comment_id": None}

    body = _format_github_response(output)

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{GITHUB_API_URL}/api/v1/repos/{repo}/issues/{number}/comments",
            json={"body": body},
        )
        response.raise_for_status()

    comment_id = None
    try:
        resp_data = response.json()
        comment_id = resp_data.get("id") or resp_data.get("comment_id")
    except Exception:
        pass

    logger.info(
        "response_posted", platform="github", repo=repo, number=number, comment_id=comment_id
    )
    return {"posted": True, "comment_id": comment_id}


async def _post_slack_message(task: dict, output: str) -> dict[str, object]:
    channel = task.get("channel", "")
    thread_ts = task.get("thread_ts", "")
    if not channel:
        return {"posted": False, "comment_id": None}

    body = _format_slack_response(output)

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{SLACK_API_URL}/api/v1/messages",
            json={
                "channel": channel,
                "text": body,
                "thread_ts": thread_ts or None,
            },
        )
        response.raise_for_status()

    comment_id = None
    try:
        resp_data = response.json()
        comment_id = resp_data.get("ts") or resp_data.get("message_id")
    except Exception:
        pass

    logger.info("response_posted", platform="slack", channel=channel, comment_id=comment_id)
    return {"posted": True, "comment_id": comment_id}
