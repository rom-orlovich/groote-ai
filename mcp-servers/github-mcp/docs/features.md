# GitHub MCP - Features

## Overview

FastMCP-based MCP server that exposes 15 GitHub operations as tools for AI agents. Translates MCP protocol calls into HTTP requests to the GitHub API service.

## Core Features

### Repository Operations

Read repository metadata, list accessible repositories, and search code across the installation.

**Capabilities:**
- Get repository details (name, description, default branch, visibility)
- List all repositories accessible to the GitHub App installation
- Search code across repositories with pagination

### Issue Management

Full lifecycle management of GitHub issues including creation, commenting, and reactions.

**Capabilities:**
- Get issue details with title, body, state, labels, and assignee
- Create issues with title, body, and label assignment
- Add comments to existing issues
- Add emoji reactions to issue comments (+1, -1, laugh, heart, rocket, eyes)

### Pull Request Operations

Create and inspect pull requests with inline review comments.

**Capabilities:**
- Get PR details including title, body, state, and diff
- Create pull requests with head/base branches and draft mode
- Add review comments on specific files and line numbers

### Branch Management

Create and inspect branches for automated workflows.

**Capabilities:**
- List repository branches with pagination
- Get the SHA of a branch HEAD
- Create new branches from a specific SHA

### File Operations

Read and write files in repositories via the GitHub Contents API.

**Capabilities:**
- Get file contents with optional git ref (branch, tag, SHA)
- Create new files with commit message and branch
- Update existing files (requires current file SHA)

### Credential Isolation

MCP server never stores API credentials. All requests are proxied through the GitHub API service which holds the actual tokens.

**Security Model:**
- No environment variables for GitHub tokens
- HTTP-only communication with github-api service
- Complete credential isolation from agent runtime

### SSE Transport

Provides Server-Sent Events transport for MCP protocol communication.

**Transport Features:**
- SSE endpoint at `/sse`
- Health check at `/health`
- Configurable port (default: 9001)

## MCP Tools

| Tool | Description |
|------|-------------|
| `get_repository` | Get repository details |
| `get_issue` | Get issue details |
| `create_issue` | Create a new issue |
| `add_issue_comment` | Comment on an issue |
| `add_reaction` | React to a comment |
| `create_pull_request` | Create a PR |
| `get_pull_request` | Get PR details |
| `create_pr_review_comment` | Review comment on PR |
| `get_file_contents` | Read file from repo |
| `search_code` | Search code across repos |
| `list_branches` | List repository branches |
| `list_repos` | List installation repos |
| `get_branch_sha` | Get branch HEAD SHA |
| `create_branch` | Create branch from SHA |
| `create_or_update_file` | Create/update file via Contents API |
