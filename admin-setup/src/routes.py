import service
import validators
from config import get_settings
from db import get_db
from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from models import (
    AuthRequest,
    AuthResponse,
    CompleteResponse,
    ExportResponse,
    InfrastructureResponse,
    SaveStepRequest,
    SaveStepResponse,
    ServiceHealth,
    SetupStatusResponse,
    ValidateRequest,
    ValidateResponse,
)
from sqlalchemy.ext.asyncio import AsyncSession

admin_router = APIRouter(prefix="/api", tags=["admin"])
settings = get_settings()

CATEGORY_MAP: dict[str, tuple[str, dict[str, str]]] = {
    "public_url": ("domain", {"PUBLIC_URL": "Public URL"}),
    "github": (
        "github",
        {
            "GITHUB_APP_ID": "GitHub App ID",
            "GITHUB_APP_NAME": "GitHub App Name",
            "GITHUB_CLIENT_ID": "GitHub Client ID",
            "GITHUB_CLIENT_SECRET": "GitHub Client Secret",
            "GITHUB_PRIVATE_KEY_FILE": "GitHub Private Key File",
            "GITHUB_WEBHOOK_SECRET": "GitHub Webhook Secret",
        },
    ),
    "jira": (
        "jira",
        {
            "JIRA_CLIENT_ID": "Jira Client ID",
            "JIRA_CLIENT_SECRET": "Jira Client Secret",
            "JIRA_SITE_URL": "Jira Site URL",
        },
    ),
    "slack": (
        "slack",
        {
            "SLACK_CLIENT_ID": "Slack Client ID",
            "SLACK_CLIENT_SECRET": "Slack Client Secret",
            "SLACK_SIGNING_SECRET": "Slack Signing Secret",
            "SLACK_STATE_SECRET": "Slack State Secret",
        },
    ),
}

SENSITIVE_KEYS = {
    "GITHUB_CLIENT_SECRET",
    "GITHUB_WEBHOOK_SECRET",
    "JIRA_CLIENT_SECRET",
    "SLACK_CLIENT_SECRET",
    "SLACK_SIGNING_SECRET",
    "SLACK_STATE_SECRET",
}


def get_admin_session(admin_session: str | None = Cookie(None)) -> str:
    if not admin_session or admin_session != settings.admin_setup_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return admin_session


@admin_router.post("/auth", response_model=AuthResponse)
async def authenticate(request: AuthRequest, response: Response) -> AuthResponse:
    if request.token != settings.admin_setup_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    response.set_cookie(
        key="admin_session",
        value=settings.admin_setup_token,
        httponly=True,
        samesite="strict",
        max_age=86400,
    )
    return AuthResponse(authenticated=True)


@admin_router.get("/setup/status", response_model=SetupStatusResponse)
async def get_setup_status(
    _auth: str = Depends(get_admin_session),
    db: AsyncSession = Depends(get_db),
) -> SetupStatusResponse:
    state = await service.get_setup_state(db)
    return SetupStatusResponse(
        is_complete=state.is_complete,
        current_step=state.current_step,
        completed_steps=state.get_completed_steps(),
        skipped_steps=state.get_skipped_steps(),
        progress_percent=int(state.progress_percent),
    )


@admin_router.get("/setup/infrastructure", response_model=InfrastructureResponse)
async def get_infrastructure(
    _auth: str = Depends(get_admin_session),
) -> InfrastructureResponse:
    result = await validators.check_infrastructure()
    return InfrastructureResponse(
        postgres=ServiceHealth(**result["postgres"]),
        redis=ServiceHealth(**result["redis"]),
    )


@admin_router.post("/setup/steps/{step_id}", response_model=SaveStepResponse)
async def save_step(
    step_id: str,
    request: SaveStepRequest,
    _auth: str = Depends(get_admin_session),
    db: AsyncSession = Depends(get_db),
) -> SaveStepResponse:
    if not request.skip and step_id in CATEGORY_MAP:
        category, field_names = CATEGORY_MAP[step_id]
        for key, value in request.configs.items():
            if key in field_names:
                await service.save_config(
                    db,
                    key,
                    value,
                    category,
                    field_names[key],
                    is_sensitive=key in SENSITIVE_KEYS,
                )

    state = await service.update_setup_step(db, step_id, skip=request.skip)
    return SaveStepResponse(
        success=True,
        current_step=state.current_step,
        progress_percent=int(state.progress_percent),
    )


@admin_router.get("/setup/steps/{step_id}/config")
async def get_step_config(
    step_id: str,
    _auth: str = Depends(get_admin_session),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    if step_id not in CATEGORY_MAP:
        return {}
    category, _ = CATEGORY_MAP[step_id]
    return await service.get_configs_by_category(db, category)


@admin_router.post("/setup/validate/{service_name}", response_model=ValidateResponse)
async def validate_service(
    service_name: str,
    request: ValidateRequest,
    _auth: str = Depends(get_admin_session),
) -> ValidateResponse:
    if service_name == "public_url":
        result = validators.validate_public_url(request.configs.get("PUBLIC_URL", ""))
    elif service_name == "github":
        result = await validators.validate_github(request.configs)
    elif service_name == "jira":
        result = await validators.validate_jira(request.configs)
    elif service_name == "slack":
        result = await validators.validate_slack(request.configs)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown service: {service_name}")
    return ValidateResponse(valid=result["valid"], message=result["message"])


@admin_router.get("/setup/summary")
async def get_config_summary(
    _auth: str = Depends(get_admin_session),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, str | bool]]:
    return await service.get_masked_configs(db)


@admin_router.get("/setup/export", response_model=ExportResponse)
async def export_config(
    _auth: str = Depends(get_admin_session),
    db: AsyncSession = Depends(get_db),
) -> ExportResponse:
    configs = await service.get_all_configs(db)
    content = service.generate_env_content(configs)
    return ExportResponse(content=content, filename=".env")


@admin_router.post("/setup/complete", response_model=CompleteResponse)
async def complete(
    _auth: str = Depends(get_admin_session),
    db: AsyncSession = Depends(get_db),
) -> CompleteResponse:
    await service.complete_setup(db)
    return CompleteResponse(status="complete", message="Setup completed successfully")


@admin_router.post("/setup/reset", response_model=CompleteResponse)
async def reset(
    _auth: str = Depends(get_admin_session),
    db: AsyncSession = Depends(get_db),
) -> CompleteResponse:
    await service.reset_setup(db)
    return CompleteResponse(status="reset", message="Setup has been reset")
