# indexer-worker - Flows

Auto-generated on 2026-02-03

## Process Flows

### Job Processing Flow [TESTED]

**Steps:**
1. Poll Redis queue for indexing jobs
2. Update job status to "running"
3. Fetch source configurations from Dashboard API
4. For each enabled source, create indexer
5. Index source to vector store
6. If GKG enabled, index code to graph store
7. Update job status to "completed"
8. Publish completion event

**Related Tests:**
- `test_job_updates_status_to_running`
- `test_successful_job_completes`
- `test_job_completion_published`

### Code Indexing Flow [TESTED]

**Steps:**
1. Clone/pull repository
2. Parse code files
3. Chunk code into segments
4. Generate embeddings for chunks
5. Store chunks in vector store
6. Index to GKG graph store (if enabled)

**Related Tests:**
- `test_code_chunks_stored_to_vector_store`
- `test_graph_indexing_when_enabled`

### Document Indexing Flow [TESTED]

**Steps:**
1. Fetch documents from source API (Jira/Confluence)
2. Parse document content
3. Chunk content into segments
4. Generate embeddings for chunks
5. Store chunks in appropriate collection
6. (jira_tickets or confluence_pages)

**Related Tests:**
- `test_document_chunks_stored_with_correct_collection`

### Source Filtering Flow [TESTED]

**Steps:**
1. Fetch source configurations
2. Filter by org_id
3. Check enabled flag
4. Skip disabled sources
5. Process only enabled sources

**Related Tests:**
- `test_disabled_source_skipped`

### Health Check Flow [TESTED]

**Steps:**
1. Check Redis queue connection
2. Check vector store connection
3. Check graph store connection
4. Return component status map

**Related Tests:**
- `test_health_check_returns_all_components`

## Flow Coverage Summary

| Metric | Count |
|--------|-------|
| Total Flows | 5 |
| Fully Tested | 5 |
| Partially Tested | 0 |
| Missing Tests | 0 |
| **Coverage** | **100.0%** |
