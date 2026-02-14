# Knowledge Graph MCP Development Guide

## Overview

Dual-backend MCP wrapper: 7 graph query tools via Knowledge Graph service (port 4000) and 5 vector storage tools via ChromaDB. Exposes 12 tools total for code search and knowledge management.

## Key Principles

1. **Dual Backend** - Graph queries via KG service, vector storage via ChromaDB
2. **Passthrough Design** - Parameters passed directly to backends
3. **Formatted Output** - Results formatted for LLM consumption

## Structure

```
knowledge-graph-mcp/
├── main.py            # FastMCP server + 12 tool registrations
├── kg_client.py       # KnowledgeGraphClient (HTTP to KG :4000)
├── chroma_client.py   # ChromaDBClient (HTTP to ChromaDB)
├── config.py          # Settings (KG_ prefix env vars)
├── models.py          # Pydantic models
├── requirements.txt
├── Dockerfile
└── tools/
    └── __init__.py
```

## Tools (12)

**Graph (7):** search_codebase, find_symbol_references, get_code_structure, find_dependencies, find_code_path, get_code_neighbors, get_graph_stats

**Vector (5):** knowledge_store, knowledge_query, knowledge_collections, knowledge_update, knowledge_delete

## Adding a New Graph Tool

1. Add HTTP method in `kg_client.py` (KnowledgeGraphClient class)
2. Add tool function in `main.py` with `@mcp.tool()` decorator
3. Ensure corresponding endpoint exists in Knowledge Graph service

## Adding a New Vector Tool

1. Add method in `chroma_client.py` (ChromaDBClient class)
2. Add tool function in `main.py` with `@mcp.tool()` decorator

## Testing Locally

```bash
docker-compose --profile knowledge up knowledge-graph chromadb
python main.py
curl http://localhost:9005/sse
```

## Development

- Port: 9005
- Language: Python
- Framework: FastMCP
- Max 300 lines per file, no comments, strict types, async/await for I/O
