from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from services.event_publisher import EventPublisher, create_event_publisher


@pytest.fixture
def mock_redis():
    client = MagicMock()
    client.xadd = AsyncMock()
    client.close = AsyncMock()
    return client


@pytest.fixture
def publisher(mock_redis):
    pub = EventPublisher("redis://localhost:6379/0")
    pub._client = mock_redis
    return pub


class TestWebhookEventPublishing:
    async def test_received_event_published_to_stream(self, publisher, mock_redis):
        webhook_event_id = EventPublisher.generate_webhook_event_id()

        await publisher.publish_webhook_received(
            webhook_event_id=webhook_event_id,
            source="github",
            event_type="issues",
            payload_size=1024,
        )

        mock_redis.xadd.assert_called_once()
        call_args = mock_redis.xadd.call_args
        assert call_args[0][0] == "task_events"
        event_data = call_args[0][1]
        assert event_data["type"] == "webhook:received"
        assert event_data["webhook_event_id"] == webhook_event_id

    async def test_validated_event_published_to_stream(self, publisher, mock_redis):
        webhook_event_id = EventPublisher.generate_webhook_event_id()

        await publisher.publish_webhook_validated(
            webhook_event_id=webhook_event_id,
            source="github",
            signature_valid=True,
        )

        call_args = mock_redis.xadd.call_args
        event_data = call_args[0][1]
        assert event_data["type"] == "webhook:validated"

    async def test_matched_event_published_to_stream(self, publisher, mock_redis):
        webhook_event_id = EventPublisher.generate_webhook_event_id()

        await publisher.publish_webhook_matched(
            webhook_event_id=webhook_event_id,
            source="github",
            event_type="issues",
            matched_handler="github-issue-handler",
        )

        call_args = mock_redis.xadd.call_args
        event_data = call_args[0][1]
        assert event_data["type"] == "webhook:matched"

    async def test_task_created_event_includes_task_id(self, publisher, mock_redis):
        webhook_event_id = EventPublisher.generate_webhook_event_id()

        await publisher.publish_webhook_task_created(
            webhook_event_id=webhook_event_id,
            task_id="task-123",
            source="github",
            event_type="issues",
            input_message="Fix authentication bug",
        )

        call_args = mock_redis.xadd.call_args
        event_data = call_args[0][1]
        assert event_data["type"] == "webhook:task_created"
        assert '"task_id": "task-123"' in event_data["data"]


class TestEventPublisherLifecycle:
    async def test_close_releases_connection(self, publisher, mock_redis):
        await publisher.close()

        mock_redis.close.assert_called_once()
        assert publisher._client is None

    async def test_factory_creates_publisher(self):
        pub = create_event_publisher("redis://localhost:6379/0")

        assert isinstance(pub, EventPublisher)
        assert pub.redis_url == "redis://localhost:6379/0"

    async def test_generate_webhook_event_id_is_unique(self):
        id1 = EventPublisher.generate_webhook_event_id()
        id2 = EventPublisher.generate_webhook_event_id()

        assert id1 != id2
        assert len(id1) == 36


class TestEventDataFormat:
    async def test_event_data_is_json_serialized(self, publisher, mock_redis):
        webhook_event_id = EventPublisher.generate_webhook_event_id()

        await publisher.publish_webhook_received(
            webhook_event_id=webhook_event_id,
            source="jira",
            event_type="jira:issue_created",
            payload_size=2048,
        )

        import json

        call_args = mock_redis.xadd.call_args
        event_data = call_args[0][1]
        parsed = json.loads(event_data["data"])
        assert parsed["source"] == "jira"
        assert parsed["event_type"] == "jira:issue_created"
        assert parsed["payload_size"] == 2048

    async def test_event_includes_iso_timestamp(self, publisher, mock_redis):
        webhook_event_id = EventPublisher.generate_webhook_event_id()

        await publisher.publish_webhook_received(
            webhook_event_id=webhook_event_id,
            source="slack",
            event_type="app_mention",
            payload_size=512,
        )

        call_args = mock_redis.xadd.call_args
        event_data = call_args[0][1]
        assert "timestamp" in event_data
        datetime.fromisoformat(event_data["timestamp"])


