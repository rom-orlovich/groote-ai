from unittest.mock import AsyncMock, MagicMock, patch


def _mock_http_client(status_code: int = 200):
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.status_code = status_code
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    return mock_client


class TestGitHubImmediateResponse:
    @patch("webhooks.github.response.httpx.AsyncClient")
    async def test_eyes_reaction_on_issue_comment(self, mock_cls):
        from webhooks.github.response import send_immediate_response

        mock_cls.return_value = _mock_http_client()

        result = await send_immediate_response(
            "http://github-api:3001", "issue_comment", "myorg", "myrepo", 456, 123
        )

        assert result.get("sent", result) is True if isinstance(result, dict) else result is True
        url = mock_cls.return_value.__aenter__.return_value.post.call_args[0][0]
        assert "/reactions" in url
        payload = mock_cls.return_value.__aenter__.return_value.post.call_args[1]["json"]
        assert payload["content"] == "eyes"

    @patch("webhooks.github.response.httpx.AsyncClient")
    async def test_comment_on_new_issue(self, mock_cls):
        from webhooks.github.response import send_immediate_response

        mock_cls.return_value = _mock_http_client()

        result = await send_immediate_response(
            "http://github-api:3001", "issues", "myorg", "myrepo", None, 123
        )

        assert result.get("sent", result) is True if isinstance(result, dict) else result is True
        url = mock_cls.return_value.__aenter__.return_value.post.call_args[0][0]
        assert "/issues/123/comments" in url

    @patch("webhooks.github.response.httpx.AsyncClient")
    async def test_comment_on_pr(self, mock_cls):
        from webhooks.github.response import send_immediate_response

        mock_cls.return_value = _mock_http_client()

        result = await send_immediate_response(
            "http://github-api:3001", "pull_request", "myorg", "myrepo", None, 42
        )

        assert result.get("sent", result) is True if isinstance(result, dict) else result is True
        url = mock_cls.return_value.__aenter__.return_value.post.call_args[0][0]
        assert "/issues/42/comments" in url

    @patch("webhooks.github.response.httpx.AsyncClient")
    async def test_error_reaction_and_comment_on_failure(self, mock_cls):
        from webhooks.github.response import send_error_response

        mock_cls.return_value = _mock_http_client()

        await send_error_response(
            "http://github-api:3001", "issue_comment", "myorg", "myrepo", 456, 123, "Redis down"
        )

        calls = mock_cls.return_value.__aenter__.return_value.post.call_args_list
        assert len(calls) >= 1

    @patch("webhooks.github.response.httpx.AsyncClient")
    async def test_completion_comment_posted(self, mock_cls):
        from webhooks.github.response import post_completion_comment

        mock_cls.return_value = _mock_http_client()

        result = await post_completion_comment(
            "http://github-api:3001", "myorg", "myrepo", 123, "Here is the fix", True
        )

        assert result.get("sent", result) is True if isinstance(result, dict) else result is True
        body = mock_cls.return_value.__aenter__.return_value.post.call_args[1]["json"]["body"]
        assert "Here is the fix" in body

    @patch("webhooks.github.response.httpx.AsyncClient")
    async def test_completion_truncates_long_output(self, mock_cls):
        from webhooks.github.response import post_completion_comment

        mock_cls.return_value = _mock_http_client()

        await post_completion_comment(
            "http://github-api:3001", "myorg", "myrepo", 123, "x" * 10000, True
        )

        body = mock_cls.return_value.__aenter__.return_value.post.call_args[1]["json"]["body"]
        assert len(body) <= 8001


class TestJiraImmediateResponse:
    @patch("webhooks.jira.response.httpx.AsyncClient")
    async def test_processing_comment_sent(self, mock_cls):
        from webhooks.jira.response import send_immediate_response

        mock_cls.return_value = _mock_http_client()

        result = await send_immediate_response("http://jira-api:3002", "PROJ-123")

        assert result.get("sent", result) is True if isinstance(result, dict) else result is True
        url = mock_cls.return_value.__aenter__.return_value.post.call_args[0][0]
        assert "/issues/PROJ-123/comments" in url

    @patch("webhooks.jira.response.httpx.AsyncClient")
    async def test_error_comment_includes_error_message(self, mock_cls):
        from webhooks.jira.response import send_error_response

        mock_cls.return_value = _mock_http_client()

        result = await send_error_response("http://jira-api:3002", "PROJ-123", "Redis down")

        assert result.get("sent", result) is True if isinstance(result, dict) else result is True
        body = mock_cls.return_value.__aenter__.return_value.post.call_args[1]["json"]["body"]
        assert "Redis down" in body

    @patch("webhooks.jira.response.httpx.AsyncClient")
    async def test_completion_comment_posted(self, mock_cls):
        from webhooks.jira.response import post_completion_comment

        mock_cls.return_value = _mock_http_client()

        result = await post_completion_comment(
            "http://jira-api:3002", "PROJ-123", "Task done", True
        )

        assert result.get("sent", result) is True if isinstance(result, dict) else result is True


