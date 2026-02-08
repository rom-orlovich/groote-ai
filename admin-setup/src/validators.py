import httpx
import structlog
from config import get_settings
from sqlalchemy import text

logger = structlog.get_logger()


async def check_infrastructure() -> dict[str, dict[str, str | bool]]:
    settings = get_settings()
    postgres_status = await _check_postgres(settings.database_url)
    redis_status = await _check_redis(settings.redis_url)
    return {"postgres": postgres_status, "redis": redis_status}


async def _check_postgres(database_url: str) -> dict[str, str | bool]:
    try:
        from sqlalchemy.ext.asyncio import create_async_engine

        engine = create_async_engine(database_url)
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        await engine.dispose()
        return {"healthy": True, "message": "Connected"}
    except Exception as e:
        logger.error("postgres_check_failed", error=str(e))
        return {"healthy": False, "message": str(e)}


async def _check_redis(redis_url: str) -> dict[str, str | bool]:
    try:
        import redis.asyncio as aioredis

        client = aioredis.from_url(redis_url)
        await client.ping()
        await client.aclose()
        return {"healthy": True, "message": "Connected"}
    except Exception as e:
        logger.error("redis_check_failed", error=str(e))
        return {"healthy": False, "message": str(e)}


def validate_public_url(url: str) -> dict[str, str | bool]:
    if not url.startswith("https://") and not url.startswith("http://"):
        return {"valid": False, "message": "URL must start with http:// or https://"}
    if " " in url or "." not in url.split("://", 1)[-1]:
        return {"valid": False, "message": "Invalid URL format"}
    return {"valid": True, "message": "URL format is valid"}


async def validate_github(configs: dict[str, str]) -> dict[str, str | bool]:
    app_id = configs.get("GITHUB_APP_ID", "")
    private_key_path = "/secrets/github-private-key.pem"
    if not app_id:
        return {"valid": False, "message": "GitHub App ID is required"}
    try:
        import time

        import jwt

        try:
            with open(private_key_path) as f:
                private_key = f.read()
        except FileNotFoundError as e:
            logger.error("github_key_file_not_found", path=private_key_path, error=str(e))
            return {"valid": False, "message": f"Private key file not found: {private_key_path}"}
        except Exception as e:
            logger.error("github_key_read_error", path=private_key_path, error=str(e))
            return {"valid": False, "message": f"Cannot read private key: {e!s}"}

        now = int(time.time())
        payload = {
            "iss": app_id,
            "exp": now + 600,
            "iat": now,
        }
        token = jwt.encode(payload, private_key, algorithm="RS256")
        logger.info("github_jwt_created", app_id=app_id, token_length=len(token))

        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.github.com/app",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github+json",
                },
                timeout=10.0,
            )
            logger.info("github_api_response", status=response.status_code)
            if response.status_code == 200:
                return {"valid": True, "message": "GitHub App verified"}
            logger.error(
                "github_validation_failed", status=response.status_code, body=response.text[:200]
            )
            return {
                "valid": False,
                "message": f"GitHub API returned {response.status_code}",
            }
    except ImportError as e:
        logger.error("jwt_import_error", error=str(e))
        return {"valid": False, "message": "PyJWT library required"}
    except Exception as e:
        logger.error("github_validation_error", error=str(e), type=type(e).__name__)
        return {"valid": False, "message": f"Validation error: {e!s}"}


async def validate_jira(configs: dict[str, str]) -> dict[str, str | bool]:
    site_url = configs.get("JIRA_SITE_URL", "")
    if not site_url:
        return {"valid": False, "message": "Jira site URL is required"}
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{site_url.rstrip('/')}/rest/api/3/myself",
                timeout=10.0,
            )
            if response.status_code == 401:
                return {
                    "valid": True,
                    "message": "Jira site reachable (auth will complete via OAuth)",
                }
            return {"valid": True, "message": "Jira site reachable"}
    except httpx.HTTPError as e:
        return {"valid": False, "message": f"Cannot reach Jira: {e!s}"}


async def validate_slack(configs: dict[str, str]) -> dict[str, str | bool]:
    client_id = configs.get("SLACK_CLIENT_ID", "")
    if not client_id:
        return {"valid": False, "message": "Client ID is required"}
    return {
        "valid": True,
        "message": "Slack credentials saved (verified during OAuth flow)",
    }
