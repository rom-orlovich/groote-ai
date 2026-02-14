import asyncio

from ..core.evaluator import FlowCriteria
from ..triggers.base import TriggerResult
from .base import BaseFlow


class JiraCommentFlow(BaseFlow):
    name = "f05_jira_comment"
    description = "Jira Comment → Agent Follow-up"

    def __init__(
        self,
        *args: object,
        existing_ticket_key: str | None = None,
        **kwargs: object,
    ) -> None:
        super().__init__(*args, **kwargs)
        self._ticket_key = existing_ticket_key
        self._created_ticket = False

    async def trigger(self) -> TriggerResult:
        from ..triggers.jira import JiraTrigger

        trigger = JiraTrigger(self._client, self._config)

        if not self._ticket_key:
            ticket = await trigger.create_ticket(
                summary="[Audit] Analyze panel generator edge cases",
                description=("Review the manga-creator panel generator for edge cases."),
                labels=["ai-agent"],
            )
            self._ticket_key = ticket.artifact_id
            self._created_ticket = True
            await asyncio.sleep(5)

        return await trigger.add_comment(
            self._ticket_key,
            "Can you also check if the panel generator handles edge cases for very large images?",
        )

    def expected_agent(self) -> str:
        return "jira-code-plan"

    def flow_criteria(self) -> FlowCriteria:
        return FlowCriteria(
            expected_agent="jira-code-plan",
            required_tools=[],
            required_response_tools=["add_jira_comment"],
            required_output_patterns=[],
            min_output_length=100,
            max_execution_seconds=120.0,
            requires_knowledge=True,
        )

    async def cleanup(self) -> None:
        if self._created_ticket and self._ticket_key:
            from ..triggers.jira import JiraTrigger

            trigger = JiraTrigger(self._client, self._config)
            await trigger.cleanup_ticket(self._ticket_key)
