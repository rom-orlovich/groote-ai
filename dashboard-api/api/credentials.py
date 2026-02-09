import httpx
import structlog
from core.config import Settings
from fastapi import APIRouter
from pydantic import BaseModel

logger = structlog.get_logger()
router = APIRouter()
settings = Settings()

CLI_BASE_URLS = [
    settings.agent_engine_url,
    "http://cli:9100",
]


class UsageBucket(BaseModel):
    used: int
    limit: int
    remaining: int
    percentage: float
    is_exceeded: bool


class OAuthUsageResponse(BaseModel):
    success: bool
    error: str | None = None
    session: UsageBucket | None = None
    weekly: UsageBucket | None = None


@router.get("/credentials/cli-status")
async def cli_status() -> dict[str, bool | str]:
    async with httpx.AsyncClient(timeout=5.0) as client:
        reachable = False
        for base_url in CLI_BASE_URLS:
            try:
                response = await client.get(f"{base_url}/health")
                if response.status_code == 200:
                    reachable = True
                    break
            except httpx.RequestError:
                continue

        if not reachable:
            return {"active": False, "message": "CLI agent is not reachable"}

        for base_url in CLI_BASE_URLS:
            try:
                auth_response = await client.get(f"{base_url}/health/auth")
                if auth_response.status_code == 200:
                    auth_data = auth_response.json()
                    if not auth_data.get("authenticated", False):
                        return {
                            "active": False,
                            "message": auth_data.get("message", "Not authenticated"),
                        }
                    return {"active": True, "message": "CLI agent is running"}
            except httpx.RequestError:
                continue

        return {"active": True, "message": "CLI agent is running"}


@router.get("/credentials/usage")
async def get_credentials_usage() -> OAuthUsageResponse:
    oauth_url = settings.agent_engine_url
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{oauth_url}/health/auth")
            if response.status_code == 200:
                auth_data = response.json()
                session_usage = auth_data.get("session_usage")
                weekly_usage = auth_data.get("weekly_usage")

                session = None
                if session_usage:
                    used = session_usage.get("used", 0)
                    limit = session_usage.get("limit", 0)
                    remaining = max(0, limit - used)
                    pct = (used / limit * 100) if limit > 0 else 0.0
                    session = UsageBucket(
                        used=used,
                        limit=limit,
                        remaining=remaining,
                        percentage=round(pct, 1),
                        is_exceeded=used >= limit and limit > 0,
                    )

                weekly = None
                if weekly_usage:
                    used = weekly_usage.get("used", 0)
                    limit = weekly_usage.get("limit", 0)
                    remaining = max(0, limit - used)
                    pct = (used / limit * 100) if limit > 0 else 0.0
                    weekly = UsageBucket(
                        used=used,
                        limit=limit,
                        remaining=remaining,
                        percentage=round(pct, 1),
                        is_exceeded=used >= limit and limit > 0,
                    )

                return OAuthUsageResponse(
                    success=True,
                    session=session,
                    weekly=weekly,
                )
    except httpx.RequestError as exc:
        logger.warning("credentials_usage_fetch_failed", error=str(exc))

    return OAuthUsageResponse(success=True, session=None, weekly=None)
