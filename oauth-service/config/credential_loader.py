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
                logger.info(
                    "credentials_loaded",
                    platform=platform,
                    key_count=len(creds),
                )
                return creds
    except httpx.RequestError as e:
        logger.warning(
            "credential_load_failed",
            platform=platform,
            error=str(e),
        )

    return {}


def apply_credentials_to_settings(
    settings: Settings,
    platform: str,
    creds: dict[str, str],
) -> None:
    field_map: dict[str, dict[str, str]] = {
        "github": {
            "GITHUB_APP_ID": "github_app_id",
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
    for env_key, attr_name in mapping.items():
        value = creds.get(env_key, "")
        if value and not getattr(settings, attr_name, ""):
            object.__setattr__(settings, attr_name, value)
