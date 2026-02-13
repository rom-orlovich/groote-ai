import logging
from datetime import UTC, datetime

from ..config import AuditConfig
from ..core.client import AuditClient
from .base import TriggerResult

logger = logging.getLogger(__name__)


class JiraTrigger:
    def __init__(self, client: AuditClient, config: AuditConfig) -> None:
        self._client = client
        self._config = config

    async def create_ticket(
        self,
        summary: str,
        description: str,
        labels: list[str] | None = None,
    ) -> TriggerResult:
        payload = {
            "project_key": self._config.jira_project,
            "summary": summary,
            "description": description,
            "issue_type": "Task",
        }

        response = await self._client.post_jira_api("/api/v1/issues", json=payload)
        data = response.json()
        issue_key = data["key"]

        if labels:
            label_fields = {"labels": [{"name": label} for label in labels]}
            await self._client.http.put(
                f"{self._config.jira_api_url}/api/v1/issues/{issue_key}",
                json={"fields": label_fields},
            )

        flow_id = f"jira:{issue_key}"

        logger.info(
            "jira_ticket_created",
            extra={"issue_key": issue_key, "flow_id": flow_id},
        )

        return TriggerResult(
            platform="jira",
            artifact_type="ticket",
            artifact_id=issue_key,
            artifact_url=data.get("self"),
            trigger_time=datetime.now(UTC),
            expected_flow_id=flow_id,
            raw_response=data,
        )

    async def add_comment(self, issue_key: str, body: str) -> TriggerResult:
        path = f"/api/v1/issues/{issue_key}/comments"
        response = await self._client.post_jira_api(path, json={"body": body})
        data = response.json()
        flow_id = f"jira:{issue_key}"

        logger.info(
            "jira_comment_added",
            extra={"issue_key": issue_key, "flow_id": flow_id},
        )

        return TriggerResult(
            platform="jira",
            artifact_type="comment",
            artifact_id=issue_key,
            artifact_url=data.get("self"),
            trigger_time=datetime.now(UTC),
            expected_flow_id=flow_id,
            raw_response=data,
        )

    async def cleanup_ticket(self, issue_key: str) -> None:
        transitions_resp = await self._client.get_jira_api(
            f"/api/v1/issues/{issue_key}/transitions"
        )
        transitions = transitions_resp.json()

        done_id: str | None = None
        for transition in transitions.get("transitions", []):
            name = transition.get("name", "").lower()
            if name in ("done", "closed", "resolved"):
                done_id = transition["id"]
                break

        if done_id:
            await self._client.post_jira_api(
                f"/api/v1/issues/{issue_key}/transitions",
                json={"transition_id": done_id},
            )
            logger.info("jira_ticket_closed", extra={"issue_key": issue_key})
        else:
            logger.warning(
                "jira_no_done_transition",
                extra={"issue_key": issue_key},
            )
