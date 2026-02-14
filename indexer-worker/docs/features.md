# Indexer Worker - Features

## Overview

Background worker service for indexing data sources (GitHub, Jira, Confluence) into vector and graph stores for knowledge retrieval. Polls Redis queue and processes indexing jobs.

## Core Features

### Job Processing

Poll and process indexing jobs from Redis queue.

**Job Operations:**
- Fetch jobs from queue
- Update job status
- Process source configurations
- Report completion

### GitHub Indexing

Index GitHub repositories into vector and graph stores.

**Indexed Content:**
- File contents
- Function definitions
- Class definitions
- Import relationships

**Processing:**
- Clone/pull repositories
- Chunk code files
- Generate embeddings
- Index to GKG for graph

### Jira Indexing

Index Jira tickets for semantic search.

**Indexed Content:**
- Ticket summaries
- Descriptions
- Comments
- Custom fields

**Processing:**
- Fetch via Jira API
- Parse rich text
- Chunk large descriptions
- Generate embeddings

### Confluence Indexing

Index Confluence pages for documentation search.

**Indexed Content:**
- Page content
- Page titles
- Space metadata
- Attachments metadata

**Processing:**
- Fetch via Confluence API
- Convert storage format to text
- Chunk pages
- Generate embeddings

### Embedding Generation

Generate vector embeddings for content chunks.

**Configuration:**
- Model: sentence-transformers/all-MiniLM-L6-v2
- Dimension: 384
- Batch processing

### Chunking Strategy

Split content into searchable chunks.

**Parameters:**
- Chunk size: 1500 characters
- Overlap: 200 characters
- Separator-aware splitting

### Parallel Processing

Process multiple repositories concurrently.

**Configuration:**
- Max parallel repos: 5 (configurable)
- Async processing
- Resource limiting

## Feature Flags

| Flag | Default | Description |
|------|---------|-------------|
| ENABLE_GKG_INDEXING | true | Index code to graph store |
| ENABLE_PARALLEL | true | Process repos in parallel |

## Redis Interface

| Queue/Channel | Direction | Description |
|---------------|-----------|-------------|
| `indexer:jobs` | BRPOP | Consume indexing jobs |
| `indexer:status:{job_id}` | SET | Job status updates |
| `indexer:completed:{org_id}` | PUBLISH | Job completion events |
