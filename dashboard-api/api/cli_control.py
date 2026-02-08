import os
from datetime import UTC, datetime

import structlog
from core.database.redis_client import redis_client
from fastapi import APIRouter
from pydantic import BaseModel

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
        status = data.get("status", "")
        detail = data.get("detail", "")
        startup_steps.append(CLIStartupStep(step=step, status=status, detail=detail))

        if step == "ready" and status == "healthy":
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
