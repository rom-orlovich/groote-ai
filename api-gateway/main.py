from contextlib import asynccontextmanager

import structlog
import uvicorn
from config import get_settings
from fastapi import FastAPI
from routes import webhooks_router
from services.event_publisher import EventPublisher, create_event_publisher
from webhooks.github.validator import GitHubAuthMiddleware
from webhooks.jira.validator import JiraAuthMiddleware
from webhooks.slack.validator import SlackAuthMiddleware

logger = structlog.get_logger(__name__)

event_publisher: EventPublisher | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global event_publisher
    settings = get_settings()
    event_publisher = create_event_publisher(settings.redis_url)
    app.state.event_publisher = event_publisher
    logger.info("api_gateway_starting", port=settings.port)
    yield
    if event_publisher:
        await event_publisher.close()
    logger.info("api_gateway_shutting_down")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Agent API Gateway",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(SlackAuthMiddleware)
    app.add_middleware(JiraAuthMiddleware)
    app.add_middleware(GitHubAuthMiddleware)

    app.include_router(webhooks_router)

    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "api-gateway"}

    @app.get("/")
    async def root():
        return {
            "service": "agent-api-gateway",
            "version": "1.0.0",
            "endpoints": {
                "github": "/webhooks/github",
                "jira": "/webhooks/jira",
                "slack": "/webhooks/slack",
            },
        }

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
