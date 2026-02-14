# Knowledge Graph MCP - Features

## Overview

FastMCP-based MCP server that exposes 12 tools across two backends: graph queries via the Knowledge Graph service and vector storage via ChromaDB. Provides semantic code search, dependency tracking, and persistent knowledge storage.

## Core Features

### Semantic Code Search

Search for code entities across the knowledge graph using natural language or symbol names.

**Capabilities:**
- Search by query string, node types (function, class, file, module), and language
- Find all references to a specific symbol across the codebase
- Get repository or directory structure with code entities
- Configurable result limits

### Dependency Analysis

Track and navigate code dependencies and relationships.

**Capabilities:**
- Find outgoing dependencies (what a symbol uses) and incoming (what uses it)
- Discover relationship paths between two code entities
- Get neighboring entities filtered by edge types (calls, imports, inherits)
- Configurable traversal depth

### Graph Statistics

Monitor the knowledge graph for size and composition.

**Capabilities:**
- Total node and edge counts
- Breakdown by node type and edge type

### Vector Knowledge Storage

Store and retrieve knowledge documents in ChromaDB with semantic search.

**Capabilities:**
- Store documents with metadata tags in named collections
- Query documents by semantic similarity with configurable result count
- Manage collections (list, create, delete)
- Update and delete individual documents

### Dual Backend Architecture

Combines graph-based code intelligence with vector-based knowledge retrieval.

**Backend Split:**
- Graph queries routed to Knowledge Graph service (Rust, port 4000)
- Vector operations handled by ChromaDB (port 8000)
- Each backend independently scalable

## MCP Tools

### Graph Tools (7)

| Tool | Description |
|------|-------------|
| `search_codebase` | Search knowledge graph for code entities |
| `find_symbol_references` | Find all references to a symbol |
| `get_code_structure` | Get repository/directory file structure |
| `find_dependencies` | Find outgoing or incoming dependencies |
| `find_code_path` | Find relationship path between two entities |
| `get_code_neighbors` | Get neighboring entities by edge type and depth |
| `get_graph_stats` | Get graph node/edge statistics |

### Vector Tools (5)

| Tool | Description |
|------|-------------|
| `knowledge_store` | Store document in ChromaDB collection |
| `knowledge_query` | Semantic search in ChromaDB collection |
| `knowledge_collections` | List, create, or delete collections |
| `knowledge_update` | Update existing document content or metadata |
| `knowledge_delete` | Delete document from collection |
