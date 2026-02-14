from ..core.evaluator import FlowCriteria
from ..triggers.base import TriggerResult
from .base import BaseFlow


class GitHubPRReviewFlow(BaseFlow):
    name = "f04_github_pr_review"
    description = "GitHub PR → Agent Review"

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        self._pr_number: int | None = None

    async def trigger(self) -> TriggerResult:
        from ..triggers.github import GitHubTrigger

        trigger = GitHubTrigger(self._client, self._config)
        result = await trigger.create_branch_and_pr(
            title="[Audit] Add type hints to core modules",
            body="Added type hints to improve code quality and IDE support.",
        )
        self._pr_number = int(result.artifact_id)
        return result

    def expected_agent(self) -> str:
        return "github-pr-review"

    def flow_criteria(self) -> FlowCriteria:
        return FlowCriteria(
            expected_agent="github-pr-review",
            required_tools=["get_pull_request", "get_file_contents"],
            required_response_tools=["add_issue_comment"],
            required_output_patterns=[],
            min_output_length=100,
            max_execution_seconds=180.0,
            requires_knowledge=False,
        )

    async def cleanup(self) -> None:
        if self._pr_number:
            from ..triggers.github import GitHubTrigger

            trigger = GitHubTrigger(self._client, self._config)
            await trigger.cleanup_pr(self._pr_number)
