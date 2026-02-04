import json
from typing import Literal

import structlog
from core.database import get_session
from core.setup.encryption import get_deployment_mode, is_cloud
from core.setup.service import (
    SETUP_STEPS,
    complete_setup,
    generate_docker_secrets_script,
    generate_env_content,
    generate_github_actions_env,
    generate_k8s_secret,
    get_all_configs,
    get_configs_by_category,
    get_setup_state,
    reset_setup,
    save_config,
    update_setup_step,
)
from core.setup.validators import (
    validate_anthropic,
    validate_github_oauth,
    validate_jira_oauth,
    validate_sentry,
    validate_slack_oauth,
)
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()
router = APIRouter()


class SetupStatusResponse(BaseModel):
    model_config = ConfigDict(strict=True)

    is_complete: bool
    current_step: str
    completed_steps: list[str]
    skipped_steps: list[str]
    progress_percent: float
    total_steps: int
    steps: list[str]
    deployment_mode: str
    is_cloud: bool


class StepConfigItem(BaseModel):
    model_config = ConfigDict(strict=True)

    key: str
    value: str
    display_name: str
    is_sensitive: bool = False


class SaveStepRequest(BaseModel):
    model_config = ConfigDict(strict=True)

    configs: list[StepConfigItem]
    skip: bool = False


class SaveStepResponse(BaseModel):
    model_config = ConfigDict(strict=True)

    success: bool
    step: str
    action: str
    current_step: str
    progress_percent: float


class ValidateRequest(BaseModel):
    model_config = ConfigDict(strict=True)

    credentials: dict[str, str]


class ValidateResponse(BaseModel):
    model_config = ConfigDict(strict=True)

    service: str
    success: bool
    message: str
    details: dict[str, str] | None = None


@router.get("/setup/status")
async def get_status(db: AsyncSession = Depends(get_session)) -> SetupStatusResponse:
    state = await get_setup_state(db)
    return SetupStatusResponse(
        is_complete=state.is_complete,
        current_step=state.current_step,
        completed_steps=json.loads(state.completed_steps),
        skipped_steps=json.loads(state.skipped_steps),
        progress_percent=state.progress_percent,
        total_steps=len(SETUP_STEPS),
        steps=SETUP_STEPS,
        deployment_mode=get_deployment_mode(),
        is_cloud=is_cloud(),
    )


@router.post("/setup/steps/{step}")
async def save_step(
    step: str,
    request: SaveStepRequest,
    db: AsyncSession = Depends(get_session),
) -> SaveStepResponse:
    if step not in SETUP_STEPS:
        raise HTTPException(status_code=400, detail=f"Invalid step: {step}")

    action = "skip" if request.skip else "complete"

    if not request.skip:
        for item in request.configs:
            await save_config(
                db=db,
                key=item.key,
                value=item.value,
                category=step,
                display_name=item.display_name,
                is_sensitive=item.is_sensitive,
            )

    state = await update_setup_step(db, step, action)

    logger.info("setup_step_saved", step=step, action=action)

    return SaveStepResponse(
        success=True,
        step=step,
        action=action,
        current_step=state.current_step,
        progress_percent=state.progress_percent,
    )


@router.get("/setup/steps/{step}/config")
async def get_step_config(
    step: str,
    db: AsyncSession = Depends(get_session),
) -> list[dict[str, str | bool]]:
    if step not in SETUP_STEPS:
        raise HTTPException(status_code=400, detail=f"Invalid step: {step}")
    return await get_configs_by_category(db, step)


@router.post("/setup/validate/{service}")
async def validate_service(
    service: Literal["github_oauth", "jira_oauth", "slack_oauth", "sentry", "anthropic"],
    request: ValidateRequest,
) -> ValidateResponse:
    creds = request.credentials

    if service == "github_oauth":
        result = await validate_github_oauth(
            creds.get("GITHUB_APP_ID", ""),
            creds.get("GITHUB_CLIENT_ID", ""),
            creds.get("GITHUB_CLIENT_SECRET", ""),
        )
    elif service == "jira_oauth":
        result = await validate_jira_oauth(
            creds.get("JIRA_CLIENT_ID", ""),
            creds.get("JIRA_CLIENT_SECRET", ""),
        )
    elif service == "slack_oauth":
        result = await validate_slack_oauth(
            creds.get("SLACK_CLIENT_ID", ""),
            creds.get("SLACK_CLIENT_SECRET", ""),
        )
    elif service == "sentry":
        result = await validate_sentry(creds.get("SENTRY_AUTH_TOKEN", ""))
    elif service == "anthropic":
        result = await validate_anthropic(creds.get("ANTHROPIC_API_KEY", ""))
    else:
        raise HTTPException(status_code=400, detail=f"Unknown service: {service}")

    return ValidateResponse(
        service=result.service,
        success=result.success,
        message=result.message,
        details=result.details,
    )


