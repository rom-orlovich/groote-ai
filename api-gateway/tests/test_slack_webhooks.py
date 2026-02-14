from webhooks.slack.events import extract_task_info, should_process_event

from .fixtures import (
    slack_app_mention_payload,
    slack_message_payload,
)


class TestSlackEventProcessing:
    def test_app_mention_creates_task(self):
        payload = slack_app_mention_payload(
            channel="C1234567890",
            user="U1234567890",
            text="<@U0BOTUSER> help me fix this bug",
        )

        assert should_process_event(payload["event"]) is True

    def test_direct_message_creates_task(self):
        payload = slack_message_payload(
            channel="D1234567890",
            user="U1234567890",
            text="<@U0BOTUSER> Please analyze this code",
        )

        assert should_process_event(payload["event"]) is True

    def test_bot_own_message_ignored(self):
        payload = slack_message_payload(
            channel="C1234567890",
            user="",
            text="Bot response",
            bot_id="B1234567890",
            subtype="bot_message",
        )

        assert should_process_event(payload["event"]) is False

    def test_bot_message_subtype_ignored(self):
        payload = slack_message_payload(
            channel="C1234567890",
            user="",
            text="Bot response",
            subtype="bot_message",
        )

        assert should_process_event(payload["event"]) is False


class TestSlackTaskExtraction:
    def test_task_contains_slack_context(self):
        payload = slack_app_mention_payload(
            channel="C1234567890",
            user="U1234567890",
            text="<@U0BOTUSER> help",
            thread_ts="1706702300.000001",
        )

        task_info = extract_task_info(payload["event"], payload.get("team_id", ""))

        assert task_info["source"] == "slack"
        assert task_info["channel"] == "C1234567890"
        assert task_info["user"] == "U1234567890"
        assert task_info["thread_ts"] == "1706702300.000001"

    def test_message_without_thread(self):
        payload = slack_app_mention_payload(
            channel="C1234567890",
            user="U1234567890",
            text="<@U0BOTUSER> quick question",
        )

        task_info = extract_task_info(payload["event"], payload.get("team_id", ""))

        assert task_info["thread_ts"] == payload["event"]["ts"]
        assert task_info["text"] == "<@U0BOTUSER> quick question"

    def test_team_id_extracted(self):
        payload = slack_app_mention_payload(
            team="T9876543210",
        )

        task_info = extract_task_info(payload["event"], payload.get("team_id", ""))

        assert task_info["team_id"] == "T9876543210"


class TestSlackPromptField:
    def test_extracted_task_includes_prompt(self):
        payload = slack_app_mention_payload(
            text="<@U0BOTUSER> help me fix this bug",
        )
        task_info = extract_task_info(payload["event"], payload.get("team_id", ""))
        assert task_info["prompt"] == "<@U0BOTUSER> help me fix this bug"

    def test_thread_message_includes_prompt(self):
        payload = slack_app_mention_payload(
            text="<@U0BOTUSER> follow up question",
            thread_ts="1706702300.000001",
        )
        task_info = extract_task_info(payload["event"], payload.get("team_id", ""))
        assert task_info["prompt"] == "<@U0BOTUSER> follow up question"
        assert task_info["thread_ts"] == "1706702300.000001"

    def test_empty_text_gives_empty_prompt(self):
        payload = slack_message_payload(text="")
        task_info = extract_task_info(payload["event"], payload.get("team_id", ""))
        assert task_info["prompt"] == ""


class TestSlackEventTypes:
    def test_supported_slack_events(self):
        mention_payload = slack_app_mention_payload()
        message_payload = slack_message_payload(
            text="<@U0BOTUSER> test",
        )

        assert should_process_event(mention_payload["event"]) is True
        assert should_process_event(message_payload["event"]) is True
