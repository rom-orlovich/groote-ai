"""CLI agent control endpoints."""

import os
from datetime import UTC, datetime

import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = structlog.get_logger()

router = APIRouter()


class CLIStatusResponse(BaseModel):
    """CLI status response model."""

    status: str
    active_instances: int
    max_instances: int
    health_check: bool
    last_checked: str


class CLIControlResponse(BaseModel):
    """CLI control response model."""

    status: str
    message: str
    timestamp: str


@router.get("/cli-status")
async def get_cli_status() -> CLIStatusResponse:
    """Get current CLI agent status."""
    import httpx

    try:
        agent_engine_url = os.getenv("AGENT_ENGINE_URL", "http://agent-engine:8080")
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{agent_engine_url}/health")

            if response.status_code == 200:
                data = response.json()
                return CLIStatusResponse(
                    status="running",
                    active_instances=data.get("active_agents", 1),
                    max_instances=5,
                    health_check=True,
                    last_checked=datetime.now(UTC).isoformat(),
                )

        return CLIStatusResponse(
            status="stopped",
            active_instances=0,
            max_instances=5,
            health_check=False,
            last_checked=datetime.now(UTC).isoformat(),
        )
    except httpx.TimeoutException:
        logger.warning("cli_health_check_timeout")
        return CLIStatusResponse(
            status="unknown",
            active_instances=0,
            max_instances=5,
            health_check=False,
            last_checked=datetime.now(UTC).isoformat(),
        )
    except Exception as e:
        logger.error("cli_status_error", error=str(e))
        return CLIStatusResponse(
            status="unknown",
            active_instances=0,
            max_instances=5,
            health_check=False,
            last_checked=datetime.now(UTC).isoformat(),
        )


@router.post("/cli-control/start")
async def start_cli_agent() -> CLIControlResponse:
    """Start the CLI agent."""
    import httpx

    try:
        agent_engine_url = os.getenv("AGENT_ENGINE_URL", "http://agent-engine:8080")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(f"{agent_engine_url}/start")

            if response.status_code >= 200 and response.status_code < 300:
                logger.info("cli_agent_started")
                return CLIControlResponse(
                    status="started",
                    message="CLI agent is starting up",
                    timestamp=datetime.now(UTC).isoformat(),
                )

        logger.error("start_cli_failed", status=response.status_code)
        raise HTTPException(status_code=response.status_code, detail="Failed to start CLI agent")
    except httpx.TimeoutException:
        logger.error("start_cli_timeout")
        raise HTTPException(status_code=503, detail="Start CLI timeout")
    except Exception as e:
        logger.error("start_cli_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cli-control/stop")
async def stop_cli_agent() -> CLIControlResponse:
    """Stop the CLI agent."""
    import httpx

    try:
        agent_engine_url = os.getenv("AGENT_ENGINE_URL", "http://agent-engine:8080")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(f"{agent_engine_url}/stop")

            if response.status_code >= 200 and response.status_code < 300:
                logger.info("cli_agent_stopped")
                return CLIControlResponse(
                    status="stopped",
                    message="CLI agent stopped",
                    timestamp=datetime.now(UTC).isoformat(),
                )

        logger.error("stop_cli_failed", status=response.status_code)
        raise HTTPException(status_code=response.status_code, detail="Failed to stop CLI agent")
    except httpx.TimeoutException:
        logger.error("stop_cli_timeout")
        raise HTTPException(status_code=503, detail="Stop CLI timeout")
    except Exception as e:
        logger.error("stop_cli_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
