from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from services.webhook_service import WebhookRegistrationResult, WebhookRegistrationService


@pytest.fixture
def mock_settings():
    settings = MagicMock()
    settings.frontend_url = "https://example.com"
    settings.github_app_id = "123456"
    settings.github_private_key = (
        "-----BEGIN RSA PRIVATE KEY-----\ntest\n-----END RSA PRIVATE KEY-----"
    )
    settings.github_webhook_secret = "webhook-secret"
    return settings


@pytest.fixture
def service(mock_settings):
    return WebhookRegistrationService(mock_settings)


class TestWebhookRegistrationResult:
    def test_result_dataclass_defaults(self):
        result = WebhookRegistrationResult(success=True)

        assert result.success is True
        assert result.webhook_url is None
        assert result.external_id is None
        assert result.error is None

    def test_result_with_all_fields(self):
        result = WebhookRegistrationResult(
            success=True,
            webhook_url="https://example.com/webhooks/jira",
            external_id="123",
            error=None,
        )

        assert result.webhook_url == "https://example.com/webhooks/jira"
        assert result.external_id == "123"


class TestJiraWebhookRegistration:
    @pytest.mark.asyncio
    async def test_register_jira_webhook_success(self, service):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "webhookRegistrationResult": [
                {"createdWebhookId": 10001},
                {"createdWebhookId": 10002},
            ]
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await service.register_jira_webhook("token-123", "cloud-abc")

        assert result.success is True
        assert result.webhook_url == "https://example.com/webhooks/jira"
        assert result.external_id == "10001,10002"

    @pytest.mark.asyncio
    async def test_register_jira_webhook_url_points_to_gateway(self, service):
        mock_response = MagicMock()
        mock_response.json.return_value = {"webhookRegistrationResult": []}
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = mock_client.return_value.__aenter__.return_value
            mock_instance.post = AsyncMock(return_value=mock_response)

            await service.register_jira_webhook("token", "cloud-id")

            call_kwargs = mock_instance.post.call_args
            payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
            webhook_url = payload["webhooks"][0]["url"]

        assert webhook_url == "https://example.com/webhooks/jira"

    @pytest.mark.asyncio
    async def test_register_jira_webhook_events_include_required(self, service):
        mock_response = MagicMock()
        mock_response.json.return_value = {"webhookRegistrationResult": []}
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = mock_client.return_value.__aenter__.return_value
            mock_instance.post = AsyncMock(return_value=mock_response)

            await service.register_jira_webhook("token", "cloud-id")

            call_kwargs = mock_instance.post.call_args
            payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
            events = payload["webhooks"][0]["events"]

        assert "jira:issue_created" in events
        assert "jira:issue_updated" in events
        assert "comment_created" in events

    @pytest.mark.asyncio
    async def test_register_jira_webhook_api_failure_returns_error(self, service):
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=httpx.HTTPStatusError(
                    "403 Forbidden",
                    request=MagicMock(),
                    response=MagicMock(status_code=403),
                )
            )

            result = await service.register_jira_webhook("bad-token", "cloud-id")

        assert result.success is False
        assert result.error is not None
        assert "403" in result.error

    @pytest.mark.asyncio
    async def test_register_jira_webhook_extracts_webhook_ids(self, service):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "webhookRegistrationResult": [
                {"createdWebhookId": 42},
                {"createdWebhookId": 99},
                {"createdWebhookId": 7},
            ]
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await service.register_jira_webhook("token", "cloud-id")

        assert result.external_id == "42,99,7"

    @pytest.mark.asyncio
    async def test_register_jira_webhook_calls_correct_url(self, service):
        mock_response = MagicMock()
        mock_response.json.return_value = {"webhookRegistrationResult": []}
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = mock_client.return_value.__aenter__.return_value
            mock_instance.post = AsyncMock(return_value=mock_response)

            await service.register_jira_webhook("token", "my-cloud-123")

            call_args = mock_instance.post.call_args
            url = call_args.args[0] if call_args.args else call_args[0][0]

        assert url == "https://api.atlassian.com/ex/jira/my-cloud-123/rest/api/3/webhook"


class TestGitHubWebhookConfiguration:
    @pytest.mark.asyncio
    async def test_configure_github_webhook_success(self, service):
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.patch = AsyncMock(
                return_value=mock_response
            )
            with patch.object(service, "_generate_github_jwt", return_value="fake-jwt"):
                result = await service.configure_github_app_webhook()

        assert result.success is True
        assert result.webhook_url == "https://example.com/webhooks/github"

    @pytest.mark.asyncio
    async def test_configure_github_webhook_failure(self, service):
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.patch = AsyncMock(
                side_effect=httpx.HTTPStatusError(
                    "401 Unauthorized",
                    request=MagicMock(),
                    response=MagicMock(status_code=401),
                )
            )
            with patch.object(service, "_generate_github_jwt", return_value="fake-jwt"):
                result = await service.configure_github_app_webhook()

        assert result.success is False
        assert result.error is not None
