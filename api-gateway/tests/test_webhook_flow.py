import hashlib
import hmac
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

import pytest

from .fixtures import (
    github_issue_comment_payload,
    github_issue_opened_payload,
    github_pr_opened_payload,
    jira_issue_created_payload,
    slack_app_mention_payload,
    slack_message_payload,
)


@dataclass
class Task:
    task_id: str
    source: str
    source_metadata: dict[str, Any]
    input_message: str
    status: str = "queued"
    priority: str = "normal"
    agent_type: str = "default"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class WebhookResponse:
    status_code: int
    body: dict[str, Any]
    task_id: str | None = None


class TaskQueue:
    def __init__(self):
        self.tasks: list[Task] = []
        self._task_counter = 0

    async def enqueue(self, task: Task) -> str:
        self._task_counter += 1
        task.task_id = f"task-{self._task_counter}"
        self.tasks.append(task)
        return task.task_id

    async def get_task(self, task_id: str) -> Task | None:
        for task in self.tasks:
            if task.task_id == task_id:
                return task
        return None

    def clear(self):
        self.tasks = []
        self._task_counter = 0


class LoopPreventionStore:
    def __init__(self):
        self.posted_comments: set[str] = set()

    async def mark_as_posted(self, comment_id: str) -> None:
        self.posted_comments.add(comment_id)

    async def was_posted_by_agent(self, comment_id: str) -> bool:
        return comment_id in self.posted_comments

    def clear(self):
        self.posted_comments = set()


