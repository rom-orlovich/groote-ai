from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from services.response_publisher import ResponsePublisher


@pytest.fixture
def publisher():
    return ResponsePublisher(
        github_api_url="http://github-api:3001",
        jira_api_url="http://jira-api:3002",
        slack_api_url="http://slack-api:3003",
    )


def _github_task(
    event_type: str = "issues",
    repo: str = "myorg/myrepo",
    issue_number: int = 123,
    pr_number: int | None = None,
) -> dict:
    task: dict = {
        "task_id": "task-001",
        "source": "github",
        "event_type": event_type,
        "repository": {"full_name": repo},
        "prompt": "Fix the bug",
    }
    if event_type in ("pull_request", "pull_request_review_comment"):
        task["pull_request"] = {"number": pr_number or 42}
    else:
        task["issue"] = {"number": issue_number}
    return task


def _jira_task(issue_key: str = "PROJ-123") -> dict:
    return {
        "task_id": "task-002",
        "source": "jira",
        "event_type": "jira:issue_created",
        "issue": {"key": issue_key, "id": "10001"},
        "prompt": "Fix authentication",
    }


def _slack_task(
    channel: str = "C123CHANNEL",
    thread_ts: str = "1234567890.123456",
) -> dict:
    return {
        "task_id": "task-003",
        "source": "slack",
        "event_type": "app_mention",
        "channel": channel,
        "thread_ts": thread_ts,
        "prompt": "Help me debug",
    }


def _success_result(output: str = "Here is the fix...") -> dict:
    return {"output": output, "success": True}


class TestGitHubResponsePosting:
    @patch("services.response_publisher.httpx.AsyncClient")
    async def test_github_issue_comment_posted(self, mock_client_cls, publisher):
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        success = await publisher.post_response(_github_task(), _success_result())

        assert success is True
        mock_client.post.assert_called_once()
        url = mock_client.post.call_args[0][0]
        assert "myorg/myrepo" in url
        assert "/issues/123/comments" in url

    @patch("services.response_publisher.httpx.AsyncClient")
    async def test_github_pr_comment_posted(self, mock_client_cls, publisher):
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        task = _github_task(event_type="pull_request", pr_number=42)
        success = await publisher.post_response(task, _success_result())

        assert success is True
        url = mock_client.post.call_args[0][0]
        assert "/issues/42/comments" in url

    async def test_github_missing_repo_returns_false(self, publisher):
        task = {"task_id": "t1", "source": "github", "event_type": "issues"}

        success = await publisher.post_response(task, _success_result())

        assert success is False


class TestJiraResponsePosting:
    @patch("services.response_publisher.httpx.AsyncClient")
    async def test_jira_comment_posted(self, mock_client_cls, publisher):
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        success = await publisher.post_response(_jira_task(), _success_result())

        assert success is True
        url = mock_client.post.call_args[0][0]
        assert "/issues/PROJ-123/comments" in url

    async def test_jira_missing_key_returns_false(self, publisher):
        task = {"task_id": "t1", "source": "jira", "event_type": "jira:issue_created"}

        success = await publisher.post_response(task, _success_result())

        assert success is False


class TestSlackResponsePosting:
    @patch("services.response_publisher.httpx.AsyncClient")
    async def test_slack_reply_posted(self, mock_client_cls, publisher):
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        success = await publisher.post_response(_slack_task(), _success_result())

        assert success is True
        url = mock_client.post.call_args[0][0]
        assert "/chat/postMessage" in url
        payload = mock_client.post.call_args[1]["json"]
        assert payload["channel"] == "C123CHANNEL"
        assert payload["thread_ts"] == "1234567890.123456"

    @patch("services.response_publisher.httpx.AsyncClient")
    async def test_slack_without_thread_ts(self, mock_client_cls, publisher):
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        task = _slack_task()
        del task["thread_ts"]

        success = await publisher.post_response(task, _success_result())

        assert success is True
        payload = mock_client.post.call_args[1]["json"]
        assert "thread_ts" not in payload

    async def test_slack_missing_channel_returns_false(self, publisher):
        task = {"task_id": "t1", "source": "slack", "event_type": "app_mention"}

        success = await publisher.post_response(task, _success_result())

        assert success is False


class TestUnknownPlatform:
    async def test_unknown_source_returns_false(self, publisher):
        task = {"task_id": "t1", "source": "unknown_platform"}

        success = await publisher.post_response(task, _success_result())

        assert success is False


class TestResponsePublisherErrorHandling:
    @patch("services.response_publisher.httpx.AsyncClient")
    async def test_http_error_returns_false(self, mock_client_cls, publisher):
        import httpx

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        success = await publisher.post_response(_github_task(), _success_result())

        assert success is False
