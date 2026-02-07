import time
from typing import Any

import httpx
import structlog

logger = structlog.get_logger(__name__)

CACHE_TTL_SECONDS = 300


class TokenProvider:
    def __init__(
        self,
        oauth_service_url: str,
        internal_service_key: str,
        static_token: str = "",
        use_oauth: bool = True,
    ):
        self._oauth_url = oauth_service_url.rstrip("/")
        self._service_key = internal_service_key
        self._static_token = static_token
        self._use_oauth = use_oauth
        self._cache: dict[str, tuple[str, float]] = {}

    async def get_token(self) -> str:
        if self._use_oauth and self._service_key:
            cached = self._get_cached("github")
            if cached:
                return cached

            token = await self._fetch_oauth_token()
            if token:
                return token

        if self._static_token:
            logger.debug("static_token_used", platform="github")
            return self._static_token

        raise RuntimeError("No GitHub token available (OAuth unreachable, no static token)")

    async def _fetch_oauth_token(self) -> str | None:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self._oauth_url}/internal/token/github",
                    headers={"X-Internal-Service-Key": self._service_key},
                )
                if response.status_code == 200:
                    data: dict[str, Any] = response.json()
                    if data.get("available") and data.get("token"):
                        self._set_cache("github", data["token"])
                        logger.info("oauth_token_retrieved", platform="github")
                        return data["token"]
        except httpx.RequestError as e:
            logger.warning("oauth_service_unreachable", platform="github", error=str(e))
        return None

    def _get_cached(self, key: str) -> str | None:
        if key in self._cache:
            token, timestamp = self._cache[key]
            if time.monotonic() - timestamp < CACHE_TTL_SECONDS:
                return token
            del self._cache[key]
        return None

    def _set_cache(self, key: str, token: str) -> None:
        self._cache[key] = (token, time.monotonic())
