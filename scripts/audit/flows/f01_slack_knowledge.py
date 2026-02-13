from ..core.evaluator import FlowCriteria
from ..triggers.base import TriggerResult
from .base import BaseFlow


class SlackKnowledgeFlow(BaseFlow):
    name = "f01_slack_knowledge"
    description = "Slack → Knowledge Query"

    async def trigger(self) -> TriggerResult:
        from ..triggers.slack import SlackTrigger

        trigger = SlackTrigger(self._client, self._config)
        return await trigger.send_message(
            "What are the main components and architecture of the manga-creator repo?"
        )

    def expected_agent(self) -> str:
        return "slack-inquiry"

    def flow_criteria(self) -> FlowCriteria:
        return FlowCriteria(
            expected_agent="slack-inquiry",
            required_tools=[
                "knowledge_query",
                "code_search",
                "search_jira_tickets",
                "search_confluence",
            ],
            required_response_tools=["send_slack_message"],
            required_output_patterns=["manga"],
            min_output_length=100,
            max_execution_seconds=120.0,
            requires_knowledge=True,
        )

    async def cleanup(self) -> None:
        pass
