import asyncio
import json
from contextlib import asynccontextmanager, suppress

import structlog
from api import (
    analytics,
    conversations,
    credentials,
    dashboard,
    oauth_status,
    setup,
    sources,
    user_settings,
    webhook_status,
    websocket,
)
from core.config import Settings
from core.database import init_db, shutdown_db
from core.database.redis_client import redis_client
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logger = structlog.get_logger()

settings = Settings()


async def _task_status_listener(app: FastAPI) -> None:
    import redis.asyncio as aioredis
    from shared import TaskStatusMessage

    try:
        sub_client = aioredis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)
        pubsub = sub_client.pubsub()
        await pubsub.psubscribe("task:*:status")
        logger.info("task_status_listener_started")

        async for message in pubsub.listen():
            if message["type"] != "pmessage":
                continue
            try:
                channel = message["channel"]
                task_id = channel.split(":")[1]
                data = json.loads(message["data"])
                status = data.get("status", "unknown")

                await app.state.ws_hub.broadcast(
                    TaskStatusMessage(
                        task_id=task_id,
                        status=status,
                    )
                )
            except Exception as e:
                logger.warning("task_status_broadcast_error", error=str(e))
    except asyncio.CancelledError:
        logger.info("task_status_listener_stopped")
    except Exception as e:
        logger.error("task_status_listener_fatal", error=str(e))


@asynccontextmanager
async def lifespan(app: FastAPI):
    from core.websocket_hub import WebSocketHub

    logger.info("dashboard_starting")
    await init_db()
    await redis_client.connect()
    app.state.ws_hub = WebSocketHub()

    listener_task = asyncio.create_task(_task_status_listener(app))

    logger.info("dashboard_started")
    yield
    logger.info("dashboard_shutting_down")

    listener_task.cancel()
    with suppress(asyncio.CancelledError):
        await listener_task

    await redis_client.disconnect()
    await shutdown_db()
    logger.info("dashboard_stopped")


app = FastAPI(
    title="Groote AI Dashboard",
    version="1.0.0",
    description="Enhanced dashboard with task streaming and analytics",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(",") if settings.cors_origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard.router, prefix="/api", tags=["dashboard"])
app.include_router(analytics.router, prefix="/api", tags=["analytics"])
app.include_router(conversations.router, prefix="/api", tags=["conversations"])
app.include_router(webhook_status.router, prefix="/api", tags=["webhooks"])
app.include_router(oauth_status.router, prefix="/api", tags=["oauth"])
app.include_router(setup.router, prefix="/api", tags=["setup"])
app.include_router(credentials.router, prefix="/api", tags=["credentials"])
app.include_router(user_settings.router, tags=["user-settings"])
app.include_router(sources.router, tags=["sources"])
app.include_router(websocket.router, tags=["websocket"])


@app.get("/api/health")
async def health():
    return {"status": "healthy", "service": "dashboard-api"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=False,
        log_level=settings.log_level.lower(),
    )
