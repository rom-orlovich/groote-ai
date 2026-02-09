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


class TestTaskOutputEventPublishing:
    @patch("services.slack_notifier.httpx.AsyncClient")
    async def test_task_output_published_after_cli_completes(self, mock_http_cls):
        import json

        from main import TaskWorker

        mock_http_cls.return_value = _mock_http_client()

        mock_settings = MagicMock()
        mock_settings.redis_url = "redis://localhost:6379/0"
        mock_settings.max_concurrent_tasks = 5
        mock_settings.task_timeout_seconds = 60
        mock_settings.slack_api_url = "http://slack-api:3003"
        mock_settings.slack_notification_channel = "#ops"
        mock_settings.dashboard_api_url = "http://dashboard-api:5000"

        worker = TaskWorker(mock_settings, MagicMock())
        worker._redis = AsyncMock()
        worker._redis.xadd = AsyncMock()
        worker._redis.hset = AsyncMock()
        worker._redis.publish = AsyncMock()

        mock_result = {
            "output": "Fixed the authentication bug",
            "cost_usd": 0.05,
            "input_tokens": 1000,
            "output_tokens": 500,
            "success": True,
            "error": None,
        }

        with patch.object(worker, "_execute_task", return_value=mock_result):
            task_data = json.dumps(
                {"task_id": "task-output-test", "source": "github", "prompt": "Fix bug"}
            ).encode()
            await worker._process_task(task_data)

        xadd_calls = worker._redis.xadd.call_args_list
        event_types = [c[0][1]["type"] for c in xadd_calls]
        assert "task:output" in event_types

        output_call = next(c for c in xadd_calls if c[0][1]["type"] == "task:output")
        output_data = json.loads(output_call[0][1]["data"])
        assert output_data["content"] == "Fixed the authentication bug"

    async def test_empty_output_skips_task_output_event(self):
        import json

        from main import TaskWorker

        mock_settings = MagicMock()
        mock_settings.redis_url = "redis://localhost:6379/0"
        mock_settings.max_concurrent_tasks = 5
        mock_settings.task_timeout_seconds = 60
        mock_settings.slack_api_url = "http://slack-api:3003"
        mock_settings.slack_notification_channel = ""
        mock_settings.dashboard_api_url = "http://dashboard-api:5000"

        worker = TaskWorker(mock_settings, MagicMock())
        worker._redis = AsyncMock()
        worker._redis.xadd = AsyncMock()
        worker._redis.hset = AsyncMock()
        worker._redis.publish = AsyncMock()

        mock_result = {
            "output": "",
            "cost_usd": 0.0,
            "input_tokens": 0,
            "output_tokens": 0,
            "success": True,
            "error": None,
        }

        with patch.object(worker, "_execute_task", return_value=mock_result):
            task_data = json.dumps({"task_id": "task-no-output", "prompt": "Test"}).encode()
            await worker._process_task(task_data)

        xadd_calls = worker._redis.xadd.call_args_list
        event_types = [c[0][1]["type"] for c in xadd_calls]
        assert "task:output" not in event_types


class TestNotificationOpsEventPublishing:
    @patch("services.slack_notifier.httpx.AsyncClient")
    async def test_ops_completion_publishes_notification_event(self, mock_cls):
        import json

        from main import TaskWorker

        mock_cls.return_value = _mock_http_client()

        mock_settings = MagicMock()
        mock_settings.slack_api_url = "http://slack-api:3003"
        mock_settings.slack_notification_channel = "#ops"

        worker = TaskWorker(mock_settings, MagicMock())
        worker._redis = AsyncMock()
        worker._redis.xadd = AsyncMock()

        task = {"task_id": "task-notif-test", "source": "github"}
        result = {"output": "Bug fixed"}

        await worker._notify_ops_completion(task, result)

        worker._redis.xadd.assert_called_once()
        call_args = worker._redis.xadd.call_args
        assert call_args[0][1]["type"] == "notification:ops"
        data = json.loads(call_args[0][1]["data"])
        assert data["notification_type"] == "task_completed"
        assert data["source"] == "github"

    @patch("services.slack_notifier.httpx.AsyncClient")
    async def test_ops_failure_publishes_notification_event(self, mock_cls):
        import json

        from main import TaskWorker

        mock_cls.return_value = _mock_http_client()

        mock_settings = MagicMock()
        mock_settings.slack_api_url = "http://slack-api:3003"
        mock_settings.slack_notification_channel = "#ops"

        worker = TaskWorker(mock_settings, MagicMock())
        worker._redis = AsyncMock()
        worker._redis.xadd = AsyncMock()

        task = {"task_id": "task-fail-test", "source": "jira"}

        await worker._notify_platform_failure(task, "Redis timeout")

        worker._redis.xadd.assert_called_once()
        call_args = worker._redis.xadd.call_args
        assert call_args[0][1]["type"] == "notification:ops"
        data = json.loads(call_args[0][1]["data"])
        assert data["notification_type"] == "task_failed"
        assert data["source"] == "jira"

    async def test_no_notification_event_when_slack_send_fails(self):
        from main import TaskWorker

        mock_settings = MagicMock()
        mock_settings.slack_api_url = "http://slack-api:3003"
        mock_settings.slack_notification_channel = ""

        worker = TaskWorker(mock_settings, MagicMock())
        worker._redis = AsyncMock()
        worker._redis.xadd = AsyncMock()

        task = {"task_id": "task-no-notif", "source": "github"}
        result = {"output": "Done"}

        await worker._notify_ops_completion(task, result)

        worker._redis.xadd.assert_not_called()
