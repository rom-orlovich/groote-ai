from unittest.mock import AsyncMock, MagicMock, patch


def _mock_http_client():
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    return mock_client


class TestSlackOpsNotificationOnCompletion:
    @patch("services.slack_notifier.httpx.AsyncClient")
    async def test_notify_completed_sends_to_ops_channel(self, mock_cls):
        from services.slack_notifier import notify_task_completed

        mock_cls.return_value = _mock_http_client()

        result = await notify_task_completed(
            "http://slack-api:3003",
            "#notifications",
            "github",
            "task-001",
            "Fixed the bug",
        )

        assert result is True
        payload = mock_cls.return_value.__aenter__.return_value.post.call_args[1]["json"]
        assert payload["channel"] == "#notifications"
        assert "Task Completed" in payload["text"]
        assert "github" in payload["text"]
        assert "task-001" in payload["text"]

    @patch("services.slack_notifier.httpx.AsyncClient")
    async def test_notify_failed_sends_error_to_ops_channel(self, mock_cls):
        from services.slack_notifier import notify_task_failed

        mock_cls.return_value = _mock_http_client()

        result = await notify_task_failed(
            "http://slack-api:3003",
            "#notifications",
            "jira",
            "task-002",
            "Redis connection refused",
        )

        assert result is True
        payload = mock_cls.return_value.__aenter__.return_value.post.call_args[1]["json"]
        assert "Task Failed" in payload["text"]
        assert "Redis connection refused" in payload["text"]

    async def test_empty_channel_skips_completion_notification(self):
        from services.slack_notifier import notify_task_completed

        result = await notify_task_completed(
            "http://slack-api:3003", "", "github", "task-001", "Done"
        )
        assert result is False

    async def test_empty_channel_skips_failure_notification(self):
        from services.slack_notifier import notify_task_failed

        result = await notify_task_failed("http://slack-api:3003", "", "jira", "task-002", "Error")
        assert result is False


class TestSlackNotifierHttpErrors:
    @patch("services.slack_notifier.httpx.AsyncClient")
    async def test_completion_http_error_returns_false(self, mock_cls):
        import httpx
        from services.slack_notifier import notify_task_completed

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_cls.return_value = mock_client

        result = await notify_task_completed(
            "http://slack-api:3003", "#ops", "github", "task-001", "Done"
        )
        assert result is False

    @patch("services.slack_notifier.httpx.AsyncClient")
    async def test_failure_http_error_returns_false(self, mock_cls):
        import httpx
        from services.slack_notifier import notify_task_failed

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_cls.return_value = mock_client

        result = await notify_task_failed(
            "http://slack-api:3003", "#ops", "slack", "task-003", "CLI crashed"
        )
        assert result is False


class TestCLIHandlesResponsesViaMCP:
    """
    The CLI agent (Claude/Cursor) posts responses to platforms via MCP tools:
    - GitHub: github:add_issue_comment
    - Jira: jira:add_jira_comment
    - Slack: slack:send_slack_message

    Agent-engine only sends ops Slack notifications, not platform responses.
    """

    @patch("services.slack_notifier.httpx.AsyncClient")
    async def test_github_task_gets_ops_notification_only(self, mock_cls):
        from services.slack_notifier import notify_task_completed

        mock_cls.return_value = _mock_http_client()

        await notify_task_completed(
            "http://slack-api:3003", "#ops", "github", "task-gh", "PR reviewed"
        )

        payload = mock_cls.return_value.__aenter__.return_value.post.call_args[1]["json"]
        assert payload["channel"] == "#ops"
        assert "github" in payload["text"]

    @patch("services.slack_notifier.httpx.AsyncClient")
    async def test_jira_task_gets_ops_notification_only(self, mock_cls):
        from services.slack_notifier import notify_task_completed

        mock_cls.return_value = _mock_http_client()

        await notify_task_completed(
            "http://slack-api:3003", "#ops", "jira", "task-jira", "Plan posted"
        )

        payload = mock_cls.return_value.__aenter__.return_value.post.call_args[1]["json"]
        assert payload["channel"] == "#ops"
        assert "jira" in payload["text"]

    @patch("services.slack_notifier.httpx.AsyncClient")
    async def test_slack_task_gets_ops_notification_only(self, mock_cls):
        from services.slack_notifier import notify_task_completed

        mock_cls.return_value = _mock_http_client()

        await notify_task_completed(
            "http://slack-api:3003", "#ops", "slack", "task-slack", "Reply sent"
        )

        payload = mock_cls.return_value.__aenter__.return_value.post.call_args[1]["json"]
        assert payload["channel"] == "#ops"
        assert "slack" in payload["text"]
