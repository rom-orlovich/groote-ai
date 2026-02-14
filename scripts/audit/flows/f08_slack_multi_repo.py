from ..core.evaluator import FlowCriteria
from ..triggers.base import TriggerResult
from .base import BaseFlow


class SlackMultiRepoFlow(BaseFlow):
    name = "f08_slack_multi_repo"
    description = "Slack → Knowledge-First Multi-Repo Inquiry"

    async def trigger(self) -> TriggerResult:
        from ..triggers.slack import SlackTrigger

        repo = self._config.github_repo
        owner = self._config.github_owner
        trigger = SlackTrigger(self._client, self._config)
        return await trigger.send_message(
            f"@agent [Audit] How does user authentication work in the {repo} project ({owner}/{repo})? "
            f"Search the knowledge layer for {owner}/{repo} to identify how auth is implemented, "
            f"describe the auth flow, and list the key files involved."
        )

    def expected_agent(self) -> str:
        return "slack-inquiry"

    def flow_criteria(self) -> FlowCriteria:
        repo = self._config.github_repo
        return FlowCriteria(
            expected_agent="slack-inquiry",
            required_tools=[
                "knowledge_query",
                "code_search",
            ],
            required_response_tools=["send_slack_message"],
            required_output_patterns=[
                repo,
                r"auth",
            ],
            domain_terms=[
                repo,
                "auth",
                "token",
                "login",
                "session",
                "middleware",
                "user",
                "credential",
            ],
            negative_terms=[
                "groote-ai",
                "groote",
                "webhook",
                "api-gateway",
                "agent-engine",
                "dashboard-api",
                "oauth-service",
            ],
            target_repo=repo,
            min_output_length=200,
            max_execution_seconds=180.0,
            requires_knowledge=True,
        )

    async def cleanup(self) -> None:
        pass
