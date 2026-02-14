import time

import httpx
import structlog

logger = structlog.get_logger()

CACHE_TTL_SECONDS = 300


class GitHubTokenProvider:
    def __init__(
        self,
        oauth_service_url: str,
        internal_service_key: str,
        static_token: str = "",
    ):
        self._oauth_url = oauth_service_url.rstrip("/")
        self._service_key = internal_service_key
        self._static_token = static_token
        self._cached_token: str | None = None
        self._cached_at: float = 0.0

    async def get_token(self) -> str:
        if self._service_key:
            if self._cached_token and (time.monotonic() - self._cached_at) < CACHE_TTL_SECONDS:
                return self._cached_token

            token = await self._fetch_oauth_token()
            if token:
                self._cached_token = token
                self._cached_at = time.monotonic()
                logger.info("oauth_token_retrieved", platform="github")
                return token

        if self._static_token:
            logger.debug("static_token_used", platform="github")
            return self._static_token

        raise RuntimeError("No GitHub token available")

    async def _fetch_oauth_token(self) -> str | None:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self._oauth_url}/internal/token/github",
                    headers={"X-Internal-Service-Key": self._service_key},
                )
                if response.status_code == 200:
                    data = response.json()
                    if data.get("available") and data.get("token"):
                        return data["token"]
        except httpx.RequestError as e:
            logger.warning("oauth_service_unreachable", platform="github", error=str(e))
        return None
