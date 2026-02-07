from contextlib import asynccontextmanager

import httpx
import structlog
from config import get_settings
from fastapi import FastAPI
from middleware import AuthMiddleware, error_handler
from token_provider import TokenProvider

from .routes import router

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    app.state.token_provider = TokenProvider(
        oauth_service_url=settings.oauth_service_url,
        internal_service_key=settings.internal_service_key,
        static_token=settings.github_token,
        use_oauth=settings.use_oauth,
    )
    logger.info("github_api_starting", use_oauth=settings.use_oauth)
    yield
    logger.info("github_api_shutting_down")


def create_app() -> FastAPI:
    app = FastAPI(
        title="GitHub API Service",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(AuthMiddleware)
    app.add_exception_handler(httpx.HTTPStatusError, error_handler)
    app.add_exception_handler(Exception, error_handler)

    app.include_router(router)

    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "github-api"}

    return app
