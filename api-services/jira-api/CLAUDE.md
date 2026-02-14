# Jira API Service

REST API wrapper for Jira operations with issue and project management.

## Development

- Port: 3002
- Language: Python
- Framework: FastAPI
- Max 300 lines per file, no comments, strict types, async/await for I/O
- Tests: `uv run pytest api-services/jira-api/tests/ -v`

## Key Features

- Issue management (create, read, update)
- Comment posting
- JQL search
- Transition management
- Credential isolation (stored only in this container)

## Environment

```bash
JIRA_URL=https://company.atlassian.net
JIRA_EMAIL=agent@company.com
JIRA_API_TOKEN=xxx
PORT=3002
```
