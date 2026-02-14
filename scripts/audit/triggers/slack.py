import hashlib
import hmac
import json
import logging
import time
import uuid
from datetime import UTC, datetime

from ..config import AuditConfig
from ..core.client import AuditClient
from .base import TriggerResult

logger = logging.getLogger(__name__)


class SlackTrigger:
    def __init__(self, client: AuditClient, config: AuditConfig) -> None:
        self._client = client
        self._config = config

    async def send_message(
        self,
        text: str,
        thread_ts: str | None = None,
    ) -> TriggerResult:
        event_ts = f"{int(time.time())}.{uuid.uuid4().hex[:6]}"
        channel = self._config.slack_channel

        event_payload = {
            "token": "audit-token",
            "team_id": "T_AUDIT",
            "event_id": f"Ev{uuid.uuid4().hex[:10].upper()}",
            "event": {
                "type": "message",
                "channel": channel,
                "user": "U_AUDIT_USER",
                "text": text,
                "ts": event_ts,
            },
            "type": "event_callback",
        }
        if thread_ts:
            event_payload["event"]["thread_ts"] = thread_ts

        body = json.dumps(event_payload).encode()
        headers = self._build_slack_headers(body)

        response = await self._client.http.post(
            f"{self._config.api_gateway_url}/webhooks/slack",
            content=body,
            headers=headers,
        )
        response.raise_for_status()
        data = response.json()

        flow_id = f"slack:{channel}:{event_ts}"

        logger.info(
            "slack_webhook_simulated",
            extra={
                "channel": channel,
                "ts": event_ts,
                "flow_id": flow_id,
                "response_status": response.status_code,
            },
        )

        return TriggerResult(
            platform="slack",
            artifact_type="message",
            artifact_id=event_ts,
            trigger_time=datetime.now(UTC),
            expected_flow_id=flow_id,
            raw_response=data,
        )

    def _build_slack_headers(self, body: bytes) -> dict[str, str]:
        timestamp = str(int(time.time()))
        headers: dict[str, str] = {"Content-Type": "application/json"}

        signing_secret = self._config.slack_signing_secret
        if signing_secret:
            sig_basestring = f"v0:{timestamp}:{body.decode()}"
            signature = (
                "v0="
                + hmac.new(
                    signing_secret.encode(),
                    sig_basestring.encode(),
                    hashlib.sha256,
                ).hexdigest()
            )
            headers["X-Slack-Signature"] = signature
            headers["X-Slack-Request-Timestamp"] = timestamp

        return headers
