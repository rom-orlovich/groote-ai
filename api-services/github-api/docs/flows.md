# api-services/github-api - Flows

Auto-generated on 2026-02-03

## Process Flows

### Request Processing Flow [TESTED]

**Steps:**
1. Receive HTTP request
2. Authenticate (internal token)
3. Get GitHub token (single-tenant or OAuth)
4. Call GitHub REST API
5. Return standardized response

**Related Tests:**
- `test_get_repository`
- `test_get_issue`
- `test_get_pull_request`
- `test_get_file_contents`

### Issue Comment Flow [TESTED]

**Steps:**
1. Receive POST request with body
2. Authenticate request
3. Get GitHub token for organization
4. Call GitHub API to create comment
5. Return comment URL

**Related Tests:**
- `test_add_comment_to_issue`
- `test_create_issue`

### PR Review Flow [TESTED]

**Steps:**
1. Receive review request
2. Authenticate request
3. Get GitHub token
4. Create PR review comment
5. Return review comment details

**Related Tests:**
- `test_get_pull_request`
- `test_add_comment_to_pr`

### OAuth Token Lookup Flow [NEEDS TESTS]

**Steps:**
1. Extract organization_id from request
2. Call oauth-service for token lookup
3. If token found, use OAuth token
4. If not found, fallback to GITHUB_TOKEN
5. Make GitHub API call

## Flow Coverage Summary

| Metric | Count |
|--------|-------|
| Total Flows | 4 |
| Fully Tested | 3 |
| Partially Tested | 0 |
| Missing Tests | 1 |
| **Coverage** | **75.0%** |
