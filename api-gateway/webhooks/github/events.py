from typing import Any

SUPPORTED_EVENTS = {
    "issues": ["opened", "edited", "labeled"],
    "issue_comment": ["created"],
    "pull_request": ["review_requested"],
    "pull_request_review_comment": ["created"],
    "push": None,
}


def is_bot_sender(payload: dict[str, Any]) -> bool:
    sender = payload.get("sender", {})
    if sender.get("type") == "Bot":
        return True

    comment = payload.get("comment", {})
    if comment.get("performed_via_github_app"):
        return True

    comment_user = comment.get("user", {})
    return comment_user.get("type") == "Bot"


def _has_bot_mention(payload: dict[str, Any], bot_mentions: list[str] | None = None) -> bool:
    comment_body = payload.get("comment", {}).get("body", "").lower()
    if bot_mentions is None:
        from config import get_settings
        bot_mentions = get_settings().bot_mention_list
    return any(mention in comment_body for mention in bot_mentions)


def _is_pr_comment(payload: dict[str, Any]) -> bool:
    issue = payload.get("issue", {})
    return bool(issue.get("pull_request"))


def should_process_event(
    event_type: str, action: str | None, payload: dict[str, Any] | None = None,
    bot_mentions: list[str] | None = None,
) -> bool:
    if event_type not in SUPPORTED_EVENTS:
        return False

    allowed_actions = SUPPORTED_EVENTS[event_type]
    if allowed_actions is not None and action not in allowed_actions:
        return False

    if payload and event_type in ("issue_comment", "pull_request_review_comment"):
        if is_bot_sender(payload):
            return False

    if payload and event_type == "issue_comment" and _is_pr_comment(payload):
        if not _has_bot_mention(payload, bot_mentions):
            return False

    return True


def extract_task_info(event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
    task_info: dict[str, Any] = {
        "source": "github",
        "event_type": event_type,
        "action": payload.get("action"),
    }

    if "repository" in payload:
        repo = payload["repository"]
        task_info["repository"] = {
            "full_name": repo.get("full_name"),
            "clone_url": repo.get("clone_url"),
            "default_branch": repo.get("default_branch"),
        }

    if event_type in ("issues", "issue_comment"):
        issue = payload.get("issue", {})
        issue_title = issue.get("title", "")
        issue_body = issue.get("body") or ""
        task_info["issue"] = {
            "number": issue.get("number"),
            "title": issue_title,
            "body": issue.get("body"),
            "labels": [label.get("name") for label in issue.get("labels", [])],
        }
        if event_type == "issue_comment":
            comment = payload.get("comment", {})
            comment_body = comment.get("body", "")
            task_info["comment"] = {
                "id": comment.get("id"),
                "body": comment_body,
                "user": comment.get("user", {}).get("login"),
            }
            task_info["prompt"] = f"{issue_title}\n\n{issue_body}\n\nComment: {comment_body}"
        else:
            task_info["prompt"] = f"{issue_title}\n\n{issue_body}"

    elif event_type in ("pull_request", "pull_request_review_comment"):
        pr = payload.get("pull_request", {})
        pr_title = pr.get("title", "")
        pr_body = pr.get("body") or ""
        task_info["pull_request"] = {
            "number": pr.get("number"),
            "title": pr_title,
            "body": pr.get("body"),
            "head_ref": pr.get("head", {}).get("ref"),
            "base_ref": pr.get("base", {}).get("ref"),
        }
        if event_type == "pull_request_review_comment":
            comment = payload.get("comment", {})
            comment_body = comment.get("body", "")
            path = comment.get("path", "")
            line = comment.get("line", 0)
            task_info["comment"] = {
                "id": comment.get("id"),
                "body": comment_body,
                "path": path,
                "line": line,
            }
            task_info["prompt"] = (
                f"{pr_title}\n\n{pr_body}\n\nReview comment on {path}:{line}: {comment_body}"
            )
        else:
            task_info["prompt"] = f"{pr_title}\n\n{pr_body}"

    elif event_type == "push":
        ref = payload.get("ref", "")
        commits = payload.get("commits", [])
        commit_messages = [c.get("message", "") for c in commits]
        task_info["push"] = {
            "ref": ref,
            "before": payload.get("before"),
            "after": payload.get("after"),
            "commits": [{"message": c.get("message"), "sha": c.get("id")} for c in commits],
        }
        task_info["prompt"] = f"Push to {ref}: {', '.join(commit_messages)}"

    return task_info
