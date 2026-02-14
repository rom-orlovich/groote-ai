from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from services.task_routing import (
    _is_duplicate_content,
    build_task_context,
    detect_mcp_posting,
)


@pytest.fixture(autouse=True)
def _mock_settings():
    mock_settings = MagicMock()
    mock_settings.bot_mentions = "@agent,@groote"
    mock_settings.bot_approve_command = "approve"
    mock_settings.bot_improve_keywords = "improve,fix,update,refactor,change,implement,address"
    with patch("config.get_settings", return_value=mock_settings):
        yield mock_settings


@pytest.fixture(autouse=True)
def _mock_knowledge():
    empty_ctx = {"knowledge": "", "repos": [], "code_snippets": []}
    with patch(
        "services.task_routing._fetch_knowledge_context",
        new_callable=AsyncMock,
        return_value=empty_ctx,
    ):
        yield


@pytest.mark.asyncio
async def test_build_task_context_basic():
    task = {"prompt": "Fix the bug", "source": "jira"}
    prompt = await build_task_context(task)
    assert "Fix the bug" in prompt
    assert "Source: jira" in prompt


@pytest.mark.asyncio
async def test_build_task_context_with_context():
    task = {"prompt": "Fix the bug", "source": "jira"}
    context = [
        {"role": "user", "content": "Previous message 1"},
        {"role": "assistant", "content": "Previous response 1"},
        {"role": "user", "content": "Previous message 2"},
    ]

    prompt = await build_task_context(task, context)
    assert "Previous message 1" in prompt
    assert "Previous response 1" in prompt
    assert "Fix the bug" in prompt


@pytest.mark.asyncio
async def test_build_task_context_includes_event_type():
    task = {"prompt": "Analyze", "source": "github", "event_type": "issue.opened"}
    prompt = await build_task_context(task)
    assert "Event: issue.opened" in prompt


@pytest.mark.asyncio
async def test_build_task_context_includes_metadata():
    task = {
        "prompt": "Analyze ticket",
        "source": "jira",
        "issue": {"key": "KAN-6", "summary": "Fix login"},
    }
    prompt = await build_task_context(task)
    assert "KAN-6" in prompt


@pytest.mark.asyncio
async def test_build_task_context_with_knowledge():
    knowledge_ctx = {
        "knowledge": "The login module uses JWT tokens",
        "repos": ["auth-service"],
        "code_snippets": [
            {"repo": "auth-service", "file_path": "src/auth.py", "content": "def login():", "score": 0.95}
        ],
    }
    with patch(
        "services.task_routing._fetch_knowledge_context",
        new_callable=AsyncMock,
        return_value=knowledge_ctx,
    ):
        task = {"prompt": "Fix login", "source": "jira"}
        prompt = await build_task_context(task)
        assert "Knowledge Context" in prompt
        assert "JWT tokens" in prompt
        assert "Affected Repos" in prompt
        assert "auth-service" in prompt
        assert "Relevant Code" in prompt


@pytest.mark.asyncio
async def test_build_task_context_includes_bot_config():
    task = {"prompt": "Fix the bug", "source": "github", "event_type": "issue_comment"}
    prompt = await build_task_context(task)
    assert "Bot-Mentions: @agent,@groote" in prompt
    assert "Approve-Command: approve" in prompt
    assert "Improve-Keywords: improve,fix,update,refactor,change,implement,address" in prompt


@pytest.mark.asyncio
async def test_build_task_context_no_target_agent():
    task = {"prompt": "Fix the bug", "source": "github", "event_type": "issue_comment"}
    prompt = await build_task_context(task)
    assert "Target-Agent:" not in prompt


def test_detect_mcp_posting_true():
    assert detect_mcp_posting("[TOOL] Using add_jira_comment\n  body: test")
    assert detect_mcp_posting("[TOOL] Using add_issue_comment\n  body: review")
    assert detect_mcp_posting("[TOOL] Using send_slack_message\n  channel: C123")


def test_detect_mcp_posting_false():
    assert not detect_mcp_posting("General analysis output")
    assert not detect_mcp_posting(None)
    assert not detect_mcp_posting("")


class TestDuplicateContentDetection:
    def test_short_content_never_duplicate(self):
        assert _is_duplicate_content("short", "short text here") is False

    def test_identical_content_is_duplicate(self):
        text = "This is a long enough piece of text that should be detected as duplicate content"
        assert _is_duplicate_content(text, text) is True

    def test_different_content_not_duplicate(self):
        content = "The weather is nice today and the sun is shining brightly in the clear blue sky"
        prompt = "Please fix the authentication bug in the login flow for the user management system"
        assert _is_duplicate_content(content, prompt) is False

    @pytest.mark.asyncio
    async def test_duplicate_context_filtered_from_prompt(self):
        task = {"prompt": "Fix the login bug in the authentication module for user sessions", "source": "jira"}
        context = [
            {"role": "assistant", "content": "Fix the login bug in the authentication module for user sessions and handle edge cases"},
            {"role": "assistant", "content": "The database migration was completed successfully with all tables created"},
        ]
        prompt = await build_task_context(task, context)
        assert "database migration" in prompt
        assert "Previous Conversation" in prompt
