from functools import lru_cache

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = ConfigDict(strict=True, env_file=".env", extra="ignore")

    port: int = 8000
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_db: int = 0
    github_webhook_secret: str = ""
    jira_webhook_secret: str = ""
    slack_signing_secret: str = ""
    jira_ai_agent_name: str = "ai-agent"
    log_level: str = "INFO"
    knowledge_graph_url: str = "http://knowledge-graph:4000"
    agent_engine_url: str = "http://agent-engine:8080"
    github_api_url: str = "http://github-api:3001"
    jira_api_url: str = "http://jira-api:3002"
    slack_api_url: str = "http://slack-api:3003"
    slack_notification_channel: str = ""
    oauth_service_url: str = "http://oauth-service:8010"
    internal_service_key: str = ""

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


@lru_cache
def get_settings() -> Settings:
    return Settings()
