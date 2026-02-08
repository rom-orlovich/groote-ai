from functools import lru_cache

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = ConfigDict(strict=True, env_file=".env", extra="ignore")

    port: int = 8015
    admin_setup_token: str = ""
    database_url: str = "postgresql+asyncpg://agent:agent@postgres:5432/agent_system"
    redis_url: str = "redis://redis:6379/0"
    dashboard_url: str = "http://localhost:3005"
    log_level: str = "INFO"
    token_encryption_key: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
