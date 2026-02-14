import httpx
import structlog

logger = structlog.get_logger(__name__)

MESSAGE_PROCESSING = "Agent is analyzing this issue and will respond shortly."


async def send_jira_comment(jira_api_url: str, issue_key: str, body: str) -> dict[str, object]:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{jira_api_url}/api/v1/issues/{issue_key}/comments",
                json={"body": body},
            )
            response.raise_for_status()
        comment_id = None
        try:
            resp_data = response.json()
            comment_id = resp_data.get("id") or resp_data.get("comment_id")
        except Exception:
            pass
        logger.info("jira_comment_sent", issue_key=issue_key, comment_id=comment_id)
        return {"sent": True, "comment_id": comment_id}
    except Exception as e:
        logger.warning("jira_comment_failed", error=str(e), issue_key=issue_key)
        return {"sent": False, "comment_id": None}


async def send_immediate_response(jira_api_url: str, issue_key: str) -> dict[str, object]:
    return await send_jira_comment(jira_api_url, issue_key, MESSAGE_PROCESSING)


async def send_error_response(jira_api_url: str, issue_key: str, error: str) -> dict[str, object]:
    return await send_jira_comment(jira_api_url, issue_key, f"Failed to process: {error}")


async def post_completion_comment(
    jira_api_url: str, issue_key: str, output: str, success: bool
) -> dict[str, object]:
    prefix = "" if success else "Task failed.\n\n"
    body = f"{prefix}{output}"
    if len(body) > 8000:
        body = body[:7990] + "\n..."
    return await send_jira_comment(jira_api_url, issue_key, body)
