import logging

from .client import AuditClient
from .redis_monitor import RedisEventMonitor
from .scoring import (
    CRITICAL_DIMENSIONS,
    DIMENSION_WEIGHTS,
    FlowCriteria,
    QualityDimension,
    QualityReport,
    score_completeness,
    score_content_quality,
    score_delivery,
    score_errors,
    score_execution,
    score_knowledge,
    score_knowledge_first,
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
            score_knowledge_first(tool_calls, criteria),
            score_completeness(events, criteria),
            score_relevance(events, criteria),
            score_content_quality(events, criteria),
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

        critical_failed = any(
            dim.score < 50 for dim in dimensions
            if dim.name in CRITICAL_DIMENSIONS
        )
        passed = overall >= self._pass_threshold and not critical_failed

        suggestions = self._generate_suggestions(dimensions, critical_failed)

        return QualityReport(
            task_id=task_id,
            dimensions=dimensions,
            overall_score=overall,
            passed=passed,
            suggestions=suggestions,
        )

    def _generate_suggestions(
        self, dimensions: list[QualityDimension], critical_failed: bool
    ) -> list[str]:
        suggestions: list[str] = []
        if critical_failed:
            for dim in dimensions:
                if dim.name in CRITICAL_DIMENSIONS and dim.score < 50:
                    suggestions.append(f"CRITICAL FAIL - {dim.name}: {dim.detail}")
        for dim in dimensions:
            if dim.score < 50 and dim.name not in CRITICAL_DIMENSIONS:
                suggestions.append(f"{dim.name}: {dim.detail}")
        return suggestions
