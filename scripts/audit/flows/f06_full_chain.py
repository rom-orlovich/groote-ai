import logging
import time

from ..core.evaluator import FlowCriteria
from ..triggers.base import TriggerResult
from .base import BaseFlow, FlowResult

logger = logging.getLogger(__name__)


class FullChainFlow(BaseFlow):
    name = "f06_full_chain"
    description = "Full Chain: Jira → PR → PR Review"

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        self._ticket_key: str | None = None

    async def trigger(self) -> TriggerResult:
        from ..triggers.jira import JiraTrigger

        trigger = JiraTrigger(self._client, self._config)
        result = await trigger.create_ticket(
            summary="[Audit-Chain] Implement input validation for manga panel sizes",
            description=(
                "Add comprehensive input validation for panel width, height, "
                "and format. This should include range checks and type validation."
            ),
            labels=["ai-agent"],
        )
        self._ticket_key = result.artifact_id
        return result

    def expected_agent(self) -> str:
        return "jira-code-plan"

    def flow_criteria(self) -> FlowCriteria:
        return FlowCriteria(
            expected_agent="jira-code-plan",
            required_tools=["get_jira_issue"],
            required_response_tools=["add_jira_comment"],
            required_output_patterns=[],
            min_output_length=100,
            max_execution_seconds=300.0,
            requires_knowledge=True,
        )

    async def run(self) -> FlowResult:
        start = time.monotonic()

        phase1_result = await super().run()
        if not phase1_result.passed:
            phase1_result.error = (
                f"Phase 1 failed: {phase1_result.error or 'components/quality check failed'}"
            )
            return phase1_result

        try:
            return await self._run_phase2(start, phase1_result)
        except TimeoutError:
            return FlowResult(
                name=self.name,
                description=self.description,
                passed=False,
                components=phase1_result.components,
                quality_score=phase1_result.quality_score,
                duration_seconds=round(time.monotonic() - start, 2),
                task_id=phase1_result.task_id,
                error="Phase 2 failed: PR webhook not received within timeout",
            )

    async def _run_phase2(
        self,
        start: float,
        phase1_result: FlowResult,
    ) -> FlowResult:
        task_id = phase1_result.task_id
        if not task_id:
            raise ValueError("Phase 1 did not produce a task_id")

        tool_calls = await self._monitor.get_tool_calls(task_id)
        pr_created = any(
            "create_pull_request" in str(tc.get("data", {}).get("name", "")) for tc in tool_calls
        )

        if not pr_created:
            logger.info("chain_no_pr_created", extra={"task_id": task_id})
            return FlowResult(
                name=self.name,
                description=self.description,
                passed=True,
                components=phase1_result.components,
                quality_score=phase1_result.quality_score,
                quality_report=phase1_result.quality_report,
                duration_seconds=round(time.monotonic() - start, 2),
                task_id=task_id,
                error="Phase 2 skipped: no PR was created by phase 1",
            )

        pr_event = await self._monitor.wait_for_source_event(
            "github",
            "webhook:task_created",
            self._config.timeout_webhook * self._config.timeout_multiplier * 2,
        )
        if not pr_event:
            raise TimeoutError("PR webhook:task_created not received")

        pr_task_id = pr_event.get("data", {}).get("task_id", "")
        if not pr_task_id:
            raise ValueError("PR task_created event missing task_id")

        completed = await self._monitor.wait_for_event(
            pr_task_id,
            "task:completed",
            self._config.timeout_execution * self._config.timeout_multiplier,
        )
        if not completed:
            raise TimeoutError(f"PR task {pr_task_id} did not complete")

        from ..core.component_monitor import ComponentMonitor

        comp_monitor = ComponentMonitor(self._client, self._monitor)
        owner = self._config.github_owner
        repo = self._config.github_repo
        pr_flow_id = f"github:{owner}/{repo}#unknown"
        pr_components = await comp_monitor.full_component_audit(
            pr_task_id, "github-pr-review", pr_flow_id, ""
        )

        all_ok = all(c.status != "failed" for c in pr_components)
        return FlowResult(
            name=self.name,
            description=self.description,
            passed=phase1_result.passed and all_ok,
            components=phase1_result.components + [c.model_dump() for c in pr_components],
            quality_score=phase1_result.quality_score,
            duration_seconds=round(time.monotonic() - start, 2),
            task_id=task_id,
        )

    async def cleanup(self) -> None:
        if self._ticket_key:
            from ..triggers.jira import JiraTrigger

            trigger = JiraTrigger(self._client, self._config)
            await trigger.cleanup_ticket(self._ticket_key)
