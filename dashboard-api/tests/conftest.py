"""Dashboard API test fixtures."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from .factories import ConversationFactory, SessionFactory, TaskFactory, WebhookFactory


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
    """Mock database session."""
    session = MagicMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.add = MagicMock()
    return session


@pytest.fixture
async def db_session(mock_db_session):
    """Database session fixture."""
    return mock_db_session


@pytest.fixture
async def async_client(mock_db_session):
    """Async HTTP client for testing."""
    from main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
