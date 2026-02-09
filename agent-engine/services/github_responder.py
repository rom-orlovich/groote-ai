import httpx
import structlog

logger = structlog.get_logger(__name__)


async def post_completion(github_api_url: str, task: dict, output: str, success: bool) -> bool:
    full_name = task.get("repository", {}).get("full_name")
    if not full_name:
        logger.warning("missing_github_repo", task_id=task.get("task_id"))
        return False

    event_type = task.get("event_type")
    number = (
        task.get("pull_request", {}).get("number")
        if event_type in ("pull_request", "pull_request_review_comment")
        else task.get("issue", {}).get("number")
    )
    if not number:
        logger.warning("missing_github_number", task_id=task.get("task_id"))
        return False

    parts = full_name.split("/", 1)
    owner = parts[0] if len(parts) == 2 else ""
    repo = parts[1] if len(parts) == 2 else ""

    prefix = "" if success else "Task failed.\n\n"
    body = f"{prefix}{output}"
    if len(body) > 8000:
        body = body[:7990] + "\n..."

    url = f"{github_api_url}/api/v1/repos/{owner}/{repo}/issues/{number}/comments"
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json={"body": body})
            response.raise_for_status()
        logger.info(
            "github_completion_posted",
            task_id=task.get("task_id"),
            repo=full_name,
            number=number,
        )
        return True
    except Exception as e:
        logger.error(
            "github_completion_failed",
            task_id=task.get("task_id"),
            error=str(e),
        )
        return False
