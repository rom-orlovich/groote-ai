import httpx
import structlog

logger = structlog.get_logger(__name__)

REACTION_EYES = "eyes"
REACTION_X = "x"
MESSAGE_ISSUE_PROCESSING = "I'll analyze this issue and get back to you shortly."
MESSAGE_PR_PROCESSING = "I'll review this PR and provide feedback shortly."


async def send_eyes_reaction(github_api_url: str, owner: str, repo: str, comment_id: int) -> bool:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{github_api_url}/api/v1/repos/{owner}/{repo}/issues/comments/{comment_id}/reactions",
                json={"content": REACTION_EYES},
            )
            response.raise_for_status()
        logger.info("github_reaction_sent", owner=owner, repo=repo, comment_id=comment_id)
        return True
    except Exception as e:
        logger.warning("github_reaction_failed", error=str(e), comment_id=comment_id)
        return False


async def send_error_reaction(github_api_url: str, owner: str, repo: str, comment_id: int) -> bool:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{github_api_url}/api/v1/repos/{owner}/{repo}/issues/comments/{comment_id}/reactions",
                json={"content": REACTION_X},
            )
            response.raise_for_status()
        return True
    except Exception as e:
        logger.warning("github_error_reaction_failed", error=str(e))
        return False


async def send_issue_comment(
    github_api_url: str, owner: str, repo: str, issue_number: int, body: str
) -> bool:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{github_api_url}/api/v1/repos/{owner}/{repo}/issues/{issue_number}/comments",
                json={"body": body},
            )
            response.raise_for_status()
        return True
    except Exception as e:
        logger.warning("github_comment_failed", error=str(e))
        return False


async def send_immediate_response(
    github_api_url: str,
    event_type: str,
    owner: str,
    repo: str,
    comment_id: int | None,
    issue_number: int | None,
) -> bool:
    if event_type == "issue_comment" and comment_id:
        return await send_eyes_reaction(github_api_url, owner, repo, comment_id)
    if event_type == "issues" and issue_number:
        return await send_issue_comment(
            github_api_url, owner, repo, issue_number, MESSAGE_ISSUE_PROCESSING
        )
    if event_type in ("pull_request", "pull_request_review_comment") and issue_number:
        return await send_issue_comment(
            github_api_url, owner, repo, issue_number, MESSAGE_PR_PROCESSING
        )
    return True


async def send_error_response(
    github_api_url: str,
    event_type: str,
    owner: str,
    repo: str,
    comment_id: int | None,
    issue_number: int | None,
    error: str,
) -> bool:
    if comment_id and event_type == "issue_comment":
        await send_error_reaction(github_api_url, owner, repo, comment_id)
    if issue_number:
        await send_issue_comment(
            github_api_url, owner, repo, issue_number, f"Failed to process: {error}"
        )
    return True


async def post_completion_comment(
    github_api_url: str, owner: str, repo: str, issue_number: int, output: str, success: bool
) -> bool:
    prefix = "" if success else "Task failed.\n\n"
    body = f"{prefix}{output}"
    if len(body) > 8000:
        body = body[:7990] + "\n..."
    return await send_issue_comment(github_api_url, owner, repo, issue_number, body)