class WebhookHandler:
    GITHUB_SUPPORTED_EVENTS = {
        "issues": ["opened", "edited", "labeled"],
        "issue_comment": ["created"],
        "pull_request": ["opened", "synchronize", "reopened"],
        "pull_request_review_comment": ["created"],
        "push": [None],
    }

    def __init__(
        self,
        task_queue: TaskQueue,
        loop_prevention: LoopPreventionStore,
        github_secret: str = "test-secret",
        jira_secret: str = "test-jira-secret",
        slack_signing_secret: str = "test-slack-secret",
        bot_user_id: str = "bot-user-123",
    ):
        self.task_queue = task_queue
        self.loop_prevention = loop_prevention
        self.github_secret = github_secret
        self.jira_secret = jira_secret
        self.slack_signing_secret = slack_signing_secret
        self.bot_user_id = bot_user_id

    def _verify_github_signature(self, payload: str, signature: str) -> bool:
        expected = (
            "sha256="
            + hmac.new(
                self.github_secret.encode(),
                payload.encode(),
                hashlib.sha256,
            ).hexdigest()
        )
        return hmac.compare_digest(expected, signature)

    def _verify_jira_signature(self, payload: str, signature: str) -> bool:
        expected = hmac.new(
            self.jira_secret.encode(),
            payload.encode(),
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, signature)

    async def handle_github(
        self,
        payload: dict,
        signature: str,
        event_type: str,
    ) -> WebhookResponse:
        payload_str = json.dumps(payload)

        if not self._verify_github_signature(payload_str, signature):
            return WebhookResponse(
                status_code=401,
                body={"error": "Invalid signature"},
            )

        action = payload.get("action")
        supported_actions = self.GITHUB_SUPPORTED_EVENTS.get(event_type, [])

        if action not in supported_actions and None not in supported_actions:
            return WebhookResponse(
                status_code=200,
                body={"action": "ignored", "reason": "unsupported event"},
            )

        if event_type == "issue_comment":
            comment_id = str(payload.get("comment", {}).get("id", ""))
            if await self.loop_prevention.was_posted_by_agent(comment_id):
                return WebhookResponse(
                    status_code=200,
                    body={"action": "ignored", "reason": "loop prevention"},
                )

            if payload.get("comment", {}).get("user", {}).get("type") == "Bot":
                return WebhookResponse(
                    status_code=200,
                    body={"action": "ignored", "reason": "bot comment"},
                )

        repo = payload.get("repository", {}).get("full_name", "")
        issue = payload.get("issue", {})
        pr = payload.get("pull_request", {})
        comment = payload.get("comment", {})

        if issue:
            input_message = f"GitHub issue #{issue.get('number')}: {issue.get('title')}\n\n{issue.get('body', '')}"
        elif pr:
            input_message = (
                f"GitHub PR #{pr.get('number')}: {pr.get('title')}\n\n{pr.get('body', '')}"
            )
        else:
            input_message = f"GitHub {event_type} event on {repo}"

        if comment:
            input_message += f"\n\nComment: {comment.get('body', '')}"

        task = Task(
            task_id="",
            source="webhook",
            source_metadata={
                "provider": "github",
                "event_type": event_type,
                "action": action,
                "repo": repo,
                "issue_number": issue.get("number") if issue else None,
                "pr_number": pr.get("number") if pr else None,
            },
            input_message=input_message,
            agent_type="github-issue-handler" if issue else "github-pr-review",
        )

        task_id = await self.task_queue.enqueue(task)

        return WebhookResponse(
            status_code=202,
            body={"action": "accepted", "task_id": task_id},
            task_id=task_id,
        )

    async def handle_jira(
        self,
        payload: dict,
        signature: str,
    ) -> WebhookResponse:
        payload_str = json.dumps(payload)

        if not self._verify_jira_signature(payload_str, signature):
            return WebhookResponse(
                status_code=401,
                body={"error": "Invalid signature"},
            )

        event = payload.get("webhookEvent", "")
        issue = payload.get("issue", {})
        fields = issue.get("fields", {})
        labels = [
            lbl.get("name", lbl) if isinstance(lbl, dict) else lbl
            for lbl in fields.get("labels", [])
        ]

        assignee = fields.get("assignee") or {}
        assignee_name = assignee.get("displayName", "").lower()
        has_ai_label = "AI-Fix" in labels
        has_ai_assignee = assignee_name == "ai-agent"

        if not has_ai_label and not has_ai_assignee:
            return WebhookResponse(
                status_code=200,
                body={
                    "action": "ignored",
                    "reason": "missing AI-Fix label or ai-agent assignee",
                },
            )

        issue_key = issue.get("key", "")
        summary = fields.get("summary", "")
        description = fields.get("description", "")

        task = Task(
            task_id="",
            source="webhook",
            source_metadata={
                "provider": "jira",
                "event_type": event,
                "issue_key": issue_key,
                "project": issue_key.split("-")[0] if issue_key else "",
            },
            input_message=f"Jira {issue_key}: {summary}\n\n{description}",
            agent_type="jira-code-plan",
        )

        task_id = await self.task_queue.enqueue(task)

        return WebhookResponse(
            status_code=202,
            body={"action": "accepted", "task_id": task_id},
            task_id=task_id,
        )

    async def handle_slack(
        self,
        payload: dict,
    ) -> WebhookResponse:
        event = payload.get("event", {})
        event_type = event.get("type", "")
        user = event.get("user", "")
        bot_id = event.get("bot_id")

        if bot_id or user == self.bot_user_id:
            return WebhookResponse(
                status_code=200,
                body={"action": "ignored", "reason": "bot message"},
            )

        text = event.get("text", "")
        channel = event.get("channel", "")
        thread_ts = event.get("thread_ts")

        task = Task(
            task_id="",
            source="webhook",
            source_metadata={
                "provider": "slack",
                "event_type": event_type,
                "channel": channel,
                "thread_ts": thread_ts,
                "user": user,
            },
            input_message=text,
            agent_type="slack-inquiry",
        )

        task_id = await self.task_queue.enqueue(task)

        return WebhookResponse(
            status_code=202,
            body={"action": "accepted", "task_id": task_id},
            task_id=task_id,
        )


@pytest.fixture
def task_queue():
    queue = TaskQueue()
    yield queue
    queue.clear()


@pytest.fixture
def loop_prevention():
    store = LoopPreventionStore()
    yield store
    store.clear()


@pytest.fixture
def webhook_handler(task_queue, loop_prevention):
    return WebhookHandler(task_queue, loop_prevention)


def generate_github_signature(payload: dict, secret: str = "test-secret") -> str:
    payload_str = json.dumps(payload)
    return (
        "sha256="
        + hmac.new(
            secret.encode(),
            payload_str.encode(),
            hashlib.sha256,
        ).hexdigest()
    )


def generate_jira_signature(payload: dict, secret: str = "test-jira-secret") -> str:
    payload_str = json.dumps(payload)
    return hmac.new(
        secret.encode(),
        payload_str.encode(),
        hashlib.sha256,
    ).hexdigest()


