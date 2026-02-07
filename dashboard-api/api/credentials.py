import httpx
import structlog
from core.config import Settings
from fastapi import APIRouter

logger = structlog.get_logger()
router = APIRouter()
settings = Settings()

CLI_HEALTH_URLS = [
    f"{settings.agent_engine_url}/health",
    "http://cli:8080/health",
]


@router.get("/credentials/cli-status")
async def cli_status() -> dict[str, bool | str]:
    async with httpx.AsyncClient(timeout=5.0) as client:
        for url in CLI_HEALTH_URLS:
            try:
                response = await client.get(url)
                if response.status_code == 200:
                    return {"active": True, "message": "CLI agent is running"}
            except httpx.RequestError:
                continue
    return {"active": False, "message": "CLI agent is not reachable"}
