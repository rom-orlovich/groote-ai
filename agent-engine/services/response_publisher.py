import httpx
import structlog

logger = structlog.get_logger(__name__)


class ResponsePublisher:
    def __init__(
        self, github_api_url: str, jira_api_url: str, slack_api_url: str, timeout: float = 30.0
    ):
        self._github_api_url = github_api_url.rstrip("/")
        self._jira_api_url = jira_api_url.rstrip("/")
        self._slack_api_url = slack_api_url.rstrip("/")
        self._timeout = timeout

    async def post_response(self, task: dict, result: dict) -> bool:
        handlers = {"github": self._post_github, "jira": self._post_jira, "slack": self._post_slack}
        handler = handlers.get(task.get("source"))
        if not handler:
            logger.warning("unknown_source", source=task.get("source"), task_id=task.get("task_id"))
            return False
        return await handler(task, result)

    async def _post_github(self, task: dict, result: dict) -> bool:
        full_name = task.get("repository", {}).get("full_name")
        if not full_name:
            logger.warning("missing_github_repo", task_id=task.get("task_id"))
            return False
        event_type = task.get("event_type")
        number = (
            task.get("pull_request", {}).get("number")
            if event_type == "pull_request"
            else task.get("issue", {}).get("number")
        )
        if not number:
            logger.warning("missing_github_number", task_id=task.get("task_id"))
            return False
        url = f"{self._github_api_url}/api/repos/{full_name}/issues/{number}/comments"
        return await self._post_request(
            url,
            {"body": result.get("output", "")},
            "github",
            task.get("task_id"),
            {"repo": full_name, "number": number},
        )

    async def _post_jira(self, task: dict, result: dict) -> bool:
        issue_key = task.get("issue", {}).get("key")
        if not issue_key:
            logger.warning("missing_jira_key", task_id=task.get("task_id"))
            return False
        url = f"{self._jira_api_url}/api/issues/{issue_key}/comments"
        return await self._post_request(
            url,
            {"body": result.get("output", "")},
            "jira",
            task.get("task_id"),
            {"issue_key": issue_key},
        )

    async def _post_slack(self, task: dict, result: dict) -> bool:
        channel = task.get("channel")
        if not channel:
            logger.warning("missing_slack_channel", task_id=task.get("task_id"))
            return False
        payload = {"channel": channel, "text": result.get("output", "")}
        thread_ts = task.get("thread_ts")
        if thread_ts:
            payload["thread_ts"] = thread_ts
        url = f"{self._slack_api_url}/api/chat/postMessage"
        return await self._post_request(
            url,
            payload,
            "slack",
            task.get("task_id"),
            {"channel": channel, "threaded": bool(thread_ts)},
        )

    async def _post_request(
        self, url: str, payload: dict, platform: str, task_id: str | None, log_metadata: dict
    ) -> bool:
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
            logger.info(f"{platform}_response_posted", task_id=task_id, **log_metadata)
            return True
        except httpx.HTTPError as e:
            logger.error(f"{platform}_post_failed", task_id=task_id, error=str(e))
            return False
        except Exception as e:
            logger.error(f"{platform}_post_error", task_id=task_id, error=str(e))
            return False
