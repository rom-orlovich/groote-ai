# Sentry API Service - Features

## Overview

REST API wrapper for Sentry operations with issue management and error tracking. Provides endpoints for issue retrieval, event analysis, comment posting, status management, and impact analysis.

## Core Features

### Issue Retrieval

Get issue details including metadata, stacktrace, and aggregated event information.

**Information Retrieved:**
- Issue title and message
- First/last seen timestamps
- Event count
- User impact count
- Status (unresolved, resolved, ignored)
- Assigned user/team

### Event Analysis

Retrieve error events with full context for debugging.

**Event Details:**
- Stacktrace frames
- Request context
- User context
- Tags and extra data
- Browser/device info

### Stacktrace Processing

Extract and format stacktrace information for analysis.

**Stacktrace Data:**
- Function names
- File paths and line numbers
- Context lines (before/after)
- Local variables (if available)
- In-app vs library frames

### Comment Posting

Post investigation notes and resolution updates to issues.

**Features:**
- Plain text comments
- Markdown support
- Mention users
- Link to commits

### Status Management

Update issue status through the lifecycle.

**Status Values:**
- `unresolved` - Active issue
- `resolved` - Marked as fixed
- `ignored` - Suppressed
- `resolvedInNextRelease` - Auto-resolve on deploy

### Impact Analysis

Get affected user count and occurrence frequency.

**Metrics:**
- Unique users affected
- Total event count
- Events per hour/day
- First/last occurrence

### Project Operations

Access project metadata and issue lists.

**Operations:**
- List projects
- Get project details
- List project issues
- Get project stats

## API Endpoints

### Issues

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/issues/{issue_id}` | GET | Get issue details |
| `/issues/{issue_id}/events` | GET | Get issue events |
| `/issues/{issue_id}/comments` | POST | Add comment |
| `/issues/{issue_id}/status` | PUT | Update status |

### Events

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/events/{event_id}` | GET | Get event details |
| `/events/{event_id}/stacktrace` | GET | Get stacktrace |

### Projects

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/projects` | GET | List projects |
| `/projects/{org}/{proj}` | GET | Get project |
| `/projects/{org}/{proj}/issues` | GET | Project issues |

### Analysis

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/issues/{issue_id}/affected-users` | GET | Get affected users |
