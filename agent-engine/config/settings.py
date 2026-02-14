from functools import lru_cache
from typing import Literal

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = ConfigDict(strict=True, env_file=".env", extra="ignore")

    port: int = 9100
    cli_provider: Literal["claude", "cursor"] = "claude"
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_db: int = 0
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_user: str = "agent"
    postgres_password: str = "agent"
    postgres_db: str = "agent_system"
    max_concurrent_tasks: int = 5
    task_timeout_seconds: int = 3600
    log_level: str = "INFO"
    internal_dashboard_api_url: str = "http://internal-dashboard-api:5000"
    dashboard_api_url: str = "http://dashboard-api:5000"

    slack_api_url: str = "http://slack-api:3003"
    slack_notification_channel: str = ""
    oauth_service_url: str = "http://oauth-service:8010"
    internal_service_key: str = ""

    knowledge_services_enabled: bool = True
    knowledge_graph_url: str = "http://gkg-service:4000"
    llamaindex_url: str = "http://llamaindex-service:8002"
    knowledge_timeout_seconds: float = 10.0
    knowledge_retry_count: int = 2

    # Bot configuration
    bot_mentions: str = "@agent,@groote"
    bot_approve_command: str = "approve"
    bot_improve_keywords: str = "improve,fix,update,refactor,change,implement,address"

    @property
    def bot_mention_list(self) -> list[str]:
        return [m.strip().lower() for m in self.bot_mentions.split(",") if m.strip()]

    @property
    def approve_patterns(self) -> list[str]:
        return [f"{m} {self.bot_approve_command}" for m in self.bot_mention_list]

    @property
    def improve_keyword_set(self) -> set[str]:
        return {k.strip().lower() for k in self.bot_improve_keywords.split(",") if k.strip()}

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @property
    def postgres_url(self) -> str:
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
