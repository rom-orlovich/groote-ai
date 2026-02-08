from typing import Any
from uuid import UUID

import structlog
from config.settings import Settings, get_settings
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from providers.github import GitHubOAuthProvider
from providers.jira import JiraOAuthProvider
from providers.slack import SlackOAuthProvider
from services.installation_service import InstallationService
from services.token_service import TokenService
from services.webhook_service import WebhookRegistrationService
from sqlalchemy.ext.asyncio import AsyncSession

from .server import get_session

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/oauth", tags=["oauth"])

PROVIDERS = {
    "github": GitHubOAuthProvider,
    "slack": SlackOAuthProvider,
    "jira": JiraOAuthProvider,
}


def validate_platform_credentials(platform: str, settings: Settings) -> tuple[bool, str]:
    required_fields: dict[str, list[tuple[str, str]]] = {
        "github": [
            ("client_id", settings.github_client_id),
            ("client_secret", settings.github_client_secret),
            ("private_key", settings.github_private_key),
            ("app_id", settings.github_app_id),
        ],
        "jira": [
            ("client_id", settings.jira_client_id),
            ("client_secret", settings.jira_client_secret),
        ],
        "slack": [
            ("client_id", settings.slack_client_id),
            ("client_secret", settings.slack_client_secret),
        ],
    }

    missing = [name for name, value in required_fields.get(platform, []) if not value]
    if missing:
        return False, f"Missing credentials: {', '.join(missing).upper()}"
    return True, ""


@router.get("/install/{platform}")
async def start_installation(
    platform: str,
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> RedirectResponse:
    if platform not in PROVIDERS:
        raise HTTPException(status_code=400, detail=f"Unknown platform: {platform}")

    valid, error = validate_platform_credentials(platform, settings)
    if not valid:
        raise HTTPException(
            status_code=503,
            detail=f"OAuth not configured for {platform}. {error}. Complete setup wizard first.",
        )

    provider = PROVIDERS[platform](settings)
    installation_service = InstallationService(session)

    code_verifier = None
    if platform == "jira":
        code_verifier = provider._generate_code_verifier()

    state = await installation_service.create_oauth_state(
        platform=platform,
        code_verifier=code_verifier,
    )

    if platform == "jira" and code_verifier:
        provider._code_verifiers[state] = code_verifier

    auth_url = provider.get_authorization_url(state)
    logger.info("oauth_flow_started", platform=platform, state=state[:8])

    return RedirectResponse(url=auth_url)


@router.get("/callback/{platform}")
async def oauth_callback(
    platform: str,
    code: str | None = Query(None),
    state: str | None = Query(None),
    installation_id: str | None = Query(None),
    setup_action: str | None = Query(None),  # noqa: ARG001
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> RedirectResponse:
    frontend_base = settings.frontend_url
    if platform not in PROVIDERS:
        return RedirectResponse(
            url=f"{frontend_base}/integrations?oauth_callback={platform}&error=unknown_platform"
        )

    try:
        provider = PROVIDERS[platform](settings)
        installation_service = InstallationService(session)

        if platform == "github" and installation_id:
            info = await provider.get_installation_by_id(installation_id)
            tokens = await provider.get_installation_token(installation_id)
        elif code and state:
            oauth_state = await installation_service.validate_oauth_state(state)

            if not oauth_state:
                return RedirectResponse(
                    url=f"{frontend_base}/integrations?oauth_callback={platform}&error=invalid_state"
                )

            if platform == "jira" and oauth_state.code_verifier:
                provider._code_verifiers[state] = oauth_state.code_verifier

            tokens = await provider.exchange_code(code, state)
            info = await provider.get_installation_info(tokens)
        else:
            return RedirectResponse(
                url=f"{frontend_base}/integrations?oauth_callback={platform}&error=missing_params"
            )

        installation = await installation_service.create_installation(
            platform=platform,
            tokens=tokens,
            info=info,
        )

        logger.info(
            "oauth_installation_created",
            platform=platform,
            org_id=info.external_org_id,
            installation_id=str(installation.id),
        )

        webhook_param = ""
        try:
            webhook_service = WebhookRegistrationService(settings)
            if platform == "github":
                result = await webhook_service.configure_github_app_webhook()
            elif platform == "jira":
                cloud_id = info.external_org_id
                result = await webhook_service.register_jira_webhook(
                    access_token=tokens.access_token,
                    cloud_id=cloud_id,
                )
            else:
                result = None

            if result:
                await installation_service.update_webhook_status(
                    installation_id=installation.id,
                    webhook_registered=result.success,
                    webhook_url=result.webhook_url,
                    webhook_external_id=result.external_id,
                    webhook_error=result.error,
                )
                webhook_param = "&webhook=ok" if result.success else "&webhook=failed"
        except Exception as webhook_err:
            logger.error(
                "webhook_registration_error",
                platform=platform,
                error=str(webhook_err),
            )
            webhook_param = "&webhook=failed"

        return RedirectResponse(
            url=f"{frontend_base}/integrations?oauth_callback={platform}&success=true{webhook_param}"
        )
    except Exception as e:
        logger.error("oauth_callback_error", platform=platform, error=str(e))
        return RedirectResponse(
            url=f"{frontend_base}/integrations?oauth_callback={platform}&error=callback_failed"
        )


@router.get("/installations")
async def list_installations(
    platform: str | None = Query(None),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    installation_service = InstallationService(session)
    installations = await installation_service.list_installations(platform)
    return {"installations": installations}


@router.delete("/installations/{installation_id}")
async def revoke_installation(
    installation_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> dict[str, bool]:
    installation_service = InstallationService(session)
    success = await installation_service.revoke_installation(installation_id)

    if not success:
        raise HTTPException(status_code=404, detail="Installation not found")

    return {"success": True}


@router.get("/token/{platform}")
async def get_token(
    platform: str,
    org_id: str | None = Query(None),
    install_id: str | None = Query(None),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    if platform not in PROVIDERS:
        raise HTTPException(status_code=400, detail=f"Unknown platform: {platform}")

    token_service = TokenService(session)

    if platform == "github" and install_id:
        token = await token_service.get_github_installation_token(install_id)
    else:
        token = await token_service.get_token(platform, org_id=org_id)

    if not token:
        raise HTTPException(status_code=404, detail="No active installation found")

    return {"token": token[:10] + "..." if token else None, "available": bool(token)}
