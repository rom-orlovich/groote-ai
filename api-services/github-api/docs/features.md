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

### Issues

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/issues/{owner}/{repo}/{number}` | GET | Get issue details |
| `/issues/{owner}/{repo}/{number}/comments` | GET | List comments |
| `/issues/{owner}/{repo}/{number}/comments` | POST | Add comment |

### Pull Requests

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/pulls/{owner}/{repo}/{number}` | GET | Get PR details |
| `/pulls/{owner}/{repo}/{number}/comments` | POST | Add PR comment |
| `/pulls/{owner}/{repo}/{number}/reviews` | POST | Create review |

### Repository Files

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/repos/{owner}/{repo}/contents/{path}` | GET | Read file |
| `/repos/{owner}/{repo}/contents/{path}` | POST | Create/update file |

### Repositories

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/repos/{owner}/{repo}` | GET | Get repository |
| `/orgs/{org}/repos` | GET | List org repos |
