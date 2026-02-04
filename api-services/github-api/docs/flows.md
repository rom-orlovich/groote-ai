# GitHub API Service - Flows

## Process Flows

### Request Processing Flow

```
[Internal Service] → HTTP Request → [GitHub API Service]
                                            ↓
                                   [Authenticate Request]
                                            ↓
                                   [Resolve GitHub Token]
                                       ↓          ↓
                             [Has org_id?]   [No org_id]
                                   ↓              ↓
                          [Query OAuth]    [Use GITHUB_TOKEN]
                                   ↓              ↓
                              [Get Token]         ↓
                                   └──────────────┘
                                            ↓
                                   [Call GitHub API]
                                            ↓
                                   [Parse Response]
                                            ↓
                                   [Return Standardized JSON]
```

**Processing Steps:**
1. Receive HTTP request from internal service
2. Validate internal authentication
3. Check if request includes organization_id
4. If org_id present: Query oauth-service for OAuth token
5. If no org_id or no OAuth token: Use default GITHUB_TOKEN
6. Make authenticated request to GitHub REST API
7. Parse GitHub response
8. Return standardized JSON response

### Token Resolution Flow

```
[Request with org_id] → [Query OAuth Service]
                               ↓
                    [GET /oauth/token/github?org_id={org}]
                               ↓
                       [Token Found?]
                          ↓      ↓
                       [Yes]    [No]
                          ↓      ↓
                   [Use OAuth]  [Fallback to PAT]
```

**Token Priority:**
1. OAuth token for specific organization
2. GitHub App installation token
3. Default Personal Access Token (GITHUB_TOKEN)

### Issue Comment Flow

```
[Agent Engine] → POST /issues/{owner}/{repo}/{num}/comments
                               ↓
                      [Resolve Token]
                               ↓
                      [Build Comment Body]
                               ↓
           [POST github.com/repos/{owner}/{repo}/issues/{num}/comments]
                               ↓
                      [GitHub Response]
                               ↓
                      [Return comment_id, url]
```

**Comment Processing:**
1. Agent Engine sends POST request with comment body
2. Service resolves appropriate GitHub token
3. Comment body may include markdown formatting
4. Request sent to GitHub Issues API
5. Returns comment ID and URL for tracking

### PR Review Flow

```
[Agent Engine] → POST /pulls/{owner}/{repo}/{num}/reviews
                               ↓
                      [Resolve Token]
                               ↓
                      [Build Review Payload]
                          ↓
            ┌─────────────┼─────────────┐
            │             │             │
            ▼             ▼             ▼
       [APPROVE]   [COMMENT]   [REQUEST_CHANGES]
            │             │             │
            └─────────────┼─────────────┘
                          ↓
           [POST github.com/repos/{owner}/{repo}/pulls/{num}/reviews]
                          ↓
                  [Return review_id]
```

**Review Events:**
- `APPROVE` - Approve the pull request
- `COMMENT` - Add review comment without approval
- `REQUEST_CHANGES` - Request changes before merge

### File Operations Flow

```
[Read File]
[Service] → GET /repos/{owner}/{repo}/contents/{path}
                      ↓
              [GitHub API Call]
                      ↓
              [Base64 Decode Content]
                      ↓
              [Return decoded content + metadata]

[Write File]
[Service] → POST /repos/{owner}/{repo}/contents/{path}
                      ↓
              [Base64 Encode Content]
                      ↓
              [Include SHA for updates]
                      ↓
              [GitHub API Call]
                      ↓
              [Return commit SHA]
```

**File Metadata:**
- `content` - Decoded file content
- `sha` - File SHA for updates
- `size` - File size in bytes
- `encoding` - Original encoding

### Rate Limit Handling Flow

```
[GitHub API Call] → [Check Response]
                          ↓
                 [Status 403 + X-RateLimit-Remaining: 0?]
                          ↓
                       [Yes]
                          ↓
              [Read X-RateLimit-Reset header]
                          ↓
              [Calculate wait time]
                          ↓
              [Wait with exponential backoff]
                          ↓
              [Retry request]
```

**Rate Limits:**
- Core API: 5,000 requests/hour
- Search API: 30 requests/minute
- GraphQL: 5,000 points/hour
- Automatic retry on rate limit with backoff

### Error Handling Flow

```
[GitHub API Response] → [Check Status Code]
                              ↓
              ┌───────────────┼───────────────┐
              │               │               │
              ▼               ▼               ▼
         [2xx OK]        [4xx Error]     [5xx Error]
              │               │               │
              ▼               ▼               ▼
       [Return Data]   [Map to Error]   [Retry/Return]
                              ↓
                      [Return Standardized Error]
```

**Error Response Format:**
```json
{
  "error": "not_found",
  "message": "Issue not found",
  "status_code": 404,
  "details": {"owner": "acme", "repo": "project"}
}
```
