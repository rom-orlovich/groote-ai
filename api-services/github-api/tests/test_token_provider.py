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
        static_token="ghp_static_fallback",
        use_oauth=True,
    )


@pytest.fixture
def provider_no_oauth() -> TokenProvider:
    return TokenProvider(
        oauth_service_url="http://oauth-service:8010",
        internal_service_key="test-key",
        static_token="ghp_static_fallback",
        use_oauth=False,
    )


@pytest.fixture
def provider_no_static() -> TokenProvider:
    return TokenProvider(
        oauth_service_url="http://oauth-service:8010",
        internal_service_key="test-key",
        static_token="",
        use_oauth=True,
    )


@pytest.mark.asyncio
async def test_oauth_token_returned(provider: TokenProvider) -> None:
    mock_response = httpx.Response(
        200,
        json={"token": "gho_oauth_token", "available": True, "platform": "github"},
        request=httpx.Request("GET", "http://test"),
    )
    with patch("token_provider.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_cls.return_value = mock_client

        token = await provider.get_token()
        assert token == "gho_oauth_token"


@pytest.mark.asyncio
async def test_fallback_to_static_when_oauth_unreachable(provider: TokenProvider) -> None:
    with patch("token_provider.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.get.side_effect = httpx.ConnectError("Connection refused")
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_cls.return_value = mock_client

        token = await provider.get_token()
        assert token == "ghp_static_fallback"


@pytest.mark.asyncio
async def test_error_when_neither_available(provider_no_static: TokenProvider) -> None:
    with patch("token_provider.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.get.side_effect = httpx.ConnectError("Connection refused")
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_cls.return_value = mock_client

        with pytest.raises(RuntimeError, match="No GitHub token available"):
            await provider_no_static.get_token()


@pytest.mark.asyncio
async def test_cache_hit_within_ttl(provider: TokenProvider) -> None:
    mock_response = httpx.Response(
        200,
        json={"token": "gho_cached", "available": True, "platform": "github"},
        request=httpx.Request("GET", "http://test"),
    )
    with patch("token_provider.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_cls.return_value = mock_client

        await provider.get_token()
        token = await provider.get_token()

        assert token == "gho_cached"
        assert mock_client.get.call_count == 1


@pytest.mark.asyncio
async def test_cache_expired_triggers_new_call(provider: TokenProvider) -> None:
    mock_response = httpx.Response(
        200,
        json={"token": "gho_fresh", "available": True, "platform": "github"},
        request=httpx.Request("GET", "http://test"),
    )
    with patch("token_provider.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_cls.return_value = mock_client

        await provider.get_token()
        provider._cache["github"] = (
            "gho_stale",
            time.monotonic() - CACHE_TTL_SECONDS - 1,
        )
        token = await provider.get_token()

        assert token == "gho_fresh"
        assert mock_client.get.call_count == 2


@pytest.mark.asyncio
async def test_oauth_disabled_uses_static(provider_no_oauth: TokenProvider) -> None:
    token = await provider_no_oauth.get_token()
    assert token == "ghp_static_fallback"
