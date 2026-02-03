# api-gateway - Features

Auto-generated on 2026-02-03

## Overview

Central webhook reception and routing service for groote-ai system. Receives webhooks from GitHub, Jira, Slack, and Sentry, validates signatures, extracts routing metadata, and enqueues tasks to Redis.

## Features

### Webhook Reception [TESTED]

HTTP POST from external services

**Related Tests:**
- `test_github_issue_to_task_flow`
- `test_github_issue_comment_flow`
- `test_github_pr_opened_flow`
- `test_jira_ai_fix_label_creates_task`
- `test_slack_app_mention_creates_task`
- `test_sentry_new_error_creates_task`

### Security Validation [TESTED]

HMAC signature verification (middleware)

**Related Tests:**
- `test_github_invalid_signature_rejected`
- `test_jira_invalid_signature_rejected`

### Event Parsing [TESTED]

Extract metadata (repo, PR, ticket key)

**Related Tests:**
- `test_issue_opened_extracts_task_info`
- `test_issue_comment_extracts_comment_info`
- `test_pr_opened_extracts_pr_info`
- `test_pr_review_comment_extracts_path_info`
- `test_push_extracts_commit_info`
- `test_repository_info_always_included`
- `test_labels_extracted_from_issue`
- `test_jira_metadata_preserved`

### Task Creation [TESTED]

Generate task_id, create task metadata

**Related Tests:**
- `test_github_issue_to_task_flow`
- `test_jira_ai_fix_label_creates_task`
- `test_slack_app_mention_creates_task`
- `test_sentry_new_error_creates_task`
- `test_jira_metadata_preserved`

### Queue Management [TESTED]

Enqueue to Redis for agent-engine

**Related Tests:**
- `test_github_issue_to_task_flow`
- `test_jira_ai_fix_label_creates_task`
- `test_slack_app_mention_creates_task`

### Immediate Response [TESTED]

Return 202/200 within 50ms

**Related Tests:**
- `test_github_unsupported_event_ignored`
- `test_jira_without_ai_fix_ignored`
- `test_sentry_resolved_ignored`

### POST /webhooks/github [TESTED]

GitHub events (PR, issues, comments)

**Related Tests:**
- `test_github_issue_to_task_flow`
- `test_github_issue_comment_flow`
- `test_github_pr_opened_flow`
- `test_github_invalid_signature_rejected`
- `test_github_unsupported_event_ignored`
- `test_github_bot_comment_ignored`
- `test_github_issue_routes_to_issue_handler`
- `test_github_pr_routes_to_pr_review`

### POST /webhooks/jira [TESTED]

Jira events (ticket assignment, status)

**Related Tests:**
- `test_jira_ai_fix_label_creates_task`
- `test_jira_without_ai_fix_ignored`
- `test_jira_invalid_signature_rejected`
- `test_jira_metadata_preserved`
- `test_jira_routes_to_code_plan`

### POST /webhooks/slack [TESTED]

Slack events (mentions, commands)

**Related Tests:**
- `test_slack_app_mention_creates_task`
- `test_slack_bot_message_ignored`
- `test_slack_thread_context_preserved`
- `test_slack_routes_to_inquiry`

### POST /webhooks/sentry [TESTED]

Sentry alerts

**Related Tests:**
- `test_sentry_new_error_creates_task`
- `test_sentry_regression_high_priority`
- `test_sentry_resolved_ignored`
- `test_sentry_routes_to_error_handler`

### GET /health [NEEDS TESTS]

Health check endpoint

### Loop Prevention [TESTED]

Redis tracking of posted comment IDs, bot username detection

**Related Tests:**
- `test_agent_posted_comment_ignored`
- `test_different_comment_processed`
- `test_github_bot_comment_ignored`
- `test_slack_bot_message_ignored`

### Event Filtering [TESTED]

Only relevant events processed

**Related Tests:**
- `test_issue_opened_is_processed`
- `test_issue_edited_is_processed`
- `test_issue_labeled_is_processed`
- `test_issue_comment_created_is_processed`
- `test_pr_opened_is_processed`
- `test_pr_synchronize_is_processed`
- `test_pr_reopened_is_processed`
- `test_pr_review_comment_is_processed`
- `test_push_is_processed`
- `test_unsupported_event_ignored`
- `test_unsupported_action_ignored`
- `test_supported_issues_actions`
- `test_supported_issue_comment_actions`
- `test_supported_pr_actions`
- `test_supported_pr_review_comment_actions`

### Agent Routing [TESTED]

Route webhooks to correct agent types

**Related Tests:**
- `test_github_issue_routes_to_issue_handler`
- `test_github_pr_routes_to_pr_review`
- `test_jira_routes_to_code_plan`
- `test_slack_routes_to_inquiry`
- `test_sentry_routes_to_error_handler`

## Test Coverage Summary

| Metric | Count |
|--------|-------|
| Total Features | 14 |
| Fully Tested | 13 |
| Partially Tested | 0 |
| Missing Tests | 1 |
| **Coverage** | **92.9%** |
