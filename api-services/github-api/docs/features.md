# GitHub API Service - Features

## Overview

REST API wrapper for GitHub operations with multi-tenant OAuth support. Provides endpoints for issue management, PR operations, file access, and repository metadata supporting both single-tenant (PAT) and multi-tenant (OAuth) authentication.

## Core Features

### Issue Management

Full issue lifecycle management including creation, reading, updating, and commenting.

**Operations:**
- Get issue details with labels and assignees
- Create new issues
- Update issue status and properties
- Add comments to issues
- List issue comments

### Pull Request Operations

Complete PR management including reviews, comments, and status checks.

**Operations:**
- Get PR details with diff stats
- Add line-level comments
- Create PR reviews (approve, request changes, comment)
- List PR files changed
- Get PR review comments

### File Operations

Read and write repository files with commit support.

**Operations:**
- Read file contents (with base64 decoding)
- Create new files with commit message
- Update existing files
- Get file metadata (size, SHA, encoding)

### Repository Operations

Access repository metadata and organizational information.

**Operations:**
- Get repository details
- List organization repositories
- Get repository branches
- Access repository settings

### Multi-Tenant Support

Organization-level OAuth token management for multi-tenant deployments.

**Features:**
- OAuth token lookup per organization
- Automatic fallback to default token
- Token refresh via oauth-service
- Installation-based access

### Response Posting

Post agent results back to GitHub issues and PRs.

**Formats:**
- Markdown-formatted comments
- Code block support
- Emoji reactions
- Collapsible sections

## API Endpoints

All endpoints use the `/api/v1` prefix.

### Issues

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/repos/{owner}/{repo}/issues/{number}` | GET | Get issue details |
| `/repos/{owner}/{repo}/issues` | POST | Create issue |
| `/repos/{owner}/{repo}/issues/{number}/comments` | POST | Add comment |
| `/repos/{owner}/{repo}/issues/comments/{id}/reactions` | POST | Add reaction |

### Pull Requests

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/repos/{owner}/{repo}/pulls/{number}` | GET | Get PR details |
| `/repos/{owner}/{repo}/pulls/{number}/comments` | POST | Add PR review comment |
| `/repos/{owner}/{repo}/pulls` | POST | Create pull request |

### Repository Files

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/repos/{owner}/{repo}/contents/{path}` | GET | Read file |
| `/repos/{owner}/{repo}/contents/{path}` | PUT | Create/update file |

### Repositories & Search

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/repos/{owner}/{repo}` | GET | Get repository |
| `/repos/{owner}/{repo}/branches` | GET | List branches |
| `/repos/{owner}/{repo}/git/ref/heads/{branch}` | GET | Get branch SHA |
| `/repos/{owner}/{repo}/git/refs` | POST | Create branch |
| `/search/code` | GET | Search code |
| `/search/repositories` | GET | Search repos |
| `/installation/repos` | GET | List installation repos |
| `/users/{username}/repos` | GET | List user repos |
