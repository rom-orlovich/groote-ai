from unittest.mock import AsyncMock, patch

import pytest
from core.user_settings.models import AgentScalingSettings, AIProviderSettings


@pytest.mark.asyncio
async def test_save_ai_provider_settings(async_client, db_session):
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
    token = "Bearer test-user-123"
    settings = AgentScalingSettings(agent_count=5)

    with patch(
        "api.user_settings.redis_client.publish", new_callable=AsyncMock
    ) as mock_publish:
        response = await async_client.post(
            "/api/user-settings/agent-scaling",
            json=settings.model_dump(),
            headers={"Authorization": token},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "scaling"
    assert data["agent_count"] == 5
    mock_publish.assert_called_once_with(
        "cli:scaling",
        {"provider": "claude", "agent_count": 5},
    )


@pytest.mark.asyncio
async def test_save_agent_scaling_out_of_range(async_client, db_session):
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
    response = await async_client.get("/api/user-settings/ai-provider")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_save_agent_scaling_uses_saved_provider(async_client, mock_db_session):
    token = "Bearer test-user-123"
    settings = AgentScalingSettings(agent_count=3)

    with patch(
        "api.user_settings.redis_client.publish", new_callable=AsyncMock
    ) as mock_publish, patch(
        "api.user_settings.get_user_setting", new_callable=AsyncMock
    ) as mock_get:
        mock_get.side_effect = lambda db, uid, cat, key: (
            "cursor" if cat == "ai_provider" and key == "provider" else None
        )
        response = await async_client.post(
            "/api/user-settings/agent-scaling",
            json=settings.model_dump(),
            headers={"Authorization": token},
        )

    assert response.status_code == 200
    mock_publish.assert_called_once_with(
        "cli:scaling",
        {"provider": "cursor", "agent_count": 3},
    )


@pytest.mark.asyncio
async def test_save_agent_scaling_falls_back_to_env_provider(
    async_client, mock_db_session
):
    token = "Bearer test-user-123"
    settings = AgentScalingSettings(agent_count=2)

    with patch(
        "api.user_settings.redis_client.publish", new_callable=AsyncMock
    ) as mock_publish, patch(
        "api.user_settings.get_user_setting", new_callable=AsyncMock, return_value=None
    ), patch.dict("os.environ", {"CLI_PROVIDER": "cursor"}):
        response = await async_client.post(
            "/api/user-settings/agent-scaling",
            json=settings.model_dump(),
            headers={"Authorization": token},
        )

    assert response.status_code == 200
    mock_publish.assert_called_once_with(
        "cli:scaling",
        {"provider": "cursor", "agent_count": 2},
    )


@pytest.mark.asyncio
async def test_delete_user_setting(async_client, db_session):
    token = "Bearer test-user-123"

    response = await async_client.delete(
        "/api/user-settings/user-settings/ai_provider/provider",
        headers={"Authorization": token},
    )

    assert response.status_code in [200, 404]
