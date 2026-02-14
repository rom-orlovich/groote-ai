import asyncio
import signal
from contextlib import asynccontextmanager, suppress
from typing import Any

import redis.asyncio as redis
import structlog
import uvicorn
from config import get_settings
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from services.knowledge import KnowledgeService, NoopKnowledgeService
from worker import TaskWorker

logger = structlog.get_logger(__name__)

shutdown_event = asyncio.Event()

worker: TaskWorker | None = None
knowledge_service: KnowledgeService | NoopKnowledgeService | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global worker, knowledge_service
    settings = get_settings()

    if settings.knowledge_services_enabled:
        knowledge_service = KnowledgeService(
            llamaindex_url=settings.llamaindex_url,
            gkg_url=settings.knowledge_graph_url,
            enabled=True,
            timeout=settings.knowledge_timeout_seconds,
            retry_count=settings.knowledge_retry_count,
        )
        status = await knowledge_service.health_check()
        logger.info(
            "knowledge_services_initialized",
            llamaindex_available=status.llamaindex_available,
            gkg_available=status.gkg_available,
        )
    else:
        knowledge_service = NoopKnowledgeService()
        logger.info("knowledge_services_disabled")

    worker = TaskWorker(settings, knowledge_service)

    worker_task = asyncio.create_task(worker.start())

    def handle_shutdown(sig: signal.Signals) -> None:
        logger.info("shutdown_signal_received", signal=sig.name)
        shutdown_event.set()

    loop = asyncio.get_event_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda s=sig: handle_shutdown(s))

    logger.info("agent_engine_started", port=settings.port, cli_provider=settings.cli_provider)
    yield

    await worker.stop()
    worker_task.cancel()
    with suppress(asyncio.CancelledError):
        await worker_task
    logger.info("agent_engine_shutdown")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Agent Engine",
        version="1.0.0",
        lifespan=lifespan,
    )

    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "agent-engine"}

    @app.get("/health/auth")
    async def auth_health_check():
        import json as _json
        from datetime import UTC, datetime
        from pathlib import Path

        settings = get_settings()
        provider = settings.cli_provider
        result: dict[str, str | bool] = {
            "provider": provider,
            "authenticated": False,
        }

        if provider == "claude":
            creds_path = Path.home() / ".claude" / ".credentials.json"
            if not creds_path.exists():
                result["message"] = "No credentials file found"
                return result
            try:
                creds_data = _json.loads(creds_path.read_text())
                oauth = creds_data.get("claudeAiOauth", creds_data)
                expires_at = oauth.get("expiresAt") or oauth.get("expires_at", 0)
                now_ms = int(datetime.now(UTC).timestamp() * 1000)
                if now_ms >= expires_at:
                    result["message"] = "OAuth token expired"
                    return result
                result["authenticated"] = True
                result["message"] = "Token valid"
            except Exception as e:
                result["message"] = f"Credentials read error: {e}"
                return result
        elif provider == "cursor":
            import os

            if os.environ.get("CURSOR_API_KEY"):
                result["authenticated"] = True
                result["message"] = "API key configured"
            else:
                result["message"] = "No CURSOR_API_KEY set"
        return result

    @app.get("/health/detailed")
    async def detailed_health_check():
        settings = get_settings()
        result = {
            "status": "healthy",
            "service": "agent-engine",
            "components": {
                "worker": worker._running if worker else False,
                "redis": False,
            },
            "knowledge_services": {
                "enabled": settings.knowledge_services_enabled,
                "available": False,
                "llamaindex": False,
                "gkg": False,
            },
        }

        try:
            redis_client = redis.from_url(settings.redis_url)
            await redis_client.ping()
            result["components"]["redis"] = True
            await redis_client.aclose()
        except Exception:
            result["status"] = "degraded"

        if knowledge_service:
            ks_status = await knowledge_service.health_check()
            result["knowledge_services"]["available"] = knowledge_service.is_available
            result["knowledge_services"]["llamaindex"] = ks_status.llamaindex_available
            result["knowledge_services"]["gkg"] = ks_status.gkg_available

        return result

    @app.get("/status")
    async def get_status():
        settings = get_settings()
        return {
            "service": "agent-engine",
            "cli_provider": settings.cli_provider,
            "max_concurrent_tasks": settings.max_concurrent_tasks,
            "worker_running": worker._running if worker else False,
            "knowledge_services_enabled": settings.knowledge_services_enabled,
            "knowledge_available": (knowledge_service.is_available if knowledge_service else False),
        }

    @app.post("/knowledge/toggle")
    async def toggle_knowledge_services(enabled: bool):
        if knowledge_service is None:
            return JSONResponse(
                status_code=400,
                content={"error": "Knowledge service not initialized"},
            )

        if enabled:
            knowledge_service.enable()
        else:
            knowledge_service.disable()

        return {
            "knowledge_services_enabled": enabled,
            "message": f"Knowledge services {'enabled' if enabled else 'disabled'}",
        }

    @app.post("/tasks")
    async def create_task(task: dict[str, Any]):
        import json
        import uuid

        settings = get_settings()
        redis_client = redis.from_url(settings.redis_url)

        task_id = str(uuid.uuid4())
        task["task_id"] = task_id

        await redis_client.lpush("agent:tasks", json.dumps(task))
        await redis_client.aclose()

        return JSONResponse(
            status_code=202,
            content={"task_id": task_id, "status": "queued"},
        )

    @app.get("/tasks/{task_id}")
    async def get_task(task_id: str):
        import json

        settings = get_settings()
        redis_client = redis.from_url(settings.redis_url)

        data = await redis_client.hget(f"task:{task_id}", "data")
        await redis_client.aclose()

        if data:
            return json.loads(data)
        return JSONResponse(status_code=404, content={"error": "Task not found"})

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
