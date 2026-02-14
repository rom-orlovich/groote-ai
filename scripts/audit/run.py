import argparse
import logging
from datetime import UTC, datetime
from pathlib import Path

from .config import AuditConfig, load_config
from .core.client import AuditClient
from .core.evidence import EvidenceCollector
from .core.models import QualityReport
from .core.redis_monitor import RedisEventMonitor
from .core.report import AuditReport, FlowReport, ReportGenerator

FLOW_ALIASES: dict[str, list[str]] = {
    "all": ["f01", "f02", "f03", "f04", "f05", "f06", "f07", "f08", "f09"],
    "slack": ["f01", "f08"],
    "jira": ["f02", "f05", "f09"],
    "github": ["f03", "f04"],
    "chain": ["f06"],
    "knowledge": ["f07"],
    "multi-repo": ["f08"],
    "plan-approval": ["f09"],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Groote AI End-to-End System Audit")
    parser.add_argument("--flow", nargs="+", default=["all"], help="Flows to run")
    parser.add_argument("--timeout-multiplier", type=float, default=1.0)
    parser.add_argument("--output-dir", default="./audit-results")
    parser.add_argument("--cleanup", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--quality-threshold", type=int, default=70)
    parser.add_argument("--slack-channel", default=None)
    parser.add_argument("--github-owner", default=None)
    parser.add_argument("--github-repo", default=None)
    parser.add_argument("--jira-project", default=None)
    parser.add_argument(
        "--ticket",
        default=None,
        help="Existing ticket key to audit (e.g. KAN-41) instead of creating new",
    )
    return parser.parse_args()


def resolve_flows(flow_args: list[str]) -> list[str]:
    result: list[str] = []
    for arg in flow_args:
        if arg in FLOW_ALIASES:
            result.extend(FLOW_ALIASES[arg])
        else:
            result.append(arg)
    seen: set[str] = set()
    deduped: list[str] = []
    for f in result:
        if f not in seen:
            seen.add(f)
            deduped.append(f)
    return deduped


async def check_prerequisites(client: AuditClient, config: AuditConfig) -> list[str]:
    services = {
        "API Gateway": config.api_gateway_url,
        "Dashboard API": config.dashboard_api_url,
        "Task Logger": config.task_logger_url,
    }
    failures: list[str] = []
    for name, url in services.items():
        try:
            healthy = await client.check_health(url)
            if not healthy:
                failures.append(f"{name} ({url}) is unhealthy")
        except Exception as e:
            failures.append(f"{name} ({url}) unreachable: {e}")
    return failures


def _build_flow_report(result: object) -> FlowReport:
    from .flows.base import FlowResult

    assert isinstance(result, FlowResult)

    quality: QualityReport | None = None
    if result.quality_report:
        quality = QualityReport(**result.quality_report)

    return FlowReport(
        name=result.name,
        description=result.description,
        passed=result.passed,
        components=result.components,
        checkpoints=result.checkpoints,
        quality=quality,
        duration_seconds=result.duration_seconds,
        evidence_dir=result.evidence_dir,
        error=result.error,
    )


async def main() -> int:
    args = parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    log = logging.getLogger("audit")

    config = load_config()
    config.timeout_multiplier = args.timeout_multiplier
    config.quality_pass_threshold = args.quality_threshold
    config.output_dir = args.output_dir
    config.cleanup = args.cleanup
    config.verbose = args.verbose
    if args.slack_channel:
        config.slack_channel = args.slack_channel
    if args.github_owner:
        config.github_owner = args.github_owner
    if args.github_repo:
        config.github_repo = args.github_repo
    if args.jira_project:
        config.jira_project = args.jira_project

    flow_ids = resolve_flows(args.flow)
    log.info("resolved_flows", extra={"flows": flow_ids})

    from .flows import FLOW_REGISTRY

    timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H-%M-%S")
    base_output = Path(config.output_dir) / timestamp
    base_output.mkdir(parents=True, exist_ok=True)

    async with AuditClient(config) as client:
        log.info("checking_prerequisites")
        failures = await check_prerequisites(client, config)
        if failures:
            for f in failures:
                log.error("prerequisite_failed", extra={"detail": f})
            print(f"\nPrerequisite check failed ({len(failures)} issues). Fix and retry.")
            return 1

        log.info("all_prerequisites_passed")

        monitor = RedisEventMonitor(config.redis_url)
        await monitor.start()

        flow_reports: list[FlowReport] = []
        cleanup_flows: list[object] = []

        try:
            for flow_id in flow_ids:
                flow_cls = FLOW_REGISTRY.get(flow_id)
                if not flow_cls:
                    log.warning("unknown_flow_skipped", extra={"flow_id": flow_id})
                    continue

                evidence = EvidenceCollector(str(base_output), flow_id)
                flow_kwargs: dict = {
                    "client": client,
                    "monitor": monitor,
                    "config": config,
                    "evidence_collector": evidence,
                }
                if args.ticket and flow_id in ("f02", "f05", "f09"):
                    flow_kwargs["existing_ticket_key"] = args.ticket
                flow = flow_cls(**flow_kwargs)
                cleanup_flows.append(flow)

                log.info(
                    "running_flow",
                    extra={
                        "flow": flow.name,
                        "description": flow.description,
                    },
                )
                result = await flow.run()

                status = "PASSED" if result.passed else "FAILED"
                score_str = (
                    f" (quality: {result.quality_score}/100)"
                    if result.quality_score is not None
                    else ""
                )
                log.info(
                    "flow_complete",
                    extra={
                        "flow": flow.name,
                        "status": status,
                        "score": score_str,
                        "duration": result.duration_seconds,
                    },
                )

                flow_reports.append(_build_flow_report(result))

            if config.cleanup:
                log.info("cleaning_up_artifacts")
                for flow in cleanup_flows:
                    try:
                        await flow.cleanup()
                    except Exception as e:
                        log.warning(
                            "cleanup_failed",
                            extra={"flow": getattr(flow, "name", "?"), "error": str(e)},
                        )

        finally:
            await monitor.stop()

        total_passed = sum(1 for r in flow_reports if r.passed)
        total_failed = len(flow_reports) - total_passed
        scores = [r.quality.overall_score for r in flow_reports if r.quality is not None]
        avg_quality = sum(scores) / len(scores) if scores else 0.0

        report = AuditReport(
            timestamp=timestamp,
            flows=flow_reports,
            total_passed=total_passed,
            total_failed=total_failed,
            average_quality=round(avg_quality, 1),
            evidence_dir=str(base_output),
        )

        generator = ReportGenerator()
        terminal_output = generator.generate_terminal(report)
        print(terminal_output)
        await generator.save(report, str(base_output))

        log.info("evidence_saved", extra={"path": str(base_output)})
        return 0 if total_failed == 0 else 1
