import os
from datetime import UTC, datetime

import structlog
from core.database import get_session
from core.database.redis_client import redis_client
from core.user_settings.service import get_user_setting
from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()

router = APIRouter()


class CLIStartupStep(BaseModel):
    step: str
    status: str
    detail: str


class CLIStatusResponse(BaseModel):
    provider: str
    status: str
    version: str
    active: bool
    health_check: bool
    startup_steps: list[CLIStartupStep]
    last_checked: str


def _get_user_id(authorization: str = Header(None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization",
        )
    return authorization[7:]


@router.get("/cli-status")
async def get_cli_status() -> CLIStatusResponse:
    import httpx

    now = datetime.now(UTC).isoformat()
    provider = "unknown"
    version = ""
    active = False
    health_ok = False
    startup_steps: list[CLIStartupStep] = []

    data = await redis_client.get_json("cli:startup_status")
    if data:
        provider = data.get("provider", "unknown")
        version = data.get("version", "")

        step = data.get("step", "")
        status_val = data.get("status", "")
        detail = data.get("detail", "")
        startup_steps.append(CLIStartupStep(step=step, status=status_val, detail=detail))

        if step == "ready" and status_val == "healthy":
            active = True

    agent_engine_url = os.getenv("AGENT_ENGINE_URL", "http://cli:9100")
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{agent_engine_url}/health")
            if response.status_code == 200:
                health_ok = True

            auth_response = await client.get(f"{agent_engine_url}/health/auth")
            if auth_response.status_code == 200:
                auth_data = auth_response.json()
                provider = auth_data.get("provider", provider)
                if auth_data.get("authenticated", False):
                    active = True
    except httpx.RequestError:
        pass

    return CLIStatusResponse(
        provider=provider,
        status="running" if health_ok else "stopped",
        version=version,
        active=active,
        health_check=health_ok,
        startup_steps=startup_steps,
        last_checked=now,
    )


@router.post("/cli-control/start")
async def start_cli_agent(
    user_id: str = Depends(_get_user_id),
    db: AsyncSession = Depends(get_session),
) -> dict[str, str | int]:
    agent_count_str = await get_user_setting(
        db, user_id, "agent_scaling", "agent_count"
    )
    agent_count = int(agent_count_str) if agent_count_str else 1

    provider_setting = await get_user_setting(db, user_id, "ai_provider", "provider")
    provider = provider_setting or os.environ.get("CLI_PROVIDER", "claude")

    await redis_client.publish(
        "cli:scaling",
        {"provider": provider, "agent_count": agent_count},
    )

    logger.info(
        "cli_agent_start_requested",
        provider=provider,
        agent_count=agent_count,
        user_id=user_id,
    )

    return {"status": "starting", "provider": provider, "agent_count": agent_count}


@router.post("/cli-control/stop")
async def stop_cli_agent(
    user_id: str = Depends(_get_user_id),
    db: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    provider_setting = await get_user_setting(db, user_id, "ai_provider", "provider")
    provider = provider_setting or os.environ.get("CLI_PROVIDER", "claude")

    await redis_client.publish(
        "cli:scaling",
        {"provider": provider, "agent_count": 0, "action": "stop"},
    )

    logger.info(
        "cli_agent_stop_requested",
        provider=provider,
        user_id=user_id,
    )

    return {"status": "stopping", "provider": provider}
