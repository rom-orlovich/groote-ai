import os
from typing import Literal

import httpx
import structlog
from core.database import get_session
from core.setup.service import get_config
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()
router = APIRouter()

OAUTH_SERVICE_URL = os.getenv("OAUTH_SERVICE_URL", "http://oauth-service:8010")

SUPPORTED_PLATFORMS = ["github", "jira", "slack"]

PLATFORM_CONFIG = {
    "github": {
        "name": "GitHub",
        "icon": "github",
        "description": "Connect to GitHub for repository access",
        "required_env": ["GITHUB_CLIENT_ID", "GITHUB_CLIENT_SECRET"],
    },
    "jira": {
        "name": "Jira",
        "icon": "clipboard-list",
        "description": "Connect to Jira for issue tracking",
        "required_env": ["JIRA_CLIENT_ID", "JIRA_CLIENT_SECRET"],
    },
    "slack": {
        "name": "Slack",
        "icon": "message-square",
        "description": "Connect to Slack for notifications",
        "required_env": ["SLACK_CLIENT_ID", "SLACK_CLIENT_SECRET"],
    },
}


class OAuthStatus(BaseModel):
    model_config = ConfigDict(strict=True)

    platform: str
    name: str
    connected: bool
    configured: bool
    icon: str
    description: str
    installed_at: str | None = None
    scopes: list[str] | None = None
    webhook_registered: bool = False
    webhook_url: str | None = None
    webhook_error: str | None = None


class OAuthStatusResponse(BaseModel):
    model_config = ConfigDict(strict=True)

    success: bool
    statuses: dict[str, OAuthStatus]


class OAuthInstallResponse(BaseModel):
    model_config = ConfigDict(strict=True)

    success: bool
    redirect_url: str


class OAuthRevokeResponse(BaseModel):
    model_config = ConfigDict(strict=True)

    success: bool
    platform: str
    message: str


async def is_platform_configured(platform: str, db: AsyncSession) -> bool:
    config = PLATFORM_CONFIG.get(platform, {})
    required_env = config.get("required_env", [])
    for var in required_env:
        if os.getenv(var):
            continue
        db_value = await get_config(db, var)
        if not db_value:
            return False
    return True


async def _fetch_platform_status(
    platform: str,
    config: dict,
    db: AsyncSession,
) -> OAuthStatus:
    configured = await is_platform_configured(platform, db)
    connected = False
    installed_at = None
    scopes = None
    webhook_registered = False
    webhook_url = None
    webhook_error = None

    if configured:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{OAUTH_SERVICE_URL}/oauth/installations",
                    params={"platform": platform},
                )
                if response.status_code == 200:
                    data = response.json()
                    installations = data.get("installations", [])
                    if installations:
                        connected = True
                        latest = installations[0]
                        installed_at = latest.get("installed_at")
                        scopes = latest.get("scopes")
                        webhook_registered = latest.get("webhook_registered", False)
                        webhook_url = latest.get("webhook_url")
                        webhook_error = latest.get("webhook_error")
        except httpx.RequestError as e:
            logger.warning(
                "oauth_service_unreachable",
                platform=platform,
                error=str(e),
            )

    return OAuthStatus(
        platform=platform,
        name=config.get("name", platform.title()),
        connected=connected,
        configured=configured,
        icon=config.get("icon", "link"),
        description=config.get("description", ""),
        installed_at=installed_at,
        scopes=scopes,
        webhook_registered=webhook_registered,
        webhook_url=webhook_url,
        webhook_error=webhook_error,
    )


@router.get("/oauth/status")
async def get_all_oauth_status(
    db: AsyncSession = Depends(get_session),
) -> OAuthStatusResponse:
    statuses: dict[str, OAuthStatus] = {}

    for platform in SUPPORTED_PLATFORMS:
        config = PLATFORM_CONFIG.get(platform, {})
        statuses[platform] = await _fetch_platform_status(platform, config, db)

    return OAuthStatusResponse(success=True, statuses=statuses)


@router.get("/oauth/status/{platform}")
async def get_platform_oauth_status(
    platform: Literal["github", "jira", "slack"],
    db: AsyncSession = Depends(get_session),
) -> OAuthStatus:
    if platform not in SUPPORTED_PLATFORMS:
        raise HTTPException(status_code=400, detail=f"Unsupported platform: {platform}")

    config = PLATFORM_CONFIG.get(platform, {})
    return await _fetch_platform_status(platform, config, db)


@router.post("/oauth/install/{platform}")
async def start_oauth_install(
    platform: Literal["github", "jira", "slack"],
    db: AsyncSession = Depends(get_session),
) -> OAuthInstallResponse:
    if platform not in SUPPORTED_PLATFORMS:
        raise HTTPException(status_code=400, detail=f"Unsupported platform: {platform}")

    if not await is_platform_configured(platform, db):
        raise HTTPException(
            status_code=400,
            detail=f"Platform {platform} is not configured. Check environment variables.",
        )

    redirect_url = f"/oauth/install/{platform}"

    return OAuthInstallResponse(success=True, redirect_url=redirect_url)


@router.delete("/oauth/revoke/{platform}")
async def revoke_oauth(
    platform: Literal["github", "jira", "slack"],
) -> OAuthRevokeResponse:
    if platform not in SUPPORTED_PLATFORMS:
        raise HTTPException(status_code=400, detail=f"Unsupported platform: {platform}")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{OAUTH_SERVICE_URL}/oauth/installations",
                params={"platform": platform},
            )
            if response.status_code != 200:
                raise HTTPException(status_code=500, detail="Failed to fetch installations")

            data = response.json()
            installations = data.get("installations", [])

            if not installations:
                return OAuthRevokeResponse(
                    success=True,
                    platform=platform,
                    message="No installation found to revoke",
                )

            for installation in installations:
                installation_id = installation.get("id")
                if installation_id:
                    delete_response = await client.delete(
                        f"{OAUTH_SERVICE_URL}/oauth/installations/{installation_id}"
                    )
                    if delete_response.status_code != 200:
                        logger.warning(
                            "oauth_revoke_failed",
                            platform=platform,
                            installation_id=installation_id,
                        )

            return OAuthRevokeResponse(
                success=True,
                platform=platform,
                message=f"Successfully revoked {len(installations)} installation(s)",
            )

    except httpx.RequestError as e:
        logger.error("oauth_revoke_error", platform=platform, error=str(e))
        raise HTTPException(status_code=503, detail=f"OAuth service unavailable: {e!s}")
