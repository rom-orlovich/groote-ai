# LlamaIndex Service - Flows

## Process Flows

### Hybrid Query Flow

```
[Client] → POST /query → [Parse Request]
                              ↓
                      [Check Cache]
                         ↓       ↓
                     [Hit]     [Miss]
                         ↓       ↓
                    [Return]  [Continue]
                                  ↓
                      [For each source_type:]
                              │
              ┌───────────────┼───────────────┐
              │               │               │
              ▼               ▼               ▼
          [Code]         [Tickets]        [Docs]
              │               │               │
              ▼               ▼               ▼
        [ChromaDB]      [ChromaDB]      [ChromaDB]
              │               │               │
              └───────────────┼───────────────┘
                              ↓
                      [Combine Results]
                              ↓
                      [Graph Enrichment?]
                         ↓       ↓
                       [Yes]   [No]
                         ↓       │
                   [Query GKG]   │
                         │       │
                         └───────┘
                              ↓
                      [Sort by Score]
                              ↓
                      [Limit to top_k]
                              ↓
                      [Cache Results]
                              ↓
                      [Return Response]
```

**Processing Steps:**
1. Receive POST request with query and source_types
2. Check cache for existing results
3. If cached, return cached results immediately
4. Query vector store for each requested source type
5. Combine results from all sources
6. If GKG enrichment enabled, add relationship context
7. Sort results by relevance score
8. Limit to top_k results
9. Cache results with TTL
10. Return response

### Code Query Flow

```
[Client] → POST /query/code → [Parse Request]
                                    ↓
                           [Set source_types=["code"]]
                                    ↓
                           [Apply Repository Filter]
                                    ↓
                           [Query Code Collection]
                                    ↓
                           [Graph Enrichment?]
                              ↓       ↓
                            [Yes]   [No]
                              ↓       │
                          [Add Context] │
                              │       │
                              └───────┘
                                    ↓
                           [Return Results]
```

**Processing Steps:**
1. Receive POST request with code-specific query
2. Set source_types to ["code"] only
3. Apply repository filter if provided
4. Query code collection in vector store
5. Optionally enrich with graph context
6. Return code-specific results

### Graph Enrichment Flow

```
[Code Results] → [For each result:]
                        ↓
               [Extract file_path, symbol]
                        ↓
               [Query GKG Service]
                        │
       ┌────────────────┼────────────────┐
       │                │                │
       ▼                ▼                ▼
  [Callers]        [Callees]      [Dependencies]
       │                │                │
       └────────────────┼────────────────┘
                        ↓
               [Add to result.context]
                        ↓
               [Return Enriched Results]
```

**Processing Steps:**
1. Take code search results
2. For each code result, extract file path and symbol
3. Query GKG for relationships
4. Add callers/callees/dependencies to result context
5. Return enriched results

### Related Entities Flow

```
[Client] → POST /graph/related → [Parse Request]
                                       ↓
                              [Check Graph Store]
                                    ↓       ↓
                              [Available] [Unavailable]
                                    ↓       ↓
                             [Query Graph] [Return Empty]
                                    ↓
                              [Build Relationship Map]
                                    ↓
                              [Return Response]
```

**Processing Steps:**
1. Receive POST request with entity info
2. Check if graph store is available
3. If not available, return empty map
4. Query graph store for relationships
5. Build relationship map
6. Return relationship response

### Caching Flow

```
[Query Request] → [Generate Cache Key]
                        ↓
                [Hash(query_params)]
                        ↓
                [Check Redis Cache]
                    ↓       ↓
               [Found]   [Not Found]
                    ↓       ↓
               [Check TTL] [Execute Query]
                    │           ↓
                    ▼       [Store with TTL]
               [Return]         ↓
                    ↓       [Return]
                    └───────────┘
```

**Cache Configuration:**
- TTL: 300 seconds (configurable)
- Key format: `llamaindex:{query_type}:{hash(params)}`
- Invalidation: On repository re-index

### Ticket Query Flow

```
[Client] → POST /query/tickets → [Parse Request]
                                       ↓
                              [Set source_types=["tickets"]]
                                       ↓
                              [Query Tickets Collection]
                                       ↓
                              [Filter by Project (optional)]
                                       ↓
                              [Sort by Relevance]
                                       ↓
                              [Return Results]
```

**Processing Steps:**
1. Receive POST request with ticket query
2. Set source_types to ["tickets"]
3. Query tickets collection in ChromaDB
4. Apply project filter if provided
5. Sort by relevance score
6. Return ticket results

### Docs Query Flow

```
[Client] → POST /query/docs → [Parse Request]
                                    ↓
                           [Set source_types=["docs"]]
                                    ↓
                           [Query Docs Collection]
                                    ↓
                           [Filter by Space (optional)]
                                    ↓
                           [Sort by Relevance]
                                    ↓
                           [Return Results]
```

**Processing Steps:**
1. Receive POST request with docs query
2. Set source_types to ["docs"]
3. Query docs collection in ChromaDB
4. Apply space filter if provided
5. Sort by relevance score
6. Return documentation results
