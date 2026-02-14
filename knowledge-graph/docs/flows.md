# Knowledge Graph - Flows

## Process Flows

### Create Node Flow

```
[Client] -> POST /api/v1/nodes -> [Handler: parse CreateNodeRequest]
                                          |
                                  [Acquire write lock]
                                          |
                                  [Generate UUID + timestamps]
                                          |
                                  [Add to petgraph DiGraph]
                                          |
                                  [Store in nodes HashMap]
                                          |
                                  [201 Created {id, node}]
```

**Processing Steps:**
1. Parse JSON body into CreateNodeRequest
2. Convert request to Node with auto-generated UUID and timestamps
3. Acquire write lock on KnowledgeGraph
4. Add node UUID to petgraph, store NodeIndex mapping
5. Insert Node into nodes HashMap
6. Return 201 with node ID and full node data

### Create Edge Flow

```
[Client] -> POST /api/v1/edges -> [Handler: parse CreateEdgeRequest]
                                          |
                                  [Acquire write lock]
                                          |
                                  [Lookup source + target NodeIndex]
                                       |            |
                                  [Not Found]   [Both Found]
                                      |              |
                                 [400 Error]   [Add to petgraph]
                                                     |
                                              [Store in edges HashMap]
                                                     |
                                              [201 Created {id, edge}]
```

**Processing Steps:**
1. Parse JSON body into CreateEdgeRequest
2. Acquire write lock on KnowledgeGraph
3. Look up source and target node indices
4. If either node missing, return 400 "Source or target node not found"
5. Add weighted edge to petgraph DiGraph
6. Store Edge in edges HashMap
7. Return 201 with edge ID and full edge data

### Path Finding Flow

```
[Client] -> POST /api/v1/query/path -> [Handler: parse PathQuery]
                                               |
                                       [Acquire read lock]
                                               |
                                       [Lookup source + target indices]
                                               |
                                       [Run Dijkstra algorithm]
                                            |          |
                                       [No Path]  [Path Found]
                                          |            |
                                     [404 Error]  [Reconstruct path]
                                                       |
                                                [Resolve node names]
                                                       |
                                                [200 OK {path, names, weight}]
```

**Processing Steps:**
1. Parse source_id, target_id from request
2. Acquire read lock on KnowledgeGraph
3. Map UUIDs to petgraph NodeIndex values
4. Run Dijkstra's algorithm from source to target
5. If target unreachable, return 404
6. Backtrack from target to source using distance map
7. Resolve UUID path to node names
8. Return PathResult with path, node_names, total_weight

### Neighbor Discovery Flow

```
[Client] -> POST /api/v1/query/neighbors -> [Handler: parse NeighborsQuery]
                                                     |
                                             [Acquire read lock]
                                                     |
                                             [BFS from node_id]
                                                     |
                                         [Filter by direction + edge_types]
                                                     |
                                             [Traverse up to depth]
                                                     |
                                             [200 OK {neighbors, count}]
```

**Processing Steps:**
1. Parse node_id, optional direction/edge_types/depth
2. Default direction to "both", depth to 1
3. Acquire read lock on KnowledgeGraph
4. Initialize BFS with starting node
5. For each depth level, find connected edges matching filters
6. Collect unique neighbor nodes not yet visited
7. Return neighbor nodes with count

### Search Nodes Flow

```
[Client] -> POST /api/v1/query/search -> [Handler: parse SearchQuery]
                                                 |
                                         [Acquire read lock]
                                                 |
                                         [Iterate all nodes]
                                                 |
                                     [Filter by name/description match]
                                                 |
                                     [Filter by node_type + language]
                                                 |
                                         [Apply limit]
                                                 |
                                         [200 OK {results, count}]
```

**Processing Steps:**
1. Parse query string, optional node_types/language/limit
2. Default limit to 20
3. Acquire read lock on KnowledgeGraph
4. Scan all nodes, case-insensitive substring match on name and description
5. Filter by node type if specified
6. Filter by language if specified
7. Take up to limit results
8. Return matching nodes with count

## Health Check Flow

```
[Client] -> GET /health -> [Return {"status": "healthy", "service": "knowledge-graph"}]
```

## Statistics Flow

```
[Client] -> GET /api/v1/stats -> [Acquire read lock]
                                         |
                                 [Count nodes by type]
                                         |
                                 [Count edges by type]
                                         |
                                 [Calculate avg edges/node]
                                         |
                                 [200 OK {GraphStats}]
```
