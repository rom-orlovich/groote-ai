from contextlib import asynccontextmanager

import httpx
import structlog
from fastapi import FastAPI
from middleware import AuthMiddleware, error_handler

from .routes import router

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("sentry_api_starting")
    yield
    logger.info("sentry_api_shutting_down")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Sentry API Service",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(AuthMiddleware)
    app.add_exception_handler(httpx.HTTPStatusError, error_handler)
    app.add_exception_handler(Exception, error_handler)

    app.include_router(router)

    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "sentry-api"}

    return app