class TestGitHubWebhookFlow:
    @pytest.mark.asyncio
    async def test_github_issue_to_task_flow(self, webhook_handler, task_queue):
        payload = github_issue_opened_payload(
            repo="myorg/myrepo",
            issue_number=123,
            title="Authentication fails for SSO users",
            body="When logging in via SSO, users see a 500 error...",
        )
        signature = generate_github_signature(payload)

        response = await webhook_handler.handle_github(payload, signature, event_type="issues")

        assert response.status_code == 202
        assert response.task_id is not None

        task = await task_queue.get_task(response.task_id)
        assert task is not None
        assert task.source == "webhook"
        assert task.source_metadata["provider"] == "github"
        assert task.source_metadata["repo"] == "myorg/myrepo"
        assert task.source_metadata["issue_number"] == 123
        assert "Authentication fails" in task.input_message

    @pytest.mark.asyncio
    async def test_github_issue_comment_flow(self, webhook_handler, task_queue):
        payload = github_issue_comment_payload(
            repo="myorg/myrepo",
            issue_number=123,
            comment_id=456,
            body="Can you fix this ASAP?",
            user="developer",
        )
        signature = generate_github_signature(payload)

        response = await webhook_handler.handle_github(
            payload, signature, event_type="issue_comment"
        )

        assert response.status_code == 202
        task = await task_queue.get_task(response.task_id)
        assert "Can you fix this ASAP?" in task.input_message

    @pytest.mark.asyncio
    async def test_github_pr_opened_flow(self, webhook_handler, task_queue):
        payload = github_pr_opened_payload(
            repo="myorg/myrepo",
            pr_number=42,
            title="Add new feature",
            head="feature-branch",
            base="main",
        )
        signature = generate_github_signature(payload)

        response = await webhook_handler.handle_github(
            payload, signature, event_type="pull_request"
        )

        assert response.status_code == 202
        task = await task_queue.get_task(response.task_id)
        assert task.agent_type == "github-pr-review"
        assert task.source_metadata["pr_number"] == 42

    @pytest.mark.asyncio
    async def test_github_invalid_signature_rejected(self, webhook_handler, task_queue):
        payload = github_issue_opened_payload(repo="myorg/myrepo")
        invalid_signature = "sha256=invalid"

        response = await webhook_handler.handle_github(
            payload, invalid_signature, event_type="issues"
        )

        assert response.status_code == 401
        assert len(task_queue.tasks) == 0

    @pytest.mark.asyncio
    async def test_github_unsupported_event_ignored(self, webhook_handler, task_queue):
        payload = {"action": "deleted", "repository": {"full_name": "myorg/myrepo"}}
        signature = generate_github_signature(payload)

        response = await webhook_handler.handle_github(payload, signature, event_type="issues")

        assert response.status_code == 200
        assert response.body["action"] == "ignored"
        assert len(task_queue.tasks) == 0

    @pytest.mark.asyncio
    async def test_github_bot_comment_ignored(self, webhook_handler, task_queue):
        payload = {
            "action": "created",
            "comment": {
                "id": 789,
                "body": "Automated response",
                "user": {"login": "github-bot", "type": "Bot"},
            },
            "issue": {"number": 123, "title": "Test"},
            "repository": {"full_name": "myorg/myrepo"},
        }
        signature = generate_github_signature(payload)

        response = await webhook_handler.handle_github(
            payload, signature, event_type="issue_comment"
        )

        assert response.status_code == 200
        assert response.body["reason"] == "bot comment"
        assert len(task_queue.tasks) == 0


