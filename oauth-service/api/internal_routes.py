from typing import Any
from uuid import UUID

import structlog
from config.settings import get_settings
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from services.token_service import TokenService
from sqlalchemy.ext.asyncio import AsyncSession

from .server import get_session

logger = structlog.get_logger(__name__)
internal_router = APIRouter(prefix="/internal", tags=["internal"])


async def validate_service_key(
    x_internal_service_key: str = Header(...),
) -> str:
    settings = get_settings()
    if not settings.internal_service_key:
        raise HTTPException(status_code=503, detail="Internal API not configured")
    if x_internal_service_key != settings.internal_service_key:
        raise HTTPException(status_code=401, detail="Invalid service key")
    return x_internal_service_key


@internal_router.get("/token/{platform}")
async def get_internal_token(
    platform: str,
    org_id: str | None = Query(None),
    install_id: UUID | None = Query(None),
    _key: str = Depends(validate_service_key),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    token_service = TokenService(session)

    if org_id or install_id:
        if platform == "github" and install_id:
            installation_token = await token_service.get_github_installation_token(str(install_id))
            return {
                "token": installation_token,
                "available": bool(installation_token),
                "platform": platform,
            }
        token = await token_service.get_token(platform, org_id=org_id, installation_id=install_id)
        return {"token": token, "available": bool(token), "platform": platform}

    token, installation = await token_service.get_any_active_token(platform)

    if not token or not installation:
        return {"token": None, "available": False, "platform": platform}

    metadata: dict[str, Any] = {}
    if platform == "jira" and installation.external_org_id:
        metadata["cloud_id"] = installation.external_org_id

    logger.info(
        "internal_token_retrieved",
        platform=platform,
        org_id=installation.external_org_id,
    )

    return {
        "token": token,
        "available": True,
        "platform": platform,
        "org_id": installation.external_org_id,
        "metadata": metadata,
    }
