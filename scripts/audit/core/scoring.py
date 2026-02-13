import re

from pydantic import BaseModel, ConfigDict

DIMENSION_WEIGHTS = {
    "Routing Accuracy": 20,
    "Tool Efficiency": 15,
    "Knowledge Utilization": 10,
    "Response Completeness": 15,
    "Response Relevance": 10,
    "Delivery Success": 15,
    "Execution Metrics": 10,
    "Error Freedom": 5,
}

KNOWLEDGE_TOOLS = [
    "knowledge_query",
    "llamaindex_search",
    "gkg_query",
    "knowledge_graph",
]

DOMAIN_TERMS = [
    "manga", "creator", "panel", "page", "chapter",
    "character", "story", "layout", "comic", "art",
]


class QualityDimension(BaseModel):
    model_config = ConfigDict(strict=True)

    name: str
    score: int
    detail: str


class QualityReport(BaseModel):
    model_config = ConfigDict(strict=True)

    task_id: str
    dimensions: list[QualityDimension]
    overall_score: int
    passed: bool
    suggestions: list[str]


class FlowCriteria(BaseModel):
    model_config = ConfigDict(strict=True)

    expected_agent: str
    required_tools: list[str] = []
    required_response_tools: list[str] = []
    required_output_patterns: list[str] = []
    min_output_length: int = 100
    max_execution_seconds: float = 300.0
    requires_knowledge: bool = True


def extract_output(events: list[dict]) -> str:
    for evt in reversed(events):
        if evt["type"] in ("task:output", "task:response_posted", "task:completed"):
            data = evt.get("data", {})
            output = data.get("output", "") or data.get("response", "") or data.get("content", "")
            if output:
                return str(output)
    return ""


def score_routing(events: list[dict], criteria: FlowCriteria) -> QualityDimension:
    routed_agent = ""
    for evt in events:
        if evt["type"] == "task:created":
            routed_agent = evt.get("data", {}).get("assigned_agent", "")
            break

    if routed_agent == criteria.expected_agent:
        return QualityDimension(
            name="Routing Accuracy",
            score=100,
            detail=f"Correctly routed to {criteria.expected_agent}",
        )
    return QualityDimension(
        name="Routing Accuracy",
        score=0,
        detail=f"Expected {criteria.expected_agent}, got {routed_agent or 'none'}",
    )


def score_tool_efficiency(tool_calls: list[dict], criteria: FlowCriteria) -> QualityDimension:
    called_tools = [tc.get("data", {}).get("name", "") for tc in tool_calls]
    required_found = sum(1 for t in criteria.required_tools if t in called_tools)
    required_total = len(criteria.required_tools)

    base_score = 100 if required_total == 0 else int((required_found / required_total) * 100)

    unique_tools = set(called_tools)
    redundant = max(0, len(called_tools) - len(unique_tools) - 2)
    penalty = min(redundant * 10, 40)
    score = max(0, base_score - penalty)

    missing = [t for t in criteria.required_tools if t not in called_tools]
    detail = f"Used {len(unique_tools)} tools, {len(called_tools)} calls"
    if missing:
        detail += f", missing: {', '.join(missing)}"

    return QualityDimension(name="Tool Efficiency", score=score, detail=detail)


def score_knowledge(tool_calls: list[dict], criteria: FlowCriteria) -> QualityDimension:
    if not criteria.requires_knowledge:
        return QualityDimension(
            name="Knowledge Utilization",
            score=100,
            detail="Knowledge not required for this flow",
        )

    called_tools = [tc.get("data", {}).get("name", "") for tc in tool_calls]
    used = [t for t in called_tools if t in KNOWLEDGE_TOOLS]

    if len(used) >= 2:
        return QualityDimension(
            name="Knowledge Utilization",
            score=100,
            detail=f"Used knowledge tools: {', '.join(used)}",
        )
    if len(used) == 1:
        return QualityDimension(
            name="Knowledge Utilization",
            score=50,
            detail=f"Partial knowledge use: {used[0]}",
        )
    return QualityDimension(
        name="Knowledge Utilization",
        score=0,
        detail="No knowledge tools used",
    )


