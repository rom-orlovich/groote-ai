import base64
from typing import Any

import httpx
import structlog

logger = structlog.get_logger(__name__)


class JiraClient:
    def __init__(
        self,
        base_url: str,
        email: str = "",
        api_token: str = "",
        oauth_token: str = "",
        timeout: int = 30,
    ):
        self._base_url = base_url.rstrip("/")
        self._email = email
        self._api_token = api_token
        self._oauth_token = oauth_token
        self._timeout = timeout
        self._client: httpx.AsyncClient | None = None

    def _get_auth_header(self) -> str:
        if self._oauth_token:
            return f"Bearer {self._oauth_token}"
        credentials = f"{self._email}:{self._api_token}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=f"{self._base_url}/rest/api/3",
                headers={
                    "Authorization": self._get_auth_header(),
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
                timeout=self._timeout,
            )
        return self._client

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def get_issue(self, issue_key: str) -> dict[str, Any]:
        client = await self._get_client()
        response = await client.get(f"/issue/{issue_key}")
        response.raise_for_status()
        return response.json()

    async def create_issue(
        self,
        project_key: str,
        summary: str,
        description: str,
        issue_type: str = "Task",
    ) -> dict[str, Any]:
        from .markdown_to_adf import markdown_to_adf

        client = await self._get_client()
        payload = {
            "fields": {
                "project": {"key": project_key},
                "summary": summary,
                "description": markdown_to_adf(description),
                "issuetype": {"name": issue_type},
            }
        }
        response = await client.post("/issue", json=payload)
        response.raise_for_status()
        return response.json()

    async def update_issue(self, issue_key: str, fields: dict[str, Any]) -> dict[str, Any]:
        client = await self._get_client()
        response = await client.put(f"/issue/{issue_key}", json={"fields": fields})
        response.raise_for_status()
        return {"success": True, "issue_key": issue_key}

    async def add_comment(self, issue_key: str, body: str) -> dict[str, Any]:
        from .markdown_to_adf import markdown_to_adf

        client = await self._get_client()
        payload = {"body": markdown_to_adf(body)}
        response = await client.post(f"/issue/{issue_key}/comment", json=payload)
        response.raise_for_status()
        return response.json()

    async def search_issues(
        self,
        jql: str,
        max_results: int = 50,
        start_at: int = 0,
        expand: str = "",
        next_page_token: str = "",
        fields: list[str] | None = None,
    ) -> dict[str, Any]:
        client = await self._get_client()
        payload: dict[str, Any] = {"jql": jql, "maxResults": max_results}
        if next_page_token:
            payload["nextPageToken"] = next_page_token
        if expand:
            payload["expand"] = expand
        if fields:
            payload["fields"] = fields
        response = await client.post("/search/jql", json=payload)
        response.raise_for_status()
        return response.json()

    async def get_transitions(self, issue_key: str) -> dict[str, Any]:
        client = await self._get_client()
        response = await client.get(f"/issue/{issue_key}/transitions")
        response.raise_for_status()
        return response.json()

    async def transition_issue(self, issue_key: str, transition_id: str) -> dict[str, Any]:
        client = await self._get_client()
        response = await client.post(
            f"/issue/{issue_key}/transitions",
            json={"transition": {"id": transition_id}},
        )
        response.raise_for_status()
        return {"success": True, "issue_key": issue_key}

    async def get_projects(self) -> list[dict[str, Any]]:
        client = await self._get_client()
        response = await client.get("/project")
        response.raise_for_status()
        return response.json()

    async def get_confluence_pages(
        self, space_key: str, start: int = 0, limit: int = 50, expand: str = ""
    ) -> dict[str, Any]:
        confluence_base = self._base_url.replace("/ex/jira/", "/ex/confluence/")
        url = f"{confluence_base}/wiki/api/v2/pages"
        params: dict[str, str | int] = {"spaceKey": space_key, "start": start, "limit": limit}
        if expand:
            params["expand"] = expand
        async with httpx.AsyncClient(
            headers={
                "Authorization": self._get_auth_header(),
                "Accept": "application/json",
            },
            timeout=self._timeout,
        ) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()

    async def get_confluence_spaces(self) -> list[dict[str, Any]]:
        confluence_base = self._base_url.replace("/ex/jira/", "/ex/confluence/")
        url = f"{confluence_base}/wiki/api/v2/spaces"
        async with httpx.AsyncClient(
            headers={
                "Authorization": self._get_auth_header(),
                "Accept": "application/json",
            },
            timeout=self._timeout,
        ) as client:
            response = await client.get(url, params={"limit": 250})
            response.raise_for_status()
            data = response.json()
            return data.get("results", [])
