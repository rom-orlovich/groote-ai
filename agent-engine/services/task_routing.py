from typing import Any


def build_prompt(task: dict[str, Any]) -> str:
    source = task.get("source", "")
    base_prompt = task.get("prompt", "")

    if source == "jira":
        issue = task.get("issue", {})
        issue_key = issue.get("key", "")
        return (
            f"Jira ticket: {issue_key}\n\n"
            f"{base_prompt}\n\n"
            f"IMPORTANT: After completing your analysis, post your response "
            f"back to Jira ticket {issue_key} using `jira:add_jira_comment`."
        )

    if source == "github":
        repo = task.get("repository", {})
        repo_name = repo.get("full_name", "")
        issue = task.get("issue", {})
        pr = task.get("pull_request", {})
        number = issue.get("number") or pr.get("number", "")
        return (
            f"GitHub {repo_name}#{number}\n\n"
            f"{base_prompt}\n\n"
            f"IMPORTANT: After completing your analysis, post your response "
            f"back using `github:add_issue_comment` on {repo_name}#{number}."
        )

    return base_prompt
