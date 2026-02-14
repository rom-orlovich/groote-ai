from ..core.evaluator import FlowCriteria
from ..triggers.base import TriggerResult
from .base import BaseFlow


class SlackKnowledgeFlow(BaseFlow):
    name = "f01_slack_knowledge"
    description = "Slack → Knowledge Query (target repo)"

    async def trigger(self) -> TriggerResult:
        from ..triggers.slack import SlackTrigger

        repo = self._config.github_repo
        owner = self._config.github_owner
        trigger = SlackTrigger(self._client, self._config)
        return await trigger.send_message(
            f"@agent [Audit] What is the {repo} project? "
            f"Describe its architecture and main features. "
            f"Search the knowledge layer for {owner}/{repo} code and documentation."
        )

    def expected_agent(self) -> str:
        return "slack-inquiry"

    def flow_criteria(self) -> FlowCriteria:
        repo = self._config.github_repo
        return FlowCriteria(
            expected_agent="slack-inquiry",
            required_tools=[
                "knowledge_query",
            ],
            required_response_tools=["send_slack_message"],
            required_output_patterns=[repo],
            domain_terms=[
                repo,
                "architecture",
                "feature",
                "component",
                "service",
                "module",
                "endpoint",
                "database",
            ],
            negative_terms=[
                "groote-ai",
                "groote",
                "webhook",
                "api-gateway",
                "agent-engine",
                "dashboard-api",
            ],
            target_repo=repo,
            min_output_length=200,
            max_execution_seconds=180.0,
            requires_knowledge=True,
        )

    async def cleanup(self) -> None:
        pass
