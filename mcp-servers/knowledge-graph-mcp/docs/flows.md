# Knowledge Graph MCP - Flows

## Process Flows

### Code Search Flow

```
[Agent] --> search_codebase(query, node_types, language, limit)
                    |
         [KnowledgeGraphClient.search_nodes()]
                    |
         [POST /api/v1/query/search to knowledge-graph:4000]
                    |
         [Return matching code entities with relationships]
                    |
         [Agent analyzes search results]
```

**Processing Steps:**
1. Agent calls `search_codebase` with query and optional filters
2. KnowledgeGraphClient sends POST to Knowledge Graph service
3. Service performs graph search with node_types and language filters
4. Returns matching code entities with metadata
5. Agent uses results to understand code structure

### Dependency Analysis Flow

```
[Agent] --> search_codebase("MyClass")
                    |
         [Find entity node_id from results]
                    |
         --> find_dependencies(node_id, "outgoing")
                    |
         [POST /api/v1/query/neighbors]
                    |
         [Returns: imports, calls, inherits relationships]
                    |
         --> find_dependencies(node_id, "incoming")
                    |
         [Returns: what depends on this entity]
```

**Processing Steps:**
1. Agent searches for a code entity by name
2. Agent extracts the node_id from search results
3. Agent queries outgoing dependencies (what the entity uses)
4. Agent queries incoming dependencies (what uses the entity)
5. Agent builds a dependency picture

### Code Path Discovery Flow

```
[Agent] --> search_codebase("functionA")
                    |
         [Get source node_id]
                    |
         --> search_codebase("functionB")
                    |
         [Get target node_id]
                    |
         --> find_code_path(source_id, target_id)
                    |
         [POST /api/v1/query/path]
                    |
         [Returns relationship chain: A -> calls -> C -> imports -> B]
```

**Processing Steps:**
1. Agent finds source entity node_id
2. Agent finds target entity node_id
3. Agent calls `find_code_path` with both IDs
4. Knowledge Graph finds shortest relationship path
5. Returns chain of entities and relationships connecting them

### Knowledge Store/Query Flow

```
[Agent] --> knowledge_store(content, metadata, collection)
                    |
         [ChromaDBClient.store_document()]
                    |
         [collection.add(documents, metadatas, ids)]
                    |
         [Returns: {success, id, collection}]
                    |
         [Later...]
                    |
         --> knowledge_query(query, n_results, collection)
                    |
         [ChromaDBClient.query_documents()]
                    |
         [collection.query(query_texts, n_results)]
                    |
         [Returns: similar documents with distances]
```

**Processing Steps:**
1. Agent stores knowledge with content, metadata, and collection name
2. ChromaDBClient adds document to the specified collection
3. Document ID auto-generated if not provided
4. Later, agent queries with natural language
5. ChromaDB returns semantically similar documents ranked by distance

### Collection Management Flow

```
[Agent] --> knowledge_collections("list")
                    |
         [Returns all collections with document counts]
                    |
         --> knowledge_collections("create", "project-notes")
                    |
         [New collection created]
                    |
         --> knowledge_store(content, metadata, "project-notes")
                    |
         [Document stored in new collection]
                    |
         --> knowledge_collections("delete", "old-collection")
                    |
         [Collection and all documents deleted]
```

**Processing Steps:**
1. Agent lists existing collections to understand available knowledge
2. Agent creates a new collection for a specific purpose
3. Agent stores documents in the new collection
4. Agent can delete obsolete collections

### Document Update/Delete Flow

```
[Agent] --> knowledge_query("search term", collection="notes")
                    |
         [Returns documents with IDs]
                    |
         --> knowledge_update(doc_id, content="updated text", collection="notes")
                    |
         [Document updated in place]
                    |
         --> knowledge_delete(doc_id, collection="notes")
                    |
         [Document removed from collection]
```

**Processing Steps:**
1. Agent queries to find documents
2. Agent extracts document IDs from results
3. Agent updates content or metadata using document ID
4. Agent can delete documents that are no longer relevant

## Error Flow

### Graph Query Errors

```
[Tool Function] --> [KnowledgeGraphClient Method]
                          |
               [HTTP Request to knowledge-graph:4000]
                     |          |
              [Success]    [HTTP Error]
                  |              |
           [Return JSON]   [raise_for_status()]
                              |
                    [httpx.HTTPStatusError]
                              |
                    [FastMCP returns error to client]
```

### Vector Store Errors

```
[Tool Function] --> [ChromaDBClient Method]
                          |
               [ChromaDB Operation]
                     |          |
              [Success]    [ChromaDB Error]
                  |              |
           [Return dict]   [Exception propagates]
                              |
                    [FastMCP returns error to client]
```
