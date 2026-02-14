import json
import logging
from datetime import UTC, datetime
from pathlib import Path

from .scoring import QualityReport

logger = logging.getLogger(__name__)


class EvidenceCollector:
    def __init__(self, output_dir: str, flow_name: str) -> None:
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S")
        self._base_dir = Path(output_dir) / timestamp / flow_name
        self._base_dir.mkdir(parents=True, exist_ok=True)
        logger.info(
            "evidence_collector_init",
            extra={"dir": str(self._base_dir)},
        )

    @property
    def base_dir(self) -> Path:
        return self._base_dir

    async def save_events(self, events: list[dict]) -> Path:
        return self._write_json("events.json", events)

    async def save_component_status(self, statuses: list[dict]) -> Path:
        return self._write_json("component_status.json", statuses)

    async def save_quality_report(self, report: QualityReport | dict) -> Path:
        data = report.model_dump() if hasattr(report, "model_dump") else report
        return self._write_json("quality_report.json", data)

    async def save_checkpoints(self, checkpoints: list[dict]) -> Path:
        return self._write_json("checkpoints.json", checkpoints)

    async def save_api_response(self, name: str, data: dict) -> Path:
        filename = f"api_{name}.json"
        return self._write_json(filename, data)

    async def save_raw(self, filename: str, data: str | dict) -> Path:
        filepath = self._base_dir / filename
        if isinstance(data, dict):
            return self._write_json(filename, data)

        filepath.write_text(data, encoding="utf-8")
        logger.info("evidence_saved", extra={"file": str(filepath)})
        return filepath

    def _write_json(self, filename: str, data: list | dict) -> Path:
        filepath = self._base_dir / filename
        with filepath.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
        logger.info("evidence_saved", extra={"file": str(filepath)})
        return filepath
