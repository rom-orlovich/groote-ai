import asyncio
import os
import re
from typing import Any

import httpx
import structlog

from services.conversation_bridge import get_source_metadata

logger = structlog.get_logger(__name__)

POSTING_TOOLS = {"add_jira_comment", "add_issue_comment", "send_slack_message"}


async def _fetch_knowledge_context(prompt: str, org_id: str) -> dict[str, Any]:
    llamaindex_url = os.getenv("LLAMAINDEX_URL", "http://llamaindex-service:8002")
    result: dict[str, Any] = {"knowledge": "", "repos": [], "code_snippets": []}

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            knowledge_task = client.post(
                f"{llamaindex_url}/api/query",
                json={"query": prompt, "org_id": org_id},
            )
            code_task = client.post(
                f"{llamaindex_url}/api/code-search",
                json={"query": prompt, "org_id": org_id, "limit": 10},
            )
            responses = await asyncio.gather(
                knowledge_task,
                code_task,
                return_exceptions=True,
            )

            knowledge_resp = responses[0]
            if not isinstance(knowledge_resp, Exception) and knowledge_resp.status_code == 200:
                data = knowledge_resp.json()
                result["knowledge"] = data.get("response", "")

            code_resp = responses[1]
            if not isinstance(code_resp, Exception) and code_resp.status_code == 200:
                data = code_resp.json()
                results = data.get("results", [])
                seen_repos: set[str] = set()
                for item in results:
                    repo = item.get("repo", "")
                    if repo and repo not in seen_repos:
                        seen_repos.add(repo)
                        result["repos"].append(repo)
                    result["code_snippets"].append(
                        {
                            "repo": repo,
                            "file_path": item.get("file_path", ""),
                            "content": item.get("content", "")[:500],
                            "score": item.get("score", 0),
                        }
                    )
    except Exception:
        logger.warning("knowledge_context_fetch_failed", org_id=org_id)

    return result


def _format_knowledge_section(knowledge_ctx: dict[str, Any], org_id: str) -> str:
    sections: list[str] = []

    if knowledge_ctx.get("knowledge"):
        sections.append(f"## Knowledge Context\n\n{knowledge_ctx['knowledge']}")

    repos = knowledge_ctx.get("repos", [])
    if repos:
        repo_lines = [f"- `/data/repos/{org_id}/{repo}`" for repo in repos]
        sections.append("## Affected Repos\n\n" + "\n".join(repo_lines))

    snippets = knowledge_ctx.get("code_snippets", [])
    if snippets:
        snippet_parts: list[str] = []
        for s in snippets[:5]:
            snippet_parts.append(
                f"### {s['repo']}:{s['file_path']} (score: {s['score']:.2f})\n```\n{s['content']}\n```"
            )
        sections.append("## Relevant Code\n\n" + "\n\n".join(snippet_parts))

    return "\n\n".join(sections)


def _is_duplicate_content(content: str, prompt: str) -> bool:
    if len(content) < 50:
        return False
    content_words = set(content.lower().split())
    prompt_words = set(prompt.lower().split())
    if not content_words:
        return False
    overlap = len(content_words & prompt_words) / len(content_words)
    return overlap > 0.6


async def build_task_context(
    task: dict[str, Any], conversation_context: list[dict] | None = None
) -> str:
    from config import get_settings

    source = task.get("source", "unknown")
    event_type = task.get("event_type", "unknown")
    metadata = get_source_metadata(task)
    base_prompt = task.get("prompt", "")
    org_id = os.getenv("ORG_ID", "default-org")

    settings = get_settings()
    bot_mentions = settings.bot_mentions
    approve_command = settings.bot_approve_command
    improve_keywords = settings.bot_improve_keywords

    knowledge_ctx = await _fetch_knowledge_context(base_prompt, org_id)
    knowledge_section = _format_knowledge_section(knowledge_ctx, org_id)

    context_section = ""
    if conversation_context:
        filtered = [
            msg
            for msg in conversation_context
            if not _is_duplicate_content(msg.get("content", ""), base_prompt)
        ]
        if filtered:
            context_section = "\n## Previous Conversation\n\n"
            for msg in filtered:
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                context_section += f"**{role.title()}**: {content}\n\n"

    metadata_lines = "\n".join(f"- {k}: {v}" for k, v in metadata.items() if v)

    return f"""## Task
Source: {source}
Event: {event_type}
Bot-Mentions: {bot_mentions}
Approve-Command: {approve_command}
Improve-Keywords: {improve_keywords}
Knowledge-Org-ID: {org_id}
{metadata_lines}
{knowledge_section}
{context_section}
{base_prompt}""".strip()


MCP_CALL_PATTERNS = [re.compile(r"\[TOOL\]\s*Using\s+\S*" + tool) for tool in POSTING_TOOLS]


def detect_mcp_posting(output: str | None) -> bool:
    if not output:
        return False
    return any(pattern.search(output) for pattern in MCP_CALL_PATTERNS)