class TestJiraWebhookFlow:
    @pytest.mark.asyncio
    async def test_jira_ai_fix_label_creates_task(self, webhook_handler, task_queue):
        payload = jira_issue_created_payload(
            issue_key="PROJ-123",
            summary="Fix authentication bug",
            labels=["bug", "AI-Fix"],
        )
        signature = generate_jira_signature(payload)

        response = await webhook_handler.handle_jira(payload, signature)

        assert response.status_code == 202
        task = await task_queue.get_task(response.task_id)
        assert task.source_metadata["provider"] == "jira"
        assert task.source_metadata["issue_key"] == "PROJ-123"
        assert task.agent_type == "jira-code-plan"

    @pytest.mark.asyncio
    async def test_jira_without_ai_fix_ignored(self, webhook_handler, task_queue):
        payload = jira_issue_created_payload(
            issue_key="PROJ-123",
            labels=["bug", "urgent"],
        )
        payload["issue"]["fields"]["assignee"] = None
        signature = generate_jira_signature(payload)

        response = await webhook_handler.handle_jira(payload, signature)

        assert response.status_code == 200
        assert response.body["action"] == "ignored"
        assert response.body["reason"] == "missing AI-Fix label or ai-agent assignee"
        assert len(task_queue.tasks) == 0

    @pytest.mark.asyncio
    async def test_jira_invalid_signature_rejected(self, webhook_handler, task_queue):
        payload = jira_issue_created_payload(labels=["AI-Fix"])

        response = await webhook_handler.handle_jira(payload, "invalid-signature")

        assert response.status_code == 401
        assert len(task_queue.tasks) == 0

    @pytest.mark.asyncio
    async def test_jira_metadata_preserved(self, webhook_handler, task_queue):
        payload = jira_issue_created_payload(
            issue_key="PROJ-456",
            summary="Implement new API endpoint",
            description="Create a REST endpoint for user preferences",
            labels=["AI-Fix", "feature"],
        )
        signature = generate_jira_signature(payload)

        response = await webhook_handler.handle_jira(payload, signature)

        task = await task_queue.get_task(response.task_id)
        assert task.source_metadata["issue_key"] == "PROJ-456"
        assert task.source_metadata["project"] == "PROJ"
        assert "Implement new API endpoint" in task.input_message
        assert "REST endpoint" in task.input_message

    @pytest.mark.asyncio
    async def test_jira_assignee_ai_agent_creates_task(self, webhook_handler, task_queue):
        payload = jira_issue_created_payload(
            issue_key="PROJ-123",
            summary="Fix bug",
            labels=["bug"],
        )
        payload["issue"]["fields"]["assignee"] = {
            "displayName": "ai-agent",
            "emailAddress": "ai@example.com",
        }
        signature = generate_jira_signature(payload)

        response = await webhook_handler.handle_jira(payload, signature)

        assert response.status_code == 202
        assert response.task_id is not None
        task = await task_queue.get_task(response.task_id)
        assert task is not None
        assert task.source_metadata["provider"] == "jira"
        assert task.source_metadata["issue_key"] == "PROJ-123"

    @pytest.mark.asyncio
    async def test_jira_assignee_plus_label_both_work(self, webhook_handler, task_queue):
        payload = jira_issue_created_payload(
            issue_key="PROJ-456",
            summary="Both triggers",
            labels=["AI-Fix"],
        )
        payload["issue"]["fields"]["assignee"] = {
            "displayName": "ai-agent",
            "emailAddress": "ai@example.com",
        }
        signature = generate_jira_signature(payload)

        response = await webhook_handler.handle_jira(payload, signature)

        assert response.status_code == 202
        task = await task_queue.get_task(response.task_id)
        assert task is not None
        assert task.agent_type == "jira-code-plan"


class TestSlackWebhookFlow:
    @pytest.mark.asyncio
    async def test_slack_app_mention_creates_task(self, webhook_handler, task_queue):
        payload = slack_app_mention_payload(
            text="<@U123BOT> please help debug this issue",
            user="U456USER",
            channel="C789CHANNEL",
        )

        response = await webhook_handler.handle_slack(payload)

        assert response.status_code == 202
        task = await task_queue.get_task(response.task_id)
        assert task.source_metadata["provider"] == "slack"
        assert task.source_metadata["channel"] == "C789CHANNEL"
        assert task.agent_type == "slack-inquiry"

    @pytest.mark.asyncio
    async def test_slack_bot_message_ignored(self, webhook_handler, task_queue):
        payload = {
            "event": {
                "type": "message",
                "text": "I processed your request",
                "bot_id": "B123BOT",
                "channel": "C789CHANNEL",
            }
        }

        response = await webhook_handler.handle_slack(payload)

        assert response.status_code == 200
        assert response.body["reason"] == "bot message"
        assert len(task_queue.tasks) == 0

    @pytest.mark.asyncio
    async def test_slack_thread_context_preserved(self, webhook_handler, task_queue):
        payload = slack_message_payload(
            text="Can you explain this code?",
            user="U456USER",
            channel="C789CHANNEL",
            thread_ts="1234567890.123456",
        )

        response = await webhook_handler.handle_slack(payload)

        task = await task_queue.get_task(response.task_id)
        assert task.source_metadata["thread_ts"] == "1234567890.123456"
        assert task.source_metadata["user"] == "U456USER"


