# Knowledge Services Setup

The Knowledge Layer provides advanced code search, semantic retrieval, and code relationship analysis. It's optional but enhances agent capabilities.

## Overview

| Service | Port | Purpose |
|---------|------|---------|
| Knowledge Graph | 4000 | Code entity indexing (Rust) |
| ChromaDB | 8001 | Vector database |
| LlamaIndex Service | 8002 | Hybrid RAG orchestration |
| GKG Service | 8003 | Code relationship graph |
| Indexer Worker | 8004 | Background indexing |
| Knowledge Graph MCP | 9005 | Core code search tools |
| LlamaIndex MCP | 9006 | Advanced search tools |
| GKG MCP | 9007 | Graph query tools |

## Architecture

```
Data Sources (GitHub, Jira, Confluence)
         │
         v
Indexer Worker :8004 ──> ChromaDB :8001 (vectors)
         │               GKG Service :8003 (relationships)
         │
         v
Agent Engine ──(MCP)──> Knowledge Graph MCP :9005
                        LlamaIndex MCP :9006
                        GKG MCP :9007
                              │
                              v
                        Knowledge Services
```

## Core vs Optional Services

| Service | Profile | Status |
|---------|---------|--------|
| Knowledge Graph | default | Core (always starts) |
| Knowledge Graph MCP | default | Core (always starts) |
| ChromaDB | default | Core (always starts) |
| LlamaIndex Service | knowledge | Optional |
| LlamaIndex MCP | knowledge | Optional |
| GKG Service | knowledge | Optional |
| GKG MCP | knowledge | Optional |
| Indexer Worker | knowledge | Optional |

## Prerequisites

- Core services running (Redis, PostgreSQL)
- Sufficient disk space for indexed data
- API credentials for data sources to index

## Start Knowledge Services

### Core Only (Default)

The core knowledge services start automatically:

```bash
make up
# Starts: knowledge-graph, knowledge-graph-mcp, chromadb
```

### With Optional Services

```bash
# Start all knowledge services
make knowledge-up

# Or use docker-compose profile
docker-compose --profile knowledge up -d

# Or start all services including knowledge
make up-full
```

## Environment Variables

### Knowledge Graph (Rust)

```bash
PORT=4000
GKG_DATA_DIR=/data/graphs
REPOS_DIR=/data/repos
REPOS_CONFIG=/app/config/repos.json
REPO_URLS=https://github.com/org/repo1,https://github.com/org/repo2
```

### ChromaDB

```bash
IS_PERSISTENT=TRUE
ANONYMIZED_TELEMETRY=FALSE
```

### LlamaIndex Service

```bash
CHROMADB_URL=http://chromadb:8000
GKG_URL=http://gkg-service:8003
REDIS_URL=redis://redis:6379/0
POSTGRES_URL=postgresql+asyncpg://agent:agent@postgres:5432/agent_system
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
LOG_LEVEL=INFO
```

### GKG Service

```bash
DATA_DIR=/data/gkg
REPOS_DIR=/data/repos
LOG_LEVEL=INFO
```

### Indexer Worker

```bash
CHROMADB_URL=http://chromadb:8000
GKG_URL=http://gkg-service:8003
REDIS_URL=redis://redis:6379/0
POSTGRES_URL=postgresql+asyncpg://agent:agent@postgres:5432/agent_system
GITHUB_TOKEN=${GITHUB_TOKEN}
JIRA_URL=${JIRA_URL}
JIRA_EMAIL=${JIRA_EMAIL}
JIRA_API_TOKEN=${JIRA_API_TOKEN}
CONFLUENCE_URL=${CONFLUENCE_URL}
CONFLUENCE_EMAIL=${CONFLUENCE_EMAIL}
CONFLUENCE_API_TOKEN=${CONFLUENCE_API_TOKEN}
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
REPOS_DIR=/data/repos
LOG_LEVEL=INFO
```

## Verify Installation

