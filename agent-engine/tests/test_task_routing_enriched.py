from services.task_routing import build_task_context, detect_mcp_posting


def test_build_task_context_basic():
    task = {"prompt": "Fix the bug", "source": "jira"}
    prompt = build_task_context(task)
    assert "Fix the bug" in prompt
    assert "Source: jira" in prompt


def test_build_task_context_with_context():
    task = {"prompt": "Fix the bug", "source": "jira"}
    context = [
        {"role": "user", "content": "Previous message 1"},
        {"role": "assistant", "content": "Previous response 1"},
        {"role": "user", "content": "Previous message 2"},
    ]

    prompt = build_task_context(task, context)
    assert "Previous message 1" in prompt
    assert "Previous response 1" in prompt
    assert "Fix the bug" in prompt


def test_build_task_context_includes_event_type():
    task = {"prompt": "Analyze", "source": "github", "event_type": "issue.opened"}
    prompt = build_task_context(task)
    assert "Event: issue.opened" in prompt


def test_build_task_context_includes_metadata():
    task = {
        "prompt": "Analyze ticket",
        "source": "jira",
        "issue": {"key": "KAN-6", "summary": "Fix login"},
    }
    prompt = build_task_context(task)
    assert "KAN-6" in prompt


def test_detect_mcp_posting_true():
    assert detect_mcp_posting("[TOOL] Using add_jira_comment\n  body: test")
    assert detect_mcp_posting("[TOOL] Using add_issue_comment\n  body: review")
    assert detect_mcp_posting("[TOOL] Using send_slack_message\n  channel: C123")


def test_detect_mcp_posting_false():
    assert not detect_mcp_posting("General analysis output")
    assert not detect_mcp_posting(None)
    assert not detect_mcp_posting("")
