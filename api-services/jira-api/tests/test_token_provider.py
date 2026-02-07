import time
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from token_provider import CACHE_TTL_SECONDS, TokenProvider


@pytest.fixture
def provider() -> TokenProvider:
    return TokenProvider(
        oauth_service_url="http://oauth-service:8010",
        internal_service_key="test-key",
        static_url="https://company.atlassian.net",
        static_email="user@company.com",
        static_token="static-api-token",
        use_oauth=True,
    )


@pytest.fixture
def provider_no_static() -> TokenProvider:
    return TokenProvider(
        oauth_service_url="http://oauth-service:8010",
        internal_service_key="test-key",
        static_url="",
        static_email="",
        static_token="",
        use_oauth=True,
    )


@pytest.mark.asyncio
async def test_oauth_token_returned_with_bearer(provider: TokenProvider) -> None:
    mock_response = httpx.Response(
        200,
        json={
            "token": "oauth-jira-token",
            "available": True,
            "platform": "jira",
            "org_id": "cloud-123",
            "metadata": {"cloud_id": "cloud-123"},
        },
        request=httpx.Request("GET", "http://test"),
    )
    with patch("token_provider.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_cls.return_value = mock_client

        result = await provider.get_token()
        assert result.token == "oauth-jira-token"
        assert result.auth_mode == "bearer"
        assert result.base_url == "https://api.atlassian.com/ex/jira/cloud-123"


@pytest.mark.asyncio
async def test_fallback_to_static_basic_auth(provider: TokenProvider) -> None:
    with patch("token_provider.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.get.side_effect = httpx.ConnectError("Connection refused")
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_cls.return_value = mock_client

        result = await provider.get_token()
        assert result.token == "static-api-token"
        assert result.auth_mode == "basic"
        assert result.base_url == "https://company.atlassian.net"


@pytest.mark.asyncio
async def test_error_when_neither_available(provider_no_static: TokenProvider) -> None:
    with patch("token_provider.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.get.side_effect = httpx.ConnectError("Connection refused")
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_cls.return_value = mock_client

        with pytest.raises(RuntimeError, match="No Jira token available"):
            await provider_no_static.get_token()


@pytest.mark.asyncio
async def test_cache_hit_within_ttl(provider: TokenProvider) -> None:
    mock_response = httpx.Response(
        200,
        json={
            "token": "oauth-cached",
            "available": True,
            "platform": "jira",
            "metadata": {"cloud_id": "cloud-123"},
        },
        request=httpx.Request("GET", "http://test"),
    )
    with patch("token_provider.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_cls.return_value = mock_client

        await provider.get_token()
        result = await provider.get_token()

        assert result.token == "oauth-cached"
        assert mock_client.get.call_count == 1


@pytest.mark.asyncio
async def test_cache_expired_triggers_new_call(provider: TokenProvider) -> None:
    mock_response = httpx.Response(
        200,
        json={
            "token": "oauth-fresh",
            "available": True,
            "platform": "jira",
            "metadata": {"cloud_id": "cloud-456"},
        },
        request=httpx.Request("GET", "http://test"),
    )
    with patch("token_provider.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_cls.return_value = mock_client

        await provider.get_token()
        from token_provider import JiraTokenResult
        provider._cache["jira"] = (
            JiraTokenResult(token="stale", auth_mode="bearer", base_url="http://old"),
            time.monotonic() - CACHE_TTL_SECONDS - 1,
        )
        result = await provider.get_token()

        assert result.token == "oauth-fresh"
        assert mock_client.get.call_count == 2
