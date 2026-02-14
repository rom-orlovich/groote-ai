import logging
import time
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

from ..triggers.base import TriggerResult

if TYPE_CHECKING:
    from ..config import AuditConfig
    from ..core.client import AuditClient
    from ..core.evaluator import FlowCriteria
    from ..core.redis_monitor import RedisEventMonitor

logger = logging.getLogger(__name__)


class FlowResult(BaseModel):
    model_config = ConfigDict(strict=True)

    name: str
    description: str
    passed: bool
    components: list[dict] = []
    checkpoints: list[dict] = []
    quality_score: int | None = None
    quality_report: dict | None = None
    duration_seconds: float = 0.0
    evidence_dir: str | None = None
    error: str | None = None
    task_id: str | None = None
    conversation_id: str | None = None
    trigger_result: dict | None = None


class BaseFlow(ABC):
    name: str
    description: str

    def __init__(
        self,
        client: "AuditClient",
        monitor: "RedisEventMonitor",
        config: "AuditConfig",
        evidence_collector: object | None = None,
    ) -> None:
        self._client = client
        self._monitor = monitor
        self._config = config
        self._evidence = evidence_collector

    @abstractmethod
    async def trigger(self) -> TriggerResult:
        ...

    @abstractmethod
    def expected_agent(self) -> str:
        ...

    @abstractmethod
    def flow_criteria(self) -> "FlowCriteria":
        ...

    def requires_knowledge(self) -> bool:
        return True

    def _infer_source(self) -> str:
        name = self.name.lower()
        if "slack" in name:
            return "slack"
        if "jira" in name:
            return "jira"
        if "github" in name:
            return "github"
        return ""

    async def run(self) -> FlowResult:
        start = time.monotonic()
        try:
            source = self._infer_source()
            if source:
                self._monitor.clear_source_events(source)

            trigger_result = await self.trigger()
            logger.info(
                "flow_triggered",
                extra={
                    "flow": self.name,
                    "platform": trigger_result.platform,
                    "artifact_id": trigger_result.artifact_id,
                },
            )

            task_id = await self._discover_task_id(trigger_result)
            await self._wait_for_completion(task_id)
            await self._wait_for_response_posted(task_id)
            conversation_id = await self._extract_conversation_id(task_id)
            components = await self._run_component_audit(
                task_id, trigger_result, conversation_id
            )
            quality = await self._run_quality_evaluation(task_id)
            await self._save_evidence(task_id, components, quality)

            all_components_ok = all(
                c.status != "failed" for c in components
            )

            return FlowResult(
                name=self.name,
                description=self.description,
                passed=all_components_ok and quality.passed,
                components=[c.model_dump() for c in components],
                quality_score=quality.overall_score,
                quality_report=quality.model_dump(),
                duration_seconds=round(time.monotonic() - start, 2),
                evidence_dir=str(self._evidence.base_dir) if self._evidence and hasattr(self._evidence, "base_dir") else None,
                task_id=task_id,
                conversation_id=conversation_id,
                trigger_result=trigger_result.model_dump(),
            )
        except Exception as exc:
            logger.exception("flow_failed", extra={"flow": self.name})
            return FlowResult(
                name=self.name,
                description=self.description,
                passed=False,
                duration_seconds=round(time.monotonic() - start, 2),
                error=str(exc),
            )

    async def _discover_task_id(self, trigger_result: TriggerResult) -> str:
        source = trigger_result.platform
        timeout = self._config.timeout_task_created * self._config.timeout_multiplier
        event = await self._monitor.wait_for_source_event(
            source, "webhook:task_created", timeout
        )
        if not event:
            raise TimeoutError(
                f"No webhook:task_created event for source={source} "
                f"within {timeout}s"
            )
        task_id = event.get("data", {}).get("task_id", "")
        if not task_id:
            raise ValueError("webhook:task_created event missing task_id")
        logger.info("task_discovered", extra={"task_id": task_id})
        return task_id

    async def _wait_for_completion(self, task_id: str) -> None:
        timeout = self._config.timeout_execution * self._config.timeout_multiplier
        event = await self._monitor.wait_for_event(
            task_id, "task:completed", timeout
        )
        if not event:
            raise TimeoutError(
                f"task:completed not received for {task_id} within {timeout}s"
            )
        logger.info("task_completed", extra={"task_id": task_id})

    async def _wait_for_response_posted(self, task_id: str) -> None:
        timeout = self._config.timeout_response * self._config.timeout_multiplier
        event = await self._monitor.wait_for_event(
            task_id, "task:response_posted", timeout
        )
        if event:
            logger.info("response_posted_received", extra={"task_id": task_id})
        else:
            logger.warning("response_posted_timeout", extra={"task_id": task_id})

    async def _extract_conversation_id(self, task_id: str) -> str | None:
        events = await self._monitor.get_events_for_task(task_id)
        context_events = [
            e for e in events if e.get("type") == "task:context_built"
        ]
        if context_events:
            return context_events[0].get("data", {}).get("conversation_id")
        return None

    async def _run_component_audit(
        self,
        task_id: str,
        trigger_result: TriggerResult,
        conversation_id: str | None,
    ) -> list:
        from ..core.component_monitor import ComponentMonitor

        comp_monitor = ComponentMonitor(self._client, self._monitor)
        return await comp_monitor.full_component_audit(
            task_id,
            self.expected_agent(),
            trigger_result.expected_flow_id,
            conversation_id or "",
        )

    async def _run_quality_evaluation(self, task_id: str) -> object:
        from ..core.evaluator import QualityEvaluator

        evaluator = QualityEvaluator(self._client, self._monitor)
        return await evaluator.evaluate(task_id, self.flow_criteria())

    async def _save_evidence(
        self,
        task_id: str,
        components: list,
        quality: object,
    ) -> None:
        if not self._evidence:
            return
        try:
            events = await self._monitor.get_events_for_task(task_id)
            await self._evidence.save_events(events)
            await self._evidence.save_component_status(
                [c.model_dump() for c in components]
            )
            await self._evidence.save_quality_report(quality.model_dump())
        except Exception:
            logger.exception("evidence_save_failed", extra={"task_id": task_id})

    async def _warm_knowledge_services(self) -> None:
        import httpx

        urls = [
            f"{self._config.llamaindex_url}/health",
            f"{self._config.gkg_url}/health",
        ]
        async with httpx.AsyncClient(timeout=5.0) as http:
            for url in urls:
                try:
                    await http.get(url)
                except Exception:
                    pass

    async def cleanup(self) -> None:  # noqa: B027
        pass
