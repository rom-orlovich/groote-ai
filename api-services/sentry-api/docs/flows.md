# api-services/sentry-api - Flows

Auto-generated on 2026-02-03

## Process Flows

### Issue Retrieval Flow [TESTED]

**Steps:**
1. Receive GET request for issue
2. Authenticate request
3. Get Sentry Auth Token
4. Call Sentry API for issue details
5. Include stacktrace and metadata
6. Return formatted issue data

**Related Tests:**
- `test_get_issue_details`
- `test_get_issue_with_stacktrace`

### Event Analysis Flow [TESTED]

**Steps:**
1. Receive GET request for issue events
2. Authenticate request
3. Call Sentry API for events
4. Parse exception entries and stacktraces
5. Return event list with context

**Related Tests:**
- `test_get_issue_events`

### Comment Posting Flow [TESTED]

**Steps:**
1. Receive POST request with comment text
2. Authenticate request
3. Call Sentry API to add note
4. Return comment details

**Related Tests:**
- `test_add_comment_to_issue`

### Status Update Flow [TESTED]

**Steps:**
1. Receive PUT request with new status
2. Validate status (resolved/unresolved/ignored)
3. Call Sentry API to update status
4. Return updated issue

**Related Tests:**
- `test_update_issue_status_resolved`
- `test_update_issue_status_ignored`
- `test_invalid_status_rejected`

### Impact Analysis Flow [TESTED]

**Steps:**
1. Receive GET request for affected users
2. Get issue details from Sentry
3. Extract userCount from issue
4. Return impact metrics

**Related Tests:**
- `test_get_affected_users`

## Flow Coverage Summary

| Metric | Count |
|--------|-------|
| Total Flows | 5 |
| Fully Tested | 5 |
| Partially Tested | 0 |
| Missing Tests | 0 |
| **Coverage** | **100.0%** |