@router.post("/setup/complete")
async def mark_complete(
    db: AsyncSession = Depends(get_session),
) -> SetupStatusResponse:
    state = await complete_setup(db)
    return SetupStatusResponse(
        is_complete=state.is_complete,
        current_step=state.current_step,
        completed_steps=json.loads(state.completed_steps),
        skipped_steps=json.loads(state.skipped_steps),
        progress_percent=state.progress_percent,
        total_steps=len(SETUP_STEPS),
        steps=SETUP_STEPS,
        deployment_mode=get_deployment_mode(),
        is_cloud=is_cloud(),
    )


@router.post("/setup/reset")
async def reset(
    db: AsyncSession = Depends(get_session),
) -> SetupStatusResponse:
    state = await reset_setup(db)
    return SetupStatusResponse(
        is_complete=state.is_complete,
        current_step=state.current_step,
        completed_steps=json.loads(state.completed_steps),
        skipped_steps=json.loads(state.skipped_steps),
        progress_percent=state.progress_percent,
        total_steps=len(SETUP_STEPS),
        steps=SETUP_STEPS,
        deployment_mode=get_deployment_mode(),
        is_cloud=is_cloud(),
    )


@router.get("/setup/export")
async def export_config(
    format: str = Query("env", pattern="^(env|k8s|docker-secrets|github-actions)$"),
    namespace: str = Query("default"),
    db: AsyncSession = Depends(get_session),
) -> PlainTextResponse:
    configs = await get_all_configs(db)

    generators = {
        "env": lambda: generate_env_content(configs),
        "k8s": lambda: generate_k8s_secret(configs, namespace),
        "docker-secrets": lambda: generate_docker_secrets_script(configs),
        "github-actions": lambda: generate_github_actions_env(configs),
    }

    filenames = {
        "env": ".env",
        "k8s": "groote-ai-secret.yaml",
        "docker-secrets": "create-secrets.sh",
        "github-actions": "github-actions-secrets.txt",
    }

    content = generators[format]()
    return PlainTextResponse(
        content=content,
        headers={"Content-Disposition": f"attachment; filename={filenames[format]}"},
    )


PLATFORM_CREDENTIAL_KEYS: dict[str, list[str]] = {
    "github": [
        "GITHUB_APP_ID",
        "GITHUB_CLIENT_ID",
        "GITHUB_CLIENT_SECRET",
        "GITHUB_PRIVATE_KEY",
        "GITHUB_WEBHOOK_SECRET",
    ],
    "jira": ["JIRA_CLIENT_ID", "JIRA_CLIENT_SECRET"],
    "slack": ["SLACK_CLIENT_ID", "SLACK_CLIENT_SECRET", "SLACK_SIGNING_SECRET"],
    "sentry": ["SENTRY_AUTH_TOKEN", "SENTRY_DSN", "SENTRY_ORG_SLUG"],
}

PLATFORM_CATEGORY_MAP: dict[str, str] = {
    "github": "github_oauth",
    "jira": "jira_oauth",
    "slack": "slack_oauth",
    "sentry": "sentry",
}


@router.get("/setup/oauth-credentials/{platform}")
async def get_oauth_credentials(
    platform: str,
    db: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    if platform not in PLATFORM_CREDENTIAL_KEYS:
        raise HTTPException(status_code=400, detail=f"Unknown platform: {platform}")

    category = PLATFORM_CATEGORY_MAP[platform]
    configs = await get_configs_by_category(db, category)
    allowed_keys = set(PLATFORM_CREDENTIAL_KEYS[platform])
    return {
        str(c["key"]): str(c["value"]) for c in configs if c["key"] in allowed_keys and c["value"]
    }


@router.get("/setup/infrastructure")
async def check_infrastructure() -> dict[str, dict[str, str | bool]]:
    import redis.asyncio as aioredis
    from core.config import Settings

    settings = Settings()
    results: dict[str, dict[str, str | bool]] = {}

    try:
        from sqlalchemy import text
        from sqlalchemy.ext.asyncio import create_async_engine

        engine = create_async_engine(settings.database_url)
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        await engine.dispose()
        results["postgres"] = {"healthy": True, "message": "Connected"}
    except Exception as e:
        results["postgres"] = {"healthy": False, "message": str(e)}

    try:
        r = aioredis.from_url(settings.redis_url)
        await r.ping()
        await r.aclose()
        results["redis"] = {"healthy": True, "message": "Connected"}
    except Exception as e:
        results["redis"] = {"healthy": False, "message": str(e)}

    return results
