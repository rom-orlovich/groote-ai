from config import get_settings
from fastapi import APIRouter, Header, HTTPException, status
from models import SetupStatus, SetupStep

admin_router = APIRouter(prefix="/api", tags=["admin"])
settings = get_settings()


def verify_admin_token(x_admin_token: str = Header(None)) -> None:
    if x_admin_token != settings.admin_setup_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin token",
        )


@admin_router.get("/setup/status", dependencies=[])
async def get_setup_status(x_admin_token: str = Header(None)) -> SetupStatus:
    verify_admin_token(x_admin_token)
    return SetupStatus(
        is_authenticated=True,
        steps=[
            SetupStep(
                id="infrastructure",
                title="Infrastructure Health",
                description="Check database and Redis connectivity",
                status="pending",
            ),
            SetupStep(
                id="public_url",
                title="Public URL Configuration",
                description="Set your public domain for webhooks",
                status="pending",
            ),
            SetupStep(
                id="github",
                title="GitHub App Configuration",
                description="Configure GitHub OAuth credentials",
                status="pending",
            ),
            SetupStep(
                id="jira",
                title="Jira OAuth Configuration",
                description="Configure Jira OAuth credentials",
                status="pending",
            ),
            SetupStep(
                id="slack",
                title="Slack App Configuration",
                description="Configure Slack OAuth credentials",
                status="pending",
            ),
            SetupStep(
                id="review",
                title="Review and Export",
                description="Review all configuration and export .env",
                status="pending",
            ),
        ],
        progress=0,
    )


@admin_router.post("/setup/complete")
async def complete_setup(x_admin_token: str = Header(None)):
    verify_admin_token(x_admin_token)
    return {"status": "complete", "message": "Setup completed successfully"}
