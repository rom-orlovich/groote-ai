from unittest.mock import AsyncMock, patch

import pytest
from services.conversation_bridge import (
    build_conversation_title,
    build_flow_id,
    fetch_conversation_context,
    get_or_create_flow_conversation,
)


def test_build_flow_id_jira():
    task = {"source": "jira", "issue": {"key": "KAN-6", "summary": "Fix bug"}}
    assert build_flow_id(task) == "jira:KAN-6"


def test_build_flow_id_github_pr():
    task = {
        "source": "github",
        "repository": {"full_name": "owner/repo"},
        "issue": {"number": 42, "title": "Add feature"},
    }
    assert build_flow_id(task) == "github:owner/repo#42"


def test_build_flow_id_slack():
    task = {
        "source": "slack",
        "channel": "C12345",
        "thread_ts": "1234567890.123456",
    }
    assert build_flow_id(task) == "slack:C12345:1234567890.123456"


def test_build_conversation_title_jira():
    task = {
        "source": "jira",
        "issue": {"key": "KAN-6", "summary": "Fix login bug"},
    }
    title = build_conversation_title(task)
    assert "Jira: KAN-6" in title
    assert "Fix login bug" in title


def test_build_conversation_title_github_issue():
    task = {
        "source": "github",
        "repository": {"full_name": "owner/repo"},
        "issue": {"number": 42, "title": "Add feature"},
    }
    title = build_conversation_title(task)
    assert "GitHub: repo#42" in title
    assert "Add feature" in title


def test_build_conversation_title_slack():
    task = {
        "source": "slack",
        "channel": "general",
        "text": "How do I configure OAuth?",
    }
    title = build_conversation_title(task)
    assert "Slack: #general" in title


@pytest.mark.asyncio
async def test_get_or_create_flow_conversation_existing():
    task = {
        "source": "jira",
        "issue": {"key": "KAN-6", "summary": "Fix bug"},
    }

    with patch(
        "services.conversation_bridge.httpx.AsyncClient"
    ) as mock_client:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json = lambda: {"conversation_id": "conv-123"}
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=mock_response
        )

        conv_id = await get_or_create_flow_conversation(
            "http://dashboard:5000", task
        )
        assert conv_id == "conv-123"


@pytest.mark.asyncio
async def test_get_or_create_flow_conversation_new():
    task = {
        "source": "jira",
        "issue": {"key": "KAN-7", "summary": "New bug"},
    }

    with patch(
        "services.conversation_bridge.httpx.AsyncClient"
    ) as mock_client:
        mock_get_response = AsyncMock()
        mock_get_response.status_code = 404

        mock_post_response = AsyncMock()
        mock_post_response.status_code = 201
        mock_post_response.json = lambda: {"conversation_id": "conv-456"}
        mock_post_response.raise_for_status = lambda: None

        mock_client_instance = (
            mock_client.return_value.__aenter__.return_value
        )
        mock_client_instance.get = AsyncMock(return_value=mock_get_response)
        mock_client_instance.post = AsyncMock(return_value=mock_post_response)

        conv_id = await get_or_create_flow_conversation(
            "http://dashboard:5000", task
        )
        assert conv_id == "conv-456"


@pytest.mark.asyncio
async def test_fetch_conversation_context():
    with patch(
        "services.conversation_bridge.httpx.AsyncClient"
    ) as mock_client:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json = lambda: [
            {"role": "user", "content": "Message 1"},
            {"role": "assistant", "content": "Response 1"},
            {"role": "user", "content": "Message 2"},
        ]
        mock_response.raise_for_status = lambda: None
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=mock_response
        )

        messages = await fetch_conversation_context(
            "http://dashboard:5000", "conv-123", limit=5
        )
        assert len(messages) == 3
        assert messages[0]["content"] == "Message 1"
