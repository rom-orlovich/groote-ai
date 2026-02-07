from pathlib import Path

import httpx
import structlog

from config.settings import Settings, get_settings

logger = structlog.get_logger(__name__)


async def load_credentials_for_platform(
    platform: str,
    settings: Settings | None = None,
) -> dict[str, str]:
    if settings is None:
        settings = get_settings()

    url = f"{settings.dashboard_api_url}/api/setup/oauth-credentials/{platform}"

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url)
            if response.status_code == 200:
                creds = response.json()
                logger.info("credentials_fetched", platform=platform, count=len(creds))
                return creds
            logger.warning(
                "credentials_fetch_failed",
                platform=platform,
                status=response.status_code,
            )
    except httpx.RequestError as e:
        logger.warning(
            "credential_load_failed",
            platform=platform,
            error=str(e),
        )

    return {}


def _load_private_key_from_file(settings: Settings) -> str | None:
    path = settings.github_private_key_path
    if not path:
        return None
    key_file = Path(path)
    if not key_file.exists():
        logger.warning("private_key_file_not_found", path=path)
        return None
    content = key_file.read_text().strip()
    logger.info("private_key_loaded_from_file", path=path)
    return content


def _is_valid_pem_key(value: str) -> bool:
    return "BEGIN" in value and "END" in value and len(value) > 100


def apply_credentials_to_settings(
    settings: Settings,
    platform: str,
    creds: dict[str, str],
) -> None:
    field_map: dict[str, dict[str, str]] = {
        "github": {
            "GITHUB_APP_ID": "github_app_id",
            "GITHUB_APP_NAME": "github_app_name",
            "GITHUB_CLIENT_ID": "github_client_id",
            "GITHUB_CLIENT_SECRET": "github_client_secret",
            "GITHUB_PRIVATE_KEY": "github_private_key",
            "GITHUB_WEBHOOK_SECRET": "github_webhook_secret",
        },
        "jira": {
            "JIRA_CLIENT_ID": "jira_client_id",
            "JIRA_CLIENT_SECRET": "jira_client_secret",
        },
        "slack": {
            "SLACK_CLIENT_ID": "slack_client_id",
            "SLACK_CLIENT_SECRET": "slack_client_secret",
            "SLACK_SIGNING_SECRET": "slack_signing_secret",
        },
    }

    mapping = field_map.get(platform, {})
    applied = []
    skipped = []

    for env_key, attr_name in mapping.items():
        value = creds.get(env_key, "")
        current = getattr(settings, attr_name, "")
        if value and not current:
            object.__setattr__(settings, attr_name, value)
            applied.append(attr_name)
        elif current:
            skipped.append(attr_name)

    if platform == "github":
        file_key = _load_private_key_from_file(settings)
        if file_key:
            object.__setattr__(settings, "github_private_key", file_key)
            applied.append("github_private_key(file)")
        elif not _is_valid_pem_key(settings.github_private_key):
            db_key = creds.get("GITHUB_PRIVATE_KEY", "")
            if _is_valid_pem_key(db_key):
                object.__setattr__(settings, "github_private_key", db_key)
                applied.append("github_private_key(db_override)")
                logger.info("private_key_env_invalid_using_db")

    if applied:
        logger.info("credentials_applied", platform=platform, fields=applied)
    if skipped:
        logger.debug("credentials_skipped_env_set", platform=platform, fields=skipped)
