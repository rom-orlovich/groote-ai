# indexer-worker - Features

Auto-generated on 2026-02-03

## Overview

Background worker service for indexing data sources (GitHub, Jira, Confluence) into vector and graph stores for knowledge retrieval. Polls Redis queue and processes indexing jobs.

## Features

### Job Processing [TESTED]

Poll and process indexing jobs from Redis queue

**Related Tests:**
- `test_job_updates_status_to_running`
- `test_successful_job_completes`
- `test_job_completion_published`

### Code Chunk Storage [TESTED]

Store code chunks to vector store with embeddings

**Related Tests:**
- `test_code_chunks_stored_to_vector_store`

### Document Chunk Storage [TESTED]

Store document chunks (Jira/Confluence) to appropriate collections

**Related Tests:**
- `test_document_chunks_stored_with_correct_collection`

### Disabled Source Handling [TESTED]

Skip disabled sources during indexing

**Related Tests:**
- `test_disabled_source_skipped`

### Graph Indexing [TESTED]

Index code to GKG graph store

**Related Tests:**
- `test_graph_indexing_when_enabled`
- `test_graph_indexing_skipped_when_disabled`

### Health Check [TESTED]

Check health of all components

**Related Tests:**
- `test_health_check_returns_all_components`

### GitHub Source Indexer [NEEDS TESTS]

Clone/pull repos, chunk code, generate embeddings

### Jira Source Indexer [NEEDS TESTS]

Fetch tickets via API, chunk content

### Confluence Source Indexer [NEEDS TESTS]

Fetch pages via API, chunk content

### Parallel Processing [NEEDS TESTS]

Process multiple repos in parallel

### Feature Flags [PARTIAL]

Control indexing behavior via flags

**Related Tests:**
- `test_graph_indexing_when_enabled`
- `test_graph_indexing_skipped_when_disabled`

## Test Coverage Summary

| Metric | Count |
|--------|-------|
| Total Features | 11 |
| Fully Tested | 6 |
| Partially Tested | 1 |
| Missing Tests | 4 |
| **Coverage** | **59.1%** |
