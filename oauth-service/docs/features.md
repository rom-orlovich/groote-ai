# oauth-service - Features

Auto-generated on 2026-02-03

## Overview

Multi-tenant OAuth token management service for GitHub, Jira, and Slack integrations. Manages OAuth tokens for organization-level installations - no individual user accounts required.

## Features

### OAuth Flow Management [TESTED]

Handle OAuth authorization flows for all platforms

**Related Tests:**
- `test_get_authorization_url` (GitHub)
- `test_get_authorization_url` (Slack)
- `test_get_authorization_url` (Jira)

### Token Exchange [TESTED]

Exchange OAuth codes for access tokens

**Related Tests:**
- `test_exchange_code_success`

### Token Storage [NEEDS TESTS]

Securely store OAuth tokens per organization/workspace

### Token Refresh [NEEDS TESTS]

Automatically refresh expired tokens

### Token Lookup [NEEDS TESTS]

Provide token lookup APIs for other services

### Installation Management [NEEDS TESTS]

Track OAuth app installations

### GitHub OAuth Provider [TESTED]

GitHub App installation flow with state parameter

**Related Tests:**
- `test_get_authorization_url`

### Slack OAuth Provider [TESTED]

Slack OAuth v2 flow with scopes

**Related Tests:**
- `test_get_authorization_url`
- `test_exchange_code_success`

### Jira OAuth Provider [TESTED]

Jira OAuth with PKCE (code challenge)

**Related Tests:**
- `test_get_authorization_url`
- `test_code_verifier_generation`
- `test_code_challenge_generation`

### GET /oauth/install/{platform} [PARTIAL]

Start OAuth flow

**Related Tests:**
- `test_get_authorization_url` (indirect)

### GET /oauth/callback/{platform} [PARTIAL]

OAuth callback handler

**Related Tests:**
- `test_exchange_code_success` (indirect)

### GET /oauth/token/{platform} [NEEDS TESTS]

Get token for organization

### GET /oauth/installations [NEEDS TESTS]

List installations

### DELETE /oauth/installations/{id} [NEEDS TESTS]

Revoke installation

### GET /health [NEEDS TESTS]

Health check endpoint

## Test Coverage Summary

| Metric | Count |
|--------|-------|
| Total Features | 15 |
| Fully Tested | 4 |
| Partially Tested | 2 |
| Missing Tests | 9 |
| **Coverage** | **33.3%** |