class TestLoopPreventionFlow:
    @pytest.mark.asyncio
    async def test_agent_posted_comment_ignored(self, webhook_handler, task_queue, loop_prevention):
        await loop_prevention.mark_as_posted("456")

        payload = github_issue_comment_payload(
            repo="myorg/myrepo",
            issue_number=123,
            comment_id=456,
            body="I've analyzed this issue...",
            user="groote-ai",
        )
        signature = generate_github_signature(payload)

        response = await webhook_handler.handle_github(
            payload, signature, event_type="issue_comment"
        )

        assert response.status_code == 200
        assert response.body["reason"] == "loop prevention"
        assert len(task_queue.tasks) == 0

    @pytest.mark.asyncio
    async def test_different_comment_processed(self, webhook_handler, task_queue, loop_prevention):
        await loop_prevention.mark_as_posted("comment-456")

        payload = github_issue_comment_payload(
            repo="myorg/myrepo",
            issue_number=123,
            comment_id=789,
            body="A different comment",
            user="developer",
        )
        signature = generate_github_signature(payload)

        response = await webhook_handler.handle_github(
            payload, signature, event_type="issue_comment"
        )

        assert response.status_code == 202
        assert len(task_queue.tasks) == 1


class TestWebhookToTaskRouting:
    @pytest.mark.asyncio
    async def test_github_issue_routes_to_issue_handler(self, webhook_handler, task_queue):
        payload = github_issue_opened_payload(repo="myorg/myrepo")
        signature = generate_github_signature(payload)

        await webhook_handler.handle_github(payload, signature, event_type="issues")

        task = task_queue.tasks[0]
        assert task.agent_type == "github-issue-handler"

    @pytest.mark.asyncio
    async def test_github_pr_routes_to_pr_review(self, webhook_handler, task_queue):
        payload = github_pr_opened_payload(repo="myorg/myrepo")
        signature = generate_github_signature(payload)

        await webhook_handler.handle_github(payload, signature, event_type="pull_request")

        task = task_queue.tasks[0]
        assert task.agent_type == "github-pr-review"

    @pytest.mark.asyncio
    async def test_jira_routes_to_code_plan(self, webhook_handler, task_queue):
        payload = jira_issue_created_payload(labels=["AI-Fix"])
        signature = generate_jira_signature(payload)

        await webhook_handler.handle_jira(payload, signature)

        task = task_queue.tasks[0]
        assert task.agent_type == "jira-code-plan"

    @pytest.mark.asyncio
    async def test_slack_routes_to_inquiry(self, webhook_handler, task_queue):
        payload = slack_app_mention_payload(user="U123")

        await webhook_handler.handle_slack(payload)

        task = task_queue.tasks[0]
        assert task.agent_type == "slack-inquiry"


class TestWebhookTaskShape:
    @pytest.mark.asyncio
    async def test_all_webhooks_produce_input_message(self, webhook_handler, task_queue):
        github_payload = github_issue_opened_payload(
            repo="myorg/myrepo",
            title="Test issue",
            body="Issue body",
        )
        github_sig = generate_github_signature(github_payload)
        await webhook_handler.handle_github(github_payload, github_sig, event_type="issues")

        jira_payload = jira_issue_created_payload(
            issue_key="PROJ-1",
            summary="Jira task",
            labels=["AI-Fix"],
        )
        jira_sig = generate_jira_signature(jira_payload)
        await webhook_handler.handle_jira(jira_payload, jira_sig)

        slack_payload = slack_app_mention_payload(
            text="Help me debug",
            user="U123",
        )
        await webhook_handler.handle_slack(slack_payload)

        assert len(task_queue.tasks) == 3
        for task in task_queue.tasks:
            assert task.input_message, (
                f"Task from {task.source_metadata['provider']} has empty input_message"
            )

    @pytest.mark.asyncio
    async def test_task_shape_matches_agent_engine_expectations(self, webhook_handler, task_queue):
        github_payload = github_issue_opened_payload(repo="myorg/myrepo")
        github_sig = generate_github_signature(github_payload)
        await webhook_handler.handle_github(github_payload, github_sig, event_type="issues")

        jira_payload = jira_issue_created_payload(labels=["AI-Fix"])
        jira_sig = generate_jira_signature(jira_payload)
        await webhook_handler.handle_jira(jira_payload, jira_sig)

        slack_payload = slack_app_mention_payload(user="U123", text="hello")
        await webhook_handler.handle_slack(slack_payload)

        for task in task_queue.tasks:
            assert task.source == "webhook"
            assert "provider" in task.source_metadata
            assert "event_type" in task.source_metadata
            assert task.input_message
            assert task.agent_type
