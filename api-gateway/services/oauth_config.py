import time

import httpx
import structlog

logger = structlog.get_logger(__name__)

_cached_jira_site_url: str | None = None
_jira_cache_expires_at: float = 0
_CACHE_TTL_SECONDS = 300


async def get_jira_site_url(
    oauth_service_url: str,
    service_key: str,
) -> str:
    global _cached_jira_site_url, _jira_cache_expires_at

    if _cached_jira_site_url and time.monotonic() < _jira_cache_expires_at:
        return _cached_jira_site_url

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"{oauth_service_url}/internal/token/jira",
                headers={"X-Internal-Service-Key": service_key},
            )
            response.raise_for_status()
            data = response.json()

        site_url = data.get("metadata", {}).get("site_url", "")
        if site_url:
            _cached_jira_site_url = site_url.rstrip("/")
            _jira_cache_expires_at = time.monotonic() + _CACHE_TTL_SECONDS
            logger.info("jira_site_url_fetched_from_oauth", site_url=_cached_jira_site_url)
            return _cached_jira_site_url
    except Exception as e:
        logger.warning("jira_site_url_fetch_failed", error=str(e))

    return ""
