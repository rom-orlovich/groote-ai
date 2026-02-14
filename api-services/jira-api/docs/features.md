# Jira API Service - Features

## Overview

REST API wrapper for Jira operations with issue and project management. Provides endpoints for issue management, comment posting, JQL search, transition handling, and project operations.

## Core Features

### Issue Management

Full issue lifecycle management including CRUD operations and status tracking.

**Operations:**
- Get issue details with fields and changelog
- Create new issues with custom fields
- Update issue fields and properties
- Delete issues (with permission)
- Get issue transitions

### Comment Posting

Post formatted comments to Jira tickets with Atlassian Document Format (ADF) support.

**Features:**
- Markdown to ADF conversion
- Code block formatting
- Mentions and links
- Inline images

### JQL Search

Execute JQL queries to find issues across projects.

**Capabilities:**
- Full JQL syntax support
- Field selection
- Pagination support
- Max results configuration

**Example Queries:**
- `project = PROJ AND status = "In Progress"`
- `assignee = currentUser() AND sprint in openSprints()`
- `labels = "ai-agent" AND created >= -7d`

### Transition Management

Move issues through workflow states programmatically.

**Operations:**
- Get available transitions for issue
- Execute transition by ID
- Include transition fields
- Add transition comment

### Project Operations

Access project metadata and configuration.

**Operations:**
- List all projects
- Get project details
- List project issue types
- Get project components

### Response Posting

Post agent results back to Jira tickets.

**Formats:**
- Structured task results
- Code diffs with syntax highlighting
- Status updates
- Error reports

## API Endpoints

All endpoints use the `/api/v1` prefix.

### Issues

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/issues/{issue_key}` | GET | Get issue details |
| `/issues` | POST | Create issue |
| `/issues/{issue_key}` | PUT | Update issue |
| `/issues/{issue_key}/comments` | POST | Add comment |
| `/issues/{issue_key}/transitions` | GET | Get transitions |
| `/issues/{issue_key}/transitions` | POST | Execute transition |

### Search

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/search` | POST | Execute JQL query (with pagination) |

### Projects & Boards

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/projects` | GET | List all projects |
| `/projects` | POST | Create project |
| `/boards` | GET | List boards |
| `/boards` | POST | Create board |

### Confluence

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/confluence/pages` | GET | List Confluence pages |
| `/confluence/spaces` | GET | List Confluence spaces |
