import os
from typing import Annotated

import httpx
import structlog
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, ConfigDict

from api.sources import check_oauth_connected

logger = structlog.get_logger()
router = APIRouter(prefix="/api/sources/browse", tags=["source-browser"])

GITHUB_API_URL = os.getenv("GITHUB_API_URL", "http://github-api:3001")
JIRA_API_URL = os.getenv("JIRA_API_URL", "http://jira-api:3002")


class PlatformResource(BaseModel):
    model_config = ConfigDict(strict=True)
    id: str
    name: str
    description: str
    metadata: dict[str, str | int | bool]


class BrowseResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    resources: list[PlatformResource]
    total_count: int
    has_more: bool


def _extract_description(desc: str | dict) -> str:
    if isinstance(desc, str):
        return desc
    if isinstance(desc, dict):
        plain = desc.get("plain", {})
        if isinstance(plain, dict):
            return plain.get("value", "")
    return ""


async def _require_oauth(platform: str) -> None:
    connected = await check_oauth_connected(platform)
    if not connected:
        raise HTTPException(
            status_code=403,
            detail=f"OAuth not connected for {platform}. Connect it in Integrations first.",
        )


async def _proxy_get(url: str, params: dict[str, int] | None = None) -> httpx.Response:
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response
    except httpx.HTTPStatusError as e:
        logger.error("browse_upstream_error", url=url, status=e.response.status_code)
        raise HTTPException(
            status_code=502,
            detail=f"Upstream API returned {e.response.status_code}",
        ) from e
    except httpx.RequestError as e:
        logger.error("browse_upstream_unreachable", url=url, error=str(e))
        raise HTTPException(
            status_code=502,
            detail="Could not reach upstream API service",
        ) from e


@router.get("/github/repos", response_model=BrowseResponse)
async def browse_github_repos(
    per_page: Annotated[int, Query(ge=1, le=100)] = 100,
    page: Annotated[int, Query(ge=1)] = 1,
):
    await _require_oauth("github")
    response = await _proxy_get(
        f"{GITHUB_API_URL}/api/v1/installation/repos",
        params={"per_page": per_page, "page": page},
    )
    data = response.json()

    repositories = data.get("repositories", [])
    total_count = data.get("total_count", len(repositories))

    resources = [
        PlatformResource(
            id=repo.get("full_name", ""),
            name=repo.get("full_name", "").split("/")[-1] if repo.get("full_name") else "",
            description=repo.get("description") or "",
            metadata={
                "full_name": repo.get("full_name", ""),
                "language": repo.get("language") or "",
                "private": repo.get("private", False),
                "stargazers_count": repo.get("stargazers_count", 0),
            },
        )
        for repo in repositories
    ]

    return BrowseResponse(
        resources=resources,
        total_count=total_count,
        has_more=len(repositories) == per_page,
    )


@router.get("/jira/projects", response_model=BrowseResponse)
async def browse_jira_projects():
    await _require_oauth("jira")
    response = await _proxy_get(f"{JIRA_API_URL}/api/v1/projects")
    projects = response.json()

    resources = [
        PlatformResource(
            id=proj.get("key", ""),
            name=proj.get("name", ""),
            description=proj.get("description") or "",
            metadata={
                "key": proj.get("key", ""),
                "style": proj.get("style", ""),
            },
        )
        for proj in projects
    ]

    return BrowseResponse(
        resources=resources,
        total_count=len(resources),
        has_more=False,
    )


@router.get("/confluence/spaces", response_model=BrowseResponse)
async def browse_confluence_spaces():
    await _require_oauth("jira")
    response = await _proxy_get(f"{JIRA_API_URL}/api/v1/confluence/spaces")
    spaces = response.json()

    resources = [
        PlatformResource(
            id=space.get("key", ""),
            name=space.get("name", ""),
            description=_extract_description(space.get("description", "")),
            metadata={
                "key": space.get("key", ""),
                "type": space.get("type", ""),
            },
        )
        for space in spaces
    ]

    return BrowseResponse(
        resources=resources,
        total_count=len(resources),
        has_more=False,
    )
