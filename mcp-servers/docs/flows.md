# MCP Servers - Flows

## Process Flows

### MCP Connection Flow (All Servers)

```
[Agent Engine] --> GET /sse --> [MCP Server]
                                     |
                        [SSE Connection Established]
                                     |
                        [Agent sends tool calls]
                                     |
                        [Server dispatches to tool function]
                                     |
                        [Tool calls backend HTTP service]
                                     |
                        [Response returned via SSE]
```

**Processing Steps:**
1. Agent Engine connects to MCP server via SSE endpoint
2. SSE connection maintained for duration of session
3. Agent sends MCP tool call requests
4. FastMCP dispatches to registered tool function
5. Tool function calls backend service via HTTP
6. Response returned to agent via SSE stream

### External Service Flow (GitHub, Jira, Slack)

```
[Agent] --> [MCP Tool Call]
                 |
         [MCP Server :900X]
                 |
         [HTTP to API Service :300X]
                 |
         [API Service adds credentials]
                 |
         [HTTPS to External API]
                 |
         [Response back through chain]
```

**Processing Steps:**
1. Agent calls MCP tool (e.g., `create_jira_issue`)
2. MCP server translates to HTTP request (no credentials)
3. API service adds authentication (tokens, API keys)
4. API service calls external API (Jira, GitHub, Slack)
5. Response flows back: External API -> API Service -> MCP -> Agent

### Knowledge Service Flow (KG, LlamaIndex, GKG)

```
[Agent] --> [MCP Tool Call]
                 |
         [MCP Server :900X]
                 |
         [HTTP to Knowledge Service]
                 |
         [Service processes query]
                 |
         [Formatted response to Agent]
```

**Processing Steps:**
1. Agent calls MCP tool (e.g., `search_codebase`)
2. MCP server translates to HTTP POST with query parameters
3. Knowledge service processes query (graph traversal, vector search, etc.)
4. Response formatted as markdown for LLM readability
5. Formatted response returned to agent

### Knowledge Graph MCP Dual-Backend Flow

```
[Agent] --> [Graph Tool]              [Agent] --> [Vector Tool]
                 |                                      |
         [KnowledgeGraphClient]                [ChromaDBClient]
                 |                                      |
         [knowledge-graph:4000]                 [ChromaDB:8000]
                 |                                      |
         [Rust graph query]                    [Vector similarity]
                 |                                      |
         [Return entities]                     [Return documents]
```

**Processing Steps (Graph):**
1. Agent calls graph tool (e.g., `find_dependencies`)
2. KnowledgeGraphClient sends HTTP POST to Knowledge Graph service
3. Rust service performs graph traversal
4. Returns code entities with relationships

**Processing Steps (Vector):**
1. Agent calls vector tool (e.g., `knowledge_query`)
2. ChromaDBClient calls ChromaDB HTTP API
3. ChromaDB performs cosine similarity search
4. Returns documents ranked by semantic distance

### LlamaIndex MCP Event Flow

```
[Agent] --> knowledge_query(query, org_id)
                    |
         [publish_query_event to Redis]
                    |
         [POST /query to llamaindex:8002]
                    |
         [Hybrid search: vector + graph]
                    |
         [publish_result_event to Redis]
                    |
         [Format markdown results]
                    |
         [Return to Agent]
```

**Processing Steps:**
1. Agent calls `knowledge_query` with query and org_id
2. Event publisher logs query event to Redis stream
3. HTTP POST to LlamaIndex service with search parameters
4. LlamaIndex performs hybrid search (vector + graph)
5. Event publisher logs result event with timing metrics
6. Results formatted as markdown and returned to agent

### Agent Workflow: Research-Act Pattern

```
[Agent receives task from webhook]
         |
         v
[Phase 1: Research]
         |
   [search_codebase] --> [find_dependencies] --> [knowledge_query]
         |
         v
[Phase 2: Plan]
         |
   [search_jira_tickets] --> [get_jira_issue] --> [create_jira_issue]
         |
         v
[Phase 3: Act]
         |
   [create_branch] --> [create_or_update_file] --> [create_pull_request]
         |
         v
[Phase 4: Report]
         |
   [add_jira_comment] --> [send_slack_message]
```

**Processing Steps:**
1. Agent uses knowledge tools to research the codebase
2. Agent uses Jira tools to understand and create tasks
3. Agent uses GitHub tools to create branches, write code, and open PRs
4. Agent uses Jira and Slack tools to report results

## Error Flow (All Servers)

```
[Tool Function] --> [Backend HTTP Call]
                         |         |
                  [Success]   [HTTP Error]
                      |            |
               [Return data]  [raise_for_status()]
                                   |
                         [httpx.HTTPStatusError]
                                   |
                         [FastMCP error response]
                                   |
                         [Agent receives error]
```

**Error Handling:**
1. All servers use `response.raise_for_status()` for HTTP errors
2. Exceptions propagate to FastMCP framework
3. FastMCP returns structured error response to agent
4. Agent can retry or adjust strategy based on error
