import hashlib
import hmac
from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture
def mock_gateway_settings():
    settings = MagicMock()
    settings.redis_url = "redis://localhost:6379/0"
    settings.github_webhook_secret = "test-github-secret"
    settings.jira_webhook_secret = "test-jira-secret"
    settings.slack_signing_secret = "test-slack-secret"
    settings.port = 8000
    return settings


@pytest.fixture
def github_signature_generator():
    def _generate(payload: bytes, secret: str) -> str:
        signature = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        return f"sha256={signature}"

    return _generate


@pytest.fixture
def mock_redis_client():
    redis = MagicMock()
    redis.lpush = AsyncMock(return_value=1)
    redis.aclose = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.setex = AsyncMock()
    return redis
