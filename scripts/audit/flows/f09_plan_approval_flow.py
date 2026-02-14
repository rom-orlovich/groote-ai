from ..core.evaluator import FlowCriteria
from ..triggers.base import TriggerResult
from .base import BaseFlow


class PlanApprovalFlow(BaseFlow):
    name = "f09_plan_approval_flow"
    description = "Jira → Plan with PR Creation → Verify"

    async def trigger(self) -> TriggerResult:
        from ..triggers.jira import JiraTrigger

        repo = self._config.github_repo
        owner = self._config.github_owner
        trigger = JiraTrigger(self._client, self._config)
        return await trigger.create_ticket(
            summary=f"[ai-agent] Add rate limiting to {repo} API endpoints",
            description=(
                f"Add rate limiting middleware to the {repo} project ({owner}/{repo}). "
                f"Search the knowledge layer for {owner}/{repo} to understand the current API structure. "
                f"Create a detailed implementation plan with specific files to change. "
                f"Then use create_branch and create_pull_request to open a draft PR on {owner}/{repo} with the plan as the PR body."
            ),
            labels=["ai-agent"],
        )

    def expected_agent(self) -> str:
        return "jira-code-plan"

    def flow_criteria(self) -> FlowCriteria:
        repo = self._config.github_repo
        return FlowCriteria(
            expected_agent="jira-code-plan",
            required_tools=[
                "knowledge_query",
                "code_search",
                "create_pull_request",
            ],
            required_response_tools=["add_jira_comment"],
            required_output_patterns=[
                r"[Pp]lan",
                r"rate[\s\-_]?limit",
                repo,
                r"[Pp]ull [Rr]equest|PR|draft",
            ],
            negative_output_patterns=[
                r"groote[\s\-]?ai",
            ],
            domain_terms=[
                repo,
                "rate limit",
                "API",
                "endpoint",
                "middleware",
                "plan",
                "file",
                "change",
            ],
            negative_terms=[
                "groote-ai",
                "groote",
                "api-gateway",
                "agent-engine",
                "dashboard-api",
            ],
            target_repo=repo,
            min_output_length=200,
            max_execution_seconds=300.0,
            requires_knowledge=True,
        )

    async def cleanup(self) -> None:
        pass
