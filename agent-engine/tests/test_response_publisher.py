from unittest.mock import AsyncMock, MagicMock, patch


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


def _mock_http_client():
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    return mock_client


class TestGitHubCompletionPosting:
    @patch("services.github_responder.httpx.AsyncClient")
    async def test_posts_comment_to_correct_issue(self, mock_cls):
        from services.github_responder import post_completion

        mock_cls.return_value = _mock_http_client()
        task = _github_task()

        result = await post_completion("http://github-api:3001", task, "Fixed!", True)

        assert result is True
        url = mock_cls.return_value.__aenter__.return_value.post.call_args[0][0]
        assert "myorg/myrepo" in url
        assert "/issues/123/comments" in url

    @patch("services.github_responder.httpx.AsyncClient")
    async def test_posts_comment_to_pr(self, mock_cls):
        from services.github_responder import post_completion

        mock_cls.return_value = _mock_http_client()
        task = _github_task(event_type="pull_request", pr_number=42)

        result = await post_completion("http://github-api:3001", task, "Reviewed!", True)

        assert result is True
        url = mock_cls.return_value.__aenter__.return_value.post.call_args[0][0]
        assert "/issues/42/comments" in url

    async def test_missing_repo_returns_false(self):
        from services.github_responder import post_completion

        task = {"task_id": "t1", "source": "github", "event_type": "issues"}
        result = await post_completion("http://github-api:3001", task, "output", True)
        assert result is False

    async def test_missing_issue_number_returns_false(self):
        from services.github_responder import post_completion

        task = {
            "task_id": "t1",
            "source": "github",
            "event_type": "issues",
            "repository": {"full_name": "myorg/myrepo"},
        }
        result = await post_completion("http://github-api:3001", task, "output", True)
        assert result is False

    @patch("services.github_responder.httpx.AsyncClient")
    async def test_failure_prefix_added_on_error(self, mock_cls):
        from services.github_responder import post_completion

        mock_cls.return_value = _mock_http_client()
        task = _github_task()

        await post_completion("http://github-api:3001", task, "Something broke", False)

        body = mock_cls.return_value.__aenter__.return_value.post.call_args[1]["json"]["body"]
        assert body.startswith("Task failed.")

    @patch("services.github_responder.httpx.AsyncClient")
    async def test_long_output_truncated(self, mock_cls):
        from services.github_responder import post_completion

        mock_cls.return_value = _mock_http_client()
        task = _github_task()

        await post_completion("http://github-api:3001", task, "x" * 10000, True)

        body = mock_cls.return_value.__aenter__.return_value.post.call_args[1]["json"]["body"]
        assert len(body) <= 8001


class TestJiraCompletionPosting:
    @patch("services.jira_responder.httpx.AsyncClient")
    async def test_posts_comment_to_correct_issue(self, mock_cls):
        from services.jira_responder import post_completion

        mock_cls.return_value = _mock_http_client()
        task = _jira_task()

        result = await post_completion("http://jira-api:3002", task, "Fixed!", True)

        assert result is True
        url = mock_cls.return_value.__aenter__.return_value.post.call_args[0][0]
        assert "/issues/PROJ-123/comments" in url

    async def test_missing_issue_key_returns_false(self):
        from services.jira_responder import post_completion

        task = {"task_id": "t1", "source": "jira", "event_type": "jira:issue_created"}
        result = await post_completion("http://jira-api:3002", task, "output", True)
        assert result is False


class TestSlackCompletionPosting:
    @patch("services.slack_responder.httpx.AsyncClient")
    async def test_posts_threaded_reply(self, mock_cls):
        from services.slack_responder import post_completion

        mock_cls.return_value = _mock_http_client()
        task = _slack_task()

        result = await post_completion("http://slack-api:3003", task, "Done!", True)

        assert result is True
        payload = mock_cls.return_value.__aenter__.return_value.post.call_args[1]["json"]
        assert payload["channel"] == "C123CHANNEL"
        assert payload["thread_ts"] == "1234567890.123456"

    @patch("services.slack_responder.httpx.AsyncClient")
    async def test_posts_without_thread_ts(self, mock_cls):
        from services.slack_responder import post_completion

        mock_cls.return_value = _mock_http_client()
        task = _slack_task()
        del task["thread_ts"]

        result = await post_completion("http://slack-api:3003", task, "Done!", True)

        assert result is True
        payload = mock_cls.return_value.__aenter__.return_value.post.call_args[1]["json"]
        assert "thread_ts" not in payload

    async def test_missing_channel_returns_false(self):
        from services.slack_responder import post_completion

        task = {"task_id": "t1", "source": "slack", "event_type": "app_mention"}
        result = await post_completion("http://slack-api:3003", task, "output", True)
        assert result is False

    @patch("services.slack_responder.httpx.AsyncClient")
    async def test_long_output_truncated_at_4000(self, mock_cls):
        from services.slack_responder import post_completion

        mock_cls.return_value = _mock_http_client()
        task = _slack_task()

        await post_completion("http://slack-api:3003", task, "x" * 5000, True)

        payload = mock_cls.return_value.__aenter__.return_value.post.call_args[1]["json"]
        assert len(payload["text"]) <= 4001


class TestSlackNotifier:
    @patch("services.slack_notifier.httpx.AsyncClient")
    async def test_notify_completed_sends_message(self, mock_cls):
        from services.slack_notifier import notify_task_completed

        mock_cls.return_value = _mock_http_client()

        result = await notify_task_completed(
            "http://slack-api:3003", "#notifications", "github", "task-001", "Fixed the bug"
        )

        assert result is True
        payload = mock_cls.return_value.__aenter__.return_value.post.call_args[1]["json"]
        assert payload["channel"] == "#notifications"
        assert "Task Completed" in payload["text"]
        assert "github" in payload["text"]

    @patch("services.slack_notifier.httpx.AsyncClient")
    async def test_notify_failed_sends_error(self, mock_cls):
        from services.slack_notifier import notify_task_failed

        mock_cls.return_value = _mock_http_client()

        result = await notify_task_failed(
            "http://slack-api:3003", "#notifications", "jira", "task-002", "Redis down"
        )

        assert result is True
        payload = mock_cls.return_value.__aenter__.return_value.post.call_args[1]["json"]
        assert "Task Failed" in payload["text"]
        assert "Redis down" in payload["text"]

    async def test_empty_channel_skips_notification(self):
        from services.slack_notifier import notify_task_completed

        result = await notify_task_completed(
            "http://slack-api:3003", "", "github", "task-001", "Done"
        )
        assert result is False


class TestHttpErrorHandling:
    @patch("services.github_responder.httpx.AsyncClient")
    async def test_github_http_error_returns_false(self, mock_cls):
        import httpx
        from services.github_responder import post_completion

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_cls.return_value = mock_client

        result = await post_completion("http://github-api:3001", _github_task(), "out", True)
        assert result is False

    @patch("services.jira_responder.httpx.AsyncClient")
    async def test_jira_http_error_returns_false(self, mock_cls):
        import httpx
        from services.jira_responder import post_completion

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_cls.return_value = mock_client

        result = await post_completion("http://jira-api:3002", _jira_task(), "out", True)
        assert result is False

    @patch("services.slack_responder.httpx.AsyncClient")
    async def test_slack_http_error_returns_false(self, mock_cls):
        import httpx
        from services.slack_responder import post_completion

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_cls.return_value = mock_client

        result = await post_completion("http://slack-api:3003", _slack_task(), "out", True)
        assert result is False
