import logging

from .client import AuditClient
from .redis_monitor import RedisEventMonitor
from .scoring import (
    DIMENSION_WEIGHTS,
    FlowCriteria,
    QualityDimension,
    QualityReport,
    score_completeness,
    score_delivery,
    score_errors,
    score_execution,
    score_knowledge,
    score_relevance,
    score_routing,
    score_tool_efficiency,
)

logger = logging.getLogger(__name__)


class QualityEvaluator:
    def __init__(
        self,
        client: AuditClient,
        monitor: RedisEventMonitor,
        pass_threshold: int = 70,
    ) -> None:
        self._client = client
        self._monitor = monitor
        self._pass_threshold = pass_threshold

    async def evaluate(
        self, task_id: str, criteria: FlowCriteria
    ) -> QualityReport:
        events = await self._monitor.get_events_for_task(task_id)
        tool_calls = await self._monitor.get_tool_calls(task_id)

        dimensions = [
            score_routing(events, criteria),
            score_tool_efficiency(tool_calls, criteria),
            score_knowledge(tool_calls, criteria),
            score_completeness(events, criteria),
            score_relevance(events),
            score_delivery(events),
            score_execution(events, criteria),
            score_errors(events),
        ]

        weighted_sum = 0
        total_weight = 0
        for dim in dimensions:
            weight = DIMENSION_WEIGHTS.get(dim.name, 10)
            weighted_sum += dim.score * weight
            total_weight += weight

        overall = weighted_sum // total_weight if total_weight > 0 else 0
        passed = overall >= self._pass_threshold

        suggestions = self._generate_suggestions(dimensions)

        return QualityReport(
            task_id=task_id,
            dimensions=dimensions,
            overall_score=overall,
            passed=passed,
            suggestions=suggestions,
        )

    def _generate_suggestions(
        self, dimensions: list[QualityDimension]
    ) -> list[str]:
        suggestions: list[str] = []
        for dim in dimensions:
            if dim.score < 50:
                suggestions.append(f"{dim.name}: {dim.detail}")
        return suggestions
