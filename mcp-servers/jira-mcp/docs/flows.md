# Jira MCP - Flows

## Process Flows

### Tool Invocation Flow

```
[MCP Client] --> SSE /sse --> [FastMCP Server :9002]
                                        |
                              [Dispatch to Tool Function]
                                        |
                              [JiraAPI Client Method]
                                        |
                              [HTTP Request to jira-api:3002]
                                        |
                              [Return JSON Response]
                                        |
                              [MCP Response to Client]
```

**Processing Steps:**
1. MCP client connects via SSE to port 9002
2. Client sends MCP tool call with parameters
3. FastMCP dispatches to registered tool function
4. Tool function calls corresponding JiraAPI method
5. JiraAPI sends HTTP request to jira-api:3002
6. Backend returns JSON response
7. Tool function returns result to MCP framework
8. MCP framework sends response back via SSE

### Issue Creation Flow

```
[Agent] --> create_jira_issue(project_key, summary, description, issue_type)
                    |
         [JiraAPI.create_issue()]
                    |
         [POST /api/v1/issues]
                    |
                    v
         [jira-api:3002] --> [Jira REST API]
                    |
         [Return created issue key and details]
                    |
         [Agent receives issue key (e.g., PROJ-123)]
```

**Processing Steps:**
1. Agent calls `create_jira_issue` with project_key, summary, description
2. Description should use markdown with Overview, Acceptance Criteria, Technical Notes
3. JiraAPI sends POST to jira-api service with all fields
4. Backend creates issue via Jira REST API
5. Returns created issue details including new issue key

### Issue Transition Flow

```
[Agent] --> get_jira_transitions(issue_key)
                    |
         [GET /api/v1/issues/{key}/transitions]
                    |
         [Returns available transitions with IDs]
                    |
         --> transition_jira_issue(issue_key, transition_id)
                    |
         [POST /api/v1/issues/{key}/transitions]
                    |
         [Issue moved to new status]
```

**Processing Steps:**
1. Agent queries available transitions for an issue
2. Backend returns list of transitions with IDs and target statuses
3. Agent selects appropriate transition ID
4. Agent calls `transition_jira_issue` with issue key and transition ID
5. Issue status changes in Jira

### JQL Search Flow

```
[Agent] --> search_jira_issues(jql, max_results, start_at)
                    |
         [POST /api/v1/search]
                    |
         [jira-api:3002] --> [Jira Search API]
                    |
         [Return matching issues with pagination]
                    |
         [Agent processes results]
```

**Processing Steps:**
1. Agent constructs JQL query (e.g., `project=PROJ AND status=Open`)
2. Tool sends POST with jql, max_results, and start_at for pagination
3. Backend executes JQL via Jira REST API
4. Returns matching issues with summary, status, and metadata

### Project Setup Flow

```
[Agent] --> create_jira_project(key, name, project_type_key)
                    |
         [POST /api/v1/projects]
                    |
         [Project created in Jira]
                    |
         --> create_jira_board(name, project_key, board_type)
                    |
         [POST /api/v1/boards]
                    |
         [Board created with auto-generated JQL filter]
```

**Processing Steps:**
1. Agent creates a new project with key and name
2. Backend creates project via Jira REST API
3. Agent creates a board (Kanban or Scrum) for the project
4. Backend creates board with auto-generated JQL filter

## Error Flow

```
[Tool Function] --> [JiraAPI Method]
                          |
               [HTTP Request to jira-api]
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
1. All JiraAPI methods call `response.raise_for_status()`
2. HTTP errors propagate as `httpx.HTTPStatusError`
3. FastMCP framework catches exceptions and returns error responses
