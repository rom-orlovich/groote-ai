from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from config.credential_loader import apply_credentials_to_settings, load_credentials_for_platform
from config.settings import get_settings
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

logger = structlog.get_logger(__name__)

engine = None
async_session_factory = None

PLATFORMS = ["github", "jira", "slack"]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    global engine, async_session_factory

    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=False)
    async_session_factory = async_sessionmaker(engine, expire_on_commit=False)

    logger.info("database_connected", url=settings.database_url[:30] + "...")

    for platform in PLATFORMS:
        try:
            creds = await load_credentials_for_platform(platform, settings)
            if creds:
                apply_credentials_to_settings(settings, platform, creds)
                logger.info("credentials_loaded", platform=platform, fields=list(creds.keys()))
        except Exception as e:
            logger.warning("credential_load_failed", platform=platform, error=str(e))

    yield

    await engine.dispose()
    logger.info("database_disconnected")


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    if async_session_factory is None:
        raise RuntimeError("Database not initialized")

    async with async_session_factory() as session:
        yield session


def create_app() -> FastAPI:
    app = FastAPI(
        title="OAuth Service",
        description="Multi-tenant OAuth installation service",
        version="1.0.0",
        lifespan=lifespan,
    )

    from .internal_routes import internal_router
    from .routes import router

    app.include_router(router)
    app.include_router(internal_router)

    @app.get("/health")
    async def health_check() -> dict[str, str]:
        return {"status": "healthy"}

    return app
