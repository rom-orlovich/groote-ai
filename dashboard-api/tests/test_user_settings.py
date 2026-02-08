"""Tests for user settings endpoints."""

import pytest
from core.user_settings.models import AgentScalingSettings, AIProviderSettings


@pytest.mark.asyncio
async def test_save_ai_provider_settings(async_client, db_session):
    """User can save AI provider configuration."""
    token = "Bearer test-user-123"
    settings = AIProviderSettings(
        provider="claude",
        api_key="sk-ant-xxx",
        model_complex="opus",
        model_execution="sonnet",
    )

    response = await async_client.post(
        "/api/user-settings/ai-provider",
        json=settings.model_dump(),
        headers={"Authorization": token},
    )

    assert response.status_code == 200
    assert response.json()["provider"] == "claude"


@pytest.mark.asyncio
async def test_get_ai_provider_settings(async_client, db_session):
    """User can retrieve AI provider configuration."""
    token = "Bearer test-user-123"

    response = await async_client.get(
        "/api/user-settings/ai-provider",
        headers={"Authorization": token},
    )

    assert response.status_code == 200
    data = response.json()
    assert "provider" in data
    assert "settings" in data


@pytest.mark.asyncio
async def test_test_ai_provider_anthropic(async_client):
    """Test connection for Anthropic API key."""
    settings = AIProviderSettings(
        provider="claude",
        api_key="sk-ant-invalid",
    )

    response = await async_client.post(
        "/api/user-settings/ai-provider/test",
        json=settings.model_dump(),
        headers={"Authorization": "Bearer test-user-123"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "valid" in data
    assert "message" in data


@pytest.mark.asyncio
async def test_save_agent_scaling(async_client, db_session):
    """User can save agent scaling configuration."""
    token = "Bearer test-user-123"
    settings = AgentScalingSettings(agent_count=5)

    response = await async_client.post(
        "/api/user-settings/agent-scaling",
        json=settings.model_dump(),
        headers={"Authorization": token},
    )

    assert response.status_code == 200
    assert response.json()["agent_count"] == 5


@pytest.mark.asyncio
async def test_save_agent_scaling_out_of_range(async_client, db_session):
    """Agent count must be within valid range."""
    token = "Bearer test-user-123"
    settings = AgentScalingSettings(agent_count=100)

    response = await async_client.post(
        "/api/user-settings/agent-scaling",
        json=settings.model_dump(),
        headers={"Authorization": token},
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_agent_scaling(async_client, db_session):
    """User can retrieve agent scaling configuration."""
    token = "Bearer test-user-123"

    response = await async_client.get(
        "/api/user-settings/agent-scaling",
        headers={"Authorization": token},
    )

    assert response.status_code == 200
    data = response.json()
    assert "agent_count" in data
    assert "min_agents" in data
    assert "max_agents" in data


@pytest.mark.asyncio
async def test_missing_authorization_header(async_client):
    """Requests without auth header are rejected."""
    response = await async_client.get("/api/user-settings/ai-provider")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_delete_user_setting(async_client, db_session):
    """User can delete a setting."""
    token = "Bearer test-user-123"

    response = await async_client.delete(
        "/api/user-settings/user-settings/ai_provider/provider",
        headers={"Authorization": token},
    )

    assert response.status_code in [200, 404]
