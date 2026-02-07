import time
from dataclasses import dataclass
from typing import Any

import httpx
import structlog

logger = structlog.get_logger(__name__)

CACHE_TTL_SECONDS = 300


@dataclass
class JiraTokenResult:
    token: str
    auth_mode: str
    base_url: str


class TokenProvider:
    def __init__(
        self,
        oauth_service_url: str,
        internal_service_key: str,
        static_url: str = "",
        static_email: str = "",
        static_token: str = "",
        use_oauth: bool = True,
    ):
        self._oauth_url = oauth_service_url.rstrip("/")
        self._service_key = internal_service_key
        self._static_url = static_url
        self._static_email = static_email
        self._static_token = static_token
        self._use_oauth = use_oauth
        self._cache: dict[str, tuple[JiraTokenResult, float]] = {}

    async def get_token(self) -> JiraTokenResult:
        if self._use_oauth and self._service_key:
            cached = self._get_cached("jira")
            if cached:
                return cached

            result = await self._fetch_oauth_token()
            if result:
                return result

        if self._static_token and self._static_url:
            logger.debug("static_token_used", platform="jira")
            return JiraTokenResult(
                token=self._static_token,
                auth_mode="basic",
                base_url=self._static_url,
            )

        raise RuntimeError("No Jira token available (OAuth unreachable, no static token)")

    @property
    def static_email(self) -> str:
        return self._static_email

    async def _fetch_oauth_token(self) -> JiraTokenResult | None:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self._oauth_url}/internal/token/jira",
                    headers={"X-Internal-Service-Key": self._service_key},
                )
                if response.status_code == 200:
                    data: dict[str, Any] = response.json()
                    if data.get("available") and data.get("token"):
                        metadata = data.get("metadata", {})
                        cloud_id = metadata.get("cloud_id", "")
                        base_url = f"https://api.atlassian.com/ex/jira/{cloud_id}"
                        result = JiraTokenResult(
                            token=data["token"],
                            auth_mode="bearer",
                            base_url=base_url,
                        )
                        self._set_cache("jira", result)
                        logger.info("oauth_token_retrieved", platform="jira")
                        return result
        except httpx.RequestError as e:
            logger.warning("oauth_service_unreachable", platform="jira", error=str(e))
        return None

    def _get_cached(self, key: str) -> JiraTokenResult | None:
        if key in self._cache:
            result, timestamp = self._cache[key]
            if time.monotonic() - timestamp < CACHE_TTL_SECONDS:
                return result
            del self._cache[key]
        return None

    def _set_cache(self, key: str, result: JiraTokenResult) -> None:
        self._cache[key] = (result, time.monotonic())
