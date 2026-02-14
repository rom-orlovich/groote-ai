from typing import Any


def jira_issue_created_payload(
    issue_key: str = "PROJ-123",
    summary: str = "Test Issue",
    description: str = "Test description",
    labels: list[str] | None = None,
    project: str = "PROJ",
    issue_type: str = "Bug",
    priority: str = "Medium",
    reporter: str = "testuser",
    assignee: str | None = None,
) -> dict[str, Any]:
    assignee_field = None
    if assignee:
        assignee_field = {
            "displayName": assignee,
            "emailAddress": f"{assignee.lower().replace(' ', '.')}@example.com",
        }

    return {
        "webhookEvent": "jira:issue_created",
        "timestamp": 1706702400000,
        "issue": {
            "id": "10001",
            "key": issue_key,
            "self": f"https://jira.example.com/rest/api/2/issue/{issue_key}",
            "fields": {
                "summary": summary,
                "description": description,
                "labels": labels or [],
                "project": {
                    "key": project,
                    "name": f"{project} Project",
                },
                "issuetype": {
                    "name": issue_type,
                },
                "priority": {
                    "name": priority,
                },
                "reporter": {
                    "displayName": reporter,
                    "emailAddress": f"{reporter}@example.com",
                },
                "assignee": assignee_field,
                "status": {
                    "name": "To Do",
                },
                "created": "2026-01-31T12:00:00.000+0000",
                "updated": "2026-01-31T12:00:00.000+0000",
            },
        },
        "user": {
            "displayName": reporter,
            "emailAddress": f"{reporter}@example.com",
        },
    }


def jira_issue_updated_payload(
    issue_key: str = "PROJ-123",
    summary: str = "Updated Issue",
    labels: list[str] | None = None,
    project: str = "PROJ",
    change_type: str = "labels",
    from_value: str = "",
    to_value: str = "ai-agent",
    assignee: str | None = None,
) -> dict[str, Any]:
    payload = jira_issue_created_payload(
        issue_key=issue_key,
        summary=summary,
        labels=labels,
        project=project,
        assignee=assignee,
    )
    payload["webhookEvent"] = "jira:issue_updated"
    payload["changelog"] = {
        "id": "10001",
        "items": [
            {
                "field": change_type,
                "fieldtype": "jira",
                "from": from_value,
                "fromString": from_value,
                "to": to_value,
                "toString": to_value,
            }
        ],
    }
    return payload


def jira_comment_created_payload(
    issue_key: str = "PROJ-123",
    comment_id: str = "10001",
    body: str | dict[str, Any] = "Test comment",
    author: str = "testuser",
    assignee: str | None = None,
    account_type: str = "atlassian",
) -> dict[str, Any]:
    assignee_field = None
    if assignee:
        assignee_field = {
            "displayName": assignee,
            "emailAddress": f"{assignee.lower().replace(' ', '.')}@example.com",
        }

    return {
        "webhookEvent": "comment_created",
        "timestamp": 1706702400000,
        "issue": {
            "id": "10001",
            "key": issue_key,
            "self": f"https://jira.example.com/rest/api/2/issue/{issue_key}",
            "fields": {
                "summary": "Test Issue",
                "description": "Test description",
                "labels": ["ai-agent"],
                "assignee": assignee_field,
                "project": {
                    "key": "PROJ",
                },
            },
        },
        "comment": {
            "id": comment_id,
            "body": body,
            "author": {
                "displayName": author,
                "emailAddress": f"{author}@example.com",
                "accountType": account_type,
            },
            "created": "2026-01-31T12:00:00.000+0000",
            "updated": "2026-01-31T12:00:00.000+0000",
        },
    }
