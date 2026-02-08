from contextlib import asynccontextmanager

import structlog
import uvicorn
from config import get_settings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import admin_router

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info("admin_setup_starting", port=settings.port)
    yield
    logger.info("admin_setup_shutting_down")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Admin Setup Service",
        version="1.0.0",
        lifespan=lifespan,
    )

    settings = get_settings()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.dashboard_url],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "admin-setup"}

    @app.get("/")
    async def root():
        return {
            "service": "admin-setup",
            "version": "1.0.0",
        }

    app.include_router(admin_router)

    return app


app = create_app()

if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=False,
    )
