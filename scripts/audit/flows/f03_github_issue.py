from ..core.evaluator import FlowCriteria
from ..triggers.base import TriggerResult
from .base import BaseFlow


class GitHubIssueFlow(BaseFlow):
    name = "f03_github_issue"
    description = "GitHub Issue → Agent Analysis"

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        self._issue_number: int | None = None

    async def trigger(self) -> TriggerResult:
        from ..triggers.github import GitHubTrigger

        trigger = GitHubTrigger(self._client, self._config)
        result = await trigger.create_issue(
            title="[Audit] Analyze error handling patterns",
            body=(
                "Please analyze error handling patterns in this codebase. "
                "Identify files that could benefit from better error handling."
            ),
        )
        self._issue_number = int(result.artifact_id)
        return result

    def expected_agent(self) -> str:
        return "github-issue-handler"

    def flow_criteria(self) -> FlowCriteria:
        return FlowCriteria(
            expected_agent="github-issue-handler",
            required_tools=["knowledge_query", "code_search"],
            required_response_tools=["add_issue_comment"],
            required_output_patterns=["Agent Analysis", "##"],
            min_output_length=200,
            max_execution_seconds=180.0,
            requires_knowledge=True,
        )

    async def cleanup(self) -> None:
        if self._issue_number:
            from ..triggers.github import GitHubTrigger

            trigger = GitHubTrigger(self._client, self._config)
            await trigger.cleanup_issue(self._issue_number)
