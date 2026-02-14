import logging

from pydantic import BaseModel, ConfigDict

from scripts.audit.core.client import AuditClient
from scripts.audit.core.redis_monitor import RedisEventMonitor

logger = logging.getLogger(__name__)


class ComponentCheck(BaseModel):
    model_config = ConfigDict(strict=True)

    check_name: str
    passed: bool
    detail: str
    evidence: dict = {}


class ComponentStatus(BaseModel):
    model_config = ConfigDict(strict=True)

    name: str
    status: str
    checks: list[ComponentCheck]
    evidence: dict = {}


def _derive_status(checks: list[ComponentCheck]) -> str:
    if all(c.passed for c in checks):
        return "healthy"
    if any(c.passed for c in checks):
        return "degraded"
    return "failed"


def _event_check(events: list[dict], event_type: str, label: str) -> ComponentCheck:
    found = any(e["type"] == event_type for e in events)
    return ComponentCheck(
        check_name=label,
        passed=found,
        detail=f"{event_type} {'found' if found else 'missing'}",
        evidence={"event_type": event_type, "found": found},
    )


def _single_check_status(name: str, check: ComponentCheck) -> ComponentStatus:
    return ComponentStatus(
        name=name,
        status="healthy" if check.passed else "failed",
        checks=[check],
    )


