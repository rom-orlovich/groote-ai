from functools import lru_cache

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = ConfigDict(strict=True, env_file=".env", extra="ignore")

    port: int = 8010
    base_url: str = "http://localhost:8010"
    frontend_url: str = "http://localhost:3005"
    public_url: str = ""
    dashboard_api_url: str = "http://dashboard-api:5000"

    @property
    def webhook_base_url(self) -> str:
        return self.public_url or self.frontend_url

    database_url: str = "postgresql+asyncpg://agent:agent@localhost:5432/agent_system"

    github_app_id: str = ""
    github_app_name: str = ""
    github_client_id: str = ""
    github_client_secret: str = ""
    github_private_key: str = ""
    github_private_key_path: str = ""
    github_webhook_secret: str = ""

    slack_client_id: str = ""
    slack_client_secret: str = ""
    slack_signing_secret: str = ""
    slack_state_secret: str = ""

    jira_client_id: str = ""
    jira_client_secret: str = ""

    token_encryption_key: str = ""
    internal_service_key: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
