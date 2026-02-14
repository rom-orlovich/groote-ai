import re

from .models import FlowCriteria, QualityDimension, QualityReport

DIMENSION_WEIGHTS = {
    "Routing Accuracy": 15,
    "Tool Efficiency": 10,
    "Knowledge Utilization": 10,
    "Knowledge First": 10,
    "Response Completeness": 10,
    "Response Relevance": 10,
    "Content Quality": 15,
    "Delivery Success": 10,
    "Execution Metrics": 5,
    "Error Freedom": 5,
}

CRITICAL_DIMENSIONS = {"Routing Accuracy", "Content Quality"}

KNOWLEDGE_TOOL_PATTERNS = [
    "knowledge_query",
    "code_search",
    "search_jira_tickets",
    "search_confluence",
    "find_related_code",
    "analyze_dependencies",
    "find_usages",
    "get_call_graph",
    "get_class_hierarchy",
    "search_codebase",
]

DEFAULT_DOMAIN_TERMS = [
    "manga", "creator", "panel", "page", "chapter",
    "character", "story", "layout", "comic", "art",
]

RESPONSE_TOOL_PATTERNS = ["send_slack_message", "add_issue_comment", "add_jira_comment"]

INTERNAL_TOOLS = {"Read", "Write", "Edit", "Glob", "Grep", "Bash", "Task"}


def extract_output(events: list[dict]) -> str:
    for evt in reversed(events):
        if evt["type"] in ("task:output", "task:response_posted", "task:completed"):
            data = evt.get("data", {})
            output = data.get("output", "") or data.get("response", "") or data.get("content", "")
            if output:
                return str(output)
    return ""


def _tool_matches(pattern: str, tool_name: str) -> bool:
    return pattern in tool_name


def _any_tool_matches(pattern: str, tool_names: list[str]) -> bool:
    return any(_tool_matches(pattern, name) for name in tool_names)


def _word_boundary_match(term: str, text: str) -> bool:
    pattern = r"\b" + re.escape(term) + r"\b"
    return bool(re.search(pattern, text, re.IGNORECASE))


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
    required_found = sum(1 for t in criteria.required_tools if _any_tool_matches(t, called_tools))
    required_total = len(criteria.required_tools)

    base_score = 100 if required_total == 0 else int((required_found / required_total) * 100)

    unique_tools = set(called_tools)
    allowed_repeats = len(unique_tools)
    excess = max(0, len(called_tools) - len(unique_tools) - allowed_repeats)
    penalty = min(excess * 5, 30)
    score = max(0, base_score - penalty)

    missing = [t for t in criteria.required_tools if not _any_tool_matches(t, called_tools)]
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
    used = [
        tool_name for tool_name in called_tools
        if any(_tool_matches(pattern, tool_name) for pattern in KNOWLEDGE_TOOL_PATTERNS)
    ]

    if len(used) >= 3:
        return QualityDimension(
            name="Knowledge Utilization",
            score=100,
            detail=f"Used knowledge tools: {', '.join(used)}",
        )
    if len(used) == 2:
        return QualityDimension(
            name="Knowledge Utilization",
            score=75,
            detail=f"Used knowledge tools: {', '.join(used)}",
        )
    if len(used) == 1:
        return QualityDimension(
            name="Knowledge Utilization",
            score=40,
            detail=f"Partial knowledge use: {used[0]}",
        )
    return QualityDimension(
        name="Knowledge Utilization",
        score=0,
        detail="No knowledge tools used",
    )


def score_knowledge_first(tool_calls: list[dict], criteria: FlowCriteria) -> QualityDimension:
    if not criteria.requires_knowledge:
        return QualityDimension(
            name="Knowledge First",
            score=100,
            detail="Knowledge not required for this flow",
        )

    called_tools = [tc.get("data", {}).get("name", "") for tc in tool_calls]
    first_knowledge_idx = -1
    first_domain_idx = -1

    for i, tool_name in enumerate(called_tools):
        is_knowledge = any(
            _tool_matches(pattern, tool_name) for pattern in KNOWLEDGE_TOOL_PATTERNS
        )
        is_internal = tool_name in INTERNAL_TOOLS
        if is_knowledge and first_knowledge_idx == -1:
            first_knowledge_idx = i
        if not is_knowledge and not is_internal and first_domain_idx == -1:
            first_domain_idx = i

    if first_knowledge_idx == -1:
        return QualityDimension(
            name="Knowledge First",
            score=0,
            detail="No knowledge tools were called",
        )

    if first_domain_idx == -1 or first_knowledge_idx < first_domain_idx:
        return QualityDimension(
            name="Knowledge First",
            score=100,
            detail=f"Knowledge tool called first at position {first_knowledge_idx}",
        )

    gap = first_knowledge_idx - first_domain_idx
    score = max(0, 50 - gap * 10)
    return QualityDimension(
        name="Knowledge First",
        score=score,
        detail=f"Knowledge tool at position {first_knowledge_idx}, "
        f"but domain tool called first at position {first_domain_idx}",
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


def score_relevance(events: list[dict], criteria: FlowCriteria) -> QualityDimension:
    output = extract_output(events)
    terms = criteria.domain_terms if criteria.domain_terms else DEFAULT_DOMAIN_TERMS
    found = [t for t in terms if _word_boundary_match(t, output)]
    total = len(terms)
    score = min(100, int((len(found) / max(total, 1)) * 100))
    return QualityDimension(
        name="Response Relevance",
        score=score,
        detail=f"Domain terms found: {len(found)}/{total} ({', '.join(found) if found else 'none'})",
    )


def score_content_quality(events: list[dict], criteria: FlowCriteria) -> QualityDimension:
    output = extract_output(events)
    if not output:
        return QualityDimension(name="Content Quality", score=0, detail="No output to evaluate")

    score = 100
    issues: list[str] = []

    if criteria.target_repo:
        if _word_boundary_match(criteria.target_repo, output):
            score = min(score, 100)
        else:
            score = min(score, 30)
            issues.append(f"Target repo '{criteria.target_repo}' not mentioned")

    if criteria.negative_output_patterns:
        neg_found = [
            p for p in criteria.negative_output_patterns
            if re.search(p, output, re.IGNORECASE)
        ]
        if neg_found:
            penalty = len(neg_found) * 25
            score = max(0, score - penalty)
            issues.append(f"Negative patterns found: {', '.join(neg_found)}")

    if criteria.negative_terms:
        neg_terms_found = [t for t in criteria.negative_terms if _word_boundary_match(t, output)]
        if neg_terms_found:
            penalty = len(neg_terms_found) * 15
            score = max(0, score - penalty)
            issues.append(f"Wrong-context terms: {', '.join(neg_terms_found)}")

    if len(output) < criteria.min_output_length:
        score = min(score, 40)
        issues.append(f"Output too short: {len(output)} < {criteria.min_output_length}")

    detail = "Content quality OK" if not issues else "; ".join(issues)
    return QualityDimension(name="Content Quality", score=score, detail=detail)


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

    tool_calls = [e for e in events if e["type"] == "task:tool_call"]
    for tc in tool_calls:
        tool_name = tc.get("data", {}).get("name", "")
        if any(_tool_matches(p, tool_name) for p in RESPONSE_TOOL_PATTERNS):
            return QualityDimension(
                name="Delivery Success", score=80,
                detail=f"Response tool called: {tool_name} (no confirmation event)",
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
