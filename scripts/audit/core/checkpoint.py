import logging
import time
from collections.abc import Awaitable, Callable
from enum import StrEnum

from pydantic import BaseModel, ConfigDict

logger = logging.getLogger(__name__)


class CheckpointStatus(StrEnum):
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


class Checkpoint(BaseModel):
    model_config = ConfigDict(strict=True)

    name: str
    status: CheckpointStatus = CheckpointStatus.PENDING
    duration_seconds: float = 0.0
    error: str | None = None
    evidence: dict = {}
    critical: bool = True


class CheckpointRunner:
    def __init__(self) -> None:
        self.checkpoints: list[Checkpoint] = []
        self._failed_critical = False

    async def run(
        self,
        name: str,
        critical: bool,
        func: Callable[[], Awaitable[dict]],
    ) -> Checkpoint:
        checkpoint = Checkpoint(name=name, critical=critical)

        if self._failed_critical:
            checkpoint.status = CheckpointStatus.SKIPPED
            checkpoint.error = "Skipped due to prior critical failure"
            self.checkpoints.append(checkpoint)
            logger.info(
                "checkpoint_skipped",
                extra={"checkpoint_name": name},
            )
            return checkpoint

        start = time.monotonic()
        try:
            evidence = await func()
            checkpoint.status = CheckpointStatus.PASSED
            checkpoint.evidence = evidence
            logger.info(
                "checkpoint_passed",
                extra={"checkpoint_name": name, "duration": time.monotonic() - start},
            )
        except Exception as exc:
            checkpoint.status = CheckpointStatus.FAILED
            checkpoint.error = str(exc)
            if critical:
                self._failed_critical = True
            logger.warning(
                "checkpoint_failed",
                extra={"checkpoint_name": name, "error": str(exc), "critical": critical},
            )
        finally:
            checkpoint.duration_seconds = round(time.monotonic() - start, 3)

        self.checkpoints.append(checkpoint)
        return checkpoint

    def results(self) -> list[Checkpoint]:
        return list(self.checkpoints)

    def all_passed(self) -> bool:
        return all(
            cp.status == CheckpointStatus.PASSED
            for cp in self.checkpoints
            if cp.status != CheckpointStatus.SKIPPED
        )

    def summary(self) -> dict:
        total = len(self.checkpoints)
        passed = sum(1 for cp in self.checkpoints if cp.status == CheckpointStatus.PASSED)
        failed = sum(1 for cp in self.checkpoints if cp.status == CheckpointStatus.FAILED)
        skipped = sum(1 for cp in self.checkpoints if cp.status == CheckpointStatus.SKIPPED)
        total_duration = sum(cp.duration_seconds for cp in self.checkpoints)

        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "all_passed": self.all_passed(),
            "total_duration_seconds": round(total_duration, 3),
            "checkpoints": [
                {
                    "name": cp.name,
                    "status": cp.status.value,
                    "duration_seconds": cp.duration_seconds,
                    "error": cp.error,
                }
                for cp in self.checkpoints
            ],
        }
