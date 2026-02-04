# LlamaIndex Service - Features

## Overview

Hybrid RAG orchestration service combining vector search (ChromaDB) with graph traversal (GKG). Provides multi-source semantic search across code, Jira tickets, and Confluence docs.

## Core Features

### Hybrid Query

Query across multiple source types with combined results.

**Query Capabilities:**
- Multi-source search (code, tickets, docs)
- Configurable top_k limit
- Relevance-based sorting
- Source type filtering

**Request Parameters:**
- `query` - Search query string
- `source_types` - List of sources to search
- `top_k` - Maximum results to return
- `enable_graph` - Include graph enrichment

### Code-Specific Search

Search code with repository filtering.

**Code Search Features:**
- Repository filtering
- Language filtering
- Function/class search
- File path matching

### Graph Enrichment

Enrich results with code relationship context from GKG.

**Enrichment Types:**
- Callers (what calls this function)
- Callees (what this function calls)
- Dependencies (imports/exports)
- Class relationships

### Query Caching

Cache query results with configurable TTL.

**Cache Configuration:**
- TTL: 300 seconds (configurable)
- Key format: `query:{hash(params)}`
- Invalidation on index update

### Related Entities

Find related code entities via graph.

**Relationship Types:**
- Function calls
- Class inheritance
- Module imports
- Variable references

### Multi-Source Search

Search across different content types.

**Source Types:**
- `code` - Code files from GitHub repos
- `tickets` - Jira issues and comments
- `docs` - Confluence pages

## API Endpoints

### Query

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/query` | POST | Hybrid query across all sources |
| `/query/code` | POST | Code-specific search |
| `/query/tickets` | POST | Jira ticket search |
| `/query/docs` | POST | Confluence document search |

### Graph

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/graph/related` | POST | Find related entities via graph |

### Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/collections` | GET | List ChromaDB collections |
| `/health` | GET | Health check endpoint |

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| CHROMADB_URL | localhost:8000 | ChromaDB server URL |
| GKG_SERVICE_URL | localhost:9000 | GKG service URL |
| CACHE_TTL | 300 | Cache TTL in seconds |
| DEFAULT_TOP_K | 10 | Default results limit |
| ENABLE_GRAPH_ENRICHMENT | true | Enable graph enrichment |
