import os

import httpx
import structlog
from core.database import get_session
from core.database.redis_client import redis_client
from core.user_settings.models import AgentScalingSettings, AIProviderSettings
from core.user_settings.service import (
    delete_user_setting,
    get_user_setting,
    get_user_settings_by_category,
    save_user_setting,
)
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()

router = APIRouter(prefix="/api/user-settings", tags=["user-settings"])


def get_user_id(authorization: str = Header(None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization",
        )
    return authorization[7:]


@router.post("/ai-provider")
async def save_ai_provider(
    settings: AIProviderSettings,
    user_id: str = Depends(get_user_id),
    db: AsyncSession = Depends(get_session),
):
    await save_user_setting(
        db,
        user_id,
        "ai_provider",
        "provider",
        settings.provider,
        is_sensitive=False,
    )

    if settings.api_key:
        await save_user_setting(
            db,
            user_id,
            "ai_provider",
            f"{settings.provider}_api_key",
            settings.api_key,
            is_sensitive=True,
        )

    if settings.model_complex:
        await save_user_setting(
            db,
            user_id,
            "ai_provider",
            f"{settings.provider}_model_complex",
            settings.model_complex,
            is_sensitive=False,
        )

    if settings.model_execution:
        await save_user_setting(
            db,
            user_id,
            "ai_provider",
            f"{settings.provider}_model_execution",
            settings.model_execution,
            is_sensitive=False,
        )

    return {"status": "saved", "provider": settings.provider}


@router.get("/ai-provider")
async def get_ai_provider(
    user_id: str = Depends(get_user_id),
    db: AsyncSession = Depends(get_session),
):
    settings = await get_user_settings_by_category(db, user_id, "ai_provider")
    if not settings:
        return {"provider": None, "settings": []}

    provider = next((s["value"] for s in settings if s["key"] == "provider"), None)
    return {
        "provider": provider,
        "settings": settings,
    }


@router.post("/ai-provider/test")
async def test_ai_provider(
    settings: AIProviderSettings,
    _: str = Depends(get_user_id),
):
    if not settings.api_key:
        return {"valid": True, "message": "Using credential-based authentication"}

    if settings.provider == "claude":
        return await _test_anthropic(settings.api_key)
    elif settings.provider == "cursor":
        return await _test_cursor(settings.api_key)

    return {"valid": False, "message": "Unknown provider"}


async def _test_anthropic(api_key: str) -> dict:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://api.anthropic.com/v1/models",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                },
            )
            if response.status_code == 200:
                return {"valid": True, "message": "Anthropic API key is valid"}
            return {
                "valid": False,
                "message": f"Authentication failed (HTTP {response.status_code})",
            }
    except httpx.RequestError as e:
        return {"valid": False, "message": f"Connection error: {e!s}"}


async def _test_cursor(_api_key: str) -> dict:
    return {"valid": True, "message": "Cursor API key saved"}


@router.post("/agent-scaling")
async def save_agent_scaling(
    settings: AgentScalingSettings,
    user_id: str = Depends(get_user_id),
    db: AsyncSession = Depends(get_session),
):
    if settings.agent_count < settings.min_agents or settings.agent_count > settings.max_agents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Agent count must be between {settings.min_agents} and {settings.max_agents}",
        )

    await save_user_setting(
        db,
        user_id,
        "agent_scaling",
        "agent_count",
        str(settings.agent_count),
        is_sensitive=False,
    )

    provider_setting = await get_user_setting(db, user_id, "ai_provider", "provider")
    provider = provider_setting or os.environ.get("CLI_PROVIDER", "claude")

    await redis_client.publish(
        "cli:scaling",
        {
            "provider": provider,
            "agent_count": settings.agent_count,
        },
    )

    return {"status": "scaling", "agent_count": settings.agent_count}


@router.get("/agent-scaling")
async def get_agent_scaling(
    user_id: str = Depends(get_user_id),
    db: AsyncSession = Depends(get_session),
):
    agent_count = await get_user_setting(
        db,
        user_id,
        "agent_scaling",
        "agent_count",
    )
    return {
        "agent_count": int(agent_count) if agent_count else 5,
        "min_agents": 1,
        "max_agents": 20,
    }


@router.delete("/user-settings/{category}/{key}")
async def delete_setting(
    category: str,
    key: str,
    user_id: str = Depends(get_user_id),
    db: AsyncSession = Depends(get_session),
):
    success = await delete_user_setting(db, user_id, category, key)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Setting not found",
        )
    return {"status": "deleted"}
