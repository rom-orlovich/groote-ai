import pytest
from services.task_routing import build_enriched_prompt


def test_build_enriched_prompt_basic():
    task = {"prompt": "Fix the bug", "source": "jira"}
    prompt = build_enriched_prompt(task)
    assert "Fix the bug" in prompt


def test_build_enriched_prompt_with_context():
    task = {"prompt": "Fix the bug", "source": "jira"}
    context = [
        {"role": "user", "content": "Previous message 1"},
        {"role": "assistant", "content": "Previous response 1"},
        {"role": "user", "content": "Previous message 2"},
    ]

    prompt = build_enriched_prompt(task, context)
    assert "Previous message 1" in prompt
    assert "Previous response 1" in prompt
    assert "Fix the bug" in prompt


def test_build_enriched_prompt_jira_instructions():
    task = {"prompt": "Analyze ticket", "source": "jira"}
    prompt = build_enriched_prompt(task)
    assert "jira:add_jira_comment" in prompt


def test_build_enriched_prompt_github_instructions():
    task = {"prompt": "Review PR", "source": "github"}
    prompt = build_enriched_prompt(task)
    assert "github:add_issue_comment" in prompt


def test_build_enriched_prompt_slack_instructions():
    task = {"prompt": "Answer question", "source": "slack"}
    prompt = build_enriched_prompt(task)
    assert "slack:send_slack_message" in prompt