class ComponentMonitor:
    def __init__(self, client: AuditClient, monitor: RedisEventMonitor) -> None:
        self.client = client
        self.monitor = monitor

    async def _events(self, task_id: str) -> list[dict]:
        return await self.monitor.get_events_for_task(task_id)

    async def check_api_gateway(self, task_id: str) -> ComponentStatus:
        events = await self._events(task_id)
        checks = [
            _event_check(events, et, label)
            for et, label in [
                ("response:immediate", "Immediate response sent"),
                ("webhook:task_created", "Task created from webhook"),
            ]
        ]
        return ComponentStatus(name="api-gateway", status=_derive_status(checks), checks=checks)

    async def check_redis_queue(self, task_id: str) -> ComponentStatus:
        events = await self._events(task_id)
        check = _event_check(events, "webhook:task_created", "Task queued in Redis")
        check.evidence["event_count"] = len(events)
        return _single_check_status("redis-queue", check)

    async def check_agent_engine(self, task_id: str) -> ComponentStatus:
        events = await self._events(task_id)
        check = _event_check(events, "task:started", "Agent engine picked up task")
        check.evidence["task_id"] = task_id
        return _single_check_status("agent-engine", check)

    async def check_task_routing(self, task_id: str, expected_agent: str) -> ComponentStatus:
        events = await self._events(task_id)
        checks: list[ComponentCheck] = []

        created = next((e for e in events if e["type"] == "task:created"), None)
        checks.append(ComponentCheck(
            check_name="Task created event found",
            passed=created is not None,
            detail="task:created " + ("found" if created else "missing"),
        ))

        if created:
            assigned = created.get("data", {}).get("assigned_agent", "")
            checks.append(ComponentCheck(
                check_name="Correct agent assigned",
                passed=assigned == expected_agent,
                detail=f"Expected {expected_agent}, got {assigned}",
                evidence={"assigned_agent": assigned, "expected": expected_agent},
            ))

        return ComponentStatus(name="task-routing", status=_derive_status(checks), checks=checks)

    async def check_conversation_bridge(
        self, task_id: str, expected_flow_id: str
    ) -> ComponentStatus:
        events = await self._events(task_id)
        checks: list[ComponentCheck] = []

        ctx = next((e for e in events if e["type"] == "task:context_built"), None)
        checks.append(ComponentCheck(
            check_name="Context built event",
            passed=ctx is not None,
            detail="task:context_built " + ("found" if ctx else "missing"),
        ))

        if ctx:
            flow_id = ctx.get("data", {}).get("flow_id", "")
            checks.append(ComponentCheck(
                check_name="Flow ID matches",
                passed=flow_id == expected_flow_id,
                detail=f"Expected {expected_flow_id}, got {flow_id}",
                evidence={"flow_id": flow_id},
            ))

        try:
            conv = await self.client.get_conversation_by_flow(expected_flow_id)
            checks.append(ComponentCheck(
                check_name="Conversation exists in dashboard",
                passed=True,
                detail=f"Conversation found for {expected_flow_id}",
                evidence={"conversation_id": conv.get("id")},
            ))
        except Exception as exc:
            checks.append(ComponentCheck(
                check_name="Conversation exists in dashboard",
                passed=False,
                detail=f"Failed to fetch conversation: {exc}",
            ))

        return ComponentStatus(
            name="conversation-bridge", status=_derive_status(checks), checks=checks
        )

    async def check_mcp_servers(self, task_id: str) -> ComponentStatus:
        tool_calls = await self.monitor.get_tool_calls(task_id)
        events = await self._events(task_id)
        tool_results = [e for e in events if e["type"] == "task:tool_result"]
        errors = [r for r in tool_results if r.get("data", {}).get("is_error")]

        task_completed = any(
            e["type"] == "task:completed"
            and e.get("data", {}).get("status") != "failed"
            for e in events
        )
        critical_errors = errors if not task_completed else []

        checks = [
            ComponentCheck(
                check_name="Tool calls executed",
                passed=len(tool_calls) > 0,
                detail=f"{len(tool_calls)} tool call(s) found",
                evidence={"tool_call_count": len(tool_calls)},
            ),
            ComponentCheck(
                check_name="No critical MCP errors",
                passed=len(critical_errors) == 0,
                detail=(
                    f"{len(errors)} error(s) in tool results"
                    + (", non-critical (task completed)" if errors and not critical_errors else "")
                ),
                evidence={
                    "error_count": len(errors),
                    "critical_error_count": len(critical_errors),
                    "task_completed": task_completed,
                },
            ),
        ]
        return ComponentStatus(name="mcp-servers", status=_derive_status(checks), checks=checks)

    async def check_knowledge_layer(self, task_id: str) -> ComponentStatus:
        events = await self._events(task_id)
        k_calls = [e for e in events if e["type"] == "knowledge:tool_call"]
        k_results = [e for e in events if e["type"] == "knowledge:result"]

        if not k_calls and not k_results:
            return ComponentStatus(
                name="knowledge-layer",
                status="healthy",
                checks=[ComponentCheck(
                    check_name="Knowledge layer usage",
                    passed=True,
                    detail="Not used in this flow (optional)",
                )],
            )

        checks = [
            ComponentCheck(
                check_name="Knowledge queries executed",
                passed=len(k_calls) > 0,
                detail=f"{len(k_calls)} knowledge call(s)",
                evidence={"call_count": len(k_calls)},
            ),
            ComponentCheck(
                check_name="Knowledge results received",
                passed=len(k_results) > 0,
                detail=f"{len(k_results)} result(s)",
                evidence={"result_count": len(k_results)},
            ),
        ]
        return ComponentStatus(
            name="knowledge-layer", status=_derive_status(checks), checks=checks
        )

    async def check_response_poster(self, task_id: str) -> ComponentStatus:
        events = await self._events(task_id)
        check = _event_check(events, "task:response_posted", "Response posted")
        return _single_check_status("response-poster", check)

    async def check_dashboard_api(self, conversation_id: str) -> ComponentStatus:
        checks: list[ComponentCheck] = []
        try:
            messages = await self.client.get_conversation_messages(conversation_id)
            roles = {m.get("role") for m in messages}
            checks.append(ComponentCheck(
                check_name="Messages exist",
                passed=len(messages) > 0,
                detail=f"{len(messages)} message(s) found",
                evidence={"message_count": len(messages), "roles": sorted(roles)},
            ))
            for role in ["system", "assistant"]:
                checks.append(ComponentCheck(
                    check_name=f"{role.capitalize()} message present",
                    passed=role in roles,
                    detail=f"{role} role {'found' if role in roles else 'missing'}",
                ))
        except Exception as exc:
            checks.append(ComponentCheck(
                check_name="Fetch conversation messages",
                passed=False,
                detail=f"Failed: {exc}",
            ))
        return ComponentStatus(name="dashboard-api", status=_derive_status(checks), checks=checks)

    async def check_task_logger(self, task_id: str) -> ComponentStatus:
        try:
            logs = await self.client.get_task_logs(task_id)
            has_data = bool(logs)
            return ComponentStatus(
                name="task-logger",
                status="healthy" if has_data else "degraded",
                checks=[ComponentCheck(
                    check_name="Task logs available",
                    passed=has_data,
                    detail=f"Log data {'present' if has_data else 'empty'}",
                    evidence={"keys": list(logs.keys()) if isinstance(logs, dict) else []},
                )],
            )
        except Exception as exc:
            return ComponentStatus(
                name="task-logger",
                status="failed",
                checks=[ComponentCheck(
                    check_name="Task logs available",
                    passed=False,
                    detail=f"Failed to fetch logs: {exc}",
                )],
            )

    async def full_component_audit(
        self,
        task_id: str,
        expected_agent: str,
        expected_flow_id: str,
        conversation_id: str,
    ) -> list[ComponentStatus]:
        results = [
            await self.check_api_gateway(task_id),
            await self.check_redis_queue(task_id),
            await self.check_agent_engine(task_id),
            await self.check_task_routing(task_id, expected_agent),
            await self.check_conversation_bridge(task_id, expected_flow_id),
            await self.check_mcp_servers(task_id),
            await self.check_knowledge_layer(task_id),
            await self.check_response_poster(task_id),
            await self.check_dashboard_api(conversation_id),
            await self.check_task_logger(task_id),
        ]

        healthy = sum(1 for r in results if r.status == "healthy")
        logger.info(
            "full_component_audit_complete",
            extra={"healthy": healthy, "total": len(results), "task_id": task_id},
        )
        return results
