import httpx
import structlog

logger = structlog.get_logger(__name__)


async def post_completion(jira_api_url: str, task: dict, output: str, success: bool) -> bool:
    issue_key = task.get("issue", {}).get("key")
    if not issue_key:
        logger.warning("missing_jira_key", task_id=task.get("task_id"))
        return False

    prefix = "" if success else "Task failed.\n\n"
    body = f"{prefix}{output}"
    if len(body) > 8000:
        body = body[:7990] + "\n..."

    url = f"{jira_api_url}/api/v1/issues/{issue_key}/comments"
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json={"body": body})
            response.raise_for_status()
        logger.info(
            "jira_completion_posted",
            task_id=task.get("task_id"),
            issue_key=issue_key,
        )
        return True
    except Exception as e:
        logger.error(
            "jira_completion_failed",
            task_id=task.get("task_id"),
            error=str(e),
        )
        return False