class TestSlackImmediateResponse:
    @patch("webhooks.slack.response.httpx.AsyncClient")
    async def test_eyes_reaction_and_message_sent(self, mock_cls):
        from webhooks.slack.response import send_immediate_response

        mock_cls.return_value = _mock_http_client()

        result = await send_immediate_response(
            "http://slack-api:3003", "C123", "thread_ts_1", "event_ts_1"
        )

        assert result.get("sent", result) is True if isinstance(result, dict) else result is True
        calls = mock_cls.return_value.__aenter__.return_value.post.call_args_list
        assert len(calls) >= 2

    @patch("webhooks.slack.response.httpx.AsyncClient")
    async def test_error_response_sends_x_reaction_and_message(self, mock_cls):
        from webhooks.slack.response import send_error_response

        mock_cls.return_value = _mock_http_client()

        result = await send_error_response(
            "http://slack-api:3003", "C123", "thread_ts_1", "event_ts_1", "Queue full"
        )

        assert result.get("sent", result) is True if isinstance(result, dict) else result is True

    @patch("webhooks.slack.response.httpx.AsyncClient")
    async def test_thread_reply_uses_thread_ts(self, mock_cls):
        from webhooks.slack.response import send_slack_message

        mock_cls.return_value = _mock_http_client()

        result = await send_slack_message("http://slack-api:3003", "C123", "Hello", "thread_ts_1")

        assert result.get("sent", result) is True if isinstance(result, dict) else result is True
        payload = mock_cls.return_value.__aenter__.return_value.post.call_args[1]["json"]
        assert payload["thread_ts"] == "thread_ts_1"
        assert payload["channel"] == "C123"

    @patch("webhooks.slack.response.httpx.AsyncClient")
    async def test_completion_message_posted(self, mock_cls):
        from webhooks.slack.response import post_completion_message

        mock_cls.return_value = _mock_http_client()

        result = await post_completion_message(
            "http://slack-api:3003", "C123", "thread_ts_1", "All done!", True
        )

        assert result.get("sent", result) is True if isinstance(result, dict) else result is True


class TestSlackNotifier:
    @patch("services.slack_notifier.httpx.AsyncClient")
    async def test_task_started_sends_blocks(self, mock_cls):
        from services.slack_notifier import notify_task_started

        mock_cls.return_value = _mock_http_client()

        result = await notify_task_started(
            "http://slack-api:3003", "#ops", "github", "task-1", "Fix auth bug", agent="brain"
        )

        assert result.get("sent", result) is True if isinstance(result, dict) else result is True
        payload = mock_cls.return_value.__aenter__.return_value.post.call_args[1]["json"]
        assert "Task Started" in payload["text"]
        assert "blocks" in payload
        blocks = payload["blocks"]
        assert blocks[0]["type"] == "section"
        assert "Fix auth bug" in blocks[0]["text"]["text"]
        assert "brain" in blocks[1]["elements"][0]["text"]

    @patch("services.slack_notifier.httpx.AsyncClient")
    async def test_task_failed_sends_blocks(self, mock_cls):
        from services.slack_notifier import notify_task_failed

        mock_cls.return_value = _mock_http_client()

        result = await notify_task_failed(
            "http://slack-api:3003", "#ops", "jira", "task-2", "Timeout"
        )

        assert result.get("sent", result) is True if isinstance(result, dict) else result is True
        payload = mock_cls.return_value.__aenter__.return_value.post.call_args[1]["json"]
        assert "Task Failed" in payload["text"]
        assert "blocks" in payload
        assert ":x:" in payload["blocks"][0]["text"]["text"]

    async def test_no_channel_skips_notification(self):
        from services.slack_notifier import notify_task_started

        result = await notify_task_started(
            "http://slack-api:3003", "", "github", "task-1", "summary"
        )
        assert (result.get("sent", result) if isinstance(result, dict) else result) is False

    @patch("services.slack_notifier.httpx.AsyncClient")
    async def test_task_completed_sends_blocks_with_buttons(self, mock_cls):
        from services.slack_notifier import notify_task_completed

        mock_cls.return_value = _mock_http_client()

        result = await notify_task_completed(
            "http://slack-api:3003", "#ops", "slack", "task-3", "Done"
        )

        assert result.get("sent", result) is True if isinstance(result, dict) else result is True
        payload = mock_cls.return_value.__aenter__.return_value.post.call_args[1]["json"]
        assert "Task Completed" in payload["text"]
        assert "blocks" in payload
        context_block = payload["blocks"][1]
        assert context_block["type"] == "context"


class TestHttpFailuresHandledGracefully:
    @patch("webhooks.github.response.httpx.AsyncClient")
    async def test_github_reaction_failure_returns_false(self, mock_cls):
        import httpx
        from webhooks.github.response import send_eyes_reaction

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=httpx.ConnectError("down"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_cls.return_value = mock_client

        result = await send_eyes_reaction("http://github-api:3001", "o", "r", 1)
        assert (result.get("sent", result) if isinstance(result, dict) else result) is False

    @patch("webhooks.jira.response.httpx.AsyncClient")
    async def test_jira_comment_failure_returns_false(self, mock_cls):
        import httpx
        from webhooks.jira.response import send_jira_comment

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=httpx.ConnectError("down"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_cls.return_value = mock_client

        result = await send_jira_comment("http://jira-api:3002", "K-1", "text")
        assert (result.get("sent", result) if isinstance(result, dict) else result) is False

    @patch("webhooks.slack.response.httpx.AsyncClient")
    async def test_slack_message_failure_returns_false(self, mock_cls):
        import httpx
        from webhooks.slack.response import send_slack_message

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=httpx.ConnectError("down"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_cls.return_value = mock_client

        result = await send_slack_message("http://slack-api:3003", "C1", "text")
        assert (result.get("sent", result) if isinstance(result, dict) else result) is False
