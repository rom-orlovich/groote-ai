# GKG MCP - Flows

## Process Flows

### Dependency Analysis Flow

```
[Agent] --> analyze_dependencies(file_path, org_id, repo, depth)
                    |
         [POST /analyze/dependencies to gkg-service:8003]
                    |
         [GKG traverses dependency graph to specified depth]
                    |
         [Returns formatted_output (dependency tree)]
                    |
         [Agent receives dependency tree string]
```

**Processing Steps:**
1. Agent calls `analyze_dependencies` with file path, org_id, and repo
2. Tool sends POST to GKG service with depth parameter (default: 3)
3. GKG service traverses the knowledge graph for import/dependency edges
4. Returns formatted dependency tree string
5. Agent uses tree to understand file relationships

### Symbol Usage Flow

```
[Agent] --> find_usages(symbol, org_id, repo)
                    |
         [POST /query/usages to gkg-service:8003]
                    |
         [GKG searches for symbol references]
                    |
         [Returns usages: [{file, line, context}]]
                    |
         [Format: ## Usages of `symbol`]
                    |
         [- file.py:42 (function call)]
```

**Processing Steps:**
1. Agent calls `find_usages` with symbol name and optional repo filter
2. Tool sends POST to GKG service
3. GKG searches indexed code for all references
4. Tool formats results as markdown list with file:line entries
5. Returns "No usages found" if empty

### Call Graph Flow

```
[Agent] --> get_call_graph(function_name, org_id, repo, direction, depth)
                    |
         [POST /graph/calls to gkg-service:8003]
                    |
         [GKG traverses call relationships]
                    |
                    v
              [direction?]
              |     |     |
         [callers] [callees] [both]
              |     |     |
         [Functions that  [Functions this  [Both directions]
          call this one]   one calls]
                    |
         [Returns formatted_graph (call tree visualization)]
```

**Processing Steps:**
1. Agent calls `get_call_graph` with function name and direction
2. Tool sends POST to GKG service with direction and depth
3. GKG traverses call edges in the specified direction
4. Returns formatted call graph visualization
5. Returns "No call graph found" if no relationships exist

### Class Hierarchy Flow

```
[Agent] --> get_class_hierarchy(class_name, org_id, repo)
                    |
         [POST /graph/hierarchy to gkg-service:8003]
                    |
         [GKG traverses inheritance edges]
                    |
         [Returns formatted_hierarchy]
                    |
         [Agent sees parent/child class tree]
```

**Processing Steps:**
1. Agent calls `get_class_hierarchy` with class name
2. Tool sends POST to GKG service with optional repo filter
3. GKG traverses inherits/extends edges in both directions
4. Returns formatted hierarchy showing parents and children
5. Returns "No hierarchy found" if class has no inheritance

### Related Entities Flow

```
[Agent] --> get_related_entities(entity, entity_type, org_id, relationship)
                    |
         [POST /graph/related to gkg-service:8003]
                    |
         [GKG finds related entities by relationship]
                    |
         [Returns relationships: {type: [entities]}]
                    |
         [Format: ## Related Entities for `entity`]
                    |
         [### CALLS]
         [- `helper` in utils.py:15]
         [### IMPORTS]
         [- `module` in lib.py:1]
```

**Processing Steps:**
1. Agent calls `get_related_entities` with entity name, type, and relationship filter
2. Tool sends POST to GKG service
3. GKG finds entities connected by specified relationship types
4. Tool formats results grouped by relationship type
5. Each entry shows entity name, file, and line number

## Error Flow

```
[Tool Function] --> [httpx.AsyncClient]
                          |
               [HTTP POST to gkg-service:8003]
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
1. All tools use inline `httpx.AsyncClient` (not a shared client)
2. HTTP errors propagate as `httpx.HTTPStatusError`
3. FastMCP framework catches exceptions and returns error responses
4. Structured logging captures errors with context
