# Knowledge Graph MCP Server

> FastMCP-based MCP server for code search and vector knowledge storage.

## Purpose

The Knowledge Graph MCP server provides a Model Context Protocol interface for two backends: the Knowledge Graph service (Rust graph database, port 4000) for semantic code search, and ChromaDB for vector-based knowledge storage. It exposes 12 tools total.

## Architecture

```
Agent Engine (via mcp.json)
         |
         | SSE Connection
         v
+-----------------------------------------+
|   Knowledge Graph MCP :9005              |
|                                          |
|  Graph Tools (7)  |  Vector Tools (5)    |
|  kg_client.py     |  chroma_client.py    |
+-----------------------------------------+
         |                    |
         | HTTP               | HTTP
         v                    v
+------------------+  +------------------+
| Knowledge Graph  |  | ChromaDB         |
| :4000 (Rust)     |  | (Vector Store)   |
+------------------+  +------------------+
```

## Folder Structure

```
knowledge-graph-mcp/
├── main.py            # FastMCP server + 12 tool registrations
├── kg_client.py       # KnowledgeGraphClient (HTTP to KG :4000)
├── chroma_client.py   # ChromaDBClient (HTTP to ChromaDB)
├── config.py          # Settings (KG_PORT, KG_KNOWLEDGE_GRAPH_URL)
├── models.py          # Pydantic models for types
├── requirements.txt   # Dependencies
├── Dockerfile
└── tools/
    └── __init__.py    # Re-exports
```

## MCP Tools (12)

### Graph Tools (7) - Knowledge Graph :4000

| Tool | Description |
|------|-------------|
| `search_codebase` | Search code entities by query, node types, language |
| `find_symbol_references` | Find all references to a symbol |
| `get_code_structure` | Get repository/directory file structure |
| `find_dependencies` | Find incoming or outgoing code dependencies |
| `find_code_path` | Find relationship path between two entities |
| `get_code_neighbors` | Get neighboring entities by edge type and depth |
| `get_graph_stats` | Get graph node/edge statistics |

### Vector Tools (5) - ChromaDB

| Tool | Description |
|------|-------------|
| `knowledge_store` | Store document with metadata in a collection |
| `knowledge_query` | Semantic search in a collection (cosine similarity) |
| `knowledge_collections` | List, create, or delete collections |
| `knowledge_update` | Update document content or metadata |
| `knowledge_delete` | Delete document from collection |

## Environment Variables

```bash
KG_KNOWLEDGE_GRAPH_URL=http://knowledge-graph:4000
KG_PORT=9005
KG_REQUEST_TIMEOUT=30
CHROMA_HOST=chromadb
CHROMA_PORT=8000
```

## SSE Endpoint

MCP clients connect via Server-Sent Events:

```
GET /sse HTTP/1.1
Host: knowledge-graph-mcp:9005
Accept: text/event-stream
```

## Health Check

```bash
curl http://localhost:9005/health
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md) - Component diagrams and data flows
- [Features](docs/features.md) - Feature list and capabilities
- [Flows](docs/flows.md) - Process flow documentation

## Related Services

- **knowledge-graph**: Rust-based graph database service (port 4000)
- **ChromaDB**: Vector store for knowledge documents
- **agent-engine**: Connects to this MCP server via SSE
