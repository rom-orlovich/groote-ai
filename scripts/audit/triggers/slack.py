import logging
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
        payload: dict = {
            "channel": self._config.slack_channel,
            "text": text,
        }
        if thread_ts:
            payload["thread_ts"] = thread_ts

        response = await self._client.post_slack_api(
            "/api/v1/messages", json=payload
        )
        data = response.json()

        response_ts = data.get("ts", "")
        channel = self._config.slack_channel
        flow_id = f"slack:{channel}:{response_ts}"

        logger.info(
            "slack_message_sent",
            extra={"channel": channel, "ts": response_ts, "flow_id": flow_id},
        )

        return TriggerResult(
            platform="slack",
            artifact_type="message",
            artifact_id=response_ts,
            trigger_time=datetime.now(UTC),
            expected_flow_id=flow_id,
            raw_response=data,
        )
