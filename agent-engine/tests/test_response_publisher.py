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
    async def test_notify_completed_sends_blocks_with_buttons(self, mock_cls):
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
        assert "blocks" in payload
        context_block = payload["blocks"][1]
        assert context_block["type"] == "context"

    @patch("services.slack_notifier.httpx.AsyncClient")
    async def test_notify_completed_with_view_url_adds_link_button(self, mock_cls):
        from services.slack_notifier import notify_task_completed

        mock_cls.return_value = _mock_http_client()

        await notify_task_completed(
            "http://slack-api:3003",
            "#notifications",
            "github",
            "task-001",
            "Fixed the bug",
            view_url="https://github.com/org/repo/issues/42",
        )

        payload = mock_cls.return_value.__aenter__.return_value.post.call_args[1]["json"]
        actions_block = payload["blocks"][1]
        assert actions_block["type"] == "actions"
        button = actions_block["elements"][0]
        assert button["url"] == "https://github.com/org/repo/issues/42"
        assert button["text"]["text"] == "View"

    @patch("services.slack_notifier.httpx.AsyncClient")
    async def test_notify_failed_sends_blocks(self, mock_cls):
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
        assert "blocks" in payload
        assert ":x:" in payload["blocks"][0]["text"]["text"]

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
    async def test_github_task_gets_ops_notification_with_blocks(self, mock_cls):
        from services.slack_notifier import notify_task_completed

        mock_cls.return_value = _mock_http_client()

        await notify_task_completed(
            "http://slack-api:3003", "#ops", "github", "task-gh", "PR reviewed"
        )

        payload = mock_cls.return_value.__aenter__.return_value.post.call_args[1]["json"]
        assert payload["channel"] == "#ops"
        assert "Task Completed" in payload["text"]
        assert "blocks" in payload

    @patch("services.slack_notifier.httpx.AsyncClient")
    async def test_jira_task_gets_ops_notification_with_blocks(self, mock_cls):
        from services.slack_notifier import notify_task_completed

        mock_cls.return_value = _mock_http_client()

        await notify_task_completed(
            "http://slack-api:3003", "#ops", "jira", "task-jira", "Plan posted"
        )

        payload = mock_cls.return_value.__aenter__.return_value.post.call_args[1]["json"]
        assert payload["channel"] == "#ops"
        assert "blocks" in payload

    @patch("services.slack_notifier.httpx.AsyncClient")
    async def test_slack_task_gets_ops_notification_with_blocks(self, mock_cls):
        from services.slack_notifier import notify_task_completed

        mock_cls.return_value = _mock_http_client()

        await notify_task_completed(
            "http://slack-api:3003", "#ops", "slack", "task-slack", "Reply sent"
        )

        payload = mock_cls.return_value.__aenter__.return_value.post.call_args[1]["json"]
        assert payload["channel"] == "#ops"
        assert "blocks" in payload


class TestTaskOutputEventPublishing:
    @patch("services.slack_notifier.httpx.AsyncClient")
    @patch("worker.conversation_bridge.post_fallback_notice", new_callable=AsyncMock)
    @patch("worker.conversation_bridge.fetch_conversation_context", new_callable=AsyncMock, return_value=[])
    @patch("worker.conversation_bridge.post_system_message", new_callable=AsyncMock)
    @patch("worker.conversation_bridge.register_task", new_callable=AsyncMock)
    @patch("worker.conversation_bridge.get_or_create_flow_conversation", new_callable=AsyncMock, return_value="conv-123")
    async def test_task_output_published_after_cli_completes(
        self, mock_get_conv, mock_register, mock_sys_msg, mock_fetch_ctx, mock_fallback, mock_http_cls
    ):
        import json

        from worker import TaskWorker

        mock_http_cls.return_value = _mock_http_client()

        mock_settings = MagicMock()
        mock_settings.redis_url = "redis://localhost:6379/0"
        mock_settings.max_concurrent_tasks = 5
        mock_settings.task_timeout_seconds = 60
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

        from worker import TaskWorker

        mock_settings = MagicMock()
        mock_settings.redis_url = "redis://localhost:6379/0"
        mock_settings.max_concurrent_tasks = 5
        mock_settings.task_timeout_seconds = 60
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


class TestBuildViewUrl:
    def test_pr_url_extracted_from_output(self):
        from worker import _build_view_url

        task = {"source": "jira"}
        output = "PR created: https://github.com/rom-orlovich/manga-creator/pull/103"
        assert _build_view_url(task, output) == "https://github.com/rom-orlovich/manga-creator/pull/103"

    def test_pr_url_extracted_from_markdown_link(self):
        from worker import _build_view_url

        task = {"source": "jira"}
        output = "**PR**: [#103](https://github.com/org/repo/pull/103) created"
        assert _build_view_url(task, output) == "https://github.com/org/repo/pull/103"

    def test_github_issue_fallback(self):
        from worker import _build_view_url

        task = {
            "source": "github",
            "repository": {"full_name": "org/repo"},
            "issue": {"number": 42},
        }
        assert _build_view_url(task) == "https://github.com/org/repo/issues/42"

    def test_github_pr_fallback(self):
        from worker import _build_view_url

        task = {
            "source": "github",
            "repository": {"full_name": "org/repo"},
            "pull_request": {"number": 98},
        }
        assert _build_view_url(task) == "https://github.com/org/repo/issues/98"

    def test_no_pr_in_output_no_metadata_returns_empty(self):
        from worker import _build_view_url

        assert _build_view_url({"source": "jira"}, "Task completed successfully") == ""

    def test_missing_fields_returns_empty(self):
        from worker import _build_view_url

        assert _build_view_url({"source": "github"}) == ""
