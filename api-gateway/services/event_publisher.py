import json
import uuid
from datetime import UTC, datetime

import redis.asyncio as redis
import structlog

logger = structlog.get_logger()


class EventPublisher:
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self._client: redis.Redis | None = None
        self.stream_name = "task_events"

    @staticmethod
    def generate_webhook_event_id() -> str:
        return str(uuid.uuid4())

    async def _get_client(self) -> redis.Redis:
        if self._client is None:
            self._client = redis.from_url(self.redis_url, decode_responses=True)
        return self._client

    async def close(self) -> None:
        if self._client:
            await self._client.close()
            self._client = None

    async def _publish(self, event_type: str, webhook_event_id: str, data: dict) -> None:
        client = await self._get_client()
        await client.xadd(
            self.stream_name,
            {
                "type": event_type,
                "webhook_event_id": webhook_event_id,
                "timestamp": datetime.now(UTC).isoformat(),
                "data": json.dumps(data),
            },
        )

    async def publish_webhook_received(
        self, webhook_event_id: str, source: str, event_type: str, payload_size: int
    ) -> None:
        await self._publish(
            "webhook:received",
            webhook_event_id,
            {"source": source, "event_type": event_type, "payload_size": payload_size},
        )
        logger.info("webhook_received", webhook_event_id=webhook_event_id, source=source)

    async def publish_webhook_validated(
        self, webhook_event_id: str, source: str, signature_valid: bool
    ) -> None:
        await self._publish(
            "webhook:validated",
            webhook_event_id,
            {"source": source, "signature_valid": signature_valid},
        )
        logger.info(
            "webhook_validated", webhook_event_id=webhook_event_id, signature_valid=signature_valid
        )

    async def publish_webhook_matched(
        self, webhook_event_id: str, source: str, event_type: str, matched_handler: str
    ) -> None:
        await self._publish(
            "webhook:matched",
            webhook_event_id,
            {"source": source, "event_type": event_type, "matched_handler": matched_handler},
        )
        logger.info(
            "webhook_matched", webhook_event_id=webhook_event_id, matched_handler=matched_handler
        )

    async def publish_webhook_task_created(
        self, webhook_event_id: str, task_id: str, source: str, event_type: str, input_message: str
    ) -> None:
        await self._publish(
            "webhook:task_created",
            webhook_event_id,
            {
                "task_id": task_id,
                "source": source,
                "event_type": event_type,
                "input_message": input_message,
            },
        )
        logger.info("webhook_task_created", webhook_event_id=webhook_event_id, task_id=task_id)

    async def publish_response_immediate(
        self,
        webhook_event_id: str,
        task_id: str,
        source: str,
        response_type: str,
        target: str,
    ) -> None:
        await self._publish(
            "response:immediate",
            webhook_event_id,
            {
                "task_id": task_id,
                "source": source,
                "response_type": response_type,
                "target": target,
            },
        )
        logger.info(
            "response_immediate_published",
            webhook_event_id=webhook_event_id,
            source=source,
            response_type=response_type,
        )

    async def publish_notification_ops(
        self,
        webhook_event_id: str,
        task_id: str,
        source: str,
        notification_type: str,
        channel: str,
    ) -> None:
        await self._publish(
            "notification:ops",
            webhook_event_id,
            {
                "task_id": task_id,
                "source": source,
                "notification_type": notification_type,
                "channel": channel,
            },
        )
        logger.info(
            "notification_ops_published",
            webhook_event_id=webhook_event_id,
            notification_type=notification_type,
        )

    async def publish_webhook_payload(
        self, webhook_event_id: str, source: str, event_type: str, payload: dict
    ) -> None:
        await self._publish(
            "webhook:payload",
            webhook_event_id,
            {"source": source, "event_type": event_type, "payload": payload},
        )

    async def publish_webhook_skipped(
        self, webhook_event_id: str, source: str, event_type: str, reason: str
    ) -> None:
        await self._publish(
            "webhook:skipped",
            webhook_event_id,
            {"source": source, "event_type": event_type, "reason": reason},
        )


def create_event_publisher(redis_url: str) -> EventPublisher:
    return EventPublisher(redis_url)
