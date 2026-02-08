from webhooks.github.events import extract_task_info, should_process_event

from .fixtures import (
    github_issue_comment_payload,
    github_issue_opened_payload,
    github_pr_opened_payload,
    github_pr_review_comment_payload,
    github_push_payload,
)


class TestGitHubEventFiltering:
    def test_issue_opened_is_processed(self):
        assert should_process_event("issues", "opened") is True

    def test_issue_edited_is_processed(self):
        assert should_process_event("issues", "edited") is True

    def test_issue_labeled_is_processed(self):
        assert should_process_event("issues", "labeled") is True

    def test_issue_comment_created_is_processed(self):
        assert should_process_event("issue_comment", "created") is True

    def test_pr_opened_is_processed(self):
        assert should_process_event("pull_request", "opened") is True

    def test_pr_synchronize_is_processed(self):
        assert should_process_event("pull_request", "synchronize") is True

    def test_pr_reopened_is_processed(self):
        assert should_process_event("pull_request", "reopened") is True

    def test_pr_review_comment_is_processed(self):
        assert should_process_event("pull_request_review_comment", "created") is True

    def test_push_is_processed(self):
        assert should_process_event("push", None) is True

    def test_unsupported_event_ignored(self):
        assert should_process_event("fork", None) is False
        assert should_process_event("star", "created") is False
        assert should_process_event("watch", "started") is False

    def test_unsupported_action_ignored(self):
        assert should_process_event("issues", "closed") is False
        assert should_process_event("issues", "deleted") is False
        assert should_process_event("pull_request", "closed") is False


class TestGitHubTaskExtraction:
    def test_issue_opened_extracts_task_info(self):
        payload = github_issue_opened_payload(
            repo="myorg/myrepo",
            issue_number=123,
            title="Fix authentication bug",
            body="Users can't log in",
        )

        task_info = extract_task_info("issues", payload)

        assert task_info["source"] == "github"
        assert task_info["event_type"] == "issues"
        assert task_info["action"] == "opened"
        assert task_info["repository"]["full_name"] == "myorg/myrepo"
        assert task_info["issue"]["number"] == 123
        assert task_info["issue"]["title"] == "Fix authentication bug"

    def test_issue_comment_extracts_comment_info(self):
        payload = github_issue_comment_payload(
            repo="myorg/myrepo",
            issue_number=123,
            comment_id=456,
            body="Please fix this ASAP",
            user="commenter",
        )

        task_info = extract_task_info("issue_comment", payload)

        assert task_info["issue"]["number"] == 123
        assert task_info["comment"]["id"] == 456
        assert task_info["comment"]["body"] == "Please fix this ASAP"
        assert task_info["comment"]["user"] == "commenter"

    def test_pr_opened_extracts_pr_info(self):
        payload = github_pr_opened_payload(
            repo="myorg/myrepo",
            pr_number=42,
            title="Add new feature",
            head="feature-branch",
            base="main",
        )

        task_info = extract_task_info("pull_request", payload)

        assert task_info["source"] == "github"
        assert task_info["pull_request"]["number"] == 42
        assert task_info["pull_request"]["title"] == "Add new feature"
        assert task_info["pull_request"]["head_ref"] == "feature-branch"
        assert task_info["pull_request"]["base_ref"] == "main"

    def test_pr_review_comment_extracts_path_info(self):
        payload = github_pr_review_comment_payload(
            repo="myorg/myrepo",
            pr_number=42,
            comment_id=789,
            body="This needs refactoring",
            path="src/main.py",
            line=25,
        )

        task_info = extract_task_info("pull_request_review_comment", payload)

        assert task_info["comment"]["path"] == "src/main.py"
        assert task_info["comment"]["line"] == 25
        assert task_info["comment"]["body"] == "This needs refactoring"

    def test_push_extracts_commit_info(self):
        payload = github_push_payload(
            repo="myorg/myrepo",
            ref="refs/heads/main",
            commits=[
                {"message": "Fix bug", "id": "abc123"},
                {"message": "Add tests", "id": "def456"},
            ],
        )

        task_info = extract_task_info("push", payload)

        assert task_info["push"]["ref"] == "refs/heads/main"
        assert len(task_info["push"]["commits"]) == 2
        assert task_info["push"]["commits"][0]["message"] == "Fix bug"

    def test_repository_info_always_included(self):
        payload = github_issue_opened_payload(repo="myorg/myrepo")
        task_info = extract_task_info("issues", payload)

        assert "repository" in task_info
        assert task_info["repository"]["full_name"] == "myorg/myrepo"
        assert "clone_url" in task_info["repository"]
        assert "default_branch" in task_info["repository"]

    def test_labels_extracted_from_issue(self):
        payload = github_issue_opened_payload(
            labels=["bug", "AI-Fix", "urgent"],
        )

        task_info = extract_task_info("issues", payload)

        assert "AI-Fix" in task_info["issue"]["labels"]
        assert "bug" in task_info["issue"]["labels"]


class TestGitHubPromptField:
    def test_issue_prompt_from_title_and_body(self):
        payload = github_issue_opened_payload(
            title="Fix authentication bug",
            body="Users can't log in",
        )
        task_info = extract_task_info("issues", payload)
        assert task_info["prompt"] == "Fix authentication bug\n\nUsers can't log in"

    def test_issue_prompt_with_none_body(self):
        payload = github_issue_opened_payload(
            title="Fix authentication bug",
            body="",
        )
        payload["issue"]["body"] = None
        task_info = extract_task_info("issues", payload)
        assert task_info["prompt"] == "Fix authentication bug\n\n"

    def test_issue_comment_prompt_includes_comment(self):
        payload = github_issue_comment_payload(
            issue_number=123,
            body="Please fix this ASAP",
        )
        task_info = extract_task_info("issue_comment", payload)
        assert "Test Issue" in task_info["prompt"]
        assert "Test issue body" in task_info["prompt"]
        assert "Comment: Please fix this ASAP" in task_info["prompt"]

    def test_pr_prompt_from_title_and_body(self):
        payload = github_pr_opened_payload(
            title="Add new feature",
            body="This adds the feature",
        )
        task_info = extract_task_info("pull_request", payload)
        assert task_info["prompt"] == "Add new feature\n\nThis adds the feature"

    def test_pr_review_comment_prompt_includes_path_and_line(self):
        payload = github_pr_review_comment_payload(
            body="This needs refactoring",
            path="src/main.py",
            line=25,
        )
        task_info = extract_task_info("pull_request_review_comment", payload)
        assert "Test PR" in task_info["prompt"]
        assert "Review comment on src/main.py:25: This needs refactoring" in task_info["prompt"]

    def test_push_prompt_from_commits(self):
        payload = github_push_payload(
            ref="refs/heads/main",
            commits=[
                {"message": "Fix bug", "id": "abc123"},
                {"message": "Add tests", "id": "def456"},
            ],
        )
        task_info = extract_task_info("push", payload)
        assert task_info["prompt"] == "Push to refs/heads/main: Fix bug, Add tests"


class TestSupportedGitHubEvents:
    def test_supported_issues_actions(self):
        supported_actions = ["opened", "edited", "labeled"]
        for action in supported_actions:
            assert should_process_event("issues", action) is True

    def test_supported_issue_comment_actions(self):
        assert should_process_event("issue_comment", "created") is True

    def test_supported_pr_actions(self):
        supported_actions = ["opened", "synchronize", "reopened"]
        for action in supported_actions:
            assert should_process_event("pull_request", action) is True

    def test_supported_pr_review_comment_actions(self):
        assert should_process_event("pull_request_review_comment", "created") is True
