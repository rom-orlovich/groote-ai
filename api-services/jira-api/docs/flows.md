# api-services/jira-api - Flows

Auto-generated on 2026-02-03

## Process Flows

### Request Processing Flow [TESTED]

**Steps:**
1. Receive HTTP request
2. Authenticate (internal token)
3. Get Jira credentials (email + API token)
4. Call Jira REST API
5. Return standardized response

**Related Tests:**
- `test_get_issue`
- `test_create_issue`
- `test_add_comment_to_issue`

### Issue Comment Flow [TESTED]

**Steps:**
1. Receive POST request with body
2. Authenticate request
3. Get Jira credentials
4. Format comment for Jira ADF
5. Call Jira API to create comment
6. Return comment details

**Related Tests:**
- `test_add_comment_to_issue`

### Issue Transition Flow [TESTED]

**Steps:**
1. Receive transition request
2. Get available transitions for issue
3. Validate transition ID
4. Execute transition
5. Return updated issue status

**Related Tests:**
- `test_transition_issue`
- `test_get_transitions`

### JQL Search Flow [TESTED]

**Steps:**
1. Receive search request with JQL
2. Authenticate request
3. Execute JQL query via Jira API
4. Parse and format results
5. Return issue list

**Related Tests:**
- `test_search_issues_with_jql`

## Flow Coverage Summary

| Metric | Count |
|--------|-------|
| Total Flows | 4 |
| Fully Tested | 4 |
| Partially Tested | 0 |
| Missing Tests | 0 |
| **Coverage** | **100.0%** |
