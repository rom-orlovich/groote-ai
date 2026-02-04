# Jira API Service - Flows

## Process Flows

### Request Processing Flow

```
[Internal Service] → HTTP Request → [Jira API Service]
                                            ↓
                                   [Authenticate Request]
                                            ↓
                                   [Load Jira Credentials]
                                            ↓
                                   [JIRA_EMAIL + JIRA_API_TOKEN]
                                            ↓
                                   [Build Basic Auth Header]
                                            ↓
                                   [Call Jira REST API v3]
                                            ↓
                                   [Parse Response]
                                            ↓
                                   [Return Standardized JSON]
```

**Processing Steps:**
1. Receive HTTP request from internal service
2. Validate internal authentication
3. Load Jira credentials from environment
4. Build Basic Auth header (Base64 of email:api_token)
5. Make authenticated request to Jira REST API
6. Parse Jira response
7. Return standardized JSON response

### Authentication Flow

```
[Service Startup] → [Load JIRA_EMAIL, JIRA_API_TOKEN]
                              ↓
                    [Build credentials string]
                              ↓
                    [email:api_token]
                              ↓
                    [Base64 encode]
                              ↓
                    [Authorization: Basic {encoded}]
```

**Authentication Header:**
```
Authorization: Basic am9obkBjb21wYW55LmNvbTp4eHh4eHh4eA==
```

### Issue Comment Flow

```
[Agent Engine] → POST /issues/{key}/comments
                         ↓
                [Parse Comment Body]
                         ↓
                [Convert to ADF Format]
                         ↓
       [POST jira/rest/api/3/issue/{key}/comment]
                         ↓
                [Jira Response]
                         ↓
                [Return comment_id, url]
```

**ADF (Atlassian Document Format):**
```json
{
  "body": {
    "version": 1,
    "type": "doc",
    "content": [
      {
        "type": "paragraph",
        "content": [
          {"type": "text", "text": "Task completed"}
        ]
      }
    ]
  }
}
```

### JQL Search Flow

```
[Service] → GET /search?jql={query}&maxResults=50
                         ↓
                [URL Encode JQL]
                         ↓
       [POST jira/rest/api/3/search]
                         ↓
                [Parse Results]
                         ↓
                [Return issues + metadata]
```

**Search Response:**
```json
{
  "issues": [...],
  "total": 42,
  "maxResults": 50,
  "startAt": 0
}
```

### Issue Transition Flow

```
[Agent Engine] → POST /issues/{key}/transitions
                         ↓
           [GET available transitions first]
                         ↓
              [Find transition by ID]
                         ↓
              [Validate transition allowed]
                         ↓
       [POST jira/rest/api/3/issue/{key}/transitions]
                         ↓
              [204 No Content = Success]
                         ↓
              [Return success status]
```

**Transition Request:**
```json
{
  "transition": {"id": "21"},
  "fields": {
    "resolution": {"name": "Done"}
  }
}
```

### Workflow State Machine

```
        ┌──────────────────────────────────────┐
        │                                      │
        ▼                                      │
     [Open] ────────────────────────────────────┤
        │                                      │
        │ Start Progress (11)                  │
        ▼                                      │
  [In Progress] ───────────────────────────────┤
        │                                      │
        │ Submit (21)                          │
        ▼                                      │
    [Review] ──────────────────────────────────┤
     ↙     ↘                                   │
    ↓       ↓                                  │
[Reject]  [Approve]                       [CANCELLED]
 (41)      (31)
    │        │
    ↓        ↓
[In Progress] [Done]
```

### Error Handling Flow

```
[Jira API Response] → [Check Status Code]
                            ↓
            ┌───────────────┼───────────────┐
            │               │               │
            ▼               ▼               ▼
       [2xx OK]        [4xx Error]     [5xx Error]
            │               │               │
            ▼               ▼               ▼
     [Return Data]   [Parse Error]    [Retry/Return]
                            ↓
              [Extract errorMessages array]
                            ↓
              [Return Standardized Error]
```

**Error Response Format:**
```json
{
  "error": "not_found",
  "message": "Issue PROJ-999 not found",
  "status_code": 404,
  "details": {"issue_key": "PROJ-999"}
}
```

### Project Listing Flow

```
[Service] → GET /projects
                 ↓
    [GET jira/rest/api/3/project]
                 ↓
         [Parse Projects]
                 ↓
         [Filter by access]
                 ↓
    [Return project list with metadata]
```

**Project Response:**
```json
{
  "projects": [
    {
      "key": "PROJ",
      "name": "Project Name",
      "lead": "john.doe",
      "projectTypeKey": "software"
    }
  ]
}
```
