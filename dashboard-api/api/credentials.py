import httpx
import structlog
from core.config import Settings
from fastapi import APIRouter

logger = structlog.get_logger()
router = APIRouter()
settings = Settings()

CLI_BASE_URLS = [
    settings.agent_engine_url,
    "http://cli:9100",
]


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
