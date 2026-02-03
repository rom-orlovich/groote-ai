# api-gateway - Flows

Auto-generated on 2026-02-03

## Process Flows

### GitHub Flow [TESTED]

**Steps:**
1. Receive POST → Validate signature (middleware)
2. Parse `X-GitHub-Event` header
3. Extract metadata (owner, repo, PR/issue number)
4. Check `@agent` command in comment
5. Skip if from bot → Return `200 OK`
6. Create task → Queue to Redis → Return `202 Accepted`
7. Async: Add 👀 reaction via `github-api`

**Related Tests:**
- `test_github_issue_to_task_flow`
- `test_github_issue_comment_flow`
- `test_github_pr_opened_flow`
- `test_github_invalid_signature_rejected`
- `test_github_unsupported_event_ignored`
- `test_github_bot_comment_ignored`
- `test_issue_opened_extracts_task_info`
- `test_issue_comment_extracts_comment_info`
- `test_pr_opened_extracts_pr_info`

### Jira Flow [TESTED]

**Steps:**
1. Receive POST → Validate signature (middleware)
2. Parse issue data
3. Check AI-Fix label → Skip if missing → Return `200 OK`
4. Check assignee matches AI agent
5. Create task → Queue to Redis → Return `202 Accepted`

**Related Tests:**
- `test_jira_ai_fix_label_creates_task`
- `test_jira_without_ai_fix_ignored`
- `test_jira_invalid_signature_rejected`
- `test_jira_metadata_preserved`
- `test_jira_routes_to_code_plan`

### Slack Flow [TESTED]

**Steps:**
1. Receive POST → Handle URL verification challenge
2. Validate signature (middleware)
3. Parse event (mention, command)
4. Skip if from bot → Return `200 OK`
5. Create task → Queue to Redis → Return `200 OK`

**Related Tests:**
- `test_slack_app_mention_creates_task`
- `test_slack_bot_message_ignored`
- `test_slack_thread_context_preserved`
- `test_slack_routes_to_inquiry`

### Sentry Flow [TESTED]

**Steps:**
1. Receive POST → Validate signature (middleware)
2. Parse alert data
3. Skip if unsupported → Return `200 OK`
4. Create task → Queue to Redis → Return `202 Accepted`

**Related Tests:**
- `test_sentry_new_error_creates_task`
- `test_sentry_regression_high_priority`
- `test_sentry_resolved_ignored`
- `test_sentry_routes_to_error_handler`

### Loop Prevention Flow [TESTED]

**Steps:**
1. Check if comment ID in Redis posted-comments set
2. If found → Return `200 OK` with "loop prevention"
3. Check if user is bot type
4. If bot → Return `200 OK` with "bot comment"
5. Otherwise → Continue processing

**Related Tests:**
- `test_agent_posted_comment_ignored`
- `test_different_comment_processed`
- `test_github_bot_comment_ignored`
- `test_slack_bot_message_ignored`

## Flow Coverage Summary

| Metric | Count |
|--------|-------|
| Total Flows | 5 |
| Fully Tested | 5 |
| Partially Tested | 0 |
| Missing Tests | 0 |
| **Coverage** | **100.0%** |
