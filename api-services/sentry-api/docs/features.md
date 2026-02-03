# api-services/sentry-api - Features

Auto-generated on 2026-02-03

## Overview

REST API wrapper for Sentry operations with issue management and error tracking. Provides endpoints for issue retrieval, event analysis, comment posting, and status management.

## Features

### Issue Retrieval [TESTED]

Get issue details including stacktrace and metadata

**Related Tests:**
- `test_get_issue_details`
- `test_get_issue_with_stacktrace`

### Event Analysis [TESTED]

Retrieve error events with full context

**Related Tests:**
- `test_get_issue_events`

### Comment Posting [TESTED]

Post investigation notes and resolution updates

**Related Tests:**
- `test_add_comment_to_issue`

### Status Management [TESTED]

Resolve, ignore, or reopen issues

**Related Tests:**
- `test_update_issue_status_resolved`
- `test_update_issue_status_ignored`
- `test_invalid_status_rejected`

### Impact Analysis [TESTED]

Get affected user count and occurrence frequency

**Related Tests:**
- `test_get_affected_users`

### Response Posting [TESTED]

Post agent analysis back to Sentry issues

**Related Tests:**
- `test_add_comment_to_issue`

### GET /issues/{issue_id} [TESTED]

Get issue details

**Related Tests:**
- `test_get_issue_details`
- `test_get_issue_with_stacktrace`

### GET /issues/{issue_id}/events [TESTED]

Get issue events

**Related Tests:**
- `test_get_issue_events`

### POST /issues/{issue_id}/comments [TESTED]

Add comment to issue

**Related Tests:**
- `test_add_comment_to_issue`

### PUT /issues/{issue_id}/status [TESTED]

Update issue status

**Related Tests:**
- `test_update_issue_status_resolved`
- `test_update_issue_status_ignored`

### GET /issues/{issue_id}/affected-users [TESTED]

Get affected users count

**Related Tests:**
- `test_get_affected_users`

### GET /health [NEEDS TESTS]

Health check endpoint

## Test Coverage Summary

| Metric | Count |
|--------|-------|
| Total Features | 12 |
| Fully Tested | 11 |
| Partially Tested | 0 |
| Missing Tests | 1 |
| **Coverage** | **91.7%** |
