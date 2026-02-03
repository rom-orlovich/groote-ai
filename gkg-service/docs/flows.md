# GKG Service - Flows

## Process Flows

### Dependency Query Flow

```
[Client] → POST /analyze/dependencies
                     ↓
            [Parse Request]
            {file_path, depth}
                     ↓
            [Check Cache]
               ↓       ↓
           [Hit]     [Miss]
               ↓       ↓
          [Return]  [Query Graph]
                         ↓
                [Build Dependency Tree]
                         ↓
                [Traverse to depth]
                         ↓
                [Cache Result]
                         ↓
                [Return Dependencies]
```

**Processing Steps:**
1. Receive POST request with file_path and depth
2. Check cache for existing result
3. If cached, return cached result
4. Query graph analyzer for direct dependencies
5. Recursively traverse to specified depth
6. Build dependency tree structure
7. Cache result with TTL
8. Return dependency tree

### Symbol Usage Flow

```
[Client] → POST /query/usages
                    ↓
           [Parse Request]
           {symbol_name, scope}
                    ↓
           [Query Graph Index]
                    ↓
           [Find All References]
                    ↓
         ┌─────────┼─────────┐
         │         │         │
         ▼         ▼         ▼
   [Definitions] [Calls] [Imports]
         │         │         │
         └─────────┼─────────┘
                   ↓
           [Group by File]
                   ↓
           [Return Usages]
```

**Usage Response:**
```json
{
  "symbol": "process_request",
  "definition": {"file": "main.py", "line": 42},
  "usages": [
    {"file": "handler.py", "line": 15, "type": "call"},
    {"file": "test_main.py", "line": 8, "type": "import"}
  ]
}
```

### Call Graph Flow

```
[Client] → POST /graph/calls
                    ↓
           [Parse Request]
           {function_name, direction, depth}
                    ↓
           [Find Function Node]
                    ↓
           [Traverse Call Edges]
                    ↓
           [Direction?]
               ↓       ↓
          [callers] [callees]
               ↓       ↓
          [Incoming] [Outgoing]
               │       │
               └───────┘
                   ↓
           [Build Graph Structure]
                   ↓
           [Return Call Graph]
```

**Call Graph Response:**
```json
{
  "root": "process_request",
  "direction": "callees",
  "depth": 2,
  "nodes": [
    {"name": "process_request", "file": "main.py", "line": 42},
    {"name": "validate", "file": "utils.py", "line": 10}
  ],
  "edges": [
    {"from": "process_request", "to": "validate"}
  ]
}
```

### Class Hierarchy Flow

```
[Client] → POST /graph/hierarchy
                    ↓
           [Parse Request]
           {class_name, direction}
                    ↓
           [Find Class Node]
                    ↓
           [Traverse Inheritance]
                    ↓
           [Direction?]
               ↓       ↓
          [parents] [children]
               ↓       ↓
          [Superclass] [Subclass]
               │       │
               └───────┘
                   ↓
           [Build Hierarchy Tree]
                   ↓
           [Return Hierarchy]
```

**Hierarchy Response:**
```json
{
  "class": "UserService",
  "parents": ["BaseService"],
  "children": ["AdminUserService", "GuestUserService"],
  "interfaces": ["Authenticatable"]
}
```

### Repository Indexing Flow

```
[Client] → POST /index
                ↓
       [Parse Request]
       {repo_path, incremental}
                ↓
       [Load Repository]
                ↓
       [Incremental?]
           ↓       ↓
        [Yes]    [No]
           ↓       ↓
     [Git Diff]  [Full Scan]
           │       │
           └───────┘
                ↓
       [Parse Source Files]
                ↓
       [Extract Entities]
           │
    ┌──────┼──────┐
    │      │      │
    ▼      ▼      ▼
[Classes] [Functions] [Imports]
    │      │      │
    └──────┼──────┘
           ↓
       [Build Relationships]
                ↓
       [Store in Graph DB]
                ↓
       [Return Status]
```

**Indexing Response:**
```json
{
  "status": "completed",
  "files_indexed": 150,
  "entities_extracted": 1200,
  "relationships_created": 3500,
  "duration_seconds": 45.2
}
```

### Cache Management Flow

```
[Query Request] → [Generate Cache Key]
                        ↓
                 [Hash(query_params)]
                        ↓
                 [Check Redis]
                    ↓       ↓
                [Exists]  [Missing]
                    ↓       ↓
               [Return]  [Execute Query]
                              ↓
                         [Cache Result]
                              ↓
                         [Set TTL]
                              ↓
                         [Return Result]
```

**Cache Configuration:**
- TTL: 300 seconds (configurable)
- Invalidation: On repository re-index
- Key format: `gkg:{query_type}:{hash(params)}`
