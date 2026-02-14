import pytest
from unittest.mock import AsyncMock, patch

from services.task_routing import (
    _is_duplicate_content,
    _is_plan_approval,
    build_task_context,
    detect_mcp_posting,
    resolve_target_agent,
)


@pytest.fixture(autouse=True)
def _mock_knowledge(monkeypatch):
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


def test_detect_mcp_posting_true():
    assert detect_mcp_posting("[TOOL] Using add_jira_comment\n  body: test")
    assert detect_mcp_posting("[TOOL] Using add_issue_comment\n  body: review")
    assert detect_mcp_posting("[TOOL] Using send_slack_message\n  channel: C123")


def test_detect_mcp_posting_false():
    assert not detect_mcp_posting("General analysis output")
    assert not detect_mcp_posting(None)
    assert not detect_mcp_posting("")


class TestPlanApprovalRouting:
    def test_plan_approval_routes_to_pr_review(self):
        task = {
            "issue": {
                "title": "[PLAN] Implement feature X",
                "pull_request": {"url": "https://api.github.com/repos/test/pulls/1"},
            },
            "comment": {"body": "@agent approve this plan"},
        }
        assert _is_plan_approval(task) is True
        assert resolve_target_agent("github", "issue_comment", task) == "github-pr-review"

    def test_non_plan_pr_comment_not_detected(self):
        task = {
            "issue": {
                "title": "Regular PR title",
                "pull_request": {"url": "https://api.github.com/repos/test/pulls/1"},
            },
            "comment": {"body": "looks good"},
        }
        assert _is_plan_approval(task) is False

    def test_plan_without_approve_keyword_not_detected(self):
        task = {
            "issue": {
                "title": "[PLAN] Implement feature X",
                "pull_request": {"url": "https://api.github.com/repos/test/pulls/1"},
            },
            "comment": {"body": "needs changes"},
        }
        assert _is_plan_approval(task) is False

    def test_plan_on_issue_not_pr_not_detected(self):
        task = {
            "issue": {"title": "[PLAN] Implement feature X"},
            "comment": {"body": "@agent approve"},
        }
        assert _is_plan_approval(task) is False

    def test_pr_improve_request_via_issue_pull_request(self):
        task = {
            "issue": {
                "title": "Fix auth flow",
                "pull_request": {"url": "https://api.github.com/repos/test/pulls/1"},
            },
            "prompt": "Please fix the error handling",
        }
        assert resolve_target_agent("github", "issue_comment", task) == "github-pr-review"


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
