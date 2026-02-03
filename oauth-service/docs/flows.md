# oauth-service - Flows

Auto-generated on 2026-02-03

## Process Flows

### GitHub OAuth Flow [PARTIAL]

**Steps:**
1. User clicks "Install GitHub App"
2. Redirected to GitHub authorization page
3. User authorizes installation
4. GitHub redirects to `/oauth/github/callback` with code
5. Service exchanges code for access token
6. Token stored in database with organization ID

**Related Tests:**
- `test_get_authorization_url`

### Slack OAuth Flow [TESTED]

**Steps:**
1. User clicks "Add to Slack"
2. Redirected to Slack authorization page
3. User authorizes installation
4. Slack redirects to `/oauth/slack/callback` with code
5. Service exchanges code for access token
6. Token stored in database with workspace ID

**Related Tests:**
- `test_get_authorization_url`
- `test_exchange_code_success`

### Jira OAuth Flow [PARTIAL]

**Steps:**
1. User initiates Jira OAuth
2. Generate code verifier and challenge (PKCE)
3. Redirected to Jira authorization page
4. User authorizes access
5. Jira redirects to `/oauth/jira/callback` with code
6. Service exchanges code for access token + refresh token
7. Tokens stored in database

**Related Tests:**
- `test_get_authorization_url`
- `test_code_verifier_generation`
- `test_code_challenge_generation`

### Token Lookup Flow [NEEDS TESTS]

**Steps:**
1. Service requests token for organization
2. Lookup token in database by org_id
3. Check if token is expired
4. If expired, refresh token
5. Return valid token

### Token Refresh Flow [NEEDS TESTS]

**Steps:**
1. Check token expiration before use
2. If expired, use refresh token to get new access token
3. Update stored token in database
4. Return new token to caller

## Flow Coverage Summary

| Metric | Count |
|--------|-------|
| Total Flows | 5 |
| Fully Tested | 1 |
| Partially Tested | 2 |
| Missing Tests | 2 |
| **Coverage** | **40.0%** |
