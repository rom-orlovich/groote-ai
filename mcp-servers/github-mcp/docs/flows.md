# GitHub MCP - Flows

## Process Flows

### Tool Invocation Flow

```
[MCP Client] --> SSE /sse --> [FastMCP Server :9001]
                                        |
                              [Dispatch to Tool Function]
                                        |
                              [GitHubAPI Client Method]
                                        |
                              [HTTP Request to github-api:3001]
                                        |
                              [Return JSON Response]
                                        |
                              [MCP Response to Client]
```

**Processing Steps:**
1. MCP client connects via SSE to port 9001
2. Client sends MCP tool call with parameters
3. FastMCP dispatches to registered tool function
4. Tool function calls corresponding GitHubAPI method
5. GitHubAPI sends HTTP request to github-api:3001
6. Backend returns JSON response
7. Tool function returns result to MCP framework
8. MCP framework sends response back via SSE

### Issue Creation Flow

```
[Agent] --> create_issue(owner, repo, title, body, labels)
                    |
         [GitHubAPI.create_issue()]
                    |
         [POST /api/v1/repos/{owner}/{repo}/issues]
                    |
                    v
         [github-api:3001] --> [GitHub REST API]
                    |
         [Return created issue details]
                    |
         [Agent receives issue number and URL]
```

**Processing Steps:**
1. Agent calls `create_issue` tool with owner, repo, title, body, labels
2. Tool builds payload dict with title (required), body and labels (optional)
3. GitHubAPI sends POST to github-api service
4. Backend creates issue via GitHub REST API
5. Returns created issue details including new issue number

### PR Review Flow

```
[Agent] --> get_pull_request(owner, repo, pr_number)
                    |
         [Review PR details and diff]
                    |
         --> create_pr_review_comment(owner, repo, pr_number, ...)
                    |
         [POST /api/v1/repos/{owner}/{repo}/pulls/{pr}/comments]
                    |
         [Comment appears on specific file and line]
```

**Processing Steps:**
1. Agent retrieves PR details including diff
2. Agent analyzes code changes
3. Agent calls `create_pr_review_comment` with file path, line number, and comment
4. Review comment appears inline on the PR diff

### Branch + File Creation Flow

```
[Agent] --> get_branch_sha(owner, repo, "main")
                    |
         [Get SHA of main branch HEAD]
                    |
         --> create_branch(owner, repo, "refs/heads/feature-x", sha)
                    |
         [New branch created from main]
                    |
         --> create_or_update_file(owner, repo, path, content, message, "feature-x")
                    |
         [File committed to feature-x branch]
                    |
         --> create_pull_request(owner, repo, title, "feature-x", "main")
                    |
         [PR created: feature-x -> main]
```

**Processing Steps:**
1. Agent gets the SHA of the base branch (e.g., "main")
2. Agent creates a new feature branch from that SHA
3. Agent creates or updates files on the feature branch
4. Agent creates a pull request from feature branch to base branch

### Code Search Flow

```
[Agent] --> search_code(query, per_page, page)
                    |
         [GET /api/v1/search/code?q={query}]
                    |
         [github-api:3001] --> [GitHub Search API]
                    |
         [Return matching code snippets]
                    |
         [Agent reviews results]
                    |
                    v
         [Optional: get_file_contents for full file]
```

**Processing Steps:**
1. Agent searches code with a query string
2. GitHubAPI sends GET with query, per_page, and page parameters
3. Backend searches via GitHub Search API
4. Returns matching code snippets with repository and file context
5. Agent can retrieve full file contents for deeper analysis

## Error Flow

```
[Tool Function] --> [GitHubAPI Method]
                          |
               [HTTP Request to github-api]
                     |          |
              [Success]    [HTTP Error]
                  |              |
           [Return JSON]   [raise_for_status()]
                              |
                    [httpx.HTTPStatusError]
                              |
                    [FastMCP returns error to client]
```

**Error Handling:**
1. All GitHubAPI methods call `response.raise_for_status()`
2. HTTP errors propagate as `httpx.HTTPStatusError`
3. FastMCP framework catches exceptions and returns error responses
4. No custom error handling in the MCP layer (thin wrapper principle)
