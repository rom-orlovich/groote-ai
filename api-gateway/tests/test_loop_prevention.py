from unittest.mock import AsyncMock, MagicMock

import pytest
from services.loop_prevention import LoopPrevention


@pytest.fixture
def mock_redis():
    redis = MagicMock()
    redis.setex = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.delete = AsyncMock()
    return redis


@pytest.fixture
def loop_prevention(mock_redis):
    return LoopPrevention(redis_client=mock_redis)


class TestCommentTracking:
    async def test_agent_posted_comment_tracked(self, loop_prevention, mock_redis):
        await loop_prevention.track_posted_comment("comment-456")

        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        assert "posted_comments:comment-456" in call_args[0]
        assert call_args[0][1] == 3600

    async def test_subsequent_webhook_for_own_comment_detected(self, loop_prevention, mock_redis):
        mock_redis.get.return_value = b"1"

        is_own = await loop_prevention.is_own_comment("comment-456")

        assert is_own is True
        mock_redis.get.assert_called_with("posted_comments:comment-456")

    async def test_different_comment_not_blocked(self, loop_prevention, mock_redis):
        mock_redis.get.return_value = None

        is_own = await loop_prevention.is_own_comment("comment-789")

        assert is_own is False


class TestTTLExpiration:
    def test_tracking_uses_1_hour_ttl(self, loop_prevention):
        assert loop_prevention._ttl_seconds == 3600

    async def test_key_format(self, loop_prevention):
        key = loop_prevention.get_key("comment-123")
        assert key == "posted_comments:comment-123"


class TestLoopPreventionFlow:
    async def test_loop_prevention_flow(self, loop_prevention, mock_redis):
        mock_redis.get.return_value = None
        is_own_before = await loop_prevention.is_own_comment("comment-456")
        assert is_own_before is False

        await loop_prevention.track_posted_comment("comment-456")
        mock_redis.setex.assert_called_once()

        mock_redis.get.return_value = b"1"
        is_own_after = await loop_prevention.is_own_comment("comment-456")
        assert is_own_after is True

    async def test_no_redis_means_no_blocking(self):
        loop_prevention = LoopPrevention(redis_client=None)

        is_own = await loop_prevention.is_own_comment("comment-123")
        assert is_own is False

    async def test_parallel_comments_tracked_independently(self, loop_prevention, mock_redis):
        await loop_prevention.track_posted_comment("comment-1")
        await loop_prevention.track_posted_comment("comment-2")
        await loop_prevention.track_posted_comment("comment-3")

        assert mock_redis.setex.call_count == 3


class TestLoopPreventionIntegration:
    async def test_github_comment_loop_prevention(self, loop_prevention, mock_redis):
        github_comment_id = "1234567890"

        mock_redis.get.return_value = None
        assert await loop_prevention.is_own_comment(github_comment_id) is False

        await loop_prevention.track_posted_comment(github_comment_id)

        mock_redis.get.return_value = b"1"
        assert await loop_prevention.is_own_comment(github_comment_id) is True

    async def test_jira_comment_loop_prevention(self, loop_prevention, mock_redis):
        jira_comment_id = "10001"

        await loop_prevention.track_posted_comment(jira_comment_id)
        mock_redis.setex.assert_called_once()

    async def test_slack_message_loop_prevention(self, loop_prevention, mock_redis):
        slack_ts = "1706702400.000001"

        await loop_prevention.track_posted_comment(slack_ts)
        mock_redis.setex.assert_called_with(
            f"posted_comments:{slack_ts}",
            3600,
            "1",
        )
