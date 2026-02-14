import logging
import time
from datetime import UTC, datetime

from ..core.checkpoint import CheckpointRunner
from ..core.evaluator import FlowCriteria
from ..triggers.base import TriggerResult
from .base import BaseFlow, FlowResult

logger = logging.getLogger(__name__)


class KnowledgeHealthFlow(BaseFlow):
    name = "f07_knowledge_health"
    description = "Knowledge Layer Health Check"

    async def trigger(self) -> TriggerResult:
        return TriggerResult(
            platform="system",
            artifact_type="health_check",
            artifact_id="knowledge",
            trigger_time=datetime.now(UTC),
            expected_flow_id="system:knowledge-health",
        )

    def expected_agent(self) -> str:
        return "system"

    def flow_criteria(self) -> FlowCriteria:
        return FlowCriteria(
            expected_agent="system",
            requires_knowledge=False,
        )

    def requires_knowledge(self) -> bool:
        return False

    async def run(self) -> FlowResult:
        start = time.monotonic()
        runner = CheckpointRunner()

        await runner.run("llamaindex_health", True, self._check_llamaindex)
        await runner.run("gkg_health", True, self._check_gkg)
        await runner.run("code_search", True, self._check_code_search)
        await runner.run("ticket_search", False, self._check_ticket_search)

        return FlowResult(
            name=self.name,
            description=self.description,
            passed=runner.all_passed(),
            checkpoints=[cp.model_dump() for cp in runner.results()],
            duration_seconds=round(time.monotonic() - start, 2),
        )

    async def _check_llamaindex(self) -> dict:
        ok = await self._client.check_health(self._config.llamaindex_url)
        if not ok:
            raise RuntimeError("LlamaIndex service unhealthy")
        return {"healthy": True}

    async def _check_gkg(self) -> dict:
        ok = await self._client.check_health(self._config.gkg_url)
        if not ok:
            raise RuntimeError("GKG service unhealthy")
        return {"healthy": True}

    async def _check_code_search(self) -> dict:
        resp = await self._client.http.post(
            f"{self._config.llamaindex_url}/query/code",
            json={"query": "manga panel generator", "org_id": "default"},
            timeout=10.0,
        )
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])
        if not results:
            raise RuntimeError("Code search returned 0 results")
        return {"results_count": len(results)}

    async def _check_ticket_search(self) -> dict:
        resp = await self._client.http.post(
            f"{self._config.llamaindex_url}/query/tickets",
            json={"query": "manga-creator", "org_id": "default"},
            timeout=10.0,
        )
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])
        return {"results_count": len(results)}

    async def cleanup(self) -> None:
        pass
