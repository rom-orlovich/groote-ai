from webhooks.jira.events import (
    AI_AGENT_LABEL,
    extract_task_info,
    is_bot_comment,
    should_process_event,
)

from .fixtures import (
    jira_comment_created_payload,
    jira_issue_created_payload,
    jira_issue_updated_payload,
)


class TestJiraLabelFiltering:
    def test_issue_created_with_ai_fix_label_processed(self):
        payload = jira_issue_created_payload(labels=["ai-agent", "bug"])

        assert should_process_event("jira:issue_created", payload["issue"]) is True

    def test_issue_created_without_ai_fix_ignored(self):
        payload = jira_issue_created_payload(labels=["bug", "urgent"])

        assert should_process_event("jira:issue_created", payload["issue"]) is False

    def test_issue_updated_with_ai_fix_label_processed(self):
        payload = jira_issue_updated_payload(labels=["ai-agent"])

        assert should_process_event("jira:issue_updated", payload["issue"]) is True

    def test_comment_on_ai_fix_issue_processed(self):
        payload = jira_comment_created_payload(issue_key="PROJ-123")
        payload["issue"]["fields"]["labels"] = ["ai-agent"]

        assert should_process_event("comment_created", payload["issue"]) is True

    def test_comment_on_non_ai_fix_issue_ignored(self):
        payload = jira_comment_created_payload(issue_key="PROJ-123")
        payload["issue"]["fields"]["labels"] = ["bug"]

        assert should_process_event("comment_created", payload["issue"]) is False

    def test_empty_labels_ignored(self):
        payload = jira_issue_created_payload(labels=[])

        assert should_process_event("jira:issue_created", payload["issue"]) is False


class TestJiraAssigneeIsOptionalMetadata:
    def test_assignee_without_label_skipped(self):
        payload = jira_issue_created_payload(labels=[], assignee="ai-agent")

        assert should_process_event("jira:issue_created", payload["issue"]) is False

    def test_assignee_with_label_processed(self):
        payload = jira_issue_created_payload(labels=["ai-agent"], assignee="ai-agent")

        assert should_process_event("jira:issue_created", payload["issue"]) is True

    def test_no_assignee_with_label_processed(self):
        payload = jira_issue_created_payload(labels=["ai-agent"], assignee=None)

        assert should_process_event("jira:issue_created", payload["issue"]) is True

    def test_assignee_preserved_in_task_info(self):
        payload = jira_issue_created_payload(assignee="john")

        task_info = extract_task_info("jira:issue_created", payload)

        assert task_info["assignee"] == "john"


class TestJiraTaskExtraction:
    def test_issue_created_extracts_all_fields(self):
        payload = jira_issue_created_payload(
            issue_key="PROJ-123",
            summary="Fix authentication bug",
            description="Users can't log in via SSO",
            labels=["ai-agent", "bug"],
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
        assert "ai-agent" in task_info["issue"]["labels"]

    def test_comment_extracts_comment_info(self):
        payload = jira_comment_created_payload(
            issue_key="PROJ-123",
            comment_id="10001",
            body="Please prioritize this fix",
            author="reviewer",
        )
        payload["issue"]["fields"]["labels"] = ["ai-agent"]

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

    def test_jira_site_url_used_when_provided(self):
        payload = jira_issue_created_payload(issue_key="KAN-38")

        task_info = extract_task_info(
            "jira:issue_created", payload,
            jira_site_url="https://mycompany.atlassian.net",
        )

        assert task_info["jira_base_url"] == "https://mycompany.atlassian.net"

    def test_jira_site_url_falls_back_to_self_url(self):
        payload = jira_issue_created_payload(issue_key="KAN-38")
        payload["issue"]["self"] = "https://api.atlassian.com/ex/jira/abc123/rest/api/3/issue/10001"

        task_info = extract_task_info("jira:issue_created", payload)

        assert task_info["jira_base_url"] == "https://api.atlassian.com/ex/jira/abc123"


class TestJiraEventTypes:
    def test_supported_jira_events(self):
        payload_with_label = jira_issue_created_payload(labels=["ai-agent"])

        supported = ["jira:issue_created", "jira:issue_updated", "comment_created"]
        for event in supported:
            assert should_process_event(event, payload_with_label["issue"]) is True

    def test_unsupported_jira_events(self):
        payload = jira_issue_created_payload(labels=["ai-agent"])

        unsupported = [
            "jira:issue_deleted",
            "jira:worklog_created",
            "sprint:started",
        ]
        for event in unsupported:
            assert should_process_event(event, payload["issue"]) is False


class TestBotCommentDetection:
    def test_bot_detected_by_author_name(self):
        comment = {"author": {"displayName": "ai-agent"}, "body": "Hello"}
        assert is_bot_comment("comment_created", comment) is True

    def test_bot_detected_by_app_account_type(self):
        comment = {"author": {"displayName": "Jira Bot", "accountType": "app"}, "body": "x"}
        assert is_bot_comment("comment_created", comment) is True

    def test_bot_detected_by_string_body_marker(self):
        comment = {
            "author": {"displayName": "someone"},
            "body": "Here is the result\n\n_Automated by Groote AI_",
        }
        assert is_bot_comment("comment_created", comment) is True

    def test_bot_detected_by_adf_body_marker(self):
        adf_body = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": "Status: Plan Already Exists"},
                    ],
                },
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": "_Automated by Groote AI_"},
                    ],
                },
            ],
        }
        comment = {"author": {"displayName": "someone"}, "body": adf_body}
        assert is_bot_comment("comment_created", comment) is True

    def test_human_comment_not_detected_as_bot(self):
        comment = {
            "author": {"displayName": "developer", "accountType": "atlassian"},
            "body": "Please fix the login bug",
        }
        assert is_bot_comment("comment_created", comment) is False

    def test_non_comment_event_never_bot(self):
        comment = {"author": {"displayName": "ai-agent"}, "body": "test"}
        assert is_bot_comment("jira:issue_created", comment) is False

    def test_should_process_skips_bot_comment(self):
        payload = jira_comment_created_payload(
            issue_key="PROJ-1", author="ai-agent",
        )
        payload["issue"]["fields"]["labels"] = ["ai-agent"]
        assert should_process_event(
            "comment_created", payload["issue"],
            comment_data=payload["comment"],
        ) is False

    def test_should_process_skips_adf_bot_comment(self):
        adf_body = {
            "type": "doc",
            "content": [{"type": "paragraph", "content": [
                {"type": "text", "text": "## Implementation Plan"},
            ]}],
        }
        payload = jira_comment_created_payload(
            issue_key="PROJ-1", body=adf_body, author="someone",
        )
        payload["issue"]["fields"]["labels"] = ["ai-agent"]
        assert should_process_event(
            "comment_created", payload["issue"],
            comment_data=payload["comment"],
        ) is False


class TestAIAgentLabelRequirement:
    def test_label_exact_match_required(self):
        payload_correct = jira_issue_created_payload(labels=["ai-agent"])
        payload_wrong = jira_issue_created_payload(labels=["AI-Agent"])
        payload_different = jira_issue_created_payload(labels=["ai-fix"])

        assert should_process_event("jira:issue_created", payload_correct["issue"]) is True
        assert should_process_event("jira:issue_created", payload_wrong["issue"]) is False
        assert should_process_event("jira:issue_created", payload_different["issue"]) is False

    def test_label_with_other_labels(self):
        payload = jira_issue_created_payload(labels=["bug", "ai-agent", "urgent", "backend"])

        assert should_process_event("jira:issue_created", payload["issue"]) is True
        assert AI_AGENT_LABEL in payload["issue"]["fields"].get("labels", [])