def score_completeness(events: list[dict], criteria: FlowCriteria) -> QualityDimension:
    output = extract_output(events)
    if not criteria.required_output_patterns:
        length_ok = len(output) >= criteria.min_output_length
        score = 100 if length_ok else int((len(output) / max(criteria.min_output_length, 1)) * 100)
        return QualityDimension(
            name="Response Completeness",
            score=min(score, 100),
            detail=f"Output length: {len(output)} chars",
        )

    found = sum(
        1 for pattern in criteria.required_output_patterns
        if re.search(pattern, output, re.IGNORECASE)
    )
    total = len(criteria.required_output_patterns)
    score = int((found / total) * 100)
    return QualityDimension(
        name="Response Completeness",
        score=score,
        detail=f"Matched {found}/{total} required patterns",
    )


def score_relevance(events: list[dict]) -> QualityDimension:
    output = extract_output(events)
    found = [t for t in DOMAIN_TERMS if t.lower() in output.lower()]
    score = min(100, len(found) * 20)
    return QualityDimension(
        name="Response Relevance",
        score=score,
        detail=f"Domain terms found: {', '.join(found) if found else 'none'}",
    )


def score_delivery(events: list[dict]) -> QualityDimension:
    for evt in events:
        if evt["type"] == "task:response_posted":
            method = evt.get("data", {}).get("method", "")
            if method == "mcp":
                return QualityDimension(
                    name="Delivery Success", score=100, detail="Response posted via MCP",
                )
            return QualityDimension(
                name="Delivery Success", score=75, detail=f"Response posted via fallback: {method}",
            )

    has_output = any(evt["type"] in ("task:completed", "task:output") for evt in events)
    if has_output:
        return QualityDimension(
            name="Delivery Success", score=25, detail="Task completed but response not confirmed posted",
        )
    return QualityDimension(
        name="Delivery Success", score=0, detail="No response delivery detected",
    )


def score_execution(events: list[dict], criteria: FlowCriteria) -> QualityDimension:
    from datetime import datetime, timezone

    timestamps: list[datetime] = []
    for evt in events:
        ts = evt.get("timestamp")
        if not ts:
            continue
        try:
            parsed = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
            timestamps.append(parsed)
        except (ValueError, TypeError):
            continue

    if len(timestamps) < 2:
        return QualityDimension(
            name="Execution Metrics", score=50, detail="Insufficient timestamps for duration calculation",
        )

    timestamps.sort()
    duration = (timestamps[-1] - timestamps[0]).total_seconds()

    if duration <= 0:
        return QualityDimension(
            name="Execution Metrics", score=50, detail="Could not compute duration",
        )

    max_seconds = criteria.max_execution_seconds
    if duration <= max_seconds * 0.5:
        score = 100
    elif duration <= max_seconds:
        ratio = (max_seconds - duration) / (max_seconds * 0.5)
        score = 50 + int(ratio * 50)
    else:
        score = max(0, 50 - int((duration - max_seconds) / max_seconds * 50))

    return QualityDimension(
        name="Execution Metrics",
        score=score,
        detail=f"Duration: {duration:.1f}s (max: {max_seconds:.0f}s)",
    )


def score_errors(events: list[dict]) -> QualityDimension:
    error_categories: set[str] = set()
    for evt in events:
        if "error" in evt["type"].lower():
            category = evt.get("data", {}).get("category", "unknown")
            error_categories.add(category)
        if evt["type"] == "task:completed":
            status = evt.get("data", {}).get("status", "")
            if status in ("failed", "error"):
                error_categories.add("task_failure")

    score = max(0, 100 - len(error_categories) * 25)
    detail = "No errors detected" if not error_categories else f"Errors: {', '.join(sorted(error_categories))}"
    return QualityDimension(name="Error Freedom", score=score, detail=detail)
