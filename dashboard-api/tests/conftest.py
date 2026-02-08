"""Dashboard API test fixtures."""

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from .factories import ConversationFactory, SessionFactory, TaskFactory, WebhookFactory


def _make_mock_result(scalar_value=None, scalars_list=None):
    result = MagicMock()
    result.scalar_one_or_none.return_value = scalar_value
    scalars_mock = MagicMock()
    scalars_mock.all.return_value = scalars_list or []
    result.scalars.return_value = scalars_mock
    return result


@pytest.fixture
def task_factory():
    """Task factory fixture."""
    TaskFactory.reset()
    return TaskFactory


@pytest.fixture
def session_factory():
    """Session factory fixture."""
    SessionFactory.reset()
    return SessionFactory


@pytest.fixture
def conversation_factory():
    """Conversation factory fixture."""
    ConversationFactory.reset()
    return ConversationFactory


@pytest.fixture
def webhook_factory():
    """Webhook factory fixture."""
    WebhookFactory.reset()
    return WebhookFactory


@pytest.fixture
def mock_db_session():
    """Mock database session with SQLAlchemy-compatible interface."""
    session = MagicMock()
    session.execute = AsyncMock(return_value=_make_mock_result())
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.refresh = AsyncMock()
    session.delete = AsyncMock()
    session.add = MagicMock()
    return session


@pytest.fixture
async def db_session(mock_db_session):
    """Database session fixture."""
    return mock_db_session


@asynccontextmanager
async def _test_lifespan(app):
    from core.websocket_hub import WebSocketHub

    app.state.ws_hub = WebSocketHub()
    yield


@pytest.fixture
async def async_client(mock_db_session):
    """Async HTTP client for testing with mocked infrastructure."""
    from core.database import get_session
    from main import app

    async def _mock_get_session():
        yield mock_db_session

    original_lifespan = app.router.lifespan_context
    app.router.lifespan_context = _test_lifespan
    app.dependency_overrides[get_session] = _mock_get_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()
    app.router.lifespan_context = original_lifespan
