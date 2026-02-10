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
            f"Provide a clear, actionable analysis. Your response will be "
            f"automatically posted back to Jira ticket {issue_key}."
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
            f"Provide a clear, actionable analysis. Your response will be "
            f"automatically posted back to {repo_name}#{number}."
        )

    return base_prompt


def build_enriched_prompt(
    task: dict, conversation_context: list[dict] | None = None
) -> str:
    from services.conversation_bridge import get_source_metadata

    source = task.get("source", "unknown")
    base_prompt = task.get("prompt", "")
    metadata = get_source_metadata(task)

    context_section = ""
    if conversation_context:
        context_section = "\n## Previous Conversation\n\n"
        for msg in conversation_context:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            context_section += f"**{role.title()}**: {content}\n\n"

    source_context = _build_source_context(source, metadata)
    platform_instructions = _build_platform_instructions(source)

    return f"""
{source_context}

{context_section}

## Task

{base_prompt}

{platform_instructions}
""".strip()


def _build_source_context(source: str, metadata: dict) -> str:
    if source == "jira":
        key = metadata.get("key", "unknown")
        return f"## Jira Ticket: {key}\n"
    if source == "github":
        repo = metadata.get("repo", "unknown")
        number = metadata.get("number", "unknown")
        return f"## GitHub Issue/PR: {repo}#{number}\n"
    if source == "slack":
        channel = metadata.get("channel_name", "unknown")
        return f"## Slack Channel: #{channel}\n"
    return f"## Source: {source}\n"


def _build_platform_instructions(source: str) -> str:
    if source == "jira":
        return """
## Response Instructions

Provide a clear, actionable analysis. Your response will be automatically posted as a comment on the Jira ticket.
Do NOT manually post comments - the system handles this for you.
"""
    if source == "github":
        return """
## Response Instructions

Provide a clear, actionable analysis. Your response will be automatically posted as a comment on the GitHub issue/PR.
Do NOT manually post comments - the system handles this for you.
"""
    if source == "slack":
        return """
## Response Instructions

Provide a clear, concise summary (max 3000 chars). Your response will be automatically posted to the Slack thread.
Do NOT manually post messages - the system handles this for you.
"""
    return ""
