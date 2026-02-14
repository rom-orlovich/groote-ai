from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = ConfigDict(strict=True, env_file=".env")

    chromadb_url: str = "http://chromadb:8000"
    gkg_url: str = "http://gkg-service:27496"
    redis_url: str = "redis://redis:6379/0"
    postgres_url: str = "postgresql+asyncpg://agent:agent@postgres:5432/agent_system"
    oauth_service_url: str = "http://oauth-service:8010"

    jira_api_url: str = "http://jira-api:3002"
    github_api_url: str = "http://github-api:3001"
    internal_service_key: str = ""

    github_token: str = ""

    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    repos_dir: str = "/data/repos"
    chunk_size: int = 1000
    chunk_overlap: int = 200

    log_level: str = "INFO"
    host: str = "0.0.0.0"
    port: int = 8004


settings = Settings()
