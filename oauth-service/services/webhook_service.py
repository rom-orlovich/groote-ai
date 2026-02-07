from dataclasses import dataclass
from datetime import UTC, datetime

import httpx
import jwt
import structlog
from config.settings import Settings

logger = structlog.get_logger(__name__)


@dataclass
class WebhookRegistrationResult:
    success: bool
    webhook_url: str | None = None
    external_id: str | None = None
    error: str | None = None


class WebhookRegistrationService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.base_webhook_url = settings.frontend_url

    async def configure_github_app_webhook(self) -> WebhookRegistrationResult:
        webhook_url = f"{self.base_webhook_url}/webhooks/github"
        try:
            jwt_token = self._generate_github_jwt()
            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    "https://api.github.com/app/hook/config",
                    headers={
                        "Authorization": f"Bearer {jwt_token}",
                        "Accept": "application/vnd.github+json",
                    },
                    json={
                        "url": webhook_url,
                        "content_type": "json",
                        "insecure_ssl": "0",
                        "secret": self.settings.github_webhook_secret or None,
                    },
                )
                response.raise_for_status()

            logger.info("github_webhook_configured", webhook_url=webhook_url)
            return WebhookRegistrationResult(
                success=True,
                webhook_url=webhook_url,
            )
        except Exception as e:
            logger.error("github_webhook_configuration_failed", error=str(e))
            return WebhookRegistrationResult(success=False, error=str(e))

    async def register_jira_webhook(
        self,
        access_token: str,
        cloud_id: str,
    ) -> WebhookRegistrationResult:
        webhook_url = f"{self.base_webhook_url}/webhooks/jira"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3/webhook",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "webhooks": [
                            {
                                "jqlFilter": "project is not EMPTY",
                                "events": [
                                    "jira:issue_created",
                                    "jira:issue_updated",
                                    "jira:issue_deleted",
                                    "comment_created",
                                    "comment_updated",
                                ],
                                "url": webhook_url,
                            }
                        ],
                        "url": webhook_url,
                    },
                )
                response.raise_for_status()
                data = response.json()

            webhook_ids = [
                str(wh.get("createdWebhookId", ""))
                for wh in data.get("webhookRegistrationResult", [])
                if wh.get("createdWebhookId")
            ]
            external_id = ",".join(webhook_ids) if webhook_ids else None

            logger.info(
                "jira_webhook_registered",
                cloud_id=cloud_id,
                webhook_url=webhook_url,
                webhook_ids=webhook_ids,
            )
            return WebhookRegistrationResult(
                success=True,
                webhook_url=webhook_url,
                external_id=external_id,
            )
        except Exception as e:
            logger.error(
                "jira_webhook_registration_failed",
                cloud_id=cloud_id,
                error=str(e),
            )
            return WebhookRegistrationResult(success=False, error=str(e))

    def _generate_github_jwt(self) -> str:
        now = int(datetime.now(UTC).timestamp())
        payload = {
            "iat": now - 60,
            "exp": now + (10 * 60),
            "iss": self.settings.github_app_id,
        }
        private_key = self.settings.github_private_key.replace("\\n", "\n")
        return jwt.encode(payload, private_key, algorithm="RS256")
