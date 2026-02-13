import os
import re
from typing import Any

from services.conversation_bridge import get_source_metadata

POSTING_TOOLS = {"add_jira_comment", "add_issue_comment", "send_slack_message"}

GITHUB_PR_EVENTS = {"pull_request", "pull_request_review_comment"}
GITHUB_ISSUE_EVENTS = {"issues", "issue_comment"}

IMPROVE_KEYWORDS = {"improve", "fix", "update", "refactor", "change", "implement", "address"}

AGENT_ROUTING: dict[str, str | dict[str, str]] = {
    "jira": "jira-code-plan",
    "github": {
        "issues": "github-issue-handler",
        "issue_comment": "github-issue-handler",
        "pull_request": "github-pr-review",
        "pull_request_review_comment": "github-pr-review",
    },
    "slack": "slack-inquiry",
}


def _is_pr_improve_request(task: dict[str, Any]) -> bool:
    metadata = task.get("source_metadata", {})
    has_pr = bool(metadata.get("pr_number") or metadata.get("pull_request"))
    if not has_pr:
        return False
    prompt = task.get("prompt", "").lower()
    return any(kw in prompt for kw in IMPROVE_KEYWORDS)


def resolve_target_agent(source: str, event_type: str, task: dict[str, Any] | None = None) -> str:
    if source == "github" and event_type == "issue_comment" and task and _is_pr_improve_request(task):
        return "github-pr-review"

    route = AGENT_ROUTING.get(source)
    if isinstance(route, str):
        return route
    if isinstance(route, dict):
        return route.get(event_type, "brain")
    return "brain"


def build_task_context(
    task: dict[str, Any], conversation_context: list[dict] | None = None
) -> str:
    source = task.get("source", "unknown")
    event_type = task.get("event_type", "unknown")
    metadata = get_source_metadata(task)
    base_prompt = task.get("prompt", "")
    target_agent = resolve_target_agent(source, event_type, task)
    org_id = os.getenv("ORG_ID", "default-org")

    context_section = ""
    if conversation_context:
        context_section = "\n## Previous Conversation\n\n"
        for msg in conversation_context:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            context_section += f"**{role.title()}**: {content}\n\n"

    metadata_lines = "\n".join(f"- {k}: {v}" for k, v in metadata.items() if v)

    return f"""## Task
Source: {source}
Event: {event_type}
Target-Agent: {target_agent}
Knowledge-Org-ID: {org_id}
{metadata_lines}
{context_section}
{base_prompt}""".strip()


MCP_CALL_PATTERNS = [
    re.compile(r"\[TOOL\]\s*Using\s+\S*" + tool) for tool in POSTING_TOOLS
]


def detect_mcp_posting(output: str | None) -> bool:
    if not output:
        return False
    return any(pattern.search(output) for pattern in MCP_CALL_PATTERNS)
