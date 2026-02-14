import logging
from datetime import UTC, datetime

from ..config import AuditConfig
from ..core.client import AuditClient
from .base import TriggerResult

logger = logging.getLogger(__name__)


class GitHubTrigger:
    def __init__(self, client: AuditClient, config: AuditConfig) -> None:
        self._client = client
        self._config = config

    @property
    def _owner(self) -> str:
        return self._config.github_owner

    @property
    def _repo(self) -> str:
        return self._config.github_repo

    def _repo_prefix(self) -> str:
        return f"/api/v1/repos/{self._owner}/{self._repo}"

    async def create_issue(
        self,
        title: str,
        body: str,
        labels: list[str] | None = None,
    ) -> TriggerResult:
        path = f"{self._repo_prefix()}/issues"
        payload: dict = {"title": title, "body": body}
        if labels:
            payload["labels"] = labels

        response = await self._client.post_github_api(path, json=payload)
        data = response.json()
        number = data["number"]
        flow_id = f"github:{self._owner}/{self._repo}#{number}"

        logger.info(
            "github_issue_created",
            extra={"number": number, "flow_id": flow_id},
        )

        return TriggerResult(
            platform="github",
            artifact_type="issue",
            artifact_id=str(number),
            artifact_url=data.get("html_url"),
            trigger_time=datetime.now(UTC),
            expected_flow_id=flow_id,
            raw_response=data,
        )

    async def create_issue_comment(
        self,
        issue_number: int,
        body: str,
    ) -> TriggerResult:
        path = f"{self._repo_prefix()}/issues/{issue_number}/comments"
        response = await self._client.post_github_api(path, json={"body": body})
        data = response.json()
        flow_id = f"github:{self._owner}/{self._repo}#{issue_number}"

        logger.info(
            "github_comment_created",
            extra={"issue_number": issue_number, "flow_id": flow_id},
        )

        return TriggerResult(
            platform="github",
            artifact_type="comment",
            artifact_id=str(data.get("id", issue_number)),
            artifact_url=data.get("html_url"),
            trigger_time=datetime.now(UTC),
            expected_flow_id=flow_id,
            raw_response=data,
        )

    async def create_pr_comment(
        self,
        pr_number: int,
        body: str,
    ) -> TriggerResult:
        path = f"{self._repo_prefix()}/issues/{pr_number}/comments"
        response = await self._client.post_github_api(path, json={"body": body})
        data = response.json()
        flow_id = f"github:{self._owner}/{self._repo}#{pr_number}"

        logger.info(
            "github_pr_comment_created",
            extra={"pr_number": pr_number, "flow_id": flow_id},
        )

        return TriggerResult(
            platform="github",
            artifact_type="pr_comment",
            artifact_id=str(data.get("id", pr_number)),
            artifact_url=data.get("html_url"),
            trigger_time=datetime.now(UTC),
            expected_flow_id=flow_id,
            raw_response=data,
        )

    async def create_branch_and_pr(
        self,
        title: str,
        body: str,
    ) -> TriggerResult:
        timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
        head_branch = f"audit-{timestamp}"

        path = f"{self._repo_prefix()}/pulls"
        payload = {
            "title": title,
            "body": body,
            "head": head_branch,
            "base": "main",
        }

        response = await self._client.post_github_api(path, json=payload)
        data = response.json()
        pr_number = data["number"]
        flow_id = f"github:{self._owner}/{self._repo}#{pr_number}"

        logger.info(
            "github_pr_created",
            extra={"pr_number": pr_number, "flow_id": flow_id},
        )

        return TriggerResult(
            platform="github",
            artifact_type="pull_request",
            artifact_id=str(pr_number),
            artifact_url=data.get("html_url"),
            trigger_time=datetime.now(UTC),
            expected_flow_id=flow_id,
            raw_response=data,
        )

    async def cleanup_issue(self, issue_number: int) -> None:
        path = f"{self._repo_prefix()}/issues/{issue_number}/comments"
        await self._client.post_github_api(
            path, json={"body": "Audit complete, closing"}
        )
        logger.info("github_issue_cleanup", extra={"issue_number": issue_number})

    async def cleanup_pr(self, pr_number: int) -> None:
        path = f"{self._repo_prefix()}/issues/{pr_number}/comments"
        await self._client.post_github_api(
            path, json={"body": "Audit complete, closing"}
        )
        logger.info("github_pr_cleanup", extra={"pr_number": pr_number})