class TestResponseImmediateEventPublishing:
    async def test_response_immediate_published_to_stream(self, publisher, mock_redis):
        webhook_event_id = EventPublisher.generate_webhook_event_id()

        await publisher.publish_response_immediate(
            webhook_event_id=webhook_event_id,
            task_id="task-123",
            source="github",
            response_type="eyes_reaction",
            target="owner/repo#42",
        )

        mock_redis.xadd.assert_called_once()
        call_args = mock_redis.xadd.call_args
        event_data = call_args[0][1]
        assert event_data["type"] == "response:immediate"
        assert event_data["webhook_event_id"] == webhook_event_id

    async def test_response_immediate_data_contains_fields(self, publisher, mock_redis):
        import json

        webhook_event_id = EventPublisher.generate_webhook_event_id()

        await publisher.publish_response_immediate(
            webhook_event_id=webhook_event_id,
            task_id="task-456",
            source="jira",
            response_type="processing_comment",
            target="PROJ-123",
        )

        call_args = mock_redis.xadd.call_args
        parsed = json.loads(call_args[0][1]["data"])
        assert parsed["task_id"] == "task-456"
        assert parsed["source"] == "jira"
        assert parsed["response_type"] == "processing_comment"
        assert parsed["target"] == "PROJ-123"


class TestNotificationOpsEventPublishing:
    async def test_notification_ops_published_to_stream(self, publisher, mock_redis):
        webhook_event_id = EventPublisher.generate_webhook_event_id()

        await publisher.publish_notification_ops(
            webhook_event_id=webhook_event_id,
            task_id="task-789",
            source="slack",
            notification_type="task_started",
            channel="#ops",
        )

        mock_redis.xadd.assert_called_once()
        call_args = mock_redis.xadd.call_args
        event_data = call_args[0][1]
        assert event_data["type"] == "notification:ops"

    async def test_notification_ops_data_contains_fields(self, publisher, mock_redis):
        import json

        webhook_event_id = EventPublisher.generate_webhook_event_id()

        await publisher.publish_notification_ops(
            webhook_event_id=webhook_event_id,
            task_id="task-789",
            source="github",
            notification_type="task_failed",
            channel="#alerts",
        )

        call_args = mock_redis.xadd.call_args
        parsed = json.loads(call_args[0][1]["data"])
        assert parsed["task_id"] == "task-789"
        assert parsed["source"] == "github"
        assert parsed["notification_type"] == "task_failed"
        assert parsed["channel"] == "#alerts"


class TestFullWebhookEventFlow:
    async def test_complete_webhook_flow_publishes_all_events(self, publisher, mock_redis):
        webhook_event_id = EventPublisher.generate_webhook_event_id()

        await publisher.publish_webhook_received(
            webhook_event_id=webhook_event_id,
            source="github",
            event_type="issues",
            payload_size=1024,
        )
        await publisher.publish_webhook_validated(
            webhook_event_id=webhook_event_id,
            source="github",
            signature_valid=True,
        )
        await publisher.publish_response_immediate(
            webhook_event_id=webhook_event_id,
            task_id="task-456",
            source="github",
            response_type="eyes_reaction",
            target="owner/repo#1",
        )
        await publisher.publish_webhook_matched(
            webhook_event_id=webhook_event_id,
            source="github",
            event_type="issues",
            matched_handler="github-issue-handler",
        )
        await publisher.publish_webhook_task_created(
            webhook_event_id=webhook_event_id,
            task_id="task-456",
            source="github",
            event_type="issues",
            input_message="Fix bug",
        )
        await publisher.publish_notification_ops(
            webhook_event_id=webhook_event_id,
            task_id="task-456",
            source="github",
            notification_type="task_started",
            channel="#ops",
        )

        assert mock_redis.xadd.call_count == 6

        event_types = [call[0][1]["type"] for call in mock_redis.xadd.call_args_list]
        assert event_types == [
            "webhook:received",
            "webhook:validated",
            "response:immediate",
            "webhook:matched",
            "webhook:task_created",
            "notification:ops",
        ]

    async def test_all_events_share_same_webhook_event_id(self, publisher, mock_redis):
        webhook_event_id = EventPublisher.generate_webhook_event_id()

        await publisher.publish_webhook_received(
            webhook_event_id=webhook_event_id,
            source="github",
            event_type="issues",
            payload_size=1024,
        )
        await publisher.publish_webhook_validated(
            webhook_event_id=webhook_event_id,
            source="github",
            signature_valid=True,
        )

        for call in mock_redis.xadd.call_args_list:
            assert call[0][1]["webhook_event_id"] == webhook_event_id
