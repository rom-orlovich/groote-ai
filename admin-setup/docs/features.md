# Admin Setup - Features

## Overview

First-run configuration service for groote-ai. Provides a token-authenticated web wizard for administrators to configure OAuth app credentials, verify infrastructure health, validate service connectivity, and export environment configuration.

## Core Features

### Token Authentication

Cookie-based session authentication using `ADMIN_SETUP_TOKEN` environment variable. Admin enters token once; session persisted via httpOnly cookie with strict SameSite policy.

**Security Features:**
- Token comparison against environment variable
- HttpOnly cookie prevents XSS access
- Strict SameSite prevents CSRF
- 24-hour session expiry

### Infrastructure Health Checks

Validates connectivity to PostgreSQL and Redis during the setup wizard. Reports health status for each service.

**Checks Performed:**
- PostgreSQL: Execute `SELECT 1` via async connection
- Redis: Execute `PING` via async connection

### Multi-Step Setup Wizard

Guided configuration flow with 6 steps: welcome, public URL, GitHub, Jira, Slack, and review. Steps can be completed or skipped, with progress tracked in the database.

**Step Capabilities:**
- Progress percentage tracking
- Skip support for optional integrations
- Resume from last incomplete step
- Reset to start over

### Credential Validation

Real-time validation of OAuth credentials against external APIs before saving.

**Validation Methods:**
- Public URL: Format validation (protocol, domain)
- GitHub: JWT creation with private key, verify against GitHub API `/app`
- Jira: HTTP reachability check to site's REST API
- Slack: Client ID presence check (full validation deferred to OAuth flow)

### Encrypted Credential Storage

Sensitive credentials encrypted with Fernet symmetric encryption before storage in PostgreSQL. Decrypted only when accessed by authorized sessions.

**Sensitive Keys:**
- GITHUB_CLIENT_SECRET, GITHUB_WEBHOOK_SECRET
- JIRA_CLIENT_SECRET
- SLACK_CLIENT_SECRET, SLACK_SIGNING_SECRET, SLACK_STATE_SECRET

### Configuration Export

Generate `.env` file content from stored configurations. Groups entries by category and appends derived values like GITHUB_PRIVATE_KEY_PATH.

**Export Features:**
- Grouped by category (domain, github, jira, slack)
- Sensitive values decrypted for export
- Derived paths auto-appended

### Configuration Summary

View all stored configurations with sensitive values masked. Shows last 3 characters of secrets for identification without exposure.

**Masking:**
- Non-sensitive values shown in full
- Sensitive values displayed as "......xxx" (last 3 chars)

### Setup Reset

Reset all setup progress and delete stored configurations. Returns wizard to welcome step with 0% progress.

### SPA Frontend Serving

FastAPI serves the React frontend build as static files. All non-API, non-asset routes fall back to index.html for client-side routing.

## API Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/health` | GET | No | Health check |
| `/api/auth` | POST | No | Authenticate with admin token |
| `/api/setup/status` | GET | Yes | Get setup progress |
| `/api/setup/infrastructure` | GET | Yes | Check Postgres + Redis health |
| `/api/setup/steps/{step_id}` | POST | Yes | Save step config or skip |
| `/api/setup/steps/{step_id}/config` | GET | Yes | Get saved config for step |
| `/api/setup/validate/{service}` | POST | Yes | Validate credentials |
| `/api/setup/summary` | GET | Yes | Get masked config summary |
| `/api/setup/export` | GET | Yes | Export .env content |
| `/api/setup/complete` | POST | Yes | Mark setup as complete |
| `/api/setup/reset` | POST | Yes | Reset setup and delete configs |

## Frontend Components

| Component | Description |
|-----------|-------------|
| AuthGate | Token input and authentication |
| DashboardView | Setup wizard container |
| Layout | Page layout wrapper |
| ServiceCard | Service health status card |
| StepIndicator | Step progress bar |
| WelcomeStep | Intro and prerequisites |
| ServiceStep | OAuth config form per service |
| ReviewStep | Configuration review and export |
