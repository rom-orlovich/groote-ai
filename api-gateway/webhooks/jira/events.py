from typing import Any

SUPPORTED_EVENTS = [
    "jira:issue_created",
    "jira:issue_updated",
    "comment_created",
]

AI_AGENT_LABEL = "ai-agent"
DEFAULT_AI_AGENT_NAME = "ai-agent"

BOT_COMMENT_PREFIX_MARKERS = [
    "Agent is analyzing this issue",
    "Event skipped:",
    "Failed to process:",
    "Implementation started",
]

BOT_COMMENT_SECTION_MARKERS = [
    "## Implementation Plan",
    "## Agent Analysis",
    "## PR Review",
    "## Jira Task Complete",
    "**Scope**:",
    "**Intent**:",
    "**Verdict**:",
    "_Automated by Groote AI_",
    "_Automated by Claude Agent_",
    "<!-- FINAL_RESPONSE -->",
    "Status: Plan Already Exists",
    "Status: Plan Created",
    "Status: Implementation Complete",
]


def _extract_text_from_adf(node: dict[str, Any]) -> str:
    if node.get("type") == "text":
        return node.get("text", "")
    parts: list[str] = []
    for child in node.get("content", []):
        if isinstance(child, dict):
            parts.append(_extract_text_from_adf(child))
    return " ".join(parts)


def _get_body_text(body: str | dict[str, Any]) -> str:
    if isinstance(body, str):
        return body
    if isinstance(body, dict):
        return _extract_text_from_adf(body)
    return ""


def _body_matches_bot_pattern(body_text: str) -> bool:
    for marker in BOT_COMMENT_PREFIX_MARKERS:
        if body_text.startswith(marker):
            return True
    for marker in BOT_COMMENT_SECTION_MARKERS:
        if marker in body_text:
            return True
    return False


def is_bot_comment(
    webhook_event: str,
    comment_data: dict[str, Any],
    ai_agent_name: str = DEFAULT_AI_AGENT_NAME,
) -> bool:
    if webhook_event != "comment_created":
        return False

    author = comment_data.get("author", {})
    author_display = author.get("displayName", "")
    if author_display.lower() == ai_agent_name.lower():
        return True

    author_type = author.get("accountType", "")
    if author_type == "app":
        return True

    body = comment_data.get("body", "")
    body_text = _get_body_text(body)
    if body_text and _body_matches_bot_pattern(body_text):
        return True

    return False


def should_process_event(
    webhook_event: str,
    issue_data: dict[str, Any],
    ai_agent_name: str = DEFAULT_AI_AGENT_NAME,
    comment_data: dict[str, Any] | None = None,
) -> bool:
    if webhook_event not in SUPPORTED_EVENTS:
        return False

    if comment_data and is_bot_comment(webhook_event, comment_data, ai_agent_name):
        return False

    fields = issue_data.get("fields", {})
    labels = fields.get("labels", [])
    return AI_AGENT_LABEL in labels


def extract_task_info(
    webhook_event: str, payload: dict[str, Any], jira_site_url: str = ""
) -> dict[str, Any]:
    issue = payload.get("issue", {})
    fields = issue.get("fields", {})

    summary = fields.get("summary", "")
    description = fields.get("description", "")
    prompt = f"{summary}\n\n{description}" if description else summary

    assignee = fields.get("assignee")
    assignee_name = assignee.get("displayName") if assignee else None

    issue_self_url = issue.get("self", "")
    jira_base_url = jira_site_url.rstrip("/") if jira_site_url else ""
    if not jira_base_url and issue_self_url:
        parts = issue_self_url.split("/rest/")
        if len(parts) >= 2:
            jira_base_url = parts[0]

    task_info: dict[str, Any] = {
        "source": "jira",
        "event_type": webhook_event,
        "jira_base_url": jira_base_url,
        "issue": {
            "key": issue.get("key"),
            "id": issue.get("id"),
            "self": issue_self_url,
            "summary": summary,
            "description": description,
            "issue_type": fields.get("issuetype", {}).get("name"),
            "status": fields.get("status", {}).get("name"),
            "priority": fields.get("priority", {}).get("name"),
            "labels": fields.get("labels", []),
            "project": {
                "key": fields.get("project", {}).get("key"),
                "name": fields.get("project", {}).get("name"),
            },
        },
        "assignee": assignee_name,
        "prompt": prompt,
    }

    if webhook_event == "comment_created":
        comment = payload.get("comment", {})
        task_info["comment"] = {
            "id": comment.get("id"),
            "body": comment.get("body"),
            "author": comment.get("author", {}).get("displayName"),
        }
        comment_body = comment.get("body", "")
        if comment_body:
            task_info["prompt"] = f"{summary}\n\n{description}\n\n{comment_body}"

    custom_fields = {}
    for key, value in fields.items():
        if key.startswith("customfield_"):
            custom_fields[key] = value
    if custom_fields:
        task_info["custom_fields"] = custom_fields

    return task_info
