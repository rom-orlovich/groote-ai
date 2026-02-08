from typing import Any

import structlog

logger = structlog.get_logger(__name__)

SUPPORTED_EVENTS = [
    "jira:issue_created",
    "jira:issue_updated",
    "comment_created",
]

AI_FIX_LABEL = "AI-Fix"
DEFAULT_AI_AGENT_NAME = "ai-agent"


def should_process_event(
    webhook_event: str,
    issue_data: dict[str, Any],
    ai_agent_name: str = DEFAULT_AI_AGENT_NAME,
) -> bool:
    if webhook_event not in SUPPORTED_EVENTS:
        return False

    fields = issue_data.get("fields", {})

    assignee = fields.get("assignee")
    if assignee:
        assignee_display = assignee.get("displayName", "")
        if assignee_display.lower() == ai_agent_name.lower():
            return True

    labels = fields.get("labels", [])
    return AI_FIX_LABEL in labels


def extract_task_info(webhook_event: str, payload: dict[str, Any]) -> dict[str, Any]:
    issue = payload.get("issue", {})
    fields = issue.get("fields", {})

    summary = fields.get("summary", "")
    description = fields.get("description", "")
    prompt = f"{summary}\n\n{description}" if description else summary

    assignee = fields.get("assignee")
    assignee_name = assignee.get("displayName") if assignee else None

    task_info: dict[str, Any] = {
        "source": "jira",
        "event_type": webhook_event,
        "issue": {
            "key": issue.get("key"),
            "id": issue.get("id"),
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
