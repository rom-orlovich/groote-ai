# LlamaIndex MCP - Flows

## Process Flows

### Knowledge Query Flow

```
[Agent] --> knowledge_query(query, org_id, source_types, top_k, task_id)
                    |
         [Publish query event to Redis]
                    |
         [POST /query to llamaindex-service:8002]
                    |
         [LlamaIndex hybrid search (vector + graph)]
                    |
         [Publish result event to Redis]
                    |
         [Format results as markdown]
                    |
         [Return formatted results to agent]
```

**Processing Steps:**
1. Agent calls `knowledge_query` with query and org_id
2. Event publisher sends `knowledge:query` event to Redis stream
3. Tool sends POST to LlamaIndex service with query, org_id, source_types, top_k
4. LlamaIndex performs hybrid search (vector similarity + graph traversal)
5. Event publisher sends `knowledge:result` with count and timing
6. Results formatted as markdown with source type, score, and content preview
7. Returns "No relevant results found." if empty

### Code Search Flow

```
[Agent] --> code_search(query, org_id, repo_filter, language, top_k, task_id)
                    |
         [Publish query event to Redis]
                    |
         [POST /query/code to llamaindex-service:8002]
                    |
         [Code-specific vector search with filters]
                    |
         [Publish result event to Redis]
                    |
         [Format: repo/file_path (lines X-Y) with code block]
                    |
         [Return formatted code snippets]
```

**Processing Steps:**
1. Agent calls `code_search` with query and optional filters
2. Event publisher logs the query
3. Tool sends POST with repo and language filters
4. LlamaIndex searches code index with applied filters
5. Results formatted with file paths, line ranges, and syntax highlighting
6. Returns "No code matches found." if empty

### Graph Relationship Flow

```
[Agent] --> find_related_code(entity, entity_type, org_id, relationship)
                    |
         [POST /graph/related to llamaindex-service:8002]
                    |
         [Knowledge graph traversal]
                    |
         [Return relationships grouped by type]
                    |
         [Format: ## Related Code Entities]
                    |
         [### CALLS / ### IMPORTS / ### EXTENDS]
```

**Processing Steps:**
1. Agent calls `find_related_code` with entity name and type
2. Tool sends POST to graph/related endpoint
3. LlamaIndex traverses the knowledge graph
4. Returns relationships grouped by type (calls, imports, extends)
5. Formatted as markdown with entity names and file locations

### Jira Ticket Search Flow

```
[Agent] --> search_jira_tickets(query, org_id, project, status, top_k)
                    |
         [POST /query/tickets to llamaindex-service:8002]
                    |
         [Semantic search in Jira index]
                    |
         [Format: [KEY] Summary with status, priority, labels]
                    |
         [Return formatted ticket results]
```

**Processing Steps:**
1. Agent calls `search_jira_tickets` with query and optional project/status filters
2. Tool sends POST with filters to LlamaIndex service
3. Service performs semantic search on indexed Jira tickets
4. Results formatted with issue key, summary, status, priority, labels
5. Content preview truncated to 500 characters

### Confluence Search Flow

```
[Agent] --> search_confluence(query, org_id, space, top_k)
                    |
         [POST /query/docs to llamaindex-service:8002]
                    |
         [Semantic search in Confluence index]
                    |
         [Format: Page Title (Space) with content preview]
                    |
         [Return formatted documentation excerpts]
```

**Processing Steps:**
1. Agent calls `search_confluence` with query and optional space filter
2. Tool sends POST with filters to LlamaIndex service
3. Service performs semantic search on indexed Confluence pages
4. Results formatted with page title, space, last modified date
5. Content preview truncated to 1000 characters

## Event Publishing Flow

```
[Tool invocation] --> [publish_query_event()]
                              |
                    [Check publish_knowledge_events setting]
                         |          |
                     [Disabled]  [Enabled]
                        |           |
                    [Return]   [Check task_id]
                                |        |
                            [None]   [Has ID]
                              |          |
                          [Return]  [XADD task_events]
                                        |
                              [Event stored in Redis stream]
```

**Event Flow:**
1. Tool function calls publish helper before and after HTTP request
2. Publisher checks if events are enabled in settings
3. Publisher checks if task_id is provided (required for publishing)
4. If both conditions met, publishes to Redis `task_events` stream
5. On failure, logs warning but does not block the tool response
