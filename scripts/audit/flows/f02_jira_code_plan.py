from ..core.evaluator import FlowCriteria
from ..triggers.base import TriggerResult
from .base import BaseFlow


class JiraCodePlanFlow(BaseFlow):
    name = "f02_jira_code_plan"
    description = "Jira Ticket → Code Plan + PR"

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        self._ticket_key: str | None = None

    async def trigger(self) -> TriggerResult:
        from ..triggers.jira import JiraTrigger

        trigger = JiraTrigger(self._client, self._config)
        result = await trigger.create_ticket(
            summary="[Audit] Add input validation to manga panel generator",
            description=(
                "The manga-creator panel generator does not validate input "
                "dimensions. Add validation for width, height, and format "
                "parameters."
            ),
            labels=["AI-Fix"],
        )
        self._ticket_key = result.artifact_id
        return result

    def expected_agent(self) -> str:
        return "jira-code-plan"

    def flow_criteria(self) -> FlowCriteria:
        return FlowCriteria(
            expected_agent="jira-code-plan",
            required_tools=["get_jira_issue", "knowledge_query", "code_search"],
            required_response_tools=["add_jira_comment"],
            required_output_patterns=["Implementation", "##"],
            min_output_length=200,
            max_execution_seconds=300.0,
            requires_knowledge=True,
        )

    async def cleanup(self) -> None:
        if self._ticket_key:
            from ..triggers.jira import JiraTrigger

            trigger = JiraTrigger(self._client, self._config)
            await trigger.cleanup_ticket(self._ticket_key)
