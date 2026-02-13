import hashlib

import httpx
import structlog
from models import DocumentChunk, JiraSourceConfig

logger = structlog.get_logger()


class JiraIndexer:
    def __init__(self, org_id: str, config: JiraSourceConfig, jira_api_url: str):
        self.org_id = org_id
        self.config = config
        self._api_url = jira_api_url.rstrip("/")

    async def fetch_tickets(self) -> list[dict]:
        tickets: list[dict] = []
        max_results = 100
        next_page_token = ""

        jql = self.config.jql
        if not jql:
            jql = self._build_default_jql()

        logger.info("fetching_jira_tickets", jql=jql, org_id=self.org_id)

        async with httpx.AsyncClient(timeout=60.0) as client:
            while len(tickets) < self.config.max_results:
                try:
                    payload: dict[str, str | int | list[str]] = {
                        "jql": jql,
                        "max_results": min(max_results, self.config.max_results - len(tickets)),
                        "expand": "renderedFields",
                        "fields": [
                            "summary", "description", "status", "issuetype",
                            "priority", "labels", "comment", "created", "updated", "project",
                        ],
                    }
                    if next_page_token:
                        payload["next_page_token"] = next_page_token

                    response = await client.post(
                        f"{self._api_url}/api/v1/search",
                        json=payload,
                    )
                    response.raise_for_status()
                    result = response.json()

                    issues = result.get("issues", [])
                    if not issues:
                        break

                    tickets.extend(issues)

                    next_page_token = result.get("nextPageToken", "")
                    if not next_page_token:
                        break

                except Exception as e:
                    logger.error("jira_fetch_failed", error=str(e))
                    break

        logger.info("jira_tickets_fetched", count=len(tickets), org_id=self.org_id)
        return tickets

    def _build_default_jql(self) -> str:
        conditions = []

        if self.config.issue_types:
            types = ", ".join(f'"{t}"' for t in self.config.issue_types)
            conditions.append(f"issuetype IN ({types})")

        if self.config.include_labels:
            labels = ", ".join(f'"{label}"' for label in self.config.include_labels)
            conditions.append(f"labels IN ({labels})")

        if self.config.exclude_labels:
            for label in self.config.exclude_labels:
                conditions.append(f'labels != "{label}"')

        return " AND ".join(conditions) if conditions else "order by created DESC"

    async def index_tickets(self, tickets: list[dict]) -> list[DocumentChunk]:
        chunks = []

        for ticket in tickets:
            try:
                chunk = self._ticket_to_chunk(ticket)
                chunks.append(chunk)
            except Exception as e:
                logger.warning(
                    "ticket_indexing_failed",
                    ticket=ticket.get("key", "unknown"),
                    error=str(e),
                )

        logger.info("jira_tickets_indexed", count=len(chunks), org_id=self.org_id)
        return chunks

    def _ticket_to_chunk(self, ticket: dict) -> DocumentChunk:
        key = ticket.get("key", "")
        fields = ticket.get("fields", {})

        summary = fields.get("summary", "")
        description = fields.get("description", "") or ""
        rendered_description = ticket.get("renderedFields", {}).get("description", "") or ""

        content_parts = [
            f"# {key}: {summary}",
            "",
            "## Description",
            rendered_description if rendered_description else description,
        ]

        if fields.get("comment", {}).get("comments"):
            content_parts.extend(["", "## Comments"])
            for comment in fields["comment"]["comments"][:5]:
                author = comment.get("author", {}).get("displayName", "Unknown")
                body = comment.get("body", "")
                content_parts.append(f"\n**{author}:**\n{body}")

        content = "\n".join(content_parts)

        labels = [
            label.get("name", label) if isinstance(label, dict) else label
            for label in fields.get("labels", [])
        ]

        return DocumentChunk(
            id=self._generate_chunk_id(key),
            content=content,
            source_type="jira",
            source_id=key,
            title=summary,
            metadata={
                "key": key,
                "summary": summary,
                "project": fields.get("project", {}).get("key", ""),
                "issue_type": fields.get("issuetype", {}).get("name", ""),
                "status": fields.get("status", {}).get("name", ""),
                "priority": fields.get("priority", {}).get("name", "")
                if fields.get("priority")
                else "",
                "labels": labels,
                "created": fields.get("created", ""),
                "updated": fields.get("updated", ""),
                "org_id": self.org_id,
            },
        )

    def _generate_chunk_id(self, key: str) -> str:
        content = f"{self.org_id}:jira:{key}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
