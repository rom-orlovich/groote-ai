from typing import Any

import httpx
from config import get_settings


class GitHubAPI:
    def __init__(self) -> None:
        settings = get_settings()
        self._base_url = settings.github_api_url.rstrip("/")
        self._timeout = settings.request_timeout
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                timeout=self._timeout,
            )
        return self._client

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def get_repository(self, owner: str, repo: str) -> dict[str, Any]:
        client = await self._get_client()
        response = await client.get(f"/api/v1/repos/{owner}/{repo}")
        response.raise_for_status()
        return response.json()

    async def get_issue(self, owner: str, repo: str, issue_number: int) -> dict[str, Any]:
        client = await self._get_client()
        response = await client.get(f"/api/v1/repos/{owner}/{repo}/issues/{issue_number}")
        response.raise_for_status()
        return response.json()

    async def create_issue(
        self,
        owner: str,
        repo: str,
        title: str,
        body: str | None = None,
        labels: list[str] | None = None,
    ) -> dict[str, Any]:
        client = await self._get_client()
        payload: dict[str, Any] = {"title": title}
        if body is not None:
            payload["body"] = body
        if labels is not None:
            payload["labels"] = labels
        response = await client.post(f"/api/v1/repos/{owner}/{repo}/issues", json=payload)
        response.raise_for_status()
        return response.json()

    async def add_issue_comment(
        self, owner: str, repo: str, issue_number: int, body: str
    ) -> dict[str, Any]:
        client = await self._get_client()
        response = await client.post(
            f"/api/v1/repos/{owner}/{repo}/issues/{issue_number}/comments",
            json={"body": body},
        )
        response.raise_for_status()
        return response.json()

    async def add_reaction(
        self, owner: str, repo: str, comment_id: int, content: str
    ) -> dict[str, Any]:
        client = await self._get_client()
        response = await client.post(
            f"/api/v1/repos/{owner}/{repo}/issues/comments/{comment_id}/reactions",
            json={"content": content},
        )
        response.raise_for_status()
        return response.json()

    async def get_pull_request(
        self, owner: str, repo: str, pr_number: int
    ) -> dict[str, Any]:
        client = await self._get_client()
        response = await client.get(f"/api/v1/repos/{owner}/{repo}/pulls/{pr_number}")
        response.raise_for_status()
        return response.json()

    async def create_pr_review_comment(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        body: str,
        commit_id: str,
        path: str,
        line: int,
    ) -> dict[str, Any]:
        client = await self._get_client()
        response = await client.post(
            f"/api/v1/repos/{owner}/{repo}/pulls/{pr_number}/comments",
            json={
                "body": body,
                "commit_id": commit_id,
                "path": path,
                "line": line,
            },
        )
        response.raise_for_status()
        return response.json()

    async def get_file_contents(
        self, owner: str, repo: str, path: str, ref: str | None = None
    ) -> dict[str, Any]:
        client = await self._get_client()
        params: dict[str, str] = {}
        if ref is not None:
            params["ref"] = ref
        response = await client.get(
            f"/api/v1/repos/{owner}/{repo}/contents/{path}",
            params=params,
        )
        response.raise_for_status()
        return response.json()

    async def search_code(
        self, query: str, per_page: int = 30, page: int = 1
    ) -> dict[str, Any]:
        client = await self._get_client()
        response = await client.get(
            "/api/v1/search/code",
            params={"q": query, "per_page": per_page, "page": page},
        )
        response.raise_for_status()
        return response.json()

    async def create_pull_request(
        self,
        owner: str,
        repo: str,
        title: str,
        head: str,
        base: str,
        body: str | None = None,
        draft: bool = False,
    ) -> dict[str, Any]:
        client = await self._get_client()
        payload: dict[str, Any] = {"title": title, "head": head, "base": base, "draft": draft}
        if body:
            payload["body"] = body
        response = await client.post(f"/api/v1/repos/{owner}/{repo}/pulls", json=payload)
        response.raise_for_status()
        return response.json()

    async def list_branches(
        self, owner: str, repo: str, per_page: int = 30, page: int = 1
    ) -> list[dict[str, Any]]:
        client = await self._get_client()
        response = await client.get(
            f"/api/v1/repos/{owner}/{repo}/branches",
            params={"per_page": per_page, "page": page},
        )
        response.raise_for_status()
        return response.json()

    async def list_repos(
        self, per_page: int = 100, page: int = 1
    ) -> dict[str, Any]:
        client = await self._get_client()
        response = await client.get(
            "/api/v1/installation/repos",
            params={"per_page": per_page, "page": page},
        )
        response.raise_for_status()
        return response.json()

    async def get_branch_sha(self, owner: str, repo: str, branch: str) -> dict[str, Any]:
        client = await self._get_client()
        response = await client.get(f"/api/v1/repos/{owner}/{repo}/git/ref/heads/{branch}")
        response.raise_for_status()
        return response.json()

    async def create_branch(self, owner: str, repo: str, ref: str, sha: str) -> dict[str, Any]:
        client = await self._get_client()
        response = await client.post(
            f"/api/v1/repos/{owner}/{repo}/git/refs",
            json={"ref": ref, "sha": sha},
        )
        response.raise_for_status()
        return response.json()

    async def create_or_update_file(
        self,
        owner: str,
        repo: str,
        path: str,
        content: str,
        message: str,
        branch: str,
        sha: str | None = None,
    ) -> dict[str, Any]:
        client = await self._get_client()
        payload: dict[str, Any] = {
            "content": content,
            "message": message,
            "branch": branch,
        }
        if sha is not None:
            payload["sha"] = sha
        response = await client.put(
            f"/api/v1/repos/{owner}/{repo}/contents/{path}",
            json=payload,
        )
        response.raise_for_status()
        return response.json()
