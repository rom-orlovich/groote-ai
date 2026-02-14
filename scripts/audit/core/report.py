import json
import logging
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from .scoring import QualityReport

logger = logging.getLogger(__name__)

ANSI_GREEN = "\033[92m"
ANSI_RED = "\033[91m"
ANSI_YELLOW = "\033[93m"
ANSI_BOLD = "\033[1m"
ANSI_RESET = "\033[0m"


class FlowReport(BaseModel):
    model_config = ConfigDict(strict=True)

    name: str
    description: str
    passed: bool
    components: list[dict] = []
    checkpoints: list[dict] = []
    quality: QualityReport | None = None
    duration_seconds: float = 0.0
    evidence_dir: str | None = None
    error: str | None = None


class AuditReport(BaseModel):
    model_config = ConfigDict(strict=True)

    timestamp: str
    flows: list[FlowReport]
    total_passed: int
    total_failed: int
    average_quality: float
    evidence_dir: str


class ReportGenerator:
    def generate_terminal(self, report: AuditReport) -> str:
        lines: list[str] = []
        lines.append("")
        lines.append(f"{ANSI_BOLD}{'=' * 60}{ANSI_RESET}")
        lines.append(f"{ANSI_BOLD}  AUDIT REPORT  {report.timestamp}{ANSI_RESET}")
        lines.append(f"{'=' * 60}")
        lines.append("")

        for i, flow in enumerate(report.flows, 1):
            status = self._pass_fail_label(flow.passed)
            lines.append(f"{'=' * 3} Flow {i}: {flow.name} {status} {'=' * 3}")
            lines.append(f"  {flow.description}")
            lines.append("")

            if flow.components:
                lines.append("  Components:")
                for comp in flow.components:
                    comp_status = self._component_label(comp.get("status") == "healthy")
                    comp_name = comp.get("name", "Unknown")
                    lines.append(f"    {comp_status} {comp_name}")
                lines.append("")

            if flow.checkpoints:
                lines.append("  Checkpoints:")
                for cp in flow.checkpoints:
                    cp_status = self._checkpoint_label(cp.get("status") == "passed")
                    cp_name = cp.get("name", "Unknown")
                    duration = cp.get("duration_seconds", 0)
                    lines.append(f"    {cp_status} {cp_name} ({duration:.1f}s)")
                lines.append("")

            if flow.quality:
                q = flow.quality
                color = ANSI_GREEN if q.passed else ANSI_RED
                lines.append(
                    f"  Quality Score: {color}{q.overall_score}/100{ANSI_RESET}"
                    f" {self._pass_fail_label(q.passed)}"
                )
                for dim in q.dimensions:
                    dim_color = self._score_color(dim.score)
                    lines.append(
                        f"    {dim_color}{dim.score:3d}{ANSI_RESET}  {dim.name}: {dim.detail}"
                    )
                if q.suggestions:
                    lines.append("  Suggestions:")
                    for suggestion in q.suggestions:
                        lines.append(f"    - {suggestion}")
                lines.append("")

            if flow.error:
                lines.append(f"  {ANSI_RED}Error: {flow.error}{ANSI_RESET}")
                lines.append("")

            lines.append(f"  Duration: {flow.duration_seconds:.1f}s")
            if flow.evidence_dir:
                lines.append(f"  Evidence: {flow.evidence_dir}")
            lines.append(f"{'_' * 60}")
            lines.append("")

        lines.append(f"{ANSI_BOLD}{'=' * 60}{ANSI_RESET}")
        lines.append(f"{ANSI_BOLD}  SUMMARY{ANSI_RESET}")
        lines.append(f"{'=' * 60}")

        passed_color = ANSI_GREEN if report.total_passed > 0 else ANSI_RESET
        failed_color = ANSI_RED if report.total_failed > 0 else ANSI_RESET

        lines.append(
            f"  Passed: {passed_color}{report.total_passed}{ANSI_RESET}"
            f"  Failed: {failed_color}{report.total_failed}{ANSI_RESET}"
            f"  Total: {len(report.flows)}"
        )

        avg_color = ANSI_GREEN if report.average_quality >= 70 else ANSI_YELLOW
        if report.average_quality < 50:
            avg_color = ANSI_RED
        lines.append(f"  Average Quality: {avg_color}{report.average_quality:.1f}/100{ANSI_RESET}")
        lines.append(f"  Evidence: {report.evidence_dir}")
        lines.append(f"{'=' * 60}")
        lines.append("")

        return "\n".join(lines)

    def generate_json(self, report: AuditReport) -> dict:
        return report.model_dump()

    async def save(self, report: AuditReport, output_dir: str) -> None:
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        json_path = out_path / "report.json"
        with json_path.open("w", encoding="utf-8") as f:
            json.dump(self.generate_json(report), f, indent=2, default=str)

        terminal_output = self.generate_terminal(report)
        txt_path = out_path / "report.txt"
        txt_path.write_text(terminal_output, encoding="utf-8")

        logger.info(
            "report_saved",
            extra={"json": str(json_path), "txt": str(txt_path)},
        )

    def _pass_fail_label(self, passed: bool) -> str:
        if passed:
            return f"{ANSI_GREEN}[PASS]{ANSI_RESET}"
        return f"{ANSI_RED}[FAIL]{ANSI_RESET}"

    def _component_label(self, healthy: bool) -> str:
        if healthy:
            return f"{ANSI_GREEN}[OK]{ANSI_RESET}"
        return f"{ANSI_RED}[FAIL]{ANSI_RESET}"

    def _checkpoint_label(self, passed: bool) -> str:
        if passed:
            return f"{ANSI_GREEN}[OK]{ANSI_RESET}"
        return f"{ANSI_RED}[FAIL]{ANSI_RESET}"

    def _score_color(self, score: int) -> str:
        if score >= 80:
            return ANSI_GREEN
        if score >= 50:
            return ANSI_YELLOW
        return ANSI_RED
