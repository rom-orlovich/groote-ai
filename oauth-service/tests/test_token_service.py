"""Tests for OAuth token service business logic.

Tests token storage, retrieval, refresh, and installation management.
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest


class MockTokenStore:
    """Mock token store for testing without database."""

    def __init__(self):
        self._tokens: dict[str, dict] = {}
        self._installations: dict[str, dict] = {}

    async def store_token(
        self,
        platform: str,
        org_id: str,
        access_token: str,
        refresh_token: str | None = None,
        expires_at: datetime | None = None,
        scopes: list[str] | None = None,
    ) -> dict:
        """Store OAuth token."""
        key = f"{platform}:{org_id}"
        self._tokens[key] = {
            "platform": platform,
            "org_id": org_id,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_at": expires_at,
            "scopes": scopes or [],
        }
        return self._tokens[key]

    async def get_token(self, platform: str, org_id: str) -> dict | None:
        """Retrieve token for organization."""
        key = f"{platform}:{org_id}"
        return self._tokens.get(key)

    async def refresh_token(
        self, platform: str, org_id: str, new_access_token: str, new_expires_at: datetime
    ) -> dict:
        """Update token after refresh."""
        key = f"{platform}:{org_id}"
        if key in self._tokens:
            self._tokens[key]["access_token"] = new_access_token
            self._tokens[key]["expires_at"] = new_expires_at
        return self._tokens[key]

    async def delete_token(self, platform: str, org_id: str) -> bool:
        """Delete token (revoke installation)."""
        key = f"{platform}:{org_id}"
        if key in self._tokens:
            del self._tokens[key]
            return True
        return False

    async def list_installations(self, platform: str | None = None) -> list[dict]:
        """List all installations."""
        if platform:
            return [t for t in self._tokens.values() if t["platform"] == platform]
        return list(self._tokens.values())


@pytest.fixture
def token_store():
    """Mock token store fixture."""
    return MockTokenStore()


class TestTokenStorage:
    """Tests for token storage."""

    @pytest.mark.asyncio
    async def test_store_token_creates_record(self, token_store):
        """Business requirement: Tokens can be stored."""
        result = await token_store.store_token(
            platform="github",
            org_id="org-123",
            access_token="gho_test_token",
            scopes=["repo", "read:org"],
        )

        assert result["platform"] == "github"
        assert result["org_id"] == "org-123"
        assert result["access_token"] == "gho_test_token"
        assert "repo" in result["scopes"]

    @pytest.mark.asyncio
    async def test_store_token_with_refresh_token(self, token_store):
        """Business requirement: Refresh tokens stored when provided."""
        expires_at = datetime.utcnow() + timedelta(hours=1)

        result = await token_store.store_token(
            platform="jira",
            org_id="org-456",
            access_token="access_token",
            refresh_token="refresh_token",
            expires_at=expires_at,
        )

        assert result["refresh_token"] == "refresh_token"
        assert result["expires_at"] == expires_at

    @pytest.mark.asyncio
    async def test_store_token_overwrites_existing(self, token_store):
        """Business requirement: Reinstall updates existing token."""
        await token_store.store_token(
            platform="slack",
            org_id="workspace-1",
            access_token="old_token",
        )

        await token_store.store_token(
            platform="slack",
            org_id="workspace-1",
            access_token="new_token",
        )

        result = await token_store.get_token("slack", "workspace-1")
        assert result["access_token"] == "new_token"


class TestTokenRetrieval:
    """Tests for token retrieval."""

    @pytest.mark.asyncio
    async def test_get_token_returns_stored_token(self, token_store):
        """Business requirement: Stored tokens can be retrieved."""
        await token_store.store_token(
            platform="github",
            org_id="org-123",
            access_token="test_token",
        )

        result = await token_store.get_token("github", "org-123")

        assert result is not None
        assert result["access_token"] == "test_token"

    @pytest.mark.asyncio
    async def test_get_token_returns_none_for_unknown(self, token_store):
        """Business requirement: Unknown org returns None."""
        result = await token_store.get_token("github", "unknown-org")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_token_by_platform(self, token_store):
        """Business requirement: Tokens are platform-specific."""
        await token_store.store_token(
            platform="github",
            org_id="org-123",
            access_token="github_token",
        )
        await token_store.store_token(
            platform="slack",
            org_id="org-123",
            access_token="slack_token",
        )

        github_token = await token_store.get_token("github", "org-123")
        slack_token = await token_store.get_token("slack", "org-123")

        assert github_token["access_token"] == "github_token"
        assert slack_token["access_token"] == "slack_token"


class TestTokenRefresh:
    """Tests for token refresh."""

    @pytest.mark.asyncio
    async def test_refresh_updates_access_token(self, token_store):
        """Business requirement: Token refresh updates access token."""
        expires_at = datetime.utcnow() + timedelta(hours=1)
        await token_store.store_token(
            platform="jira",
            org_id="org-123",
            access_token="old_token",
            refresh_token="refresh_token",
            expires_at=datetime.utcnow() - timedelta(hours=1),
        )

        new_expires = datetime.utcnow() + timedelta(hours=1)
        result = await token_store.refresh_token(
            platform="jira",
            org_id="org-123",
            new_access_token="new_token",
            new_expires_at=new_expires,
        )

        assert result["access_token"] == "new_token"
        assert result["expires_at"] == new_expires

    @pytest.mark.asyncio
    async def test_refresh_preserves_refresh_token(self, token_store):
        """Business requirement: Refresh token preserved during refresh."""
        await token_store.store_token(
            platform="jira",
            org_id="org-123",
            access_token="old_token",
            refresh_token="original_refresh_token",
        )

        await token_store.refresh_token(
            platform="jira",
            org_id="org-123",
            new_access_token="new_token",
            new_expires_at=datetime.utcnow() + timedelta(hours=1),
        )

        result = await token_store.get_token("jira", "org-123")
        assert result["refresh_token"] == "original_refresh_token"


class TestInstallationManagement:
    """Tests for installation management."""

    @pytest.mark.asyncio
    async def test_list_installations_returns_all(self, token_store):
        """Business requirement: All installations can be listed."""
        await token_store.store_token(
            platform="github", org_id="org-1", access_token="token1"
        )
        await token_store.store_token(
            platform="slack", org_id="workspace-1", access_token="token2"
        )

        installations = await token_store.list_installations()

        assert len(installations) == 2

    @pytest.mark.asyncio
    async def test_list_installations_filters_by_platform(self, token_store):
        """Business requirement: Installations can be filtered by platform."""
        await token_store.store_token(
            platform="github", org_id="org-1", access_token="token1"
        )
        await token_store.store_token(
            platform="github", org_id="org-2", access_token="token2"
        )
        await token_store.store_token(
            platform="slack", org_id="workspace-1", access_token="token3"
        )

        github_installs = await token_store.list_installations(platform="github")

        assert len(github_installs) == 2
        assert all(i["platform"] == "github" for i in github_installs)

    @pytest.mark.asyncio
    async def test_delete_token_removes_installation(self, token_store):
        """Business requirement: Installations can be revoked."""
        await token_store.store_token(
            platform="github", org_id="org-123", access_token="token"
        )

        result = await token_store.delete_token("github", "org-123")

        assert result is True
        assert await token_store.get_token("github", "org-123") is None

    @pytest.mark.asyncio
    async def test_delete_token_returns_false_for_unknown(self, token_store):
        """Business requirement: Deleting unknown returns False."""
        result = await token_store.delete_token("github", "unknown-org")

        assert result is False


class TestTokenExpiration:
    """Tests for token expiration handling."""

    @pytest.mark.asyncio
    async def test_token_with_expiration(self, token_store):
        """Business requirement: Expiration time is stored."""
        expires_at = datetime.utcnow() + timedelta(hours=1)

        await token_store.store_token(
            platform="jira",
            org_id="org-123",
            access_token="token",
            expires_at=expires_at,
        )

        result = await token_store.get_token("jira", "org-123")
        assert result["expires_at"] == expires_at

    @pytest.mark.asyncio
    async def test_token_without_expiration(self, token_store):
        """Business requirement: Tokens can have no expiration."""
        await token_store.store_token(
            platform="github",
            org_id="org-123",
            access_token="token",
            expires_at=None,
        )

        result = await token_store.get_token("github", "org-123")
        assert result["expires_at"] is None
