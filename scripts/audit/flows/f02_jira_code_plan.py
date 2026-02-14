from ..core.evaluator import FlowCriteria
from ..triggers.base import TriggerResult
from .base import BaseFlow


class JiraCodePlanFlow(BaseFlow):
    name = "f02_jira_code_plan"
    description = "Jira Ticket → Code Plan + PR"

    def __init__(
        self,
        *args: object,
        existing_ticket_key: str | None = None,
        **kwargs: object,
    ) -> None:
        super().__init__(*args, **kwargs)
        self._ticket_key = existing_ticket_key
        self._created_ticket = not bool(existing_ticket_key)

    async def trigger(self) -> TriggerResult:
        from ..triggers.jira import JiraTrigger

        trigger = JiraTrigger(self._client, self._config)

        if self._ticket_key:
            return await trigger.fire_existing_ticket_webhook(
                self._ticket_key,
                self._client,
                self._config,
            )

        repo = self._config.github_repo
        owner = self._config.github_owner
        result = await trigger.create_ticket(
            summary=f"[ai-agent] Add input validation to {repo} panel generator",
            description=(
                f"The {repo} panel generator does not validate input "
                f"dimensions. Add validation for width, height, and format "
                f"parameters. Search the knowledge layer for {owner}/{repo} "
                f"to understand the current code structure. "
                f"Create a detailed implementation plan and open a draft PR "
                f"on {owner}/{repo} with the plan."
            ),
            labels=["ai-agent"],
        )
        self._ticket_key = result.artifact_id
        return result

    def expected_agent(self) -> str:
        return "jira-code-plan"

    def flow_criteria(self) -> FlowCriteria:
        repo = self._config.github_repo
        return FlowCriteria(
            expected_agent="jira-code-plan",
            required_tools=[
                "get_jira_issue",
                "knowledge_query",
                "code_search",
                "create_pull_request",
            ],
            required_response_tools=["add_jira_comment"],
            required_output_patterns=[
                r"[Pp]lan",
                r"[Vv]alidat",
                repo,
                r"[Pp]ull [Rr]equest|PR|draft",
            ],
            negative_terms=[
                "groote-ai", "groote", "api-gateway",
                "agent-engine", "dashboard-api",
            ],
            target_repo=repo,
            min_output_length=200,
            max_execution_seconds=300.0,
            requires_knowledge=True,
        )

    async def cleanup(self) -> None:
        if self._created_ticket and self._ticket_key:
            from ..triggers.jira import JiraTrigger

            trigger = JiraTrigger(self._client, self._config)
            await trigger.cleanup_ticket(self._ticket_key)
