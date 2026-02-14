# API Services - Features

## Overview

Collection of REST API wrappers for external services (GitHub, Jira, Slack) with isolated credential management and standardized interfaces.

## Core Features

### Credential Isolation

API keys are stored only in their respective service containers. Internal consumers (MCP servers, agent engine) never handle external API tokens.

**Security Model:**
- GitHub token in github-api container only
- Jira credentials in jira-api container only
- Slack bot token in slack-api container only

### Multi-Tenant OAuth Support

Organization-level OAuth token management for multi-tenant deployments. Each service resolves tokens per-organization via the OAuth Service.

**Token Resolution:**
- Query oauth-service for organization-specific tokens
- Automatic fallback to static credentials
- Support for both OAuth Bearer and API token authentication

### Standardized Error Responses

Unified error format across all three services for consistent error handling by consumers.

**Format:**
- HTTP status code mapping
- Descriptive error type and message
- Optional details object

## GitHub API Service (Port 3001)

REST wrapper for GitHub operations with multi-tenant OAuth support.

**Capabilities:**
- Repository operations (get repo, list branches, search)
- Issue management (create, get, comment, react)
- Pull request operations (get, review comments, create)
- File operations (read contents, create/update files)
- Code and repository search
- Branch management (get SHA, create branch)

**API Endpoints (prefix: `/api/v1`):**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/repos/{owner}/{repo}` | GET | Get repository |
| `/repos/{owner}/{repo}/issues/{number}` | GET | Get issue |
| `/repos/{owner}/{repo}/issues` | POST | Create issue |
| `/repos/{owner}/{repo}/issues/{number}/comments` | POST | Add comment |
| `/repos/{owner}/{repo}/issues/comments/{id}/reactions` | POST | Add reaction |
| `/repos/{owner}/{repo}/pulls/{number}` | GET | Get PR |
| `/repos/{owner}/{repo}/pulls/{number}/comments` | POST | Add PR review comment |
| `/repos/{owner}/{repo}/pulls` | POST | Create PR |
| `/repos/{owner}/{repo}/contents/{path}` | GET | Read file |
| `/repos/{owner}/{repo}/contents/{path}` | PUT | Create/update file |
| `/repos/{owner}/{repo}/branches` | GET | List branches |
| `/repos/{owner}/{repo}/git/ref/heads/{branch}` | GET | Get branch SHA |
| `/repos/{owner}/{repo}/git/refs` | POST | Create branch |
| `/search/code` | GET | Search code |
| `/search/repositories` | GET | Search repos |
| `/installation/repos` | GET | List installation repos |
| `/users/{username}/repos` | GET | List user repos |

## Jira API Service (Port 3002)

REST wrapper for Jira operations with issue, project, board, and Confluence support.

**Capabilities:**
- Issue management (create, get, update)
- Comment posting
- JQL search with pagination
- Transition management
- Project management (list, create)
- Board management (list, create)
- Confluence page and space listing

**API Endpoints (prefix: `/api/v1`):**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/issues/{issue_key}` | GET | Get issue |
| `/issues` | POST | Create issue |
| `/issues/{issue_key}` | PUT | Update issue |
| `/issues/{issue_key}/comments` | POST | Add comment |
| `/issues/{issue_key}/transitions` | GET | Get transitions |
| `/issues/{issue_key}/transitions` | POST | Execute transition |
| `/search` | POST | JQL search |
| `/projects` | GET | List projects |
| `/projects` | POST | Create project |
| `/boards` | GET | List boards |
| `/boards` | POST | Create board |
| `/confluence/pages` | GET | List Confluence pages |
| `/confluence/spaces` | GET | List Confluence spaces |

## Slack API Service (Port 3003)

REST wrapper for Slack operations with message posting and channel management.

**Capabilities:**
- Message posting with Block Kit support
- Thread replies
- Message updates
- Channel operations (list, get info, history)
- Thread reply retrieval
- Reaction management
- User information lookup

**API Endpoints (prefix: `/api/v1`):**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/messages` | POST | Send message |
| `/messages` | PUT | Update message |
| `/reactions` | POST | Add reaction |
| `/channels` | GET | List channels |
| `/channels/{channel}` | GET | Get channel info |
| `/channels/{channel}/history` | GET | Get message history |
| `/channels/{channel}/threads/{thread_ts}` | GET | Get thread replies |
| `/users/{user_id}` | GET | Get user info |

## Health Checks

All services expose a health endpoint at the root level:

| Service | Endpoint |
|---------|----------|
| GitHub API | `GET http://localhost:3001/health` |
| Jira API | `GET http://localhost:3002/health` |
| Slack API | `GET http://localhost:3003/health` |
