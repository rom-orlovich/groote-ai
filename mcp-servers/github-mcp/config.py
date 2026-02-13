from functools import lru_cache

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = ConfigDict(strict=True, env_file=".env", extra="ignore")

    port: int = 9001
    github_api_url: str = "http://github-api:3001"
    request_timeout: int = 30


@lru_cache
def get_settings() -> Settings:
    return Settings()
