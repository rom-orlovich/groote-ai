from webhooks.jira.events import AI_FIX_LABEL, extract_task_info, should_process_event

from .fixtures import (
    jira_comment_created_payload,
    jira_issue_created_payload,
    jira_issue_updated_payload,
)


class TestJiraLabelFiltering:
    def test_issue_created_with_ai_fix_label_processed(self):
        payload = jira_issue_created_payload(labels=["AI-Fix", "bug"])

        assert should_process_event("jira:issue_created", payload["issue"]) is True

    def test_issue_created_without_ai_fix_ignored(self):
        payload = jira_issue_created_payload(labels=["bug", "urgent"])

        assert should_process_event("jira:issue_created", payload["issue"]) is False

    def test_issue_updated_with_ai_fix_label_processed(self):
        payload = jira_issue_updated_payload(labels=["AI-Fix"])

        assert should_process_event("jira:issue_updated", payload["issue"]) is True

    def test_comment_on_ai_fix_issue_processed(self):
        payload = jira_comment_created_payload(issue_key="PROJ-123")
        payload["issue"]["fields"]["labels"] = ["AI-Fix"]

        assert should_process_event("comment_created", payload["issue"]) is True

    def test_comment_on_non_ai_fix_issue_ignored(self):
        payload = jira_comment_created_payload(issue_key="PROJ-123")
        payload["issue"]["fields"]["labels"] = ["bug"]

        assert should_process_event("comment_created", payload["issue"]) is False

    def test_empty_labels_ignored(self):
        payload = jira_issue_created_payload(labels=[])

        assert should_process_event("jira:issue_created", payload["issue"]) is False


class TestJiraAssigneeTrigger:
    def test_assignee_ai_agent_triggers_processing(self):
        payload = jira_issue_created_payload(
            labels=[], assignee="ai-agent"
        )

        assert should_process_event("jira:issue_created", payload["issue"]) is True

    def test_assignee_other_user_skipped(self):
        payload = jira_issue_created_payload(
            labels=[], assignee="john"
        )

        assert should_process_event("jira:issue_created", payload["issue"]) is False

    def test_no_assignee_with_ai_fix_label_still_processed(self):
        payload = jira_issue_created_payload(
            labels=["AI-Fix"], assignee=None
        )

        assert should_process_event("jira:issue_created", payload["issue"]) is True

    def test_assignee_name_configurable(self):
        payload = jira_issue_created_payload(
            labels=[], assignee="custom-bot"
        )

        assert (
            should_process_event(
                "jira:issue_created", payload["issue"], ai_agent_name="custom-bot"
            )
            is True
        )
        assert (
            should_process_event("jira:issue_created", payload["issue"]) is False
        )

    def test_assignee_check_case_insensitive(self):
        payload = jira_issue_created_payload(
            labels=[], assignee="AI-Agent"
        )

        assert should_process_event("jira:issue_created", payload["issue"]) is True


class TestJiraTaskExtraction:
    def test_issue_created_extracts_all_fields(self):
        payload = jira_issue_created_payload(
            issue_key="PROJ-123",
            summary="Fix authentication bug",
            description="Users can't log in via SSO",
            labels=["AI-Fix", "bug"],
            project="PROJ",
            issue_type="Bug",
            priority="High",
        )

        task_info = extract_task_info("jira:issue_created", payload)

        assert task_info["source"] == "jira"
        assert task_info["event_type"] == "jira:issue_created"
        assert task_info["issue"]["key"] == "PROJ-123"
        assert task_info["issue"]["project"]["key"] == "PROJ"
        assert task_info["issue"]["summary"] == "Fix authentication bug"
        assert "AI-Fix" in task_info["issue"]["labels"]

    def test_comment_extracts_comment_info(self):
        payload = jira_comment_created_payload(
            issue_key="PROJ-123",
            comment_id="10001",
            body="Please prioritize this fix",
            author="reviewer",
        )
        payload["issue"]["fields"]["labels"] = ["AI-Fix"]

        task_info = extract_task_info("comment_created", payload)

        assert task_info["comment"]["id"] == "10001"
        assert task_info["comment"]["body"] == "Please prioritize this fix"
        assert task_info["comment"]["author"] == "reviewer"

    def test_extracted_task_includes_assignee(self):
        payload = jira_issue_created_payload(
            issue_key="PROJ-456",
            summary="Implement feature",
            assignee="ai-agent",
        )

        task_info = extract_task_info("jira:issue_created", payload)

        assert task_info["assignee"] == "ai-agent"

    def test_extracted_task_includes_prompt(self):
        payload = jira_issue_created_payload(
            issue_key="PROJ-789",
            summary="Fix login bug",
            description="SSO fails for SAML users",
        )

        task_info = extract_task_info("jira:issue_created", payload)

        assert task_info["prompt"] == "Fix login bug\n\nSSO fails for SAML users"

    def test_prompt_includes_comment_body(self):
        payload = jira_comment_created_payload(
            issue_key="PROJ-789",
            body="Also check OAuth flow",
        )

        task_info = extract_task_info("comment_created", payload)

        assert "Also check OAuth flow" in task_info["prompt"]

    def test_prompt_without_description(self):
        payload = jira_issue_created_payload(
            summary="Quick fix needed",
            description="",
        )

        task_info = extract_task_info("jira:issue_created", payload)

        assert task_info["prompt"] == "Quick fix needed"

    def test_no_assignee_returns_none(self):
        payload = jira_issue_created_payload(assignee=None)

        task_info = extract_task_info("jira:issue_created", payload)

        assert task_info["assignee"] is None


class TestJiraEventTypes:
    def test_supported_jira_events(self):
        payload_with_label = jira_issue_created_payload(labels=["AI-Fix"])

        supported = ["jira:issue_created", "jira:issue_updated", "comment_created"]
        for event in supported:
            assert should_process_event(event, payload_with_label["issue"]) is True

    def test_unsupported_jira_events(self):
        payload = jira_issue_created_payload(labels=["AI-Fix"])

        unsupported = [
            "jira:issue_deleted",
            "jira:worklog_created",
            "sprint:started",
        ]
        for event in unsupported:
            assert should_process_event(event, payload["issue"]) is False


class TestAIFixLabelRequirement:
    def test_ai_fix_label_case_sensitive(self):
        payload_correct = jira_issue_created_payload(labels=["AI-Fix"])
        payload_wrong_case = jira_issue_created_payload(labels=["ai-fix"])
        payload_different = jira_issue_created_payload(labels=["AIFix"])

        assert should_process_event("jira:issue_created", payload_correct["issue"]) is True
        assert should_process_event("jira:issue_created", payload_wrong_case["issue"]) is False
        assert should_process_event("jira:issue_created", payload_different["issue"]) is False

    def test_ai_fix_with_other_labels(self):
        payload = jira_issue_created_payload(labels=["bug", "AI-Fix", "urgent", "backend"])

        assert should_process_event("jira:issue_created", payload["issue"]) is True
        assert AI_FIX_LABEL in payload["issue"]["fields"].get("labels", [])
