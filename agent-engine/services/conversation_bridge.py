import httpx


def _extract_jira_metadata(task: dict) -> dict:
    issue = task.get("issue", {})
    jira_base_url = task.get("jira_base_url", "")
    key = issue.get("key", "unknown")
    metadata: dict = {
        "key": key,
        "summary": issue.get("summary", ""),
    }
    if jira_base_url:
        metadata["jira_base_url"] = jira_base_url
        metadata["ticket_url"] = f"{jira_base_url}/browse/{key}"
    return metadata


def _extract_github_metadata(task: dict) -> dict:
    repo = task.get("repository", {})
    issue = task.get("issue", {})
    pr = task.get("pull_request", {})
    return {
        "repo": repo.get("full_name", "unknown"),
        "number": issue.get("number") or pr.get("number", "unknown"),
        "title": issue.get("title") or pr.get("title", ""),
    }


def _extract_slack_metadata(task: dict) -> dict:
    return {
        "channel": task.get("channel", "unknown"),
        "channel_name": task.get("channel", "unknown"),
        "thread_ts": task.get("thread_ts", "unknown"),
        "text": task.get("text", ""),
    }


METADATA_EXTRACTORS = {
    "jira": _extract_jira_metadata,
    "github": _extract_github_metadata,
    "slack": _extract_slack_metadata,
}


def get_source_metadata(task: dict) -> dict:
    source = task.get("source", "unknown")
    extractor = METADATA_EXTRACTORS.get(source)
    if extractor:
        return extractor(task)
    return task.get("source_metadata", {})


def build_flow_id(task: dict) -> str:
    source = task.get("source", "unknown")
    metadata = get_source_metadata(task)

    if source == "jira":
        key = metadata.get("key", "unknown")
        return f"jira:{key}"

    if source == "github":
        repo = metadata.get("repo", "unknown")
        number = metadata.get("number", "unknown")
        return f"github:{repo}#{number}"

    if source == "slack":
        channel = metadata.get("channel", "unknown")
        thread_ts = metadata.get("thread_ts", "unknown")
        return f"slack:{channel}:{thread_ts}"

    return f"{source}:unknown"


def build_conversation_title(task: dict) -> str:
    source = task.get("source", "unknown")
    metadata = get_source_metadata(task)

    if source == "jira":
        key = metadata.get("key", "unknown")
        summary = metadata.get("summary", "")
        return f"Jira: {key} - {summary}" if summary else f"Jira: {key}"

    if source == "github":
        repo = metadata.get("repo", "unknown")
        number = metadata.get("number", "unknown")
        title = metadata.get("title", "")
        repo_short = repo.split("/")[-1] if "/" in repo else repo
        return (
            f"GitHub: {repo_short}#{number} - {title}"
            if title
            else f"GitHub: {repo_short}#{number}"
        )

    if source == "slack":
        channel_name = metadata.get("channel_name", "unknown")
        text = metadata.get("text", "")
        text_preview = text[:50] + "..." if len(text) > 50 else text
        return (
            f"Slack: #{channel_name} - {text_preview}"
            if text
            else f"Slack: #{channel_name}"
        )

    return f"{source.title()}: Unknown"


async def get_or_create_flow_conversation(
    dashboard_url: str, task: dict
) -> str:
    from urllib.parse import quote

    flow_id = build_flow_id(task)
    encoded_flow_id = quote(flow_id, safe="")

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            f"{dashboard_url}/api/conversations/by-flow/{encoded_flow_id}"
        )

        if response.status_code == 200:
            data = response.json()
            return data["conversation_id"]

        title = build_conversation_title(task)
        response = await client.post(
            f"{dashboard_url}/api/conversations",
            json={
                "flow_id": flow_id,
                "title": title,
                "source": task.get("source", "webhook"),
                "metadata": get_source_metadata(task),
            },
        )
        response.raise_for_status()

        data = response.json()
        return data["conversation_id"]


async def fetch_conversation_context(
    dashboard_url: str, conversation_id: str, limit: int = 5
) -> list[dict]:
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            f"{dashboard_url}/api/conversations/{conversation_id}/context",
            params={"max_messages": limit},
        )
        response.raise_for_status()
        return response.json()


async def register_task(
    dashboard_url: str, task: dict, conversation_id: str
) -> None:
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            f"{dashboard_url}/api/tasks",
            json={
                "task_id": task["task_id"],
                "source": task.get("source", "webhook"),
                "source_metadata": get_source_metadata(task),
                "input_message": task.get("prompt", ""),
                "assigned_agent": task.get("assigned_agent", "brain"),
                "conversation_id": conversation_id,
                "flow_id": build_flow_id(task),
            },
        )
        response.raise_for_status()


def _build_jira_system_message(metadata: dict) -> str:
    key = metadata.get("key", "unknown")
    summary = metadata.get("summary", "")
    ticket_url = metadata.get("ticket_url", "")
    ticket_ref = f"[{key}]({ticket_url})" if ticket_url else key
    return f"🎫 **Jira Webhook Triggered**\n\nTicket: {ticket_ref}\nSummary: {summary}"


def _build_github_system_message(metadata: dict) -> str:
    repo = metadata.get("repo", "unknown")
    number = metadata.get("number", "unknown")
    title = metadata.get("title", "")
    return f"🐙 **GitHub Webhook Triggered**\n\nRepo: {repo}\nIssue/PR: #{number}\nTitle: {title}"


def _build_slack_system_message(metadata: dict) -> str:
    channel = metadata.get("channel_name", "unknown")
    return f"💬 **Slack Webhook Triggered**\n\nChannel: #{channel}"


async def post_system_message(
    dashboard_url: str, conversation_id: str, task: dict, task_id: str | None = None
) -> None:
    source = task.get("source", "unknown")
    metadata = get_source_metadata(task)

    if source == "jira":
        content = _build_jira_system_message(metadata)
    elif source == "github":
        content = _build_github_system_message(metadata)
    elif source == "slack":
        content = _build_slack_system_message(metadata)
    else:
        content = f"🔔 **Webhook Triggered**\n\nSource: {source}"

    body: dict = {"role": "system", "content": content}
    if task_id:
        body["task_id"] = task_id

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            f"{dashboard_url}/api/conversations/{conversation_id}/messages",
            json=body,
        )
        response.raise_for_status()


async def post_fallback_notice(
    dashboard_url: str, conversation_id: str, source: str, posted: bool,
    task_id: str | None = None,
) -> None:
    if posted:
        content = (
            f"MCP tools unavailable - Response was posted to {source} "
            f"via fallback (direct API). Check the platform for the response."
        )
    else:
        content = (
            f"Response delivery failed - MCP tools unavailable and "
            f"fallback to {source} also failed. Manual intervention needed."
        )

    body: dict = {"role": "system", "content": content}
    if task_id:
        body["task_id"] = task_id

    async with httpx.AsyncClient(timeout=10.0) as client:
        await client.post(
            f"{dashboard_url}/api/conversations/{conversation_id}/messages",
            json=body,
        )
