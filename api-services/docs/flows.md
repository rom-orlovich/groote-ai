# API Services - Flows

## Process Flows

### Request Processing Flow (All Services)

```
[Internal Consumer] --> HTTP Request --> [API Service]
                                              |
                                    [Auth Middleware]
                                              |
                                    [Route Handler]
                                              |
                                    [Token Provider]
                                         |        |
                                    [OAuth?]   [Static]
                                       |          |
                                [Query OAuth]  [Use Env]
                                [  Service  ]  [ Var  ]
                                       |          |
                                       +----------+
                                              |
                                    [API Client]
                                              |
                                    [External API Call]
                                              |
                                    [Parse Response]
                                              |
                                    [Return Standardized JSON]
```

**Processing Steps:**
1. Internal service sends HTTP request (no credentials)
2. Auth middleware validates internal authentication
3. Route handler receives authenticated request
4. Token provider resolves credentials (OAuth or static)
5. API client makes authenticated call to external API
6. Response parsed and returned in standardized format

### GitHub Token Resolution Flow

```
[Request] --> [Token Provider]
                    |
            [OAuth Enabled?]
               |        |
            [Yes]     [No]
               |        |
      [Query OAuth]  [Use GITHUB_TOKEN]
      [  Service  ]        |
               |            |
      [Token Found?]        |
         |       |          |
      [Yes]    [No]         |
         |       |          |
   [Use OAuth]  [Fallback]--+
         |                  |
         +------------------+
                    |
            [Make GitHub API Call]
```

**Token Priority:**
1. OAuth token for specific organization
2. Default Personal Access Token (GITHUB_TOKEN)

### Jira Authentication Flow

```
[Request] --> [Token Provider]
                    |
            [OAuth Enabled?]
               |        |
            [Yes]     [No]
               |        |
      [Query OAuth]  [Basic Auth]
      [  Service  ]  [email:token]
               |        |
      [Bearer Token]    |
               |        |
               +--------+
                    |
            [Make Jira API Call]
```

**Authentication Modes:**
- OAuth: Bearer token via oauth-service
- Basic Auth: Base64(JIRA_EMAIL:JIRA_API_TOKEN)

### Slack Token Resolution Flow

```
[Request] --> [Token Provider]
                    |
            [OAuth Enabled?]
               |        |
            [Yes]     [No]
               |        |
      [Query OAuth]  [Use SLACK_BOT_TOKEN]
      [  Service  ]        |
               |            |
      [Workspace Token]     |
               |            |
               +------------+
                    |
            [Make Slack API Call]
```

### GitHub Issue Comment Flow

```
[Agent Engine] --> POST /api/v1/repos/{owner}/{repo}/issues/{num}/comments
                                    |
                          [Resolve Token]
                                    |
                          [POST github.com/repos/{owner}/{repo}/issues/{num}/comments]
                                    |
                          [GitHub Response: 201 Created]
                                    |
                          [Return {id, body, url}]
```

### Jira Search Flow

```
[MCP Server] --> POST /api/v1/search
                        |
                [Parse JQL + Pagination]
                        |
                [POST jira/rest/api/3/search]
                        |
                [Parse Results]
                        |
                [Return {issues, total, maxResults}]
```

### Slack Message Flow

```
[Agent Engine] --> POST /api/v1/messages
                           |
                  [Resolve Token]
                           |
                  [Build Payload: channel, text, thread_ts, blocks]
                           |
                  [POST chat.postMessage]
                           |
                  [Return {ts, channel}]
```

### Error Handling Flow

```
[External API Response] --> [Check Status]
                                 |
                  +--------------+--------------+
                  |              |              |
               [2xx OK]     [4xx Error]    [5xx Error]
                  |              |              |
           [Return Data]  [Map to Error]  [Retry/Return]
                                 |
                    [Return Standardized Error]
```

**Error Response Format:**
```json
{
    "error": "not_found",
    "message": "Resource not found",
    "status_code": 404
}
```

### Multi-Tenant OAuth Resolution Flow

```
[Service] --> [GET /oauth/token/{provider}?org_id={org}]
                              |
                       [OAuth Service]
                              |
                    [Lookup Stored Token]
                              |
                       [Token Valid?]
                         |       |
                      [Yes]    [No]
                         |       |
                  [Return Token] [Refresh Token]
                                       |
                                [Store New Token]
                                       |
                                [Return Token]
```
