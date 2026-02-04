# OAuth Service - Features

## Overview

Multi-tenant OAuth token management service for GitHub, Jira, and Slack integrations. Manages OAuth tokens for organization-level installations with automatic token refresh.

## Core Features

### OAuth Flow Management

Handle OAuth authorization flows for GitHub, Jira, and Slack platforms.

**Supported Platforms:**
- GitHub (OAuth App and GitHub App)
- Jira (OAuth 2.0 3LO)
- Slack (OAuth 2.0)

**Flow Capabilities:**
- Generate authorization URLs with state
- Handle OAuth callbacks
- Store tokens securely

### Token Exchange

Exchange authorization codes for access tokens during OAuth callback.

**Exchange Process:**
- Receive authorization code
- Validate state parameter
- Exchange for access/refresh tokens
- Store with organization mapping

### Token Storage

Secure storage of OAuth tokens with encryption.

**Storage Features:**
- Fernet encryption for tokens
- PostgreSQL persistence
- Organization-level mapping
- Scope tracking

### Token Refresh

Automatic refresh of expired tokens for seamless operation.

**Refresh Features:**
- Automatic expiration detection
- Transparent refresh before API calls
- Refresh token rotation support
- Failed refresh handling

### Installation Management

Track and manage OAuth installations per organization.

**Installation Data:**
- Platform (github, jira, slack)
- External organization ID
- Organization name
- Token scopes
- Installation status

### Multi-Tenant Lookup

Lookup tokens by organization for multi-tenant API access.

**Lookup Methods:**
- By organization ID
- By workspace ID (Slack)
- By site ID (Jira)

## API Endpoints

### OAuth Flows

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/oauth/install/{platform}` | GET | Start OAuth flow |
| `/oauth/callback/{platform}` | GET | OAuth callback |

### Token Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/oauth/token/{platform}` | GET | Get token for org |
| `/oauth/installations` | GET | List installations |
| `/oauth/installations/{id}` | DELETE | Revoke installation |

### Status

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/oauth/status` | GET | OAuth status summary |
