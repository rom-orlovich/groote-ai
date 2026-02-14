# Jira MCP - Features

## Overview

FastMCP-based MCP server that exposes 10 Jira operations as tools for AI agents. Translates MCP protocol calls into HTTP requests to the Jira API service.

## Core Features

### Issue Management

Full lifecycle management of Jira issues including creation, reading, updating, commenting, and status transitions.

**Capabilities:**
- Get issue details (summary, description, status, assignee)
- Create issues with structured markdown descriptions and issue types (Task, Bug, Story, Epic, Sub-task)
- Update issue fields
- Add comments to issues
- Search issues using JQL queries with pagination

### Workflow Management

Move issues through Jira workflows by querying available transitions and executing them.

**Capabilities:**
- Get available transitions for an issue
- Transition issue to new status (e.g., In Progress, Done)

### Project Management

Create and manage Jira projects and boards.

**Capabilities:**
- Create projects with configurable type (software, business, service_desk)
- List boards filtered by project key
- Create Kanban or Scrum boards with auto-generated JQL filters

### Credential Isolation

MCP server never stores Jira API credentials. All requests are proxied through the Jira API service which holds the actual tokens.

**Security Model:**
- No environment variables for Jira tokens
- HTTP-only communication with jira-api service
- Complete credential isolation from agent runtime

## MCP Tools

| Tool | Description |
|------|-------------|
| `get_jira_issue` | Get issue details by key (e.g., PROJ-123) |
| `create_jira_issue` | Create issue with project_key, summary, description, type |
| `update_jira_issue` | Update issue fields by key |
| `add_jira_comment` | Add comment to an issue |
| `search_jira_issues` | Search using JQL with pagination |
| `get_jira_transitions` | Get available status transitions |
| `transition_jira_issue` | Move issue to new status |
| `create_jira_project` | Create a new project |
| `get_jira_boards` | List boards (optionally filtered by project) |
| `create_jira_board` | Create Kanban or Scrum board |