```bash
# Core services
curl http://localhost:4000/health    # Knowledge Graph
curl http://localhost:8001/api/v1/heartbeat  # ChromaDB
curl http://localhost:9005/health    # Knowledge Graph MCP

# Optional services (if enabled)
curl http://localhost:8002/health    # LlamaIndex Service
curl http://localhost:8003/health    # GKG Service
curl http://localhost:8004/health    # Indexer Worker
curl http://localhost:9006/health    # LlamaIndex MCP
curl http://localhost:9007/health    # GKG MCP
```

## Configure Repositories to Index

### Option 1: Environment Variable

```bash
# In .env
REPO_URLS=https://github.com/org/repo1,https://github.com/org/repo2
```

### Option 2: Configuration File

Create `knowledge-graph/config/repos.json`:

```json
{
  "repositories": [
    {
      "url": "https://github.com/org/repo1",
      "branch": "main"
    },
    {
      "url": "https://github.com/org/repo2",
      "branch": "develop"
    }
  ]
}
```

## Using Knowledge Features

### From Agent Engine

Agents automatically have access to knowledge tools via MCP. Available tools:

**Knowledge Graph MCP (9005)**:
- `search_code` - Search indexed code
- `find_references` - Find code references
- `get_call_graph` - Get function call graph
- `get_dependencies` - Get code dependencies

**LlamaIndex MCP (9006)** (optional):
- `knowledge_query` - Hybrid search across all sources
- `code_search` - Semantic code search
- `docs_search` - Documentation search
- `ticket_search` - Jira/issue search

**GKG MCP (9007)** (optional):
- `analyze_dependencies` - Analyze code dependencies
- `get_call_graph` - Get detailed call graphs
- `find_related_code` - Find related code entities

### Runtime Toggle

Enable/disable knowledge features at runtime:

```bash
# Enable
curl -X POST "http://localhost:8080/knowledge/toggle?enabled=true"

# Disable
curl -X POST "http://localhost:8080/knowledge/toggle?enabled=false"

# Check status
curl http://localhost:8080/knowledge/status
```

## Indexing Data

### Manual Indexing

```bash
# Index a GitHub repository
curl -X POST http://localhost:8004/index/github \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/org/repo"}'

# Index Jira project
curl -X POST http://localhost:8004/index/jira \
  -H "Content-Type: application/json" \
  -d '{"project_key": "PROJ"}'

# Index Confluence space
curl -X POST http://localhost:8004/index/confluence \
  -H "Content-Type: application/json" \
  -d '{"space_key": "DOCS"}'
```

### Check Indexing Status

```bash
curl http://localhost:8004/jobs
curl http://localhost:8004/jobs/{job_id}
```

## Logs

```bash
# View all knowledge service logs
make knowledge-logs

# Or individual services
docker-compose logs -f knowledge-graph
docker-compose logs -f chromadb
docker-compose --profile knowledge logs -f llamaindex-service
docker-compose --profile knowledge logs -f indexer-worker
```

## Stop Knowledge Services

```bash
# Stop optional knowledge services
make knowledge-down

# Stop all services
make down
```

## Troubleshooting

### ChromaDB not starting

1. Check disk space:
   ```bash
   df -h
   ```

2. Check volume permissions:
   ```bash
   docker volume inspect groote-ai_chroma_data
   ```

### Indexing fails

1. Check credentials for data sources
2. Verify network access to external APIs
3. Check indexer logs:
   ```bash
   docker-compose --profile knowledge logs indexer-worker
   ```

### Knowledge queries return empty results

1. Verify data has been indexed:
   ```bash
   curl http://localhost:8004/jobs
   ```

2. Check ChromaDB has collections:
   ```bash
   curl http://localhost:8001/api/v1/collections
   ```

### MCP connection errors

1. Verify services are running:
   ```bash
   docker-compose ps | grep mcp
   ```

2. Test health endpoints:
   ```bash
   curl http://localhost:9005/health
   curl http://localhost:9006/health
   curl http://localhost:9007/health
   ```

## Related Documentation

- [Main Setup Guide](../SETUP.md)
- [Architecture](ARCHITECTURE.md)
- [MCP Servers Setup](../mcp-servers/SETUP.md)
